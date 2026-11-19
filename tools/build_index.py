#!/usr/bin/env python3
"""Build the overview of the registry: the generated blocks of README.md, and docs/INDEX.md.

Usage:
    python3 tools/build_index.py            # rewrites the generated blocks of README.md and docs/INDEX.md
    python3 tools/build_index.py --check    # exits 1 if either is out of date

The source is tools/catalog.json: the stages of a research project, the skills of each stage, and one line
per skill. Every skill folder under plugins/ needs exactly one line there, and every line needs a folder;
otherwise the build stops and names the difference. The counts of reference files, scripts and test cases
are read from the folders. README.md holds two generated blocks, each between a BEGIN and an END comment:
"map" (totals and the skills by stage) and "catalog" (one line per skill). docs/INDEX.md repeats the list with
each skill's own description and what ships inside it. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools" / "catalog.json"
README = ROOT / "README.md"
INDEX = ROOT / "docs" / "INDEX.md"
CODE = {".py", ".js", ".mjs", ".sh"}
BEGIN = "<!-- BEGIN GENERATED {name}: edit tools/catalog.json, then run python3 tools/build_index.py -->"
END = "<!-- END GENERATED {name} -->"
WORDS = {2: "two", 3: "three", 4: "four", 5: "five"}
MAX_LINE = 72


def find_skills() -> dict:
    """{skill name: its folder} for every plugin of this repository."""
    out: dict = {}
    for skill_md in sorted((ROOT / "plugins").glob("*/skills/*/SKILL.md")):
        name = skill_md.parent.name
        if name in out:
            raise SystemExit(f"two skills are named {name}: {out[name]} and {skill_md.parent}")
        out[name] = skill_md.parent
    return out


def plugin_of(folder: Path) -> str:
    return folder.parent.parent.name


def inside(folder: Path) -> dict:
    """Counts of what ships with one skill, by the same rules as tools/stats.py."""
    c = dict(references=0, scripts=0, tests=0, graders=0)
    for f in folder.rglob("*"):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(folder).parts
        if rel[0] == "references" and f.suffix == ".md":
            c["references"] += 1
        elif rel[0] == "scripts" and f.suffix in CODE:
            c["scripts"] += 1
        elif rel[0] == "evals" and f.name == "case.yaml":
            c["tests"] += 1
        elif rel[0] == "evals" and f.parent.name == "graders":
            c["graders"] += 1
    return c


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def inside_text(c: dict) -> str:
    parts = [plural(c[k], w) for k, w in (("references", "reference"), ("scripts", "script"), ("tests", "test")) if c[k]]
    return ", ".join(parts) or "SKILL.md only"


def first_sentence(folder: Path) -> str:
    text = (folder / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^description:\s*(.+)$", text, re.M)
    desc = m.group(1).strip().strip("\"'") if m else ""
    s = re.match(r"(.+?[.!?])(\s|$)", desc)
    return (s.group(1) if s else desc).strip().replace("|", "/")


def load() -> tuple:
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    skills = find_skills()
    listed: list = []
    problems: list = []
    for stage in cat["stages"]:
        for name, line in stage["skills"].items():
            listed.append(name)
            if "|" in line or not line.endswith(".") or len(line) > MAX_LINE:
                problems.append(f"{name}: the line must end with a period, hold no | and stay within "
                                f"{MAX_LINE} characters, so that it fits one row of the README ({len(line)} now)")
    for name in sorted(set(skills) - set(listed)):
        problems.append(f"{name}: a skill folder with no line in tools/catalog.json")
    for name in sorted(set(listed) - set(skills)):
        problems.append(f"{name}: a line in tools/catalog.json with no skill folder")
    for name in sorted({n for n in listed if listed.count(n) > 1}):
        problems.append(f"{name}: listed twice in tools/catalog.json")
    for plugin in sorted({plugin_of(f) for f in skills.values()} - set(cat["plugins"])):
        problems.append(f"{plugin}: a plugin with no entry under \"plugins\" in tools/catalog.json")
    if problems:
        raise SystemExit("tools/catalog.json and plugins/ disagree:\n  " + "\n  ".join(problems))
    return cat, skills


def mark_of(plugin: str) -> str:
    return plugin.split("-", 1)[-1].upper()


def linked(name: str, skills: dict, first_plugin: str, base: str = "") -> str:
    """The linked skill name, with a mark when the skill is in another plugin than the first one."""
    folder = skills[name]
    tag = "" if plugin_of(folder) == first_plugin else f"&nbsp;<sup>{mark_of(plugin_of(folder))}</sup>"
    return f"[`{name}`]({base}{folder.relative_to(ROOT).as_posix()}){tag}"


def render_map(cat: dict, skills: dict) -> str:
    tot = dict(references=0, scripts=0, tests=0, graders=0)
    per_plugin: dict = {}
    for folder in skills.values():
        for k, v in inside(folder).items():
            tot[k] += v
        per_plugin[plugin_of(folder)] = per_plugin.get(plugin_of(folder), 0) + 1
    plugins = " and ".join(f"`{p}` ({plural(per_plugin.get(p, 0), 'skill')}, {what})" for p, what in cat["plugins"].items())
    lines = [f"**{plural(len(skills), 'skill')}, {tot['references']:,} reference files, {tot['scripts']:,} scripts, "
             f"{tot['tests']:,} test cases with {tot['graders']:,} graded checks.** "
             f"They come as {WORDS.get(len(cat['plugins']), len(cat['plugins']))} plugins: {plugins}.", "",
             "The skills follow a research project from the first idea to the release:", "",
             "| Stage of a project | Skills |", "|---|---|"]
    for i, stage in enumerate(cat["stages"], 1):
        names = ", ".join(f"`{n}`" for n in stage["skills"])
        lines.append(f"| {i}. {stage['title']} | {names} |")
    return "\n".join(lines)


def render_catalog(cat: dict, skills: dict) -> str:
    first_plugin = next(iter(cat["plugins"]))
    others = [p for p in cat["plugins"] if p != first_plugin]
    note = ""
    if others:
        marks = " and ".join(f"<sup>{mark_of(p)}</sup> marks a skill of the `{p}` plugin" for p in others)
        note = f" {marks}; every other skill is in `{first_plugin}`."
    lines = [f"{plural(len(skills), 'skill')}, one line each.{note}", ""]
    for i, stage in enumerate(cat["stages"], 1):
        say = ", ".join(f'"{s}"' for s in stage["say"])
        lines += [f"### {i}. {stage['title']}", "", f"You say, for example: {say}.", "",
                  "| Skill | What it does |", "|---|---|"]
        for name, line in stage["skills"].items():
            lines.append(f"| {linked(name, skills, first_plugin)} | {line} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_index(cat: dict, skills: dict) -> str:
    lines = ["# Skill catalog", "",
             "Generated by `tools/build_index.py` from `tools/catalog.json` and each skill's own description. "
             "Do not edit by hand.", "",
             "The README has one short line per skill. Here each skill is described by the first sentence of the "
             "description that Claude reads when it decides whether to load it.", ""]
    for i, stage in enumerate(cat["stages"], 1):
        lines += [f"## {i}. {stage['title']}", "", "| Skill | Plugin | What it does | Inside |", "|---|---|---|---|"]
        for name in stage["skills"]:
            folder = skills[name]
            lines.append(f"| [`{name}`](../{folder.relative_to(ROOT).as_posix()}) | `{plugin_of(folder)}` | "
                         f"{first_sentence(folder)} | {inside_text(inside(folder))} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def splice(text: str, name: str, block: str) -> str:
    begin, end = BEGIN.format(name=name), END.format(name=name)
    if text.count(begin) != 1 or text.count(end) != 1:
        raise SystemExit(f"README.md needs exactly one pair of markers for the block '{name}':\n  {begin}\n  {end}")
    head, rest = text.split(begin)
    _, tail = rest.split(end)
    return f"{head}{begin}\n{block}\n{end}{tail}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if README.md or docs/INDEX.md is out of date")
    a = ap.parse_args()
    cat, skills = load()
    old_readme = README.read_text(encoding="utf-8")
    new_readme = splice(splice(old_readme, "map", render_map(cat, skills)), "catalog", render_catalog(cat, skills))
    new_index = render_index(cat, skills)
    head = "\n".join(new_readme.splitlines()[:12])
    if not re.search(rf"\b{len(skills)} (hard )?skills\b", head):
        raise SystemExit(f"README.md: the lines under the title do not say '{len(skills)} skills'; update them")
    if a.check:
        ok = True
        if old_readme != new_readme:
            ok = False
            print("README.md is out of date: run python3 tools/build_index.py")
        if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != new_index:
            ok = False
            print("docs/INDEX.md is out of date: run python3 tools/build_index.py")
        if ok:
            print(f"README.md and docs/INDEX.md are up to date ({len(skills)} skills)")
        return 0 if ok else 1
    README.write_text(new_readme, encoding="utf-8")
    INDEX.parent.mkdir(exist_ok=True)
    INDEX.write_text(new_index, encoding="utf-8")
    print(f"wrote the generated blocks of README.md and docs/INDEX.md ({len(skills)} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
