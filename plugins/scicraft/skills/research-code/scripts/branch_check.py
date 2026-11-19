#!/usr/bin/env python3
"""Check a feature branch before it is pushed or turned into a pull request.

    python3 branch_check.py [--repo .] [--base main] [--branch HEAD]
                            [--destination shared|private] [--max-lines 400]

Checks, one PASS / WARN / FAIL / INFO line each:

  base        the work is on its own branch, not on the base branch
  behind      the branch is 0 commits behind the base (rebase or merge the base in first)
  size        new code lines against --max-lines; tests, docs, Markdown, comments, blank lines and
              Python docstrings do not count
  churn       lines that changed only in whitespace (reformatting of untouched code)
  trailers    assistant traces in commit messages and author lines (Co-Authored-By, Generated with,
              Claude, Anthropic, claude.ai, CLAUDE.md, .claude/): FAIL for --destination shared,
              INFO for private
  agent files CLAUDE.md or .claude/ in the diff: FAIL for shared
  big files   added files over 50 MB (WARN) or 100 MB (FAIL, the hosting limit)
  mixed       commit subjects that read as both a fix and a feature (WARN: split the branch)

Exit code 1 when any check FAILs. Standard library and git only; Python 3.9 or later.
The trailer pattern is the assistant-trace class of a pre-publication leak scanner the author wrote.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

TRACE = re.compile(r"CLAUDE\.md|\.claude/|\bClaude\b|\bAnthropic\b|Co-Authored-By|Generated with|claude\.ai", re.I)
AGENT_FILES = re.compile(r"(^|/)(CLAUDE\.md|\.claude/)")
NOT_CODE = ["tests/*", "test/*", "*/tests/*", "*/test/*", "test_*.py", "*/test_*.py", "*_test.py",
            "docs/*", "*/docs/*", "*.md", "*.rst", "*.txt", "LICENSE*", "CHANGELOG*", "*.ipynb"]
COMMENT = re.compile(r"^\s*(#|//|--|%)")
FIX = re.compile(r"^\s*(fix|bugfix|hotfix)\b|^\s*fix\(", re.I)
FEAT = re.compile(r"^\s*(feat|feature|add)\b|^\s*feat\(", re.I)
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def git(repo: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and p.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def docstring_lines(source: str) -> set[int]:
    """Line numbers (1-based) that belong to module, class or function docstrings."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) \
                    and isinstance(first.value.value, str):
                lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def is_code_path(path: str, extra: list[str]) -> bool:
    return not any(fnmatch.fnmatch(path, g) for g in NOT_CODE + extra)


def count_new_code(repo: Path, base: str, branch: str, extra: list[str]) -> tuple[int, dict[str, int]]:
    files = [f for f in git(repo, "diff", "--name-only", "--diff-filter=AM", f"{base}...{branch}").split("\n") if f]
    per_file: dict[str, int] = {}
    for path in files:
        if not is_code_path(path, extra):
            continue
        doc = set()
        if path.endswith(".py"):
            doc = docstring_lines(git(repo, "show", f"{branch}:{path}", check=False))
        diff = git(repo, "diff", "-U0", f"{base}...{branch}", "--", path)
        n, new_line = 0, 0
        for line in diff.splitlines():
            m = HUNK.match(line)
            if m:
                new_line = int(m.group(1))
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                body = line[1:]
                if body.strip() and not COMMENT.match(body) and new_line not in doc:
                    n += 1
                new_line += 1
        if n:
            per_file[path] = n
    return sum(per_file.values()), per_file


def numstat(repo: Path, base: str, branch: str, *flags: str) -> dict[str, int]:
    out = {}
    for row in git(repo, "diff", "--numstat", *flags, f"{base}...{branch}").splitlines():
        parts = row.split("\t")
        if len(parts) == 3 and parts[0] != "-":
            out[parts[2]] = int(parts[0]) + int(parts[1])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, default=Path("."), help="repository folder (default: .)")
    ap.add_argument("--base", default="main", help="base branch the PR targets (default: main; use origin/main "
                                                   "after a fetch for a shared repository)")
    ap.add_argument("--branch", default="HEAD", help="branch to check (default: HEAD)")
    ap.add_argument("--destination", choices=["shared", "private"], default="shared",
                    help="shared: others read the history (lab repo, upstream, public); private: your own repo")
    ap.add_argument("--max-lines", type=int, default=400, help="budget of new code lines (default: 400)")
    ap.add_argument("--not-code", action="append", default=[], metavar="GLOB",
                    help="extra path pattern that does not count as code (repeatable)")
    a = ap.parse_args()

    fails = 0

    def say(level: str, check: str, msg: str):
        nonlocal fails
        fails += level == "FAIL"
        print(f"{level:<5} {check:<12} {msg}")

    repo = a.repo
    git(repo, "rev-parse", "--git-dir")
    branch_name = git(repo, "rev-parse", "--abbrev-ref", a.branch).strip()
    base_name = a.base.split("/")[-1]
    if branch_name in (a.base, base_name) or git(repo, "rev-parse", a.branch) == git(repo, "rev-parse", a.base):
        say("FAIL", "base", f"'{branch_name}' is the base branch itself; create a feature branch from {a.base}")
        return 1
    say("PASS", "base", f"'{branch_name}' is a branch of its own")

    behind = int(git(repo, "rev-list", "--count", f"{a.branch}..{a.base}").strip())
    ahead = int(git(repo, "rev-list", "--count", f"{a.base}..{a.branch}").strip())
    if behind:
        say("FAIL", "behind", f"{behind} commits behind {a.base} ({ahead} ahead); bring {a.base} in "
                              f"(git rebase {a.base} on a branch only you use, git merge {a.base} otherwise)")
    else:
        say("PASS", "behind", f"0 behind {a.base}, {ahead} ahead")

    total, per_file = count_new_code(repo, a.base, a.branch, a.not_code)
    top = ", ".join(f"{p} {n}" for p, n in sorted(per_file.items(), key=lambda kv: -kv[1])[:5])
    if total > a.max_lines:
        say("FAIL", "size", f"{total} new code lines > {a.max_lines}; split by unit ({top})")
    else:
        say("PASS", "size", f"{total} new code lines <= {a.max_lines}" + (f" ({top})" if top else ""))

    full, nows = numstat(repo, a.base, a.branch), numstat(repo, a.base, a.branch, "-w")
    churn = {p: full[p] - nows.get(p, 0) for p in full if full[p] - nows.get(p, 0) > 0}
    if churn:
        listed = ", ".join(f"{p} {n}" for p, n in sorted(churn.items(), key=lambda kv: -kv[1])[:5])
        say("WARN", "churn", f"{sum(churn.values())} changed lines differ only in whitespace ({listed}); "
                             "revert reformatting of lines the change does not need")
    else:
        say("PASS", "churn", "no whitespace-only changes")

    log = git(repo, "log", f"{a.base}..{a.branch}", "--format=%h%x09%an <%ae>%x09%s%x09%b%x1e")
    traced, subjects = [], []
    for rec in log.split("\x1e"):
        rec = rec.strip()
        if not rec:
            continue
        sha, author, subject, *body = rec.split("\t")
        subjects.append(subject)
        text = " ".join([author, subject, *body])
        if TRACE.search(text):
            traced.append(f"{sha} {subject[:60]}")
    if traced:
        level = "FAIL" if a.destination == "shared" else "INFO"
        say(level, "trailers", f"assistant traces in {len(traced)} commits: {'; '.join(traced[:5])}"
            + (" (allowed only if the repository owner wants them)" if level == "FAIL" else " (private repository)"))
    else:
        say("PASS", "trailers", f"no assistant traces in {len(subjects)} commit messages")

    changed = [f for f in git(repo, "diff", "--name-only", f"{a.base}...{a.branch}").split("\n") if f]
    agent = [f for f in changed if AGENT_FILES.search(f)]
    if agent and a.destination == "shared":
        say("FAIL", "agent files", f"{', '.join(agent)} in the diff; keep them local through .git/info/exclude")
    else:
        say("PASS" if not agent else "INFO", "agent files", "none in the diff" if not agent else ", ".join(agent))

    big = []
    added = git(repo, "diff", "--name-only", "--diff-filter=AM", f"{a.base}...{a.branch}").split("\n")
    sizes = {}
    for row in git(repo, "ls-tree", "-r", "-l", a.branch).splitlines():
        meta, _, path = row.partition("\t")
        size = meta.split()[-1]
        if size.isdigit():
            sizes[path] = int(size)
    for path in filter(None, added):
        mb = sizes.get(path, 0) / 1e6
        if mb > 50:
            big.append((path, mb))
    if any(mb > 100 for _, mb in big):
        say("FAIL", "big files", ", ".join(f"{p} {mb:.0f} MB" for p, mb in big))
    elif big:
        say("WARN", "big files", ", ".join(f"{p} {mb:.0f} MB" for p, mb in big))
    else:
        say("PASS", "big files", "no added file over 50 MB")

    has_fix = [s for s in subjects if FIX.search(s)]
    has_feat = [s for s in subjects if FEAT.search(s)]
    if has_fix and has_feat:
        say("WARN", "mixed", f"fix and feature commits on one branch ({has_fix[0][:40]} / {has_feat[0][:40]}); "
                             "fixes and features go on separate branches")
    else:
        say("PASS", "mixed", "one kind of change")

    print(f"\n{branch_name} against {a.base}: {'FAIL' if fails else 'PASS'} ({fails} failing checks)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
