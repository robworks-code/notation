#!/usr/bin/env python3
"""The whole-branch review's seam defects, one fixture per finding.

These are the failures no single-component test could see: each one needed two
components, or a component and a command doc, to be wrong together. Every case
below is the reviewer's own reproduction, run through the shipped CLI.

Isolation: every case runs with HOME and NOTATION_RUNS_DIR pointed at a temp
directory, so the real ~/.claude is never read or written.

Run: python3 tests/test_core_seams.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import check, report

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY = os.path.join(REPO, "scripts", "notation-core.py")


def run(args, env):
    e = dict(os.environ)
    e.update(env)
    p = subprocess.Popen([sys.executable, ENTRY] + args,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    out, err = p.communicate()
    return p.returncode, out.decode("utf-8"), err.decode("utf-8")


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def fresh_home(root, name):
    """-> (home, env) with a global CLAUDE.md already in place."""
    home = os.path.join(root, name)
    write(os.path.join(home, ".claude", "CLAUDE.md"), "# global\n")
    return home, {"HOME": home,
                  "NOTATION_RUNS_DIR": os.path.join(home, ".claude", "notation-runs")}


with tempfile.TemporaryDirectory() as root:

    # ------------------------------------------------------------------ C1
    print("\ncase C1: a second open on a live run id is refused, not silently reset")
    home, env = fresh_home(root, "c1")
    target = os.path.join(home, ".claude", "CLAUDE.md")

    run(["open", "--target", target, "--run-id", "shared",
         "--now", "2026-08-04T00:00:00Z"], env)
    run(["price-record", "--run-id", "shared", "--delta", "500",
         "--bucket", "global", "--target", target], env)

    rc_reopen, out_reopen, err_reopen = run(
        ["open", "--target", target, "--run-id", "shared",
         "--now", "2026-08-04T00:01:00Z"], env)
    check("re-opening an existing run id exits 2", rc_reopen == 2,
          info="rc={}".format(rc_reopen),
          detail="it used to exit 0 and write a fresh, empty ledger")
    check("and says why on stderr", "already has a ledger" in err_reopen,
          detail=repr(err_reopen[:200]))
    check("and emits no JSON that could read as a successful open",
          out_reopen == "", detail=repr(out_reopen[:120]))

    rc_gate, out_gate, _ = run(["gate", "--run-id", "shared"], env)
    verdict = json.loads(out_gate)
    check("the first run's proposal survived the attempted clobber",
          verdict["gated_net"] == 500, info="gated_net={}".format(verdict["gated_net"]))
    check("so the gate still refuses (exit 1), instead of reporting clean",
          rc_gate == 1 and verdict["refused"] is True,
          info="rc={}".format(rc_gate),
          detail="this is the defeated whole-run budget check")

    # ------------------------------------------------------------------ C2
    print("\ncase C2: a symlinked global CLAUDE.md keeps global scope")
    home2 = os.path.join(root, "c2")
    dotfiles = os.path.join(home2, "dotfiles")
    write(os.path.join(dotfiles, "CLAUDE.md"), "# from dotfiles\n" + "x" * 500)
    os.makedirs(os.path.join(home2, ".claude"))
    link = os.path.join(home2, ".claude", "CLAUDE.md")
    os.symlink(os.path.join(dotfiles, "CLAUDE.md"), link)
    env2 = {"HOME": home2,
            "NOTATION_RUNS_DIR": os.path.join(home2, ".claude", "notation-runs")}

    rc_m, out_m, _ = run(["measure", link], env2)
    m = json.loads(out_m)
    check("the symlinked global file resolves to bucket 'global'",
          m["bucket"] == "global", info=m["bucket"],
          detail="realpath used to land it outside ~ and call it 'project'")
    check("and is therefore gated", m["gated"] is True)
    check("while still measuring the real content (no false zero)",
          m["chars"] == 516, info="{} chars".format(m["chars"]))

    added = os.path.join(root, "added.txt")
    write(added, "y" * 300)
    _, out_pr, _ = run(["price", "--added", added, "--target", link], env2)
    priced = json.loads(out_pr)
    check("a proposal against it prices as gated", priced["gated"] is True)

    run(["open", "--target", link, "--run-id", "c2run",
         "--now", "2026-08-04T00:00:00Z"], env2)
    run(["price-record", "--run-id", "c2run", "--delta", str(priced["delta"]),
         "--bucket", priced["bucket"], "--target", priced["target"]], env2)
    rc_g2, out_g2, _ = run(["gate", "--run-id", "c2run"], env2)
    check("and the whole-run gate refuses the growth", rc_g2 == 1,
          info="rc={}, gated_net={}".format(rc_g2, json.loads(out_g2)["gated_net"]),
          detail="with the old resolution no amount of growth could be refused")

    print("\ncase C2b: fixing the symlink must not open a traversal hole")
    escape = os.path.join(home2, ".claude", "..", "elsewhere", "CLAUDE.md")
    write(os.path.join(home2, "elsewhere", "CLAUDE.md"), "# not the global file\n")
    rc_e, out_e, _ = run(["measure", escape], env2)
    check("a path that climbs out of .claude is not global",
          json.loads(out_e)["bucket"] == "project",
          info=json.loads(out_e)["bucket"])
    rc_n, out_n, _ = run(
        ["measure", os.path.join(home2, ".claude", "notes", "railway.md")], env2)
    check("and the other buckets still resolve",
          json.loads(out_n)["bucket"] == "notes", info=json.loads(out_n)["bucket"])

    # ------------------------------------------------------------------ I3
    print("\ncase I3: a relocation's note target is reconciled, not ignored")
    home3, env3 = fresh_home(root, "i3")
    g3 = os.path.join(home3, ".claude", "CLAUDE.md")
    note3 = os.path.join(home3, ".claude", "notes", "railway.md")
    write(g3, "# global\n" + "x" * 900)
    write(note3, "# Railway\n")

    run(["open", "--target", g3, "--run-id", "i3run",
         "--now", "2026-08-04T00:00:00Z"], env3)
    rc_unreg, out_unreg, err_unreg = run(
        ["price-record", "--run-id", "i3run", "--delta", "900",
         "--bucket", "notes", "--target", note3], env3)
    check("pricing against an unregistered file is refused (exit 2)",
          rc_unreg == 2, info="rc={}".format(rc_unreg),
          detail="this is what makes 'register every target' structural")
    check("and the refusal names the register command",
          "register --run-id" in err_unreg, detail=repr(err_unreg[:240]))
    check("and records nothing", out_unreg == "", detail=repr(out_unreg[:120]))

    rc_reg, out_reg, _ = run(
        ["register", "--run-id", "i3run", "--target", note3], env3)
    check("register adds the file to the run in progress", rc_reg == 0,
          info="rc={}".format(rc_reg))
    check("and reports it as newly registered",
          json.loads(out_reg)["registered"][0]["registered"] is True)

    run(["price-record", "--run-id", "i3run", "--delta", "-900",
         "--bucket", "global", "--target", g3], env3)
    run(["price-record", "--run-id", "i3run", "--delta", "900",
         "--bucket", "notes", "--target", note3], env3)

    # Apply the relocation HALF-WAY: the removal lands, the note append does not.
    write(g3, "# global\n")
    rc_close, out_close, err_close = run(["close", "--run-id", "i3run"], env3)
    rep = json.loads(out_close)
    check("close does NOT report success when the note append silently failed",
          rep["reconciled"] is False and rc_close == 1,
          info="rc={}, reconciled={}".format(rc_close, rep["reconciled"]),
          detail="the reviewer's run reported reconciled:true, findings:[]")
    check("and it names the note file, not just the global one",
          any(note3 in f for f in rep["findings"]),
          info="{}".format(rep["findings"]))

    # ------------------------------------------------------------------ I4
    print("\ncase I4: a target spelled differently is still the same target")
    home4, env4 = fresh_home(root, "i4")
    g4 = os.path.join(home4, ".claude", "CLAUDE.md")
    write(g4, "x" * 100)
    run(["open", "--target", g4, "--run-id", "i4run",
         "--now", "2026-08-04T00:00:00Z"], env4)
    # The literal string a shell hands over when the path was quoted: the tilde
    # was never expanded, and price-record used to store it raw.
    rc_rec, _, err_rec = run(
        ["price-record", "--run-id", "i4run", "--delta", "50",
         "--bucket", "global", "--target", "~/.claude/CLAUDE.md"], env4)
    check("a tilde-spelled target records against the opened run", rc_rec == 0,
          info="rc={}".format(rc_rec), detail=err_rec.strip())
    write(g4, "x" * 150)                    # the CORRECT 50-char edit
    rc_c4, out_c4, err_c4 = run(["close", "--run-id", "i4run"], env4)
    check("a correctly applied edit reconciles (exit 0)", rc_c4 == 0,
          info="rc={}".format(rc_c4), detail=err_c4.strip())
    check("with no bogus 'the edit did not land as drafted' finding",
          json.loads(out_c4)["findings"] == [],
          detail="{}".format(json.loads(out_c4)["findings"]))

    # The same file named relatively, from its own directory.
    home5, env5 = fresh_home(root, "i5rel")
    g5 = os.path.join(home5, ".claude", "CLAUDE.md")
    write(g5, "x" * 100)
    cwd = os.path.join(home5, ".claude")
    e_rel = dict(os.environ)
    e_rel.update(env5)
    p = subprocess.Popen(
        [sys.executable, ENTRY, "open", "--target", "./CLAUDE.md",
         "--run-id", "relrun", "--now", "2026-08-04T00:00:00Z"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e_rel, cwd=cwd)
    p.communicate()
    rc_rel, _, err_rel = run(
        ["price-record", "--run-id", "relrun", "--delta", "50",
         "--bucket", "global", "--target", g5], env5)
    check("a relative --target at open matches an absolute one at price-record",
          rc_rel == 0, info="rc={}".format(rc_rel), detail=err_rel.strip())

    # ------------------------------------------------------------------ I5
    print("\ncase I5: the concurrent case reports drift as undetermined, not false")
    home6, env6 = fresh_home(root, "i5")
    g6 = os.path.join(home6, ".claude", "CLAUDE.md")
    write(g6, "x" * 1000)
    run(["open", "--target", g6, "--run-id", "i5run",
         "--now", "2026-08-04T00:00:00Z"], env6)
    run(["price-record", "--run-id", "i5run", "--delta", "50",
         "--bucket", "global", "--target", g6], env6)
    write(g6, "x" * 1050 + "z" * 30)        # our 50 landed, another session added 30
    rc_c6, out_c6, err_c6 = run(["close", "--run-id", "i5run"], env6)
    rep6 = json.loads(out_c6)
    f6 = rep6["files"][0]
    check("drift is not reported as a bare false", f6["drift"] == "undetermined",
          info=f6["drift"],
          detail="the old boolean said false, which reads as 'no drift happened'")
    check("no boolean drift field remains to be misread",
          "drifted" not in f6)
    check("the undetermined file is listed for the caller",
          rep6["drift_undetermined"] == [f6["path"]])
    check("stderr says outside edits could not be ruled out",
          "could NOT be ruled out" in err_c6, detail=repr(err_c6[:240]))
    check("and 'reconciled' carries its own definition, so it cannot be over-read",
          "not cleared" in rep6["reconciled_means"])

    # ------------------------------------------------------------------ M6
    print("\ncase M6: an unreadable note is visible, not merely unmatched")
    home7, env7 = fresh_home(root, "m6")
    notes7 = os.path.join(home7, ".claude", "notes")
    os.makedirs(notes7)
    write(os.path.join(notes7, "good.md"), "# Railway\n## Buckets\n")
    with open(os.path.join(notes7, "broken.md"), "wb") as fh:
        fh.write(b"# Railway buckets\n\xff\xfe not utf-8\n")
    text7 = os.path.join(root, "m6-text.txt")
    write(text7, "railway bucket ttl at create time")
    rc_r7, out_r7, err_r7 = run(
        ["route", "--text-file", text7, "--target",
         os.path.join(home7, ".claude", "CLAUDE.md"), "--notes-dir", notes7], env7)
    r7 = json.loads(out_r7)
    check("route still exits 0 and ranks the readable notes", rc_r7 == 0,
          info="rc={}".format(rc_r7))
    check("the unreadable note is reported as unreadable",
          [x["path"] for x in r7["unreadable"]] == [os.path.join(notes7, "broken.md")],
          info="{}".format(r7["unreadable"]))
    check("with the decoding error named",
          bool(r7["unreadable"]) and "UnicodeDecodeError" in r7["unreadable"][0]["error"])
    check("it is still counted in notes_searched, so the denominator stays honest",
          r7["notes_searched"] == 2, info="{}".format(r7["notes_searched"]))
    check("and the session is told on stderr",
          "could not be read" in err_r7, detail=repr(err_r7[:240]))

    # ------------------------------------------------------------------ M7
    print("\ncase M7: `closed` means something - a second close is refused")
    home8, env8 = fresh_home(root, "m7")
    g8 = os.path.join(home8, ".claude", "CLAUDE.md")
    write(g8, "x" * 100)
    run(["open", "--target", g8, "--run-id", "m7run",
         "--now", "2026-08-04T00:00:00Z"], env8)
    run(["price-record", "--run-id", "m7run", "--delta", "0",
         "--bucket", "global", "--target", g8], env8)
    rc_first, _, _ = run(["close", "--run-id", "m7run"], env8)
    check("the first close succeeds", rc_first == 0, info="rc={}".format(rc_first))
    ledger_path = os.path.join(env8["NOTATION_RUNS_DIR"], "m7run.json")
    with open(ledger_path, encoding="utf-8") as fh:
        check("and the ledger records closed: true", json.load(fh)["closed"] is True,
              detail="the field used to be written false and never updated")
    rc_second, out_second, err_second = run(["close", "--run-id", "m7run"], env8)
    check("a second close exits 2 rather than repeating the first report",
          rc_second == 2, info="rc={}".format(rc_second))
    check("and says the run was already closed",
          "already closed" in err_second, detail=repr(err_second[:200]))
    rc_late, _, err_late = run(
        ["price-record", "--run-id", "m7run", "--delta", "10",
         "--bucket", "global", "--target", g8], env8)
    check("a closed run takes no further proposals", rc_late == 2,
          info="rc={}".format(rc_late), detail=repr(err_late[:200]))

    # ------------------------------------------- the documented sequence itself
    print("\ncase docs: the run-id recipe in each command doc actually runs")
    RUN_ID_RECIPE = re.compile(
        r"```sh\n(printf 'run id: [^\n]*\n(?:[^\n]*\n)*?)```", re.MULTILINE)
    for doc in ("notate.md", "notate-all.md"):
        text = open(os.path.join(REPO, "commands", doc), encoding="utf-8").read()
        found = RUN_ID_RECIPE.search(text)
        check("{} carries a run-id minting recipe".format(doc), found is not None)
        if not found:
            continue
        ids = []
        for _ in range(2):
            proc = subprocess.Popen(["/bin/sh", "-c", found.group(1)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            o, e = proc.communicate()
            ids.append((proc.returncode, o.decode("utf-8").strip(), e.decode("utf-8")))
        check("{}'s recipe runs clean".format(doc),
              all(rc == 0 for rc, _, _ in ids),
              detail="{}".format([e for _, _, e in ids]))
        minted = [o.replace("run id: ", "") for _, o, _ in ids]
        check("{} mints a non-empty id".format(doc), all(minted) and " " not in minted[0],
              info=minted[0])
        check("{} mints a DIFFERENT id each time (no collision)".format(doc),
              minted[0] != minted[1], info="{} vs {}".format(*minted))

    print("\ncase docs: the whole documented sequence composes, end to end")
    # open (two targets) -> register -> route -> price -> price-record -> gate
    # -> apply -> close, using only the flags the docs show.
    home9, env9 = fresh_home(root, "docseq")
    g9 = os.path.join(home9, ".claude", "CLAUDE.md")
    n9 = os.path.join(home9, ".claude", "notes", "railway.md")
    extra9 = os.path.join(home9, ".claude", "notes", "pytest.md")
    body = "### Railway\n" + ("Railway bucket TTL detail. " * 40) + "\n"
    write(g9, "# CLAUDE.md\n\n" + body)
    write(n9, "# Railway\n\n## Auth\n")
    write(extra9, "# Pytest\n")
    run_id = "notate-20260804T171533Z-9f3a1c2b"
    seq_rc = []
    seq_rc.append(run(["open", "--target", g9, "--target", n9,
                       "--run-id", run_id, "--now", "2026-08-04T00:00:00Z"], env9)[0])
    seq_rc.append(run(["register", "--run-id", run_id, "--target", extra9], env9)[0])
    proposal = os.path.join(root, "docseq-proposal.txt")
    pointer = os.path.join(root, "docseq-pointer.txt")
    write(proposal, body)
    write(pointer, "### Railway\nDetail: `notes/railway.md`\n")
    rc_route9, out_route9, _ = run(
        ["route", "--text-file", proposal, "--target", g9,
         "--notes-dir", os.path.dirname(n9)], env9)
    seq_rc.append(rc_route9)
    rc_price9, out_price9, _ = run(
        ["price", "--removed", proposal, "--added", pointer, "--target", g9], env9)
    seq_rc.append(rc_price9)
    priced9 = json.loads(out_price9)
    seq_rc.append(run(["price-record", "--run-id", run_id,
                       "--delta", str(priced9["delta"]),
                       "--bucket", priced9["bucket"],
                       "--target", priced9["target"]], env9)[0])
    note_added = os.path.join(root, "docseq-note-added.txt")
    write(note_added, body)
    rc_price_n, out_price_n, _ = run(
        ["price", "--added", note_added, "--target", n9], env9)
    seq_rc.append(rc_price_n)
    priced_n = json.loads(out_price_n)
    seq_rc.append(run(["price-record", "--run-id", run_id,
                       "--delta", str(priced_n["delta"]),
                       "--bucket", priced_n["bucket"],
                       "--target", priced_n["target"]], env9)[0])
    rc_gate9, _, _ = run(["gate", "--run-id", run_id], env9)
    seq_rc.append(rc_gate9)
    check("every documented step up to the gate exits 0",
          all(rc == 0 for rc in seq_rc), info="{}".format(seq_rc))

    # Apply BOTH halves of the relocation, as the doc's item 4 requires.
    write(g9, "# CLAUDE.md\n\n" + open(pointer, encoding="utf-8").read())
    with open(n9, "a", encoding="utf-8") as fh:
        fh.write(body)
    rc_close9, out_close9, err_close9 = run(["close", "--run-id", run_id], env9)
    rep9 = json.loads(out_close9)
    check("and the fully applied relocation reconciles", rc_close9 == 0,
          info="rc={}, findings={}".format(rc_close9, rep9["findings"]),
          detail=err_close9.strip())
    check("with all three registered files re-measured", len(rep9["files"]) == 3,
          info="{}".format(len(rep9["files"])))
    check("the untouched extra target is proven undrifted",
          [f["drift"] for f in rep9["files"] if f["path"] == extra9] == ["none"])

    # ------------------------------------------------------------- isolation
    print("\ncase: the real ~/.claude was never a candidate")
    real_runs = os.path.join(os.path.expanduser("~"), ".claude", "notation-runs")
    check("no ledger directory exists in the real home",
          not os.path.exists(real_runs),
          detail="{} exists - a case leaked out of its temp HOME".format(real_runs))

report("core-seams")
