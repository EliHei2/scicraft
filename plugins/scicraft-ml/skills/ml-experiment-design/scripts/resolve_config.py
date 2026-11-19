#!/usr/bin/env python3
"""Resolve an experiment config: follow its ``base:`` chain, apply ``--set section.key=value`` overrides, refuse
unknown keys, and print the resolved config with a SHA-256 of its canonical JSON.

A YAML may start from another with ``base: <relative path>`` (deep-merged, the child wins), and ``--set`` overrides
both, so an ablation config is a few lines. Key every comparison between runs on the printed hash.

``read_yaml``, ``_deep_merge`` and ``apply_overrides`` are copied from the author's research code (Apache-2.0).
The schema check is the dict form of its typed builder: "Unknown keys are fatal, a silently-defaulted typo trains
the wrong run."

Dependencies: Python 3.9+, PyYAML for .yaml files (JSON configs need nothing).

Examples:
    python3 resolve_config.py configs/ablation/mean_pooling.yaml --schema configs/base.yaml
    python3 resolve_config.py configs/base.yaml --set train.lr=3e-4 --set model.depth=6 --out resolved.yaml

Exit codes: 0 resolved; 1 a config error (unknown key, bad override, missing base, base cycle).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict:
    text = path.read_text()
    if path.suffix == ".json":
        return json.loads(text) or {}
    try:
        import yaml
    except ImportError:
        sys.exit(f"PyYAML is needed to read {path.name} (pip install pyyaml), or use a .json config")
    return yaml.safe_load(text) or {}


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def read_yaml(path: str | Path, _seen: tuple = ()) -> dict:
    """The raw dict of a config, with its ``base:`` chain resolved (paths relative to the file)."""
    path = Path(path).resolve()
    if path in _seen:
        raise ValueError(f"base cycle: {' -> '.join(p.name for p in (*_seen, path))}")
    if not path.is_file():
        raise ValueError(f"config not found: {path}")
    raw = _load(path)
    base = raw.pop("base", None)
    return _deep_merge(read_yaml(path.parent / base, (*_seen, path)), raw) if base else raw


def apply_overrides(raw: dict, sets: tuple[str, ...] | list[str]) -> dict:
    """``section.key=value`` overrides; values parse as Python literals (lists, numbers, true/false), else str."""
    for s in sets:
        key, eq, val = s.partition("=")
        if not eq or "." not in key:
            raise ValueError(f"--set expects section.key=value, got {s!r}")
        low = val.strip().lower()
        if low in ("true", "false"):
            v: Any = low == "true"
        else:
            try:
                v = ast.literal_eval(val)
            except (ValueError, SyntaxError):
                v = val
        d = raw
        parts = key.split(".")
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = v
    return raw


def unknown_keys(cfg: dict, schema: dict, prefix: str = "") -> list[str]:
    """Dotted paths present in ``cfg`` but absent from ``schema`` (the base config that lists every knob)."""
    bad = []
    for k, v in cfg.items():
        path = f"{prefix}{k}"
        if k not in schema:
            bad.append(path)
        elif isinstance(v, dict) and isinstance(schema[k], dict):
            bad += unknown_keys(v, schema[k], path + ".")
    return bad


def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="YAML or JSON config, may contain base: <relative path>")
    ap.add_argument("--set", dest="sets", action="append", default=[], metavar="SECTION.KEY=VALUE",
                    help="override one knob; repeatable")
    ap.add_argument("--schema", help="config that lists every allowed key (usually the base); unknown keys fail")
    ap.add_argument("--out", help="write the resolved config here (.json or .yaml)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of YAML")
    a = ap.parse_args(argv)
    try:
        cfg = apply_overrides(read_yaml(a.config), a.sets)
        if a.schema:
            bad = unknown_keys(cfg, read_yaml(a.schema))
            if bad:
                raise ValueError(f"unknown config key(s) {bad} (not in {a.schema})")
    except ValueError as e:
        print(f"FAIL  {e}", file=sys.stderr)
        return 1
    h = config_hash(cfg)
    if a.json or a.out and a.out.endswith(".json"):
        text = json.dumps(cfg, indent=2, sort_keys=True, default=str)
    else:
        import yaml
        text = yaml.safe_dump(cfg, sort_keys=True)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(f"# config_sha256: {h}\n{text}" if not a.out.endswith(".json") else text)
    print(text.rstrip())
    print(f"OK  resolved {a.config} with {len(a.sets)} override(s)"
          f"{', checked against ' + a.schema if a.schema else ''}; config_sha256 {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
