#!/usr/bin/env python3
"""Compare the public interface of a Python package between two versions.

    python3 interface_diff.py --repo . --old main --new WORKTREE [--paths src/pkg]
    python3 interface_diff.py --help-old old_help.txt --help-new new_help.txt

Mode 1 reads the .py files under --paths at two git refs (WORKTREE means the files on disk, including
uncommitted edits) and compares, without importing anything:

  functions   every public function, class and method (no leading underscore): parameters, order,
              defaults, *args and **kwargs
  options     every command-line option declared through add_argument, option, Option, argument,
              Argument or Parameter calls: the flag strings and the default= value

Mode 2 compares two saved `--help` outputs flag by flag, for a command line built some other way.

FAIL (exit 1): a public name or flag removed, a parameter removed or renamed, a new parameter
without a default, a default changed. INFO: additions that keep old calls working.
Standard library and git only; Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

OPTION_CALLS = {"add_argument", "option", "Option", "argument", "Argument", "Parameter"}
FLAG = re.compile(r"(?<![\w-])--?[A-Za-z][\w-]*")


def read_tree(repo: Path, ref: str, paths: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    if ref == "WORKTREE":
        for p in paths:
            root = repo / p
            cands = [root] if root.is_file() else sorted(root.rglob("*.py"))
            for f in cands:
                if f.suffix == ".py" and "__pycache__" not in f.parts:
                    files[str(f.relative_to(repo))] = f.read_text(errors="replace")
        return files
    out = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref, "--", *paths],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"git ls-tree {ref} failed: {out.stderr.strip()}")
    for name in out.stdout.split():
        if name.endswith(".py"):
            show = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{name}"], capture_output=True, text=True)
            files[name] = show.stdout
    return files


def signature(fn: ast.AST) -> dict:
    a = fn.args
    pos = a.posonlyargs + a.args
    defaults = [None] * (len(pos) - len(a.defaults)) + [ast.unparse(d) for d in a.defaults]
    params = [(p.arg, d) for p, d in zip(pos, defaults) if p.arg not in ("self", "cls")]
    kwonly = [(p.arg, ast.unparse(d) if d is not None else None) for p, d in zip(a.kwonlyargs, a.kw_defaults)]
    return {"params": params, "kwonly": kwonly, "vararg": bool(a.vararg), "kwarg": bool(a.kwarg)}


def collect(files: dict[str, str]) -> tuple[dict, dict]:
    funcs, opts = {}, {}
    for path, src in files.items():
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            print(f"WARN  cannot parse {path}: {e}")
            continue
        mod = path[:-3].replace("/", ".")

        def visit(body, prefix):
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_") \
                        or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__init__":
                    funcs[f"{prefix}.{node.name}"] = signature(node)
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    funcs[f"{prefix}.{node.name}"] = {"class": True}
                    visit(node.body, f"{prefix}.{node.name}")
        visit(tree.body, mod)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name not in OPTION_CALLS:
                continue
            flags = [c.value for c in node.args if isinstance(c, ast.Constant) and isinstance(c.value, str)
                     and c.value.startswith("-")]
            if not flags:
                continue
            default = next((ast.unparse(k.value) for k in node.keywords if k.arg == "default"), None)
            key = max(flags, key=len)
            opts[key] = {"aliases": sorted(flags), "default": default, "where": path}
    return funcs, opts


def compare(old_f, new_f, old_o, new_o, say):
    for name in sorted(old_f):
        if name not in new_f:
            say("FAIL", "removed", name)
            continue
        o, n = old_f[name], new_f[name]
        if o.get("class") or n.get("class"):
            continue
        for kind in ("params", "kwonly"):
            onames = [p for p, _ in o[kind]]
            nnames = [p for p, _ in n[kind]]
            odef, ndef = dict(o[kind]), dict(n[kind])
            for p in onames:
                if p not in nnames and not (kind == "params" and p in dict(n["kwonly"])):
                    say("FAIL", "param gone", f"{name}({p})" + (" (absorbed by **kwargs)" if n["kwarg"] else ""))
                elif p in ndef and odef[p] != ndef[p]:
                    say("FAIL", "default", f"{name}({p}): {odef[p]} -> {ndef[p]}")
            if kind == "params" and [p for p in nnames if p in onames] != [p for p in onames if p in nnames]:
                say("FAIL", "order", f"{name}: positional order {onames} -> {nnames}")
            for p in nnames:
                if p not in onames and not (kind == "kwonly" and p in dict(o["params"])):
                    if ndef[p] is None:
                        say("FAIL", "required", f"{name}({p}) is new and has no default; old calls break")
                    else:
                        say("INFO", "added", f"{name}({p}={ndef[p]})")
        if o["kwarg"] and not n["kwarg"]:
            say("FAIL", "kwargs", f"{name} no longer accepts **kwargs")
    for name in sorted(set(new_f) - set(old_f)):
        say("INFO", "new", name)

    old_alias = {f: k for k, v in old_o.items() for f in v["aliases"]}
    for key, o in sorted(old_o.items()):
        match = next((new_o[k] for k in new_o if set(new_o[k]["aliases"]) & set(o["aliases"])), None)
        if match is None:
            say("FAIL", "flag gone", f"{key} ({o['where']})")
            continue
        lost = set(o["aliases"]) - set(match["aliases"])
        if lost:
            say("FAIL", "alias gone", f"{key}: {', '.join(sorted(lost))}")
        if o["default"] != match["default"]:
            say("FAIL", "default", f"{key}: {o['default']} -> {match['default']}")
    for key, n in sorted(new_o.items()):
        if not any(f in old_alias for f in n["aliases"]):
            say("INFO", "new flag", f"{key} default={n['default']}")


def help_flags(text: str) -> set[str]:
    return {m.group(0) for m in FLAG.finditer(text) if len(m.group(0)) > 2 or m.group(0) == "-h"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, default=Path("."), help="repository folder (default: .)")
    ap.add_argument("--old", default="main", help="reference version: a git ref (default: main)")
    ap.add_argument("--new", default="WORKTREE", help="changed version: a git ref or WORKTREE (default)")
    ap.add_argument("--paths", nargs="+", default=["."], help="package folders or files to read (default: .)")
    ap.add_argument("--help-old", type=Path, help="saved --help output of the reference version")
    ap.add_argument("--help-new", type=Path, help="saved --help output of the changed version")
    a = ap.parse_args()

    counts = {"FAIL": 0, "INFO": 0}

    def say(level, kind, msg):
        counts[level] = counts.get(level, 0) + 1
        print(f"{level:<5} {kind:<11} {msg}")

    if a.help_old or a.help_new:
        if not (a.help_old and a.help_new):
            ap.error("--help-old and --help-new go together")
        old, new = help_flags(a.help_old.read_text()), help_flags(a.help_new.read_text())
        for f in sorted(old - new):
            say("FAIL", "flag gone", f)
        for f in sorted(new - old):
            say("INFO", "new flag", f)
        print(f"\n{len(old)} flags before, {len(new)} after: "
              f"{'FAIL' if counts['FAIL'] else 'PASS'} (defaults in help text are not compared)")
        return 1 if counts["FAIL"] else 0

    old_f, old_o = collect(read_tree(a.repo, a.old, a.paths))
    new_f, new_o = collect(read_tree(a.repo, a.new, a.paths))
    if not old_f and not old_o:
        print(f"nothing public found under {a.paths} at {a.old}")
        return 2
    compare(old_f, new_f, old_o, new_o, say)
    print(f"\n{a.old} -> {a.new}: {len(old_f)} public names and {len(old_o)} options before; "
          f"{'FAIL' if counts['FAIL'] else 'PASS'} ({counts['FAIL']} breaking, {counts['INFO']} additions)")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
