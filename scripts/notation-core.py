#!/usr/bin/env python3
"""Entry point for the notation measurement core.

Locates the package from __file__ rather than sys.path[0]: sys.path[0] is the
script's directory only when invoked as a path, and it silently changes under
symlinks and `-m`, which makes a moved script fail in a confusing way.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from notation_core.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
