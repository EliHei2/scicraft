#!/usr/bin/env python3
"""Validate, review and apply an edits.json returned by read-only auditors.

Auditors never edit the artifact. They return an ordered list of proposals:

    [{"id": "A3", "file": "paper/method.tex", "old": "exact text", "new": "replacement",
      "why": "reason with source", "type": "surgical", "severity": "major"}, ...]

(a top-level {"edits": [...]} object is accepted too). This script is the one writer.

Checks, all reported at once, before anything is written:
  * every file exists under --root and does not escape it;
  * every `old` is at least --min-old characters and occurs exactly once in the file;
  * no two edits to the same file overlap;
  * the edits still apply one after another in the given order (each `old` found exactly once
    in the text as it stands after the earlier edits);
  * `type` is one of surgical, semantic, query; a query carries "new": null.

By default it is a dry run: it prints the verdict and writes a review sheet. With --apply it
backs the touched files up, applies the selected edits in order, re-reads each file to confirm
every `new` landed, and writes a change log.

Only `surgical` edits are applied unless --types says otherwise. `semantic` edits (they change
what the artifact means or how the code behaves) and `query` items go to the author.
An edit with new == old is recorded as a deliberate skip and changes nothing.

The review sheet flags, per edit: numbers that change, citation/reference/label keys that
change, a change in brace balance, banned words that the new text adds (--ban FILE, one word or
regex per line), and the length change.

Standard library only. Python 3.9 or later.

Examples:
  python3 apply_edits.py edits.json --root . --sheet SHEET.md          # dry run plus review sheet
  python3 apply_edits.py edits.json --root . --skip A4,A9 --apply      # apply surgical edits
  python3 apply_edits.py edits.json --root . --types surgical,semantic --apply
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TYPES = ("surgical", "semantic", "query")
NUM_RE = re.compile(r"(?<![A-Za-z_\d.])[-+]?\d[\d,]*(?:\.\d+)?(?:e[-+]?\d+)?%?", re.I)
KEY_RE = re.compile(
    r"\\(?:cite[a-z]*|[cC]?ref|eqref|autoref|label|input|include)\*?(?:\[[^\]]*\])*\{([^}]*)\}"
    r"|\[@([^\]\s;,]+)"
    r"|\]\(([^)\s]+)\)"
)


def load_edits(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("edits", data.get("findings"))
    if not isinstance(data, list):
        raise SystemExit(f"FAILED: {path} holds neither a list nor an object with an 'edits' list")
    out = []
    for i, e in enumerate(data):
        if not isinstance(e, dict):
            raise SystemExit(f"FAILED: entry {i} is not an object")
        e = dict(e)
        e.setdefault("id", f"E{i + 1}")
        e["id"] = str(e["id"])
        e["_index"] = i
        out.append(e)
    return out


def resolve(root: Path, name: str) -> Optional[Path]:
    p = (root / name).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return None
    return p


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def keys(s: str) -> List[str]:
    found = []
    for m in KEY_RE.finditer(s):
        for g in m.groups():
            if g:
                found.extend(k.strip() for k in g.split(","))
    return sorted(found)


def braces(s: str) -> int:
    s = s.replace("\\{", "").replace("\\}", "")
    return s.count("{") - s.count("}")


def flags_for(e: dict, ban: List[re.Pattern]) -> List[str]:
    old, new = e.get("old") or "", e.get("new")
    if new is None:
        return ["query: no replacement proposed"]
    f = []
    no, nn = sorted(NUM_RE.findall(old)), sorted(NUM_RE.findall(new))
    if no != nn:
        f.append(f"numbers change: {no} -> {nn}")
    ko, kn = keys(old), keys(new)
    if ko != kn:
        f.append(f"keys change: {ko} -> {kn}")
    if braces(old) != braces(new):
        f.append("brace balance changes")
    for rx in ban:
        if len(rx.findall(new)) > len(rx.findall(old)):
            f.append(f"adds banned pattern: {rx.pattern}")
    d = len(new) - len(old)
    if d:
        f.append(f"length {d:+d} chars")
    return f


def validate(edits: List[dict], root: Path, min_old: int,
             excluded: frozenset = frozenset()) -> Tuple[List[str], Dict[str, str]]:
    """Return (errors, original texts by file name). Simulates in-order application per file,
    over every edit except those the coordinator excluded with --skip or --only."""
    errors: List[str] = []
    texts: Dict[str, str] = {}
    spans: Dict[str, List[Tuple[int, int, str]]] = {}
    seen_ids = set()
    for e in edits:
        eid = e["id"]
        if eid in seen_ids:
            errors.append(f"{eid}: duplicate id")
        seen_ids.add(eid)
        for field in ("file", "old"):
            if not isinstance(e.get(field), str) or not e.get(field):
                errors.append(f"{eid}: missing or empty '{field}'")
        t = e.get("type", "surgical")
        if t not in TYPES:
            errors.append(f"{eid}: type '{t}' is not one of {', '.join(TYPES)}")
        if t == "query" and e.get("new") is not None:
            errors.append(f"{eid}: a query carries \"new\": null")
        if t != "query" and not isinstance(e.get("new"), str):
            errors.append(f"{eid}: 'new' must be a string (use type query with null for questions)")
        if not e.get("why"):
            errors.append(f"{eid}: missing 'why'")
        if not isinstance(e.get("file"), str) or not isinstance(e.get("old"), str):
            continue
        path = resolve(root, e["file"])
        if path is None:
            errors.append(f"{eid}: {e['file']} lies outside --root")
            continue
        if not path.is_file():
            errors.append(f"{eid}: file not found: {e['file']}")
            continue
        text = texts.setdefault(e["file"], path.read_text(encoding="utf-8"))
        old = e["old"]
        if len(old) < min_old:
            errors.append(f"{eid}: old is {len(old)} characters, below --min-old {min_old}; add context")
        n = text.count(old)
        if n != 1:
            errors.append(f"{eid}: old occurs {n} times in {e['file']} (must be exactly 1)")
            continue
        a = text.index(old)
        b = a + len(old)
        for (c, d, other) in spans.get(e["file"], []):
            if a < d and c < b:
                errors.append(f"{eid}: overlaps {other} in {e['file']} (lines {line_of(text, a)} and {line_of(text, c)})")
        spans.setdefault(e["file"], []).append((a, b, eid))
    # in-order application on copies, over every edit that carries a replacement and passed so far
    failed = {x.split(":", 1)[0] for x in errors}
    work = dict(texts)
    for e in edits:
        if e["id"] in failed or e["id"] in excluded or e.get("type", "surgical") == "query" or not isinstance(e.get("new"), str):
            continue
        name, old = e.get("file"), e.get("old")
        if name not in work or not old:
            continue
        n = work[name].count(old)
        if n != 1:
            errors.append(f"{e['id']}: after the earlier edits, old occurs {n} times in {name} (order conflict)")
            continue
        work[name] = work[name].replace(old, e["new"], 1)
    return errors, texts


def context(text: str, old: str, n: int = 1) -> str:
    a = text.find(old)
    if a < 0:
        return ""
    lines = text.splitlines()
    first = line_of(text, a) - 1
    last = line_of(text, a + len(old)) - 1
    lo, hi = max(0, first - n), min(len(lines), last + n + 1)
    return "\n".join(f"{i + 1:>5}  {lines[i]}" for i in range(lo, hi))


def write_sheet(path: Path, edits: List[dict], texts: Dict[str, str], ban: List[re.Pattern],
                selected: set, errors: List[str]) -> None:
    out = [f"# Review sheet for {len(edits)} proposals", ""]
    by_type: Dict[str, int] = {}
    for e in edits:
        by_type[e.get("type", "surgical")] = by_type.get(e.get("type", "surgical"), 0) + 1
    out.append("Counts by type: " + ", ".join(f"{k} {v}" for k, v in sorted(by_type.items())))
    out.append(f"Selected to apply: {len(selected)}. Validation errors: {len(errors)}.")
    out.append("")
    if errors:
        out += ["## Validation errors", ""] + [f"- {x}" for x in errors] + [""]
    for e in edits:
        t = e.get("type", "surgical")
        state = "APPLY" if e["id"] in selected else ("AUTHOR" if t in ("semantic", "query") else "HOLD")
        if isinstance(e.get("new"), str) and e.get("new") == e.get("old"):
            state = "SKIP (new == old)"
        out.append(f"## {e['id']} [{t}{', ' + e['severity'] if e.get('severity') else ''}] {state}")
        out.append(f"File: {e.get('file')}")
        out.append(f"Why: {e.get('why', '')}")
        fl = flags_for(e, ban)
        out.append("Flags: " + ("; ".join(fl) if fl else "none"))
        ctx = context(texts.get(e.get("file"), ""), e.get("old") or "")
        out += ["", "Context:", "```", ctx, "```", "Old:", "```", e.get("old") or "", "```"]
        if e.get("new") is not None:
            out += ["New:", "```", e["new"], "```"]
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edits", type=Path, help="edits.json from an auditor")
    ap.add_argument("--root", type=Path, default=Path("."), help="folder the 'file' fields are relative to")
    ap.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    ap.add_argument("--types", default="surgical", help="comma list of types to apply (default: surgical)")
    ap.add_argument("--skip", default="", help="comma list of edit ids to leave out")
    ap.add_argument("--only", default="", help="comma list of edit ids to apply, nothing else")
    ap.add_argument("--min-old", type=int, default=12, help="minimum length of an old string (default 12)")
    ap.add_argument("--sheet", type=Path, help="write a markdown review sheet here")
    ap.add_argument("--ban", type=Path, help="file of banned words or regexes, one per line")
    ap.add_argument("--log", type=Path, help="change log path (default: <edits>.changelog.md)")
    ap.add_argument("--backup-dir", type=Path, help="backup folder (default: <root>/.audit_backup/<time>)")
    a = ap.parse_args()

    edits = load_edits(a.edits)
    root = a.root
    ban = []
    if a.ban:
        for ln in a.ban.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                ban.append(re.compile(rf"\b{ln}\b" if re.fullmatch(r"[\w' -]+", ln) else ln, re.I))

    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    types = {s.strip() for s in a.types.split(",") if s.strip()}
    bad_types = types - set(TYPES) - {"query"}
    if bad_types:
        print(f"FAILED: unknown --types {sorted(bad_types)}")
        return 2
    ids = {e["id"] for e in edits}
    for s in (skip | only) - ids:
        print(f"FAILED: --skip/--only names unknown id {s}")
        return 2

    excluded = frozenset(i for i in ids if i in skip or (only and i not in only))
    errors, texts = validate(edits, root, a.min_old, excluded)
    selected = set()
    for e in edits:
        t = e.get("type", "surgical")
        if t == "query" or e["id"] in skip or (only and e["id"] not in only) or t not in types:
            continue
        if e.get("new") == e.get("old"):
            continue
        selected.add(e["id"])

    if a.sheet:
        write_sheet(a.sheet, edits, texts, ban, selected, errors)
        print(f"Review sheet: {a.sheet}")

    n_author = sum(1 for e in edits if e.get("type", "surgical") in ("semantic", "query"))
    n_noop = sum(1 for e in edits if isinstance(e.get("new"), str) and e.get("new") == e.get("old"))
    print(f"Checked {len(edits)} proposals over {len(texts)} files: {len(selected)} selected, "
          f"{n_author} for the author (semantic or query), {n_noop} deliberate skips.")
    if errors:
        print(f"FAILED: {len(errors)} validation errors; nothing was written.")
        for x in errors:
            print("  " + x)
        return 1
    print("Validation passed: every old occurs exactly once, no overlaps, all apply in order.")
    if not a.apply:
        print("Dry run. Re-run with --apply to write.")
        return 0

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = a.backup_dir or (root / ".audit_backup" / stamp)
    touched = sorted({e["file"] for e in edits if e["id"] in selected})
    for name in touched:
        dst = backup / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolve(root, name), dst)

    work = {name: texts[name] for name in touched}
    log = [f"# Change log {stamp}", "", f"Edits file: {a.edits}", f"Backup: {backup}", ""]
    for e in edits:
        t = e.get("type", "surgical")
        if e["id"] not in selected:
            why = ("skipped by --skip" if e["id"] in skip else
                   "deliberate skip (new == old)" if e.get("new") == e.get("old") else
                   "for the author" if t in ("semantic", "query") else "not selected")
            log.append(f"- {e['id']} NOT APPLIED ({why}): {e.get('file')}: {e.get('why', '')}")
            continue
        name = e["file"]
        if work[name].count(e["old"]) != 1:
            print(f"FAILED: {e['id']}: old no longer occurs exactly once once the selected edits before it "
                  f"are applied; nothing was written. Apply in smaller sets or fix the proposal.")
            return 1
        ln = line_of(work[name], work[name].index(e["old"]))
        work[name] = work[name].replace(e["old"], e["new"], 1)
        log.append(f"- {e['id']} APPLIED [{t}] {name}:{ln}: {e.get('why', '')}")
        log.append(f"  - old: {e['old']!r}")
        log.append(f"  - new: {e['new']!r}")
    for name in touched:
        resolve(root, name).write_text(work[name], encoding="utf-8")

    # post-check: re-read and confirm each new landed
    missing = []
    for e in edits:
        if e["id"] in selected and e["new"]:
            if e["new"] not in resolve(root, e["file"]).read_text(encoding="utf-8"):
                missing.append(e["id"])
    log_path = a.log or a.edits.with_suffix(".changelog.md")
    log_path.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"Applied {len(selected)} edits to {len(touched)} files. Backup: {backup}. Change log: {log_path}")
    if missing:
        print(f"FAILED: new text not found after writing for {', '.join(missing)}; restore from the backup.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
