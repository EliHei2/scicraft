#!/usr/bin/env python3
"""Write the change log of an edit round from the exact edit pairs, and prove it by replaying them.

    python3 changelog.py edits.json --snapshot prebrush/ --edited source/ --out CHANGELOG.md
    python3 changelog.py edits.json --snapshot prebrush/ --out CHANGELOG.md --order main.tex,appendix.tex
    python3 changelog.py --self-test

edits.json is the list the edits were applied from (the same file the sibling latex-typesetting skill's
apply_edits.py takes):
    [{"id": "R2.1", "file": "main.tex", "old": "exact text", "new": "replacement"}, ...]
"file" is relative to --snapshot and --edited. Pairs are replayed in the order listed.

What it does:
  1. Replays every pair on the snapshot taken before the round (prebrush/), in order. Each "old" must occur
     exactly once in its file at the moment it is replayed, or the pair is reported.
  2. With --edited, compares each replayed file with the edited file byte for byte and prints the first line
     that differs. In the source work this check caught a trailing-whitespace mismatch, so the change log
     a co-author applies by hand reproduces exactly the files that were built.
  3. Writes the change log: files in --order (default: order of first appearance), edits in reading order inside
     each file, which is page order. For each edit: the find and replace pair for Overleaf and the old and new
     paragraph for a shared document.

Standard library only. Exit code 1 when a pair does not replay or a file differs.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def boundary(line: str) -> bool:
    """A blank line, or a TeX structure line (\\section, \\begin, \\end, \\item ...), ends a paragraph."""
    s = line.strip()
    return not s or (s.startswith("\\") and not s.startswith(("\\rev", "\\textbf", "\\emph", "\\cite")))


def paragraph(text: str, start: int, end: int) -> str:
    """The paragraph that contains text[start:end]: lines out to the nearest blank or structure line."""
    lines = text.split("\n")
    first = text.count("\n", 0, start)
    last = text.count("\n", 0, max(start, end - 1))
    while first > 0 and not boundary(lines[first - 1]):
        first -= 1
    while last + 1 < len(lines) and not boundary(lines[last + 1]):
        last += 1
    return "\n".join(lines[first:last + 1])


def fence(s: str) -> str:
    ticks = "```"
    while ticks in s:
        ticks += "`"
    return f"{ticks}\n{s}\n{ticks}"


def replay(edits: list, snapshot: Path):
    """Apply the pairs in order. Returns (texts by file, records, faults)."""
    texts, records, faults = {}, [], []
    for n, e in enumerate(edits, 1):
        f = e["file"]
        eid = e.get("id", f"#{n}")
        if f not in texts:
            p = snapshot / f
            if not p.is_file():
                faults.append(f"{eid}: {f} is not in the snapshot {snapshot}")
                texts[f] = None
                continue
            texts[f] = p.read_bytes().decode("utf-8")
        t = texts[f]
        if t is None:
            continue
        old, new = e["old"], e["new"]
        k = t.count(old)
        if k != 1:
            faults.append(f"{eid}: {f}: 'old' occurs {k} times at its turn (must be exactly once): {old[:70]!r}")
            continue
        i = t.index(old)
        before_par = paragraph(t, i, i + len(old))
        t2 = t[:i] + new + t[i + len(old):]
        after_par = paragraph(t2, i, i + len(new))
        records.append({"id": eid, "file": f, "line": t.count("\n", 0, i) + 1, "pos": i, "seq": n,
                        "old": old, "new": new, "old_par": before_par, "new_par": after_par})
        # positions of earlier records in this file after i move by the length change
        delta = len(new) - len(old)
        for r in records[:-1]:
            if r["file"] == f and r["pos"] > i:
                r["pos"] += delta
        texts[f] = t2
    return texts, records, faults


def compare(texts: dict, edited: Path) -> list:
    faults = []
    for f, t in texts.items():
        if t is None:
            continue
        p = edited / f
        if not p.is_file():
            faults.append(f"{f}: not found under {edited}")
            continue
        got = p.read_bytes()
        want = t.encode("utf-8")
        if got == want:
            print(f"replay matches {p} byte for byte")
            continue
        gl, wl = got.decode("utf-8", "replace").split("\n"), t.split("\n")
        for ln, (x, y) in enumerate(zip(wl, gl), 1):
            if x != y:
                faults.append(f"{f}: replay differs from the edited file at line {ln}: replay {x[-60:]!r}, edited {y[-60:]!r}")
                break
        else:
            faults.append(f"{f}: replay and edited file differ in length ({len(wl)} against {len(gl)} lines)")
    return faults


def write_log(records: list, order: list, out: Path, title: str) -> None:
    files = order + [r["file"] for r in records if r["file"] not in order]
    files = list(dict.fromkeys(f for f in files if any(r["file"] == f for r in records)))
    lines = [f"# {title}", "", f"{len(records)} edits in {len(files)} files, in page order. Each pair below occurs exactly "
             "once in the file at its turn; apply them in the order given.", ""]
    for f in files:
        rs = sorted((r for r in records if r["file"] == f), key=lambda r: (r["pos"], r["seq"]))
        lines += [f"## {f} ({len(rs)} edits)", ""]
        for r in rs:
            lines += [f"### {r['id']} (line {r['line']} of the pre-edit file)", "",
                      "Find (Overleaf):", "", fence(r["old"]), "", "Replace with:", "", fence(r["new"]), ""]
            if r["old_par"] != r["old"] or r["new_par"] != r["new"]:
                lines += ["Old paragraph (shared document):", "", fence(r["old_par"]), "",
                          "New paragraph:", "", fence(r["new_par"]), ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def run(edits_path: Path, snapshot: Path, edited, out, order: list, title: str) -> int:
    edits = json.loads(edits_path.read_text(encoding="utf-8"))
    if not isinstance(edits, list) or not all({"file", "old", "new"} <= set(e) for e in edits):
        print("edits file must be a list of objects with file, old and new")
        return 1
    texts, records, faults = replay(edits, snapshot)
    print(f"replayed {len(records)} of {len(edits)} pairs on {snapshot}")
    if edited is not None:
        faults += compare(texts, edited)
    if out is not None:
        write_log(records, order, out, title)
        print(f"wrote {out}")
    for f in faults:
        print("FAULT", f)
    print("change log verified" if not faults else f"{len(faults)} faults; do not send this change log")
    return 1 if faults else 0


def self_test() -> int:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "pre").mkdir()
        (d / "post").mkdir()
        main = "Intro text.\n\nWe compare five methods.\nThe score rises.\n\nEnd.\n"
        app = "Appendix A.\n\nTable rows at 10k steps.\n"
        (d / "pre/main.tex").write_text(main)
        (d / "pre/app.tex").write_text(app)
        edits = [{"id": "E2", "file": "main.tex", "old": "The score rises.", "new": "\\rev{The score rises by 0.4.}"},
                 {"id": "E1", "file": "main.tex", "old": "five methods", "new": "\\rev{six} methods"},
                 {"id": "A1", "file": "app.tex", "old": "10k steps", "new": "30k steps"}]
        (d / "edits.json").write_text(json.dumps(edits))
        good_main = "Intro text.\n\nWe compare \\rev{six} methods.\n\\rev{The score rises by 0.4.}\n\nEnd.\n"
        (d / "post/main.tex").write_text(good_main)
        (d / "post/app.tex").write_text("Appendix A.\n\nTable rows at 30k steps.\n")
        ok = run(d / "edits.json", d / "pre", d / "post", d / "CHANGELOG.md", ["main.tex"], "Change log") == 0
        log = (d / "CHANGELOG.md").read_text()
        ok &= log.index("### E1") < log.index("### E2") < log.index("### A1")      # page order, file order
        (d / "post/main.tex").write_text(good_main.replace("0.4.}\n", "0.4.} \n"))  # trailing space
        ok &= run(d / "edits.json", d / "pre", d / "post", None, [], "x") == 1
        edits.append({"id": "BAD", "file": "main.tex", "old": "methods", "new": "models"})
        (d / "post/main.tex").write_text(good_main)
        edits.insert(0, {"id": "DUP", "file": "app.tex", "old": "A", "new": "B"})  # "A" occurs twice
        (d / "edits.json").write_text(json.dumps(edits))
        ok &= run(d / "edits.json", d / "pre", None, None, [], "x") == 1
    print("self-test passed" if ok else "self-test FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("edits", nargs="?", help="edits.json: list of {id, file, old, new}")
    ap.add_argument("--snapshot", help="folder with the files as they were before the round")
    ap.add_argument("--edited", help="folder with the edited files; compared byte for byte with the replay")
    ap.add_argument("--out", help="write the change log here (Markdown)")
    ap.add_argument("--order", default="", help="comma-separated file order for the log, e.g. main.tex,appendix.tex")
    ap.add_argument("--title", default="Change log", help="heading of the log")
    ap.add_argument("--self-test", action="store_true", help="run on synthetic files and exit")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.edits or not a.snapshot:
        ap.error("edits.json and --snapshot are required")
    order = [x.strip() for x in a.order.split(",") if x.strip()]
    return run(Path(a.edits), Path(a.snapshot), Path(a.edited) if a.edited else None,
               Path(a.out) if a.out else None, order, a.title)


if __name__ == "__main__":
    sys.exit(main())
