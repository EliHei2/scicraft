#!/usr/bin/env python3
"""Check a brief for another agent before it is sent.

The checks follow the anatomy in SKILL.md section 1: each kind of brief must carry
certain elements (done-tests, a reading order with precedence, a stage-0 stop rule,
a falsifier per work unit, out-of-scope items, a report contract, an output path
written as it goes, an ask list, and so on). On top of that, every brief is checked
for unfilled [placeholders], private strings (home paths, emails, keys), multi-line
commands meant for pasting, vague references ("the latest checkpoint") and output
sent to /tmp. Briefs that hand work to a helper are also checked for the lines that
bind the task (guardrail ids, the short goal, the definition of done), because a
helper does not read the repository unless told to.

With --previous OLD.md the script compares the rewritten brief with its earlier
version token by token: every path, file name and number in the old file that the
new file lacks is reported. Name each token dropped on purpose with --dropped-ok;
every other dropped token is a miss, and it goes back into the brief.

The element checks are keyword searches. A hit means the brief mentions the element,
not that it does it well; a miss means a reader will not find it. Read the brief as
the receiver afterwards (SKILL.md section 9).

Usage:
    python3 check_brief.py BRIEF.md --kind long-run
    python3 check_brief.py lane_03.md --kind lane
    python3 check_brief.py assets/long-run-brief.md --kind long-run --template
    python3 check_brief.py --list-kinds
    python3 check_brief.py BRIEF_v2.md --previous BRIEF_v1.md --dropped-ok rc1/ --dropped-ok 450
    python3 check_brief.py --self-test

Exit code 0 when nothing is missing, 1 when an element is missing or a private
string is found, 2 on a usage error. Standard library only; Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

I = re.I | re.M

# element name -> (regex, what the reader is missing when it is absent)
ELEMENTS = {
    "version": (r"\bversion\s+\d|replaces every earlier|\bv\d+\b[^\n]*\d{4}",
                "a version and date line, so an older copy cannot be mistaken for this one"),
    "done": (r"done when|is done when|definition of done|tests? pass|passes when|acceptance|^#+ *done\b",
             "what 'done' means as checks someone can run"),
    "reading": (r"read (this |these )?first|in this order|reading (list|order)|order of authority|"
                r"read before acting|first read|read [^\n]{0,60} (in full|fully)",
                "an ordered reading list"),
    "precedence": (r"wins (on|over)|latest wins|overrid|order of authority|higher one wins|of record|takes precedence",
                   "which document wins when two disagree"),
    "stage0": (r"stage 0|before (you write )?any (code|build|change|front)|gates everything|"
               r"say so immediately and stop|report this [^\n]{0,20}before|before anything else",
               "the one cheap first measurement, reported before any build"),
    "stop": (r"\bstop\b", "a stop rule (when to halt and report)"),
    "gate_numeric": (r"(gate|threshold|at least|at most|within|below|above|>=|<=|≥|≤)[^\n]{0,80}\d",
                     "a gate with a number"),
    "falsifier": (r"falsified if", "a 'Falsified if' line per work unit"),
    "out_of_scope": (r"out of scope|not in scope|do not build|not yours|is not a|not this job|never build|"
                     r"another agent does|^#+ *not\b",
                     "out-of-scope items named"),
    "traps": (r"\btraps?\b", "known traps named with their incidents"),
    "dissent": (r"disagree", "a dissent clause on contested decisions"),
    "report": (r"report (back|contract|format)|final message|return format|reply in under|^#+ *report|"
               r"report:|what to report|you return|report outcomes",
               "a fixed report contract"),
    "output_path": (r"output( path| file| folder)?\s*:|write (it |them |each [^\n]{0,20}|your [^\n]{0,20})?"
                    r"(to|into|in) [`$/\w]|findings file|outputs? (go|land)|^#+ *output\b|\b(write|create) `",
                    "the output path"),
    "incremental": (r"first tool call|as you go|incrementally|as soon as [^\n]{0,20}(done|ready)|skeleton",
                    "writing to disk as it goes"),
    "fallback_message": (r"cannot write [^\n]{0,40}file|in your final message|in the message",
                         "a fallback when the agent cannot write files"),
    "ask": (r"ask the operator|ask (me|the user|the operator) only|only for what|ask only",
            "the short list of conditions to ask about"),
    "state": (r"state\.md|context (will be )?reset", "a state file that survives context resets"),
    "verbatim": (r"in (their|his|her|the operator's) words|verbatim|\d{4}-\d{2}-\d{2}|"
                 r"\b\d{1,2} (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
                 "the author's words quoted and dated"),
    "readonly": (r"read-only|read only|do not edit|report only|you do not edit", "a read-only statement"),
    "contract_pointer": (r"read [^\n]{0,80}(in full|first)[^\n]{0,40}(follow|obey|carry)",
                         "the line that sends the agent to the shared contract"),
    "base_file": (r"base (file|version|text)|last version", "the base file the edits start from"),
    "no_rebuild": (r"rebuild|new structure|new style", "the clause that forbids a rebuild"),
    "capability": (r"you cannot|cannot ssh|ask for exactly", "the receiver's capability limits"),
    "go_nogo": (r"go only if|go ?/ ?no-go|no-go", "the go / no-go conditions"),
    "fallbacks": (r"fallback", "pre-staged fallbacks"),
    "schema": (r"schema|severity|\{[^\n]*file[^\n]*old[^\n]*new", "an output schema per finding"),
    "counts": (r"confirmed|counts? (of|by)", "counts by verdict or severity"),
    "word_cap": (r"(under|at most|max(imum)?|cap of) \[?\d+\]? words|word cap",
                 "a word cap on the report"),
    "roles": (r"\bwriter\b|\bworker\b|stays the writer", "the roles of the two sessions"),
    "round": (r"\bround\b", "which round of the loop this is"),
    "tried": (r"tried|so far|constraints|guardrails", "what was tried and the constraints set so far"),
    "deliverables": (r"deliverable", "the exact deliverables"),
    "refusal": (r"insufficient|cannot answer|missing|unknown", "what to return when the input does not allow an answer"),
    "why_how": (r"\*\*why:\*\*[\s\S]*\*\*how to apply:\*\*", "the Why and How to apply lines"),
    "frontmatter": (r"\A---\n[\s\S]*?\bname:[\s\S]*?\bdescription:[\s\S]*?\n---", "frontmatter with name and description"),
}

KINDS = {
    "long-run": ["version", "done", "reading", "precedence", "stage0", "stop", "gate_numeric", "falsifier",
                 "out_of_scope", "traps", "dissent", "report", "output_path", "incremental", "ask", "state",
                 "verbatim"],
    "pickup": ["reading", "capability", "go_nogo", "gate_numeric", "fallbacks", "report"],
    "worker": ["roles", "output_path", "incremental", "report", "verbatim"],
    "contract": ["reading", "precedence", "verbatim", "out_of_scope", "report", "word_cap", "output_path",
                 "incremental", "fallback_message"],
    "lane": ["contract_pointer", "output_path", "out_of_scope"],
    "audit": ["readonly", "output_path", "incremental", "schema", "out_of_scope", "report"],
    "factcheck": ["readonly", "counts", "report", "output_path"],
    "proofread": ["readonly", "round", "out_of_scope", "report", "output_path"],
    "polish": ["base_file", "no_rebuild", "verbatim", "report"],
    "handoff": ["done", "tried", "deliverables", "reading"],
    "system": ["done", "schema", "refusal"],
    "claude-md": [],
    "memory": ["frontmatter", "why_how", "verbatim"],
    "skill": ["frontmatter"],
}

PRIVATE = {
    "home path": re.compile(r"/Users/[A-Za-z0-9._-]+|/home/[a-z][A-Za-z0-9._-]+"),
    "email address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"),
    "api key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}|sk-(?:proj-)?[A-Za-z0-9_\-]{32,}|AIza[0-9A-Za-z_\-]{35}"
                          r"|(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
SAFE_HOME = re.compile(r"/(Users|home)/(you|user|name|me|USER|username)\b")
SAFE_EMAIL = re.compile(r"@(example\.(com|org)|users\.noreply\.github\.com|anthropic\.com)$|^noreply@|^git@")
PLACEHOLDER = re.compile(r"\[(?!x\]|X\]| \]|PENDING)[A-Za-z<][^\]\n]{1,80}\](?![(:])")
VAGUE = re.compile(r"\bthe (latest|newest|current|last) (checkpoint|version|run|model|commit|draft|config)\b", re.I)
BINDING = re.compile(r"GUARDRAILS\.md|\bguardrails?\s+\[?[A-Z]{0,3}\d|short goal|GOALS\.md|definition of done",
                     re.I)
BINDING_KINDS = {"long-run", "contract", "worker", "audit", "handoff", "pickup"}
# tokens a rewrite must not lose: paths, file names, numbers (with their unit or suffix)
TOKEN = re.compile(r"[\w$~.<>/%+-]*[/\d][\w$~.<>/%+-]*|\b[\w-]+\.[A-Za-z][A-Za-z0-9]{0,5}\b")
TMP_OUT = re.compile(r"(write|save|output|out=)[^\n]{0,40}\s/tmp/", re.I)


def has(text: str, name: str) -> bool:
    return re.search(ELEMENTS[name][0], text, I) is not None


def check(text: str, kind: str, template: bool, max_lane_lines: int):
    misses, warns, oks = [], [], []
    for name in KINDS[kind]:
        (oks if has(text, name) else misses).append((name, ELEMENTS[name][1]))

    if kind == "lane":
        n = len([ln for ln in text.splitlines() if ln.strip()])
        if n > max_lane_lines:
            misses.append(("lane_length", f"{n} non-empty lines; a lane prompt keeps to 3 to {max_lane_lines} "
                                          "and puts the rest in the shared contract"))
        else:
            oks.append(("lane_length", f"{n} non-empty lines"))
    if kind == "claude-md":
        words = len(text.split())
        if words > 500:
            misses.append(("length", f"{words} words; CLAUDE.md loads every turn, keep it to 200 to 500 and move "
                                     "detail to guidelines/"))
        elif words < 200:
            warns.append(("length", f"{words} words; check that the contract and non-negotiables are all there"))
        else:
            oks.append(("length", f"{words} words"))
        rules = len(re.findall(r"^\s*\d+\.\s+\*\*", text, re.M))
        if rules < 5:
            misses.append(("non_negotiables", f"{rules} numbered bold rules found; give up to ten "
                                              "non-negotiables, each a bold imperative plus one sentence"))
        elif rules > 12:
            warns.append(("non_negotiables", f"{rules} numbered rules; ten is the shape that held up"))
        else:
            oks.append(("non_negotiables", f"{rules} numbered rules"))
        if re.search(r"superseded|deprecated|no longer", text, re.I):
            warns.append(("superseded", "superseded material in CLAUDE.md; record a dated one-liner and move "
                                        "the rest to memory or an archive"))

    if kind in BINDING_KINDS and not BINDING.search(text):
        warns.append(("binding", "no guardrail ids, short goal or definition of done quoted; a helper does not "
                                 "read the repository unless told to, so quote the lines that bind its task"))

    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        for kind_p, rx in PRIVATE.items():
            for m in rx.finditer(line):
                s = m.group(0)
                if kind_p == "home path" and SAFE_HOME.match(s):
                    continue
                if kind_p == "email address" and (SAFE_EMAIL.search(s) or s.split("@")[0] in ("you", "user", "name")):
                    continue
                shown = s if kind_p == "home path" else kind_p
                misses.append((f"private:{i}", f"{shown[:60]} (a brief that travels must not carry it)"))
        if not template:
            for m in PLACEHOLDER.finditer(line):
                misses.append((f"placeholder:{i}", f"unfilled {m.group(0)[:50]}"))
        if in_fence and line.rstrip().endswith("\\"):
            warns.append((f"paste:{i}", "multi-line command; give one line, or one `bash <script>` line"))
        if VAGUE.search(line):
            warns.append((f"vague:{i}", f"'{VAGUE.search(line).group(0)}': name the exact identifier"))
        if TMP_OUT.search(line):
            warns.append((f"tmp:{i}", "output to /tmp is lost on reboot; write inside the project"))
    return oks, misses, warns


def tokens(text: str) -> set:
    """Paths, file names and numbers in a text, with trailing punctuation removed."""
    out = set()
    text = re.sub(r"^\s*(\d+[.)]|[-*])\s", " ", text, flags=re.M)  # list markers are not content
    for m in TOKEN.finditer(text):
        t = m.group(0).strip(".,;:)(<>-")
        if t and (re.search(r"\d", t) or "/" in t or re.search(r"\.[A-Za-z]", t)):
            out.add(t)
    return out


def dropped(old: str, new: str, ok: list) -> tuple:
    """Tokens of the old version absent from the new one, split into intended and unintended."""
    gone = sorted(tokens(old) - tokens(new))
    okset = set(ok)
    return [t for t in gone if t in okset], [t for t in gone if t not in okset]


def self_test() -> int:
    old = ("Version 1. Write to $WORK/out/report.md. Disk floor 15% free. Cosine at least 0.99999.\n"
           "Release folders rc1/ and final/. Read DESIGN.md first.\n")
    new = ("Version 2. Write to $WORK/out/report.md. Disk floor 15% free.\n"
           "Release folder final/. Read DESIGN.md first.\n")
    meant, lost = dropped(old, new, ["rc1/"])
    assert meant == ["rc1/"], meant
    assert "0.99999" in lost and "1" in lost and "rc1/" not in lost, lost
    assert "$WORK/out/report.md" not in lost and "15%" not in lost and "DESIGN.md" not in lost, lost
    _, misses, warns = check("Read CONTRACT.md first and follow it. Output: out/a.md. Not yours: B.", "lane",
                             False, 6)
    assert not misses, misses
    _, _, warns = check("Done when the test passes. Output: x.md.", "handoff", False, 6)
    assert any(n == "binding" for n, _ in warns), warns
    _, _, warns = check("Guardrails G1 and G3, quoted: ...", "handoff", False, 6)
    assert not any(n == "binding" for n, _ in warns), warns
    print("self-test passed: token diff (kept, dropped on purpose, dropped by accident), lane check, binding warning")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="kinds: " + ", ".join(KINDS))
    ap.add_argument("brief", nargs="?", type=Path, help="the brief file (Markdown or plain text)")
    ap.add_argument("--kind", choices=sorted(KINDS), help="which kind of brief this is")
    ap.add_argument("--template", action="store_true",
                    help="the file is a skeleton: do not report [bracket] placeholders")
    ap.add_argument("--max-lane-lines", type=int, default=6, help="longest allowed lane prompt (default 6)")
    ap.add_argument("--list-kinds", action="store_true", help="print each kind and the elements it requires")
    ap.add_argument("--previous", type=Path, metavar="OLD",
                    help="the earlier version of this brief; report every path, file name and number it lost")
    ap.add_argument("--dropped-ok", action="append", default=[], metavar="TOKEN",
                    help="a token removed on purpose in the rewrite (repeat for each)")
    ap.add_argument("--self-test", action="store_true", help="run the built-in tests on synthetic briefs and exit")
    a = ap.parse_args()

    if a.list_kinds:
        for k, els in KINDS.items():
            extra = {"lane": " + length", "claude-md": " length + non-negotiables"}.get(k, "")
            print(f"{k:10s} {', '.join(els) or '-'}{extra}")
        return 0
    if a.self_test:
        return self_test()
    if not a.brief or not (a.kind or a.previous):
        ap.print_usage(sys.stderr)
        print("check_brief.py: a brief file and --kind or --previous are required (or --list-kinds)",
              file=sys.stderr)
        return 2
    for f in (a.brief, a.previous):
        if f is not None and not f.is_file():
            print(f"check_brief.py: no such file: {f}", file=sys.stderr)
            return 2

    text = a.brief.read_text(encoding="utf-8", errors="replace")
    oks, misses, warns = check(text, a.kind, a.template, a.max_lane_lines) if a.kind else ([], [], [])
    if a.previous:
        old = a.previous.read_text(encoding="utf-8", errors="replace")
        meant, lost = dropped(old, text, a.dropped_ok)
        for t in meant:
            oks.append(("dropped-ok", f"{t} (removed on purpose)"))
        for t in lost:
            misses.append(("dropped", f"{t} is in {a.previous.name} and not in {a.brief.name}; put it back or "
                                      "name it with --dropped-ok"))
        unused = sorted(set(a.dropped_ok) - set(meant))
        for t in unused:
            warns.append(("dropped-ok", f"{t} was named with --dropped-ok but is not missing"))
    for name, msg in oks:
        print(f"ok    {name}" + (f": {msg}" if name == "dropped-ok" else ""))
    for name, msg in misses:
        print(f"MISS  {name}: {msg}")
    for name, msg in warns:
        print(f"warn  {name}: {msg}")
    label = f"as '{a.kind}'" if a.kind else f"against {a.previous.name}"
    print(f"\n{a.brief.name} {label}: {len(oks)} present, {len(misses)} missing, {len(warns)} warning(s). "
          "Keyword checks only: read it as the receiver next.")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
