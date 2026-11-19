#!/usr/bin/env python3
"""Audit an ablation folder against the config you ship, before any arm is queued.

For every arm (*.yaml or *.json in the folder) it checks:
  - the arm opens with a comment block naming the claim it tests (YAML only);
  - its base: chain resolves, and the root of that chain is the shipped config given by --base
    (an ablation family built on another base ablates the wrong recipe);
  - it differs from the shipped config in at least one key (arms that differ only in comments build the
    same network);
  - it does not resolve to the same config as another arm;
  - with --max-keys N, it changes at most N keys (one arm, one intervention);
  - with --schema, every key exists in the schema.
Then it prints a markdown table: arm, claim, changed keys.

Dependencies: Python 3.9+, PyYAML; resolve_config.py beside this file.

Example:
    python3 ablation_audit.py configs/ablation --base configs/base.yaml --max-keys 3

Exit codes: 0 every arm passed; 1 at least one error.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_config import _load, config_hash, read_yaml, unknown_keys  # noqa: E402


def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict) and v:
            out.update(flatten(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def root_of(path: Path) -> Path:
    """Follow base: links to the first file without one."""
    seen = set()
    path = path.resolve()
    while path not in seen:
        seen.add(path)
        base = _load(path).get("base")
        if not base:
            return path
        path = (path.parent / base).resolve()
    raise ValueError(f"base cycle at {path}")


def claim_of(path: Path) -> str:
    if path.suffix == ".json":
        return ""
    lines = []
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s:
            if lines:
                break
            continue
        if not s.startswith("#"):
            break
        lines.append(s.lstrip("#").strip())
    return " ".join(x for x in lines if x)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="folder of ablation configs")
    ap.add_argument("--base", required=True, help="the config you ship; every arm's base chain must end here")
    ap.add_argument("--schema", help="config listing every allowed key (default: --base)")
    ap.add_argument("--max-keys", type=int, default=0, help="error when an arm changes more keys (0 = no limit)")
    a = ap.parse_args(argv)

    base_path = Path(a.base).resolve()
    shipped = flatten(read_yaml(base_path))
    schema = read_yaml(a.schema or base_path)
    arms = sorted(p for p in Path(a.folder).iterdir()
                  if p.suffix in (".yaml", ".yml", ".json") and p.resolve() != base_path)
    if not arms:
        print(f"FAIL  no configs in {a.folder}")
        return 1

    errors, rows, by_hash = [], [], {}
    for p in arms:
        try:
            raw = read_yaml(p)
            root = root_of(p)
        except ValueError as e:
            errors.append(f"{p.name}: {e}")
            continue
        if root != base_path:
            errors.append(f"{p.name}: base chain ends at {root.name}, not at the shipped {base_path.name}")
        claim = claim_of(p)
        if not claim and p.suffix != ".json":
            errors.append(f"{p.name}: no claim comment at the top")
        bad = unknown_keys(raw, schema)
        if bad:
            errors.append(f"{p.name}: unknown key(s) {bad}")
        flat = flatten(raw)
        changed = sorted(k for k in set(flat) | set(shipped) if flat.get(k, "<absent>") != shipped.get(k, "<absent>"))
        if not changed:
            errors.append(f"{p.name}: identical to the shipped config (differs only in comments?)")
        if a.max_keys and len(changed) > a.max_keys:
            errors.append(f"{p.name}: changes {len(changed)} keys (> {a.max_keys}); one arm, one intervention")
        h = config_hash(raw)
        if h in by_hash:
            errors.append(f"{p.name}: resolves to the same config as {by_hash[h]}")
        by_hash.setdefault(h, p.name)
        rows.append((p.name, claim or "(none)", ", ".join(f"{k}={flat.get(k, '<absent>')}" for k in changed)))

    print("| arm | claim | changed keys |\n|---|---|---|")
    for r in rows:
        print("| " + " | ".join(x.replace("|", "/") for x in r) + " |")
    print()
    for e in errors:
        print(f"ERROR  {e}")
    print(f"{'FAIL' if errors else 'OK'}  {len(arms)} arm(s) checked against {base_path.name}: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
