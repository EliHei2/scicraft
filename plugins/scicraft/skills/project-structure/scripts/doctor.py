#!/usr/bin/env python3
"""Check the governing documents of a research project. Reads only; writes nothing.

Run it on any project folder, whether the scaffold made it or it grew by hand:

  python3 doctor.py <project>                  report, exit 1 on a failure
  python3 doctor.py <project> --strict         warnings fail too (use before handing over)
  python3 doctor.py <project> --json           the findings as JSON
  python3 doctor.py --self-test                build two small projects in a temp folder and check both

What it checks:
  presence     the index file, README.md, NARRATIVE.md, GOALS.md, GUARDRAILS.md, GUIDELINES.md
  index        at most 500 words outside code blocks; names the four governing documents; holds no status section;
               every guardrail id it lists exists in GUARDRAILS.md
  ownership    README.md has a table of which file owns which question and names the four governing documents
  narrative    a block on what a win looks like and a block on what the narrative never says; not empty
  goals        sections for long goals, the short goal and non-goals; a due date on the short goal, and how long
               it has been past; one to five deliverables, each with "Check:"; "Test:" on each long goal; a date on
               every SUPERSEDED line
  guardrails   rule ids are unique; each rule has "Prevents:" and "Check:"; each rule is in the enforcement
               table; RETIRED lines carry a date; how many rules rest on convention alone
  guidelines   a line "The bar:" and a section "Definition of done"
  kb           INDEX.md (or llms.txt) lists every entry and names no missing file; each entry has its summary
               line, Status and Updated; archived entries name their successor
  reach        every .md at the root and under docs/, guidelines/, ops/ and experiments/ is named in a document
               that can be reached from README.md or the index file
  placeholders bracketed template text left unfilled (a citation in square brackets is counted too)

Folders never entered: .git, data, results, scratch, _attic, archive, sources, virtual environments.
Standard library only; Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
from pathlib import Path

GOVERNING = ["NARRATIVE.md", "GOALS.md", "GUARDRAILS.md", "GUIDELINES.md"]
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", "data", "results", "scratch", "_attic",
        "archive", "sources", ".claude", "site-packages", "dist", "build"}
DOC_DIRS = ["docs", "guidelines", "ops", "experiments"]
KB_DIRS = ["docs/kb", "knowledge-base", "docs/knowledge-base", "kb"]
DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# A rule is defined where its id is followed by punctuation: "- **G7. Never", "- **G7 - Never", "## G7: ...".
# A line such as "- **G7 is enforced by ..." mentions a rule and defines nothing.
RULE = re.compile(r"^\s*(?:[-*]\s+\*\*|#{2,4}\s+)([A-Z]{1,2}\d+[a-z]?)(?:\*\*)?\s*(?:[.:\u2014\u2013]|-\s|\*\*)")
MARK = re.compile(r"^\s*(?:[-*]\s|#{1,6}\s|\|)")  # a list item, a heading or a table row: where a mark sits
PLACEHOLDER = re.compile(r"\[(?![ xX]\])(?!RUN\]|DOC\]|U\]|VERIFY\]|AUTHOR ACTION\])[^\]\[\n]{12,}\](?!\()"
                         r"|\[YYYY-MM-DD\]")


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, where, msg):
        self.items.append({"level": level, "where": where, "message": msg})

    def fail(self, where, msg):
        self.add("FAIL", where, msg)

    def warn(self, where, msg):
        self.add("WARN", where, msg)

    def info(self, where, msg):
        self.add("INFO", where, msg)

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def prose(text: str) -> str:
    """Text with fenced blocks and inline code removed."""
    text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", " ", text)
    return re.sub(r"`[^`\n]*`", " ", text)


def sections(text: str, level: int = 2):
    """[(heading text, body, line number)] for headings of the given level."""
    out, cur, body, line0, fence = [], None, [], 0, False
    mark = "#" * level + " "
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        if not fence and line.startswith(mark):
            if cur is not None:
                out.append((cur, "\n".join(body), line0))
            cur, body, line0 = line[len(mark):].strip(), [], i
        elif cur is not None:
            body.append(line)
    if cur is not None:
        out.append((cur, "\n".join(body), line0))
    return out


def find_section(secs, *words):
    for head, body, line in secs:
        if any(w in head.lower() for w in words):
            return head, body, line
    return None


def check_index(root: Path, index: Path, r: Report, rule_ids: set):
    text = read(index)
    words = len(prose(text).split())
    if words > 500:
        r.warn(index.name, f"{words} words outside code blocks; an index stays at or under 500")
    for g in GOVERNING:
        if g not in text:
            r.fail(index.name, f"does not name {g}")
    if find_section(sections(text), "status"):
        r.warn(index.name, "has a status section; status lives in STATUS.md and goes stale here")
    if find_section(sections(text), "goal") and "GOALS.md" in [g for g in GOVERNING if (root / g).exists()]:
        r.warn(index.name, "has a goals section; goals live in GOALS.md, and two copies drift apart")
    for i, line in enumerate(text.splitlines(), 1):
        if "[" in line:
            continue
        for rid in re.findall(r"\*\*([A-Z]{1,2}\d+[a-z]?)\*\*", line):
            if rule_ids and rid not in rule_ids:
                r.fail(f"{index.name}:{i}", f"lists {rid}, which GUARDRAILS.md does not define")


def check_readme(root: Path, r: Report):
    p = root / "README.md"
    text = read(p)
    table = [ln for ln in text.splitlines() if ln.startswith("|") and re.search(r"(?i)\bowns?\b", ln)]
    if not table:
        r.fail("README.md", "has no table of which file owns which question")
    for g in GOVERNING:
        if g not in text:
            r.warn("README.md", f"does not name {g}")


def check_narrative(p: Path, r: Report):
    text = read(p)
    heads = [h.lower() for h, _, _ in sections(text)]
    if not any("win" in h for h in heads):
        r.warn(p.name, 'has no block on what a win looks like')
    if not any("never say" in h for h in heads):
        r.warn(p.name, 'has no block on what the narrative never says')
    body = PLACEHOLDER.sub(" ", prose(text))
    words = len(body.split())
    if words < 150:
        r.warn(p.name, f"only {words} words of its own; the argument is not written yet")
    elif words > 1500:
        r.info(p.name, f"{words} words; fine for a paper or book, long for a model or tool project (600 to 1,000)")
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"\s*[-*]\s+\*\*(Never|Always)\b", line):
            r.warn(f"{p.name}:{i}", "reads like a rule; rules live in GUARDRAILS.md or GUIDELINES.md")


def check_goals(p: Path, r: Report, today: dt.date, stale_days: int):
    text = read(p)
    secs = sections(text)
    long_ = find_section(secs, "long")
    short = find_section(secs, "short")
    non = find_section(secs, "non-goal", "non goal", "nongoal")
    if not long_:
        r.fail(p.name, 'has no section for long goals')
    else:
        goals = sections("\n" + long_[1], 3)
        if not goals:
            r.fail(f"{p.name}:{long_[2]}", "the long-goal section holds no goal (use a ### heading per goal)")
        if len(goals) > 3:
            r.warn(f"{p.name}:{long_[2]}", f"{len(goals)} long goals; a project carries one to three")
        for head, body, _ in goals:
            if "SUPERSEDED" not in head and not re.search(r"(?im)^\s*[-*]\s*Test:", body):
                r.warn(p.name, f'long goal "{head[:50]}" has no "Test:" line saying how an outsider would check it')
    if not short:
        r.fail(p.name, 'has no section for the short goal')
    else:
        body = short[1]
        where = f"{p.name}:{short[2]}"
        due = re.search(r"(?im)^\s*[-*]\s*Due:\s*(.*)$", body)
        if not due:
            r.fail(where, 'the short goal has no "Due:" line')
        else:
            m = DATE.search(due.group(1))
            d = None
            if m:
                try:
                    d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except ValueError:
                    r.fail(where, f'"Due:" carries an impossible date ({m.group(0)})')
            if d:
                late = (today - d).days
                if late > stale_days:
                    r.warn(where, f"the short goal was due {d.isoformat()}, {late} days ago: close it (reached, "
                                  f"missed, superseded, parked) in the Past table and set the next one")
            elif not m and "[" not in due.group(1):
                r.fail(where, f'"Due:" carries no date in the form YYYY-MM-DD ({due.group(1).strip()[:40]})')
        items = [ln for ln in body.splitlines() if re.match(r"\s*[-*]\s+\[[ xX]\]", ln)]
        if not items:
            r.fail(where, "the short goal lists no deliverables (use - [ ] lines)")
        if len(items) > 5:
            r.warn(where, f"{len(items)} deliverables; three to five keep a short goal short")
        for ln in items:
            if not re.search(r"(?i)\bcheck:", ln):
                r.warn(where, f'deliverable without "Check:": {ln.strip()[:70]}')
        if not re.search(r"(?im)^\s*[-*]\s*Feeds:", body):
            r.warn(where, 'the short goal has no "Feeds:" line naming the decision it settles')
        if len([h for h, _, _ in sections("\n" + body, 3) if "SUPERSEDED" not in h]) > 1:
            r.warn(where, "more than one active short goal; keep one per stream of work")
    if not non:
        r.warn(p.name, "has no section for non-goals")
    elif not re.search(r"(?m)^\s*[-*]\s+\S", non[1]):
        r.warn(f"{p.name}:{non[2]}", "the non-goals section is empty")
    for i, line in enumerate(text.splitlines(), 1):
        if MARK.match(line) and "SUPERSEDED" in line and not DATE.search(line) and "[" not in line:
            r.fail(f"{p.name}:{i}", "a SUPERSEDED mark without its date")


def parse_rules(text: str):
    """{id: (line number, block text)} in file order, plus the list of duplicate ids."""
    rules, dup, cur, fence = {}, [], None, False
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        if fence:
            continue
        m = RULE.match(line)
        if m and not line.lstrip().startswith("|"):
            rid = m.group(1)
            if rid in rules:
                dup.append((rid, i))
                cur = None
                continue
            rules[rid] = [i, [line]]
            cur = rid
        elif line.startswith("#") or line.lstrip().startswith("|"):
            cur = None
        elif cur:
            rules[cur][1].append(line)
    return {k: (v[0], "\n".join(v[1])) for k, v in rules.items()}, dup


def check_guardrails(p: Path, r: Report) -> set:
    text = read(p)
    rules, dup = parse_rules(text)
    for rid, i in dup:
        r.fail(f"{p.name}:{i}", f"rule id {rid} is used twice; ids are stable and unique")
    if not rules:
        r.fail(p.name, "defines no rule with an id (write rules as - **G1. ...**)")
        return set()
    no_prev = [k for k, (_, b) in rules.items() if "Prevents:" not in b and "[" not in b.split("\n")[0]]
    no_check = [k for k, (_, b) in rules.items() if "Check:" not in b and "[" not in b.split("\n")[0]]
    if no_prev:
        r.warn(p.name, f'{len(no_prev)} of {len(rules)} rules have no "Prevents:" line: {", ".join(no_prev[:12])}')
    if no_check:
        r.warn(p.name, f'{len(no_check)} of {len(rules)} rules have no "Check:" line: {", ".join(no_check[:12])}')
    conv = [k for k, (_, b) in rules.items() if re.search(r"(?i)Check:[^\n]*\bconvention\b", b)]
    if conv:
        r.info(p.name, f"{len(conv)} of {len(rules)} rules rest on convention alone ({', '.join(conv[:12])}); "
                       f"these are the exposure")
    enf = find_section(sections(text), "enforcement")
    if not enf:
        r.warn(p.name, "has no enforcement table (rule, enforced by, mechanism, gap)")
    else:
        listed = set(re.findall(r"(?m)^\|\s*`?\**([A-Z]{1,2}\d+[a-z]?)\b", enf[1]))
        missing = [k for k in rules if k not in listed]
        if missing:
            r.warn(f"{p.name}:{enf[2]}", f"{len(missing)} rules are not in the enforcement table: "
                                         f"{', '.join(missing[:12])}")
    for i, line in enumerate(text.splitlines(), 1):
        marked = RULE.match(line) or line.lstrip().startswith("|")  # a rule line or a table row carries the mark
        if marked and re.search(r"\bRETIRED\b", line) and not DATE.search(line) and "[" not in line:
            r.fail(f"{p.name}:{i}", "a RETIRED mark without its date")
    return set(rules)


def check_guidelines(p: Path, r: Report):
    text = read(p)
    if not re.search(r"(?im)^\W*the bar\b", text):
        r.warn(p.name, 'has no line "The bar:" naming the standard a reviewer would apply')
    if not find_section(sections(text), "definition of done"):
        r.warn(p.name, 'has no section "Definition of done"')
    hard = [i for i, ln in enumerate(text.splitlines(), 1) if re.match(r"\s*[-*]\s+\*\*Never\b", ln)]
    if hard:
        r.info(p.name, f"{len(hard)} lines open with Never (first at line {hard[0]}); a rule whose breach voids a "
                       f"result belongs in GUARDRAILS.md")


def kb_dir(root: Path, given):
    if given:
        return root / given
    for d in KB_DIRS:
        if (root / d).is_dir():
            return root / d
    return None


def check_kb(root: Path, kb, r: Report):
    if kb is None or not kb.is_dir():
        r.warn("docs/kb/", "no knowledge base folder")
        return set()
    rel = kb.relative_to(root)
    index = next((kb / n for n in ("INDEX.md", "llms.txt") if (kb / n).exists()), None)
    if index is None and (kb / "README.md").exists() and len(
            re.findall(r"(?m)^\|[^\n]*\.md\b", read(kb / "README.md"))) >= 3:
        index = kb / "README.md"
        r.info(str(rel), "the index is the table in README.md; a separate INDEX.md keeps the file an agent reads "
                         "first short")
    entries = [f for f in sorted(kb.rglob("*.md"))
               if f.name not in ("README.md", "INDEX.md") and not (set(f.relative_to(kb).parts[:-1]) & SKIP)]
    if index is None:
        r.fail(str(rel), "has no INDEX.md (or llms.txt): the one file an agent reads first")
        return set(entries)
    itext = read(index)
    headless, unlisted = [], []
    for f in entries:
        e = f.relative_to(kb).as_posix()
        top = f.relative_to(kb).parts[0]
        if e not in itext and f.name not in itext and f.stem not in itext and (top == f.name or top not in itext):
            unlisted.append(e)
        head = "\n".join(read(f).splitlines()[:14])
        gaps = [n for n, pat in (("a one-line summary (> ...)", r"(?m)^>\s*\S"), ("Status:", r"(?im)^\W*status:"),
                                 ("Updated: with a date", r"(?im)^\W*updated:.*20\d{2}-\d{2}-\d{2}"))
                if not re.search(pat, head)]
        if gaps:
            headless.append((e, gaps))
    if len(unlisted) > 5:
        r.fail(str(rel), f"{len(unlisted)} of {len(entries)} entries are not listed in {index.name}, so nobody "
                         f"finds them: {', '.join(unlisted[:6])} ...")
    else:
        for e in unlisted:
            r.fail(f"{rel}/{e}", f"is not listed in {index.name}; an unlisted entry is not found")
    if len(headless) > 5:
        r.warn(str(rel), f"{len(headless)} of {len(entries)} entries lack the header (one-line summary, Status, "
                         f"Updated): {', '.join(e for e, _ in headless[:6])} ...")
    else:
        for e, gaps in headless:
            r.warn(f"{rel}/{e}", "entry header lacks " + ", ".join(gaps))
    for i, line in enumerate(itext.splitlines(), 1):
        if "planned" in line.lower():
            continue
        for name in re.findall(r"[\w./-]+\.md\b", line):
            if name in ("README.md", "INDEX.md") or (kb / name).exists() or (root / name).exists():
                continue
            base = Path(name).name
            elsewhere = list(kb.rglob(base)) or (root / base).exists() or any(
                (root / d).is_dir() and list((root / d).rglob(base)) for d in DOC_DIRS)
            if not elsewhere:
                r.fail(f"{rel}/{index.name}:{i}", f"names {name}, which does not exist (mark it planned, or write it)")
    arch = kb / "archive"
    if arch.is_dir():
        bare = [f.name for f in sorted(arch.rglob("*.md")) if f.name != "README.md"
                and not re.search(r"(?i)supersed|replaced by|successor", "\n".join(read(f).splitlines()[:8]))]
        if bare:
            r.warn(f"{rel}/archive", f"{len(bare)} archived entries carry no banner naming their successor: "
                                     f"{', '.join(bare[:6])}")
    return set(entries)


def check_reach(root: Path, index: Path, kb_entries: set, r: Report):
    docs = [f for f in sorted(root.glob("*.md"))]
    for d in DOC_DIRS:
        base = root / d
        if not base.is_dir() or base.is_symlink():
            continue
        for f in sorted(base.rglob("*.md")):
            parts = f.relative_to(root).parts
            if len(parts) <= 4 and not (set(parts[:-1]) & SKIP):
                docs.append(f)
    docs = [f for f in docs if f not in kb_entries]
    start = [f for f in (root / "README.md", index) if f and f.exists()]
    reached, queue = set(start), list(start)
    while queue:
        text = read(queue.pop())
        for f in docs:
            if f in reached:
                continue
            relp = f.relative_to(root).as_posix()
            if relp in text or re.search(rf"(?<![\w/.-]){re.escape(f.name)}(?![\w-])", text):
                reached.add(f)
                queue.append(f)
    lost = [f.relative_to(root).as_posix() for f in docs if f not in reached]
    if lost:
        r.warn("reach", f"{len(lost)} documents are named by nothing that can be reached from README.md or "
                        f"{index.name if index else 'the index'}: {', '.join(lost[:15])}"
                        + (" ..." if len(lost) > 15 else ""))


def check_placeholders(root: Path, files, r: Report, head_only=()):
    for f in files:
        if not f.exists():
            continue
        text = read(f)
        if f in head_only:  # a knowledge base entry: only its header; its body may cite in square brackets
            text = "\n".join(text.splitlines()[:14])
        n = len(PLACEHOLDER.findall(prose(text)))
        if n:
            r.warn(f.relative_to(root).as_posix(), f"{n} bracketed placeholders left to fill")


def run(root: Path, index_name, kb_arg, stale_days: int, today: dt.date) -> Report:
    r = Report()
    index = root / index_name if index_name else next(
        (root / n for n in ("CLAUDE.md", "AGENTS.md") if (root / n).exists()), None)
    if index is None or not index.exists():
        r.fail(index_name or "CLAUDE.md", "the index file for agents is missing")
        index = None
    if not (root / "README.md").exists():
        r.fail("README.md", "missing")
    for g in GOVERNING:
        if not (root / g).exists():
            r.fail(g, "missing: " + {"NARRATIVE.md": "the argument is not written down",
                                     "GOALS.md": "long goals, the short goal and non-goals have no home",
                                     "GUARDRAILS.md": "the rules that must never be broken have no home",
                                     "GUIDELINES.md": "the conventions and the definition of done have no home"}[g])
    rule_ids = check_guardrails(root / "GUARDRAILS.md", r) if (root / "GUARDRAILS.md").exists() else set()
    if index:
        check_index(root, index, r, rule_ids)
    if (root / "README.md").exists():
        check_readme(root, r)
    if (root / "NARRATIVE.md").exists():
        check_narrative(root / "NARRATIVE.md", r)
    if (root / "GOALS.md").exists():
        check_goals(root / "GOALS.md", r, today, stale_days)
    if (root / "GUIDELINES.md").exists():
        check_guidelines(root / "GUIDELINES.md", r)
    kb = kb_dir(root, kb_arg)
    kb_entries = check_kb(root, kb, r)
    if index or (root / "README.md").exists():
        check_reach(root, index, kb_entries, r)
    check_placeholders(root, [root / g for g in GOVERNING] + ([index] if index else [])
                       + [root / "README.md", root / "STATUS.md"] + sorted(kb_entries), r, head_only=kb_entries)
    return r


def show(r: Report, root: Path, strict: bool) -> int:
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    for it in sorted(r.items, key=lambda i: order[i["level"]]):
        print(f'{it["level"]:4s}  {it["where"]}: {it["message"]}')
    f, w = r.count("FAIL"), r.count("WARN")
    bad = f > 0 or (strict and w > 0)
    print(f"\ndoctor: {root.name}: {f} failed, {w} warnings, {r.count('INFO')} notes. "
          + ("NOT READY" if bad else "governing documents in place" if not w
             else "structure in place; clear the warnings (--strict fails on them)"))
    return 1 if bad else 0


GOOD = {
    "CLAUDE.md": "# CLAUDE.md\nRead NARRATIVE.md, GOALS.md, GUARDRAILS.md, GUIDELINES.md.\n- **G1** Never tune on test.\n",
    "README.md": "# P\n| File | Owns the question |\n|---|---|\n| `NARRATIVE.md` | why |\n| `GOALS.md` | where |\n"
                 "| `GUARDRAILS.md` | never |\n| `GUIDELINES.md` | how |\n| `docs/kb/INDEX.md` | what we know |\n",
    "NARRATIVE.md": "# NARRATIVE\n## The object\n" + "word " * 200 + "\n## What a win looks like\nA.\n"
                    "## What this narrative never says\n- B.\n",
    "GOALS.md": "# GOALS\n## Long goals\n### L1. Deliver the model.\n- Test: beats the baseline.\n"
                "## Short goal (active)\n### S1. First run.\n- Due: 2999-01-01\n- Feeds: go or stop\n"
                "  - [ ] the table. Check: results/table.csv exists\n## Non-goals\n- A library: later.\n",
    "GUARDRAILS.md": "# GUARDRAILS\n- **G1. Never tune on test.** Prevents: a void number. Check: convention.\n"
                     "## Enforcement status\n| Rule | Enforced by | Mechanism | Gap |\n|---|---|---|---|\n| G1 | none | none | all |\n",
    "GUIDELINES.md": "# GUIDELINES\nThe bar: reads like the stable modules.\n## Definition of done\n1. Tests pass.\n",
    "docs/kb/INDEX.md": "| Entry | What |\n|---|---|\n| `00_overview.md` | the field |\n",
    "docs/kb/00_overview.md": "# Overview\n\n> The field in one page.\n\n- Status: verified\n- Updated: 2026-01-01\n",
}


def self_test() -> int:
    today = dt.date(2026, 1, 15)
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp) / "good"
        for name, text in GOOD.items():
            (good / name).parent.mkdir(parents=True, exist_ok=True)
            (good / name).write_text(text, encoding="utf-8")
        rg = run(good, None, None, 7, today)
        bad = Path(tmp) / "bad"
        for name, text in GOOD.items():
            (bad / name).parent.mkdir(parents=True, exist_ok=True)
            (bad / name).write_text(text, encoding="utf-8")
        (bad / "GUARDRAILS.md").write_text(GOOD["GUARDRAILS.md"].replace(
            "## Enforcement", "- **G1. Never copy labels.** Prevents: x. Check: y.\n## Enforcement"), encoding="utf-8")
        (bad / "GOALS.md").write_text(GOOD["GOALS.md"].replace("- Due: 2999-01-01\n", ""), encoding="utf-8")
        (bad / "CLAUDE.md").write_text(GOOD["CLAUDE.md"] + "- **G9** Never ship.\n", encoding="utf-8")
        (bad / "docs/kb/07_lost.md").write_text("# Lost\n", encoding="utf-8")
        (bad / "docs/ORPHAN.md").write_text("# Orphan\n", encoding="utf-8")
        (bad / "NARRATIVE.md").unlink()
        rb = run(bad, None, None, 7, today)
        late = Path(tmp) / "late"
        for name, text in GOOD.items():
            (late / name).parent.mkdir(parents=True, exist_ok=True)
            (late / name).write_text(text.replace("2999-01-01", "2025-12-01"), encoding="utf-8")
        rl = run(late, None, None, 7, today)
    msgs = " | ".join(i["message"] for i in rb.items)
    expect = [("good project has no failure", rg.count("FAIL") == 0),
              ("good project has no warning", rg.count("WARN") == 0),
              ("duplicate rule id fails", "used twice" in msgs),
              ("missing Due fails", '"Due:"' in msgs),
              ("dangling id in the index fails", "does not define" in msgs),
              ("unlisted kb entry fails", "not listed" in msgs),
              ("missing narrative fails", any(i["where"] == "NARRATIVE.md" and i["level"] == "FAIL" for i in rb.items)),
              ("unreachable document warns", "ORPHAN.md" in msgs),
              ("a short goal 45 days late warns", any("45 days ago" in i["message"] for i in rl.items))]
    for name, ok in expect:
        print(("ok    " if ok else "WRONG ") + name)
    if not all(ok for _, ok in expect):
        for it in rg.items + rb.items + rl.items:
            print("   ", it)
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", type=Path, help="project folder to check")
    ap.add_argument("--index-name", help="file name of the agent index (default: CLAUDE.md, then AGENTS.md)")
    ap.add_argument("--kb", help="knowledge base folder, relative to the project (default: docs/kb, then knowledge-base)")
    ap.add_argument("--stale-days", type=int, default=7, help="days a short goal may be past due before a warning (default 7)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    ap.add_argument("--json", action="store_true", help="print the findings as JSON")
    ap.add_argument("--self-test", action="store_true", help="check the checker on generated projects")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.project:
        ap.error("give a project folder, or --self-test")
    root = a.project.expanduser().resolve()
    if not root.is_dir():
        print(f"doctor: {root} is not a folder")
        return 1
    r = run(root, a.index_name, a.kb, a.stale_days, dt.date.today())
    if a.json:
        print(json.dumps({"project": root.name, "failed": r.count("FAIL"), "warnings": r.count("WARN"),
                          "findings": r.items}, indent=2))
        return 1 if r.count("FAIL") or (a.strict and r.count("WARN")) else 0
    return show(r, root, a.strict)


if __name__ == "__main__":
    sys.exit(main())
