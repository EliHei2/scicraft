#!/usr/bin/env python3
"""Round-trip test of the results store: resume, lineage rebuild, sharding, claims, check.

Run with pytest (`pytest tests/test_store.py`) or alone (`python3 test_store.py`). It finds the store
next to itself (results_store.py, in the skill) or at src/<pkg>/store.py of the project it sits in
(tests/test_store.py, where the scaffold puts it); --store PATH names it explicitly.

Checks, each on a fresh temporary root:
  1. a second fill reports every id as cached and calls the work function zero times;
  2. a derived id rebuilds byte-identically from its parent and the seed read off the id;
  3. a root without manifest.json fails check, and passes once finish() has run;
  4. shards (k, n) split the ids with no overlap and no gap; a claim is taken once only;
  5. a failing section prints SKIPPED, logs one failure row and lets the next section run.

Needs pandas and pyarrow (the store's views do). Exits 0 when every check passes.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STORE_PATH: Path | None = None


def _find_store() -> Path:
    if _STORE_PATH is not None:
        return _STORE_PATH
    if (HERE / "results_store.py").exists():
        return HERE / "results_store.py"
    found = sorted(HERE.parent.glob("src/*/store.py"))
    if not found:
        raise FileNotFoundError("no results_store.py beside this file and no src/<pkg>/store.py; pass --store")
    return found[0]


def _load():
    spec = importlib.util.spec_from_file_location("results_store_under_test", _find_store())
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _toy_values(iid: str, seed: int, n: int = 16) -> list:
    """Deterministic stand-in for real work: n numbers from the id and the seed."""
    out, h = [], hashlib.sha256(f"{iid}|{seed}".encode()).digest()
    while len(out) < n:
        out.extend(b / 255 for b in h)
        h = hashlib.sha256(h).digest()
    return out[:n]


def _derive(parent_vals: list, kind: str, level: float, seed: int) -> list:
    noise = _toy_values(f"{kind}@{level}", seed, len(parent_vals))
    return [v + level * (z - 0.5) for v, z in zip(parent_vals, noise)]


def _fill(rs, st, ids, calls):
    import pandas as pd
    for i in st.todo("toy", ids):
        calls.append(i)
        p = rs.parse_child_id(i)
        vals = _derive(_toy_values(p["parent"], 0), p["kind"], p["level"], p["seed"]) if p else _toy_values(i, 0)
        st.append_view("toy", pd.DataFrame([vals], index=[i], columns=[f"f{k}" for k in range(len(vals))]))
    st.set_view_meta("toy", {"model": "toy", "input": "id and seed"})


def test_cache_resume(tmp_path):
    rs = _load()
    st = rs.Store(tmp_path / "results" / "runs" / "quick", project_dir=tmp_path)
    st.start({"seed": 0})
    parents = [rs.item_id("toy", f"t{k}") for k in range(4)]
    kids = [rs.child_id(p, "noise", 0.1, 0) for p in parents[:2]]
    ids = parents + kids
    calls: list = []
    _fill(rs, st, ids, calls)
    assert len(calls) == len(ids)
    calls.clear()
    _fill(rs, st, ids, calls)
    assert calls == [], f"second fill recomputed {calls}"
    assert st.todo("toy", ids) == []


def test_lineage_rebuild(tmp_path):
    rs = _load()
    st = rs.Store(tmp_path / "results" / "runs" / "quick", project_dir=tmp_path)
    st.start({"seed": 0})
    parent = rs.item_id("toy", "t0")
    kid = rs.child_id(parent, "noise", 0.25, 7)
    _fill(rs, st, [parent, kid], [])
    stored = st.load_view("toy").loc[kid].tolist()
    p = rs.parse_child_id(kid)
    assert p == {"parent": parent, "kind": "noise", "level": 0.25, "seed": 7}
    rebuilt = _derive(st.load_view("toy").loc[parent].tolist(), p["kind"], p["level"], p["seed"])
    assert json.dumps(rebuilt) == json.dumps(stored), "derived item did not rebuild exactly from its parent"


def test_check_needs_manifest(tmp_path):
    rs = _load()
    root = tmp_path / "results" / "runs" / "quick"
    st = rs.Store(root, project_dir=tmp_path)
    st.start({"seed": 0})
    _fill(rs, st, [rs.item_id("toy", "t0")], [])
    with contextlib.redirect_stdout(io.StringIO()):
        assert any("manifest.json" in p for p in rs.check_root(root))
        st.finish(packages=())
        assert rs.check_root(root) == []


def test_shards_and_claims(tmp_path):
    rs = _load()
    st = rs.Store(tmp_path / "results" / "runs" / "quick", project_dir=tmp_path)
    ids = [f"toy/t{k}" for k in range(50)]
    parts = [st.todo("toy", ids, shard=(k, 3)) for k in range(3)]
    flat = [i for p in parts for i in p]
    assert sorted(flat) == sorted(ids) and len(flat) == len(set(flat)), "shards overlap or leave a gap"
    assert st.claim("toy", ids[0]) is True
    assert st.claim("toy", ids[0]) is False
    assert st.clear_claims("toy") == 1
    assert st.claim("toy", ids[0]) is True


def test_section_fails_softly(tmp_path):
    rs = _load()
    st = rs.Store(tmp_path / "results" / "runs" / "quick", project_dir=tmp_path)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with rs.section("broken step", st) as s:
            s["n"] = 1
            raise RuntimeError("no weights")
        with rs.section("next step", st) as s:
            s["n"] = 2
    out = buf.getvalue()
    assert "broken step: SKIPPED (RuntimeError: no weights)" in out
    assert "next step: n=2" in out
    assert [r["stage"] for r in st.failures()] == ["broken step"]


def test_setup_environment(tmp_path):
    rs = _load()
    import os
    st = rs.Store(tmp_path / "results" / "runs" / "quick", project_dir=tmp_path)
    saved = {k: os.environ.get(k) for k in ("DEMO_CACHE_A", "DEMO_CACHE_B")}
    try:
        os.environ.pop("DEMO_CACHE_A", None)
        os.environ["DEMO_CACHE_B"] = "/somewhere/else"
        got = rs.setup_environment(st, names=("DEMO_CACHE_A", "DEMO_CACHE_B"))
        # an unset variable goes to the shared cache beside runs/; a set one is kept
        assert got["DEMO_CACHE_A"] == str(tmp_path / "results" / "cache" / "demo_cache_a")
        assert os.environ["DEMO_CACHE_A"] == got["DEMO_CACHE_A"] and (tmp_path / "results" / "cache" / "demo_cache_a").is_dir()
        assert got["DEMO_CACHE_B"] == "/somewhere/else"
        st.start({"profile": "quick"})
        assert st.finish()["cache_env"] == got
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


TESTS = [test_cache_resume, test_lineage_rebuild, test_check_needs_manifest, test_shards_and_claims,
         test_section_fails_softly, test_setup_environment]


def main() -> int:
    global _STORE_PATH
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", type=Path, help="path of the store module to test")
    a = ap.parse_args()
    if a.store:
        _STORE_PATH = a.store.resolve()
    print(f"testing {_find_store()}")
    failed = 0
    for t in TESTS:
        with tempfile.TemporaryDirectory() as d:
            try:
                t(Path(d))
                print(f"ok    {t.__name__}")
            except Exception as e:
                failed += 1
                print(f"FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"{len(TESTS) - failed} of {len(TESTS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
