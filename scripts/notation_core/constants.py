"""Every threshold the core enforces. The ONLY place these numbers appear.

Command docs and checklists must refer to the band this core returns rather
than restating a number, so a change here cannot leave prose behind.
"""

# Routing bands, in characters of the proposed addition.
INLINE_MAX = 200        # at or under: inline is free, no friction
JUSTIFY_MAX = 600       # at or under: inline allowed with a recorded reason
                        # above JUSTIFY_MAX: must become a note plus a pointer

# File size targets, in characters.
GLOBAL_TARGET_CHARS = 40000     # the gated global CLAUDE.md
PROJECT_SILENT_CHARS = 20000    # project file: silent below this
PROJECT_ADVISORY_CHARS = 40000  # project file: advisory to here

# Predicted vs actual delta must agree exactly; see close().
RECONCILE_TOLERANCE = 0
