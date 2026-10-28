"""Check every quotation in the knowledge base against a file on disk.

    python data/verify_kb.py            check, print a table, exit 1 on failure
    python data/verify_kb.py --fix      also rewrite each locator to the line
                                        number where the quotation really is

Three sources are checked:

  report    lines 3260-3550 of the inquiry report, already in this repository
            (week3&4/sources/raw/...).  Locator = L<line>.
  beesley   Beesley's memoir, also already in the repository.
  tip       the Day 7 transcript extracts in sources/processed/.  Locator = Q<n>;
            the minutes' own question numbers, which cannot be recounted from a
            text file, so the check is that the quotation is really in the
            extract, and that the Q number printed beside it matches.

Why this file exists: a knowledge base that cannot be checked is just prose.
This one refuses to load a fact whose quotation is not findable, and the same
verifier runs inside the simulation's own self-check (code/check_sim.py).
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "sim"))

import paths  # noqa: E402

KB_PATH = HERE / "californian_kb.json"
TIP_EXTRACTS = ROOT / "sources" / "processed" / "tip-day7-extracts.txt"


def normalize(text):
    """Collapse whitespace; drop the markdown underscores Gutenberg added."""
    text = text.replace("_", "")
    return re.sub(r"\s+", " ", text).strip().lower()


def load_source(name):
    if name == "report":
        path = paths.require(paths.REPORT_NAME)
    elif name == "beesley":
        path = paths.require(paths.BEESLEY_NAME)
    elif name == "tip":
        path = TIP_EXTRACTS
        if not path.is_file():
            raise SystemExit("missing %s" % path)
    else:
        raise SystemExit("unknown source: %s" % name)
    return path, path.read_text(encoding="utf-8", errors="replace")


def find_line(text, quote):
    """Return the 1-based line number where `quote` starts, or None."""
    needle = normalize(quote)
    lines = text.splitlines()
    joined, offsets, cursor = [], [], 0
    for number, line in enumerate(lines, 1):
        piece = normalize(line)
        joined.append(piece)
        offsets.extend([number] * (len(piece) + 1))
        cursor += len(piece) + 1
    at = " ".join(joined).find(needle)
    if at < 0:
        return None
    return offsets[min(at, len(offsets) - 1)]


def find_q(text, quote):
    """For the transcript extracts: return the Q number on the matching line."""
    needle = normalize(quote)
    for line in text.splitlines():
        if needle and needle in normalize(line):
            match = re.match(r"\s*Q(\d+)", line)
            if match:
                return match.group(1)
    return None


def main(argv):
    fix = "--fix" in argv
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    cache, rows, failures = {}, [], 0

    for fact in kb["facts"]:
        source = fact["source"]
        if source not in cache:
            cache[source] = load_source(source)
        path, text = cache[source]
        quote = fact.get("quote") or ""
        if source == "tip":
            found = find_q(text, quote)
            expected = (fact.get("locator") or "").lstrip("Q")
            ok = found is not None and (not expected or expected == found)
            if fix and found:
                fact["locator"] = "Q" + found
        else:
            found = find_line(text, quote)
            expected = (fact.get("locator") or "").lstrip("L")
            ok = found is not None and (not expected or abs(int(expected) - int(found)) <= 4)
            if fix and found:
                fact["locator"] = "L" + str(found)
        shown = found if found is not None else "not found"
        if found is not None and not ok:
            shown = "%s  (locator said %s)" % (found, fact.get("locator"))
        rows.append((fact["id"], source, expected and (source == "tip" and "Q" + expected or "L" + expected) or "", shown, ok))
        if not ok:
            failures += 1

    width = max(len(r[0]) for r in rows)
    for fact_id, source, locator, found, ok in rows:
        print("  %-4s %-*s %-6s %-9s %s" % (
            "ok" if ok else "FAIL", width, fact_id, source, locator, found))
    print("\n%d facts, %d failed" % (len(rows), failures))

    if fix:
        KB_PATH.write_text(json.dumps(kb, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        print("locators rewritten in %s" % KB_PATH.name)

    # No fact of the future may sit in the character's memory.
    leaked = [f["id"] for f in kb["facts"]
              if f["kind"] == "evidenced" and "later" in f["who"] and "stone" in f["who"]]
    if leaked:
        print("LEAK: handed to the character: %s" % leaked)
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
