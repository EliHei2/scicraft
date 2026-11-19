#!/usr/bin/env python3
"""Quality gate for skill folders (ported from the gate of the package this skill was distilled into).

Checks every skill folder under the given paths (a skill folder holds SKILL.md):

  structure  frontmatter, name, description length, body length, eval cases
  links      every references/, scripts/ and assets/ path named in SKILL.md exists,
             and every reference file is named in SKILL.md
  scripts    .py compiles, .js passes `node --check`, .sh passes `bash -n`
  private    home paths, emails, keys, any term in --terms FILE, and any regex in
             --internal-terms FILE unless --internal is given
  voice      dashes used as punctuation, sales words, filler, separators

Usage:
    python3 check_skill.py PATH [PATH ...]           # every skill folder under the paths, all checks
    python3 check_skill.py --voice PATH              # one check only (also --private, --structure, --scripts)
    python3 check_skill.py --terms private_terms.txt PATH       # extra forbidden strings, one per line
    python3 check_skill.py --internal-terms institute.txt PATH  # regexes for institute paths and hosts
    python3 check_skill.py --internal ...            # allow the institute regexes (internal tier)

Keep the terms files in the private workspace, never in the package: the list itself names what
must not leak.

Exit code 0 when no error was found, 1 otherwise. Warnings do not fail the run.
Standard library only. Node and bash are used when present.
"""
from __future__ import annotations

import argparse
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PATH_RE = re.compile(r"(?<![\w/.-])((?:references|scripts|assets|evals)/[\w./-]+\.[A-Za-z0-9]+)")

PRIVATE = {
    "home path": r"/Users/[A-Za-z0-9._-]+|/home/[a-z][A-Za-z0-9._-]+",
    "email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}",
    "api key": r"sk-ant-[A-Za-z0-9_\-]{20,}|sk-(?:proj-)?[A-Za-z0-9_\-]{32,}|AIza[0-9A-Za-z_\-]{35}"
               r"|(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}
INSTITUTE: dict = {}  # filled from --internal-terms: one regex per line for institute paths, hosts, group codes
EMAIL_OK = re.compile(r"@(example\.(com|org)|users\.noreply\.github\.com|anthropic\.com)$|^noreply@|^git@")

DASH = re.compile(r"—|–|(?<=\w) -- (?=\w)|(?<=\w)---(?=\w)")
RANGE = re.compile(r"\d\s?–\s?\d")
SLOP = re.compile(
    r"\b(seamless(?:ly)?|cutting-edge|leverag(?:e|es|ed|ing)|delv(?:e|es|ed|ing)|game-chang\w+|holistic|synerg\w+|"
    r"meticulous(?:ly)?|tapestry|testament|load-bearing|unlock(?:s|ed|ing)?|showcas(?:es|ed|ing))\b", re.I)
# Words that are slop when figurative and fine when technical ("robust regression"). Reported as warnings.
SALES = re.compile(
    r"\b(powerful|robust|comprehensive|crucial|pivotal|novel|elegant|principled|state-of-the-art)\b", re.I)
FILLER = re.compile(
    r"\b(it is worth noting|it's worth noting|importantly,|crucially,|notably,|note that|interestingly,|"
    r"in order to|this section (?:covers|describes|explains)|this skill will|in today's)\b", re.I)
SEPARATOR = re.compile(r"\S · \S|\S • \S")
CONTRAST = re.compile(r"\bnot (?:just|only|merely|simply)\b|\bnot [\w\s,]{1,40}? but \b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-⛿✀-➿]")


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, where, msg):
        self.errors.append(f"ERROR  {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"warn   {where}: {msg}")


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    fm, body = text[4:end], text[end + 4:]
    meta, key = {}, None
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            meta[key] = m.group(2).strip().strip("\"'")
        elif key and line.startswith((" ", "\t")):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, body


def prose_lines(text: str):
    """Yield (line number, text) for prose: code fences, inline code and lint-off blocks removed."""
    fence = off = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if "voice-lint: off" in s:
            off = True
        if "voice-lint: on" in s:
            off = False
            continue
        if fence or off:
            continue
        yield i, re.sub(r"`[^`]*`", "``", line)


def check_structure(skill: Path, r: Report):
    f = skill / "SKILL.md"
    text = f.read_text(encoding="utf-8", errors="replace")
    meta, body = frontmatter(text)
    w = rel(f)
    if meta is None:
        r.err(w, "no YAML frontmatter")
        return
    name, desc = meta.get("name", ""), meta.get("description", "")
    if name != skill.name:
        r.err(w, f"name '{name}' differs from folder '{skill.name}'")
    if not NAME_RE.match(name) or len(name) > 40:
        r.err(w, "name must be lowercase words joined by hyphens, at most 40 characters")
    if not 80 <= len(desc) <= 1024:
        r.err(w, f"description has {len(desc)} characters (allowed 80 to 1024)")
    if "<" in desc or ">" in desc:
        r.err(w, "description contains angle brackets")
    n = len(text.splitlines())
    if n > 500:
        r.warn(w, f"{n} lines; move detail to references/ (target 500)")
    if len(body.split()) < 150:
        r.warn(w, "body under 150 words")
    # links
    named = set(PATH_RE.findall(text))
    for p in sorted(named):
        if p.startswith("evals/"):
            continue
        if not (skill / p).exists():
            r.err(w, f"names {p}, which does not exist")
    for sub in ("references",):
        d = skill / sub
        if d.is_dir():
            for g in sorted(d.glob("*.md")):
                if f"{sub}/{g.name}" not in text:
                    r.warn(rel(g), "not named in SKILL.md, so it will never be read")
    for big in skill.rglob("*.md"):
        if big.parent.name == "references" and len(big.read_text(errors="replace").splitlines()) > 300:
            head = "\n".join(big.read_text(errors="replace").splitlines()[:40]).lower()
            if "contents" not in head:
                r.warn(rel(big), "over 300 lines without a table of contents")
    # evals
    ev = skill / "evals"
    if not ev.is_dir() or not any(ev.iterdir()):
        r.warn(rel(skill), "no eval cases")
    else:
        for case in sorted(p for p in ev.iterdir() if p.is_dir() and p.name not in ("results", "files", "mocks")):
            cw = rel(case)
            pm, cy = case / "prompt.md", case / "case.yaml"
            if not pm.exists() or not pm.read_text(errors="replace").startswith("---\n"):
                r.err(cw, "prompt.md missing or without its settings block")
            if not cy.exists():
                r.err(cw, "case.yaml missing")
            else:
                c = cy.read_text(errors="replace")
                if 'schema_version: "1.1"' not in c:
                    r.err(cw, 'case.yaml needs schema_version: "1.1" (quoted)')
                if not re.search(rf"^name:\s*{re.escape(case.name)}\s*$", c, re.M):
                    r.err(cw, "case.yaml name differs from the folder name")
                if "expected_outcome:" not in c:
                    r.err(cw, "case.yaml has no expected_outcome")
            gr = sorted((case / "graders").glob("*.md")) if (case / "graders").is_dir() else []
            if not gr:
                r.err(cw, "no graders")
            for g in gr:
                if not g.read_text(errors="replace").startswith("---\ntype:"):
                    r.err(rel(g), "grader lacks its settings block (type, focus, weight)")


def check_scripts(skill: Path, r: Report):
    node, bash = shutil.which("node"), shutil.which("bash")
    for f in sorted(skill.rglob("*")):
        if not f.is_file() or "node_modules" in f.parts or "evals" in f.parts and "files" not in f.parts and f.suffix != ".py":
            continue
        if f.suffix == ".py":
            try:
                py_compile.compile(str(f), doraise=True, cfile=str(Path(tempfile.gettempdir()) / (f.name + "c")))
            except py_compile.PyCompileError as e:
                r.err(rel(f), f"does not compile: {str(e).splitlines()[-1][:160]}")
        elif f.suffix in (".js", ".mjs") and node and f.stat().st_size < 400_000:
            p = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
            if p.returncode:
                r.err(rel(f), f"node --check failed: {p.stderr.strip().splitlines()[-1][:160] if p.stderr.strip() else ''}")
        elif f.suffix == ".sh" and bash:
            p = subprocess.run([bash, "-n", str(f)], capture_output=True, text=True)
            if p.returncode:
                r.err(rel(f), f"bash -n failed: {p.stderr.strip()[:160]}")


TEXT_EXT = {".md", ".py", ".js", ".mjs", ".sh", ".tex", ".sty", ".cls", ".json", ".yaml", ".yml", ".toml", ".txt",
            ".html", ".css", ".cfg", ".ini", ".bib", ".tsv", ".csv", ".svg", ""}


def check_private(skill: Path, r: Report, terms: list[str], internal: bool):
    pats = dict(PRIVATE)
    if not internal:
        pats.update(INSTITUTE)
    comp = {k: re.compile(v) for k, v in pats.items()}
    term_re = re.compile("|".join(rf"(?<![A-Za-z]){re.escape(t)}(?![A-Za-z])" for t in terms), re.I) if terms else None
    for f in sorted(skill.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in TEXT_EXT or f.stat().st_size > 2_000_000:
            continue
        if f.name in ("LICENSE", "LICENSE.txt", "NOTICE") or f.name.endswith("-OFL.txt"):
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for kind, rx in comp.items():
                for m in rx.finditer(line):
                    s = m.group(0)
                    if kind == "email address" and (EMAIL_OK.search(s) or s.split("@")[0] in ("you", "user", "name")):
                        continue
                    if kind == "home path" and re.fullmatch(r"/(Users|home)/(you|user|name|me|USER|username)", s):
                        continue
                    shown = s if kind in ("home path", "institute path or host") else kind
                    r.err(f"{rel(f)}:{i}", f"private string ({kind}): {shown[:60]}")
            if term_re:
                m = term_re.search(line)
                if m:
                    r.err(f"{rel(f)}:{i}", f"forbidden term: {m.group(0)}")


def check_voice(skill: Path, r: Report):
    for f in sorted(skill.rglob("*.md")):
        if "evals" in f.parts or f.name in ("LICENSE.md", "NOTICE.md"):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        n_contrast = 0
        words = max(1, len(text.split()))
        for i, line in prose_lines(text):
            w = f"{rel(f)}:{i}"
            for m in DASH.finditer(line):
                if RANGE.search(line[max(0, m.start() - 2): m.end() + 2]):
                    r.warn(w, "en dash in a range; write 'to'")
                else:
                    r.err(w, "dash used as punctuation")
            for m in SLOP.finditer(line):
                r.err(w, f"slop word: {m.group(0)}")
            for m in SALES.finditer(line):
                r.warn(w, f"sales word unless technical: {m.group(0)}")
            for m in FILLER.finditer(line):
                r.warn(w, f"filler: {m.group(0)}")
            if SEPARATOR.search(line):
                r.err(w, "separator between phrases")
            if EMOJI.search(line):
                r.err(w, "emoji")
            n_contrast += len(CONTRAST.findall(line)) + line.lower().count("rather than")
        if n_contrast * 10000 / words > 30 and n_contrast > 3:
            r.warn(rel(f), f"{n_contrast} staged contrasts in {words} words; keep only those that name a real mistake")


def find_skills(paths: list[Path]) -> list[Path]:
    out = []
    for p in paths:
        p = p.resolve()
        if (p / "SKILL.md").exists():
            out.append(p)
        else:
            out += sorted(q.parent for q in p.rglob("SKILL.md") if "evals" not in q.parts and "node_modules" not in q.parts)
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", type=Path, help="skill folders, or folders that contain them")
    for k in ("structure", "scripts", "private", "voice"):
        ap.add_argument(f"--{k}", action="store_true", help=f"run only the {k} check (flags combine)")
    ap.add_argument("--terms", type=Path, help="file of extra forbidden strings, one per line")
    ap.add_argument("--internal-terms", type=Path, help="file of regexes for institute paths and hosts, one per line")
    ap.add_argument("--internal", action="store_true", help="allow the --internal-terms patterns (internal tier)")
    ap.add_argument("--quiet", action="store_true", help="print errors only")
    a = ap.parse_args()
    which = [k for k in ("structure", "scripts", "private", "voice") if getattr(a, k)] or ["structure", "scripts", "private", "voice"]
    terms = [t.strip() for t in a.terms.read_text().splitlines() if t.strip() and not t.startswith("#")] if a.terms else []
    if a.internal_terms:
        rx = [t.strip() for t in a.internal_terms.read_text().splitlines() if t.strip() and not t.startswith("#")]
        if rx:
            INSTITUTE["institute path or host"] = "|".join(f"(?:{x})" for x in rx)
    skills = find_skills(a.paths)
    if not skills:
        print("no skill folders found under", ", ".join(map(str, a.paths)))
        return 1
    r = Report()
    for s in skills:
        internal = a.internal
        if "structure" in which:
            check_structure(s, r)
        if "scripts" in which:
            check_scripts(s, r)
        if "private" in which:
            check_private(s, r, terms, internal)
        if "voice" in which:
            check_voice(s, r)
    for line in r.errors:
        print(line)
    if not a.quiet:
        for line in r.warnings:
            print(line)
    print(f"\n{len(skills)} skill(s) checked ({', '.join(which)}): {len(r.errors)} error(s), {len(r.warnings)} warning(s)")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main())
