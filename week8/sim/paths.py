"""Where the sources live.

The simulation stands on two files that are already in this repository, in the
Week 3&4 folder:

    week3&4/sources/raw/british-inquiry-1912-loss-of-steamship-titanic.txt
    week3&4/sources/raw/beesley-1912-loss-of-ss-titanic.txt

Nothing is copied here.  The same text that the Week 3 database was built from
is read again, so the two weeks cannot drift apart.  If the folder is moved, set
WEEK8_SOURCES to the directory that holds the two files.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../week8
REPORT_NAME = "british-inquiry-1912-loss-of-steamship-titanic.txt"
BEESLEY_NAME = "beesley-1912-loss-of-ss-titanic.txt"


def candidates(name):
    yield from (
        Path(os.environ.get("WEEK8_SOURCES") or "") / name,
        ROOT.parent / "week3&4" / "sources" / "raw" / name,
        ROOT / "sources" / "raw" / name,
        ROOT.parent.parent / "week3&4" / "sources" / "raw" / name,
    )


def find(name):
    for path in candidates(name):
        if path.is_file():
            return path
    return None


def report():
    return find(REPORT_NAME)


def beesley():
    return find(BEESLEY_NAME)


def require(name):
    path = find(name)
    if path is None:
        raise SystemExit(
            "cannot find %s.\nSet WEEK8_SOURCES to the folder that holds it,\n"
            "or run from inside the course repository where week3&4/ sits next to week8/."
            % name)
    return path
