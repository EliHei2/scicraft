#!/usr/bin/env python3
"""A small results store: one folder per run profile with a fixed contract inside.

  results_store.py init RESULTS --profile NAME     create RESULTS/runs/NAME/ and the shared folders
  results_store.py check RUN_ROOT [RUN_ROOT ...]   check run roots against the contract; exit 1 on a problem

The contract of one run root (RESULTS/runs/<profile>/), created when a Store opens it:

  config.json       resolved settings, written by start() before any work
  manifest.json     written by finish() at the end: config and its hash, packages, platform,
                    device, git commit with a dirty flag and a diff hash, item ids, view metadata,
                    failure count, cache folders, start and end time. A root without it is an
                    unfinished run.
  catalog.parquet   one row per data instance, index `id`; ids encode lineage
                    (<source>/<name>, child: <parent>~<kind>@<level>#<seed>)
  tables/           cached inputs, one file per item, named <readable stem>_<hash8>
  views/<view>/     per-view outputs as append-only part-NNNNN-<ns>.parquet, plus _meta.json
                    that says how the view was made
  models/           fitted transforms and trained weights
  analysis/         one table per analysis, plus _keys.json (recompute only when the key changes)
  figures/          <figN_topic>/panels/<panel>.{pdf,png}
  side/<name>/      ad hoc analyses by development scripts, each with a SUMMARY.md header
  logs/             run.log and failures.csv (time, stage, id, error)

Shared beside runs/: cache/ (downloads that must survive restarts), aggregate/ (cross-run tables
that feed the paper), archived/<date>_<reason>/ (superseded outputs, with MANIFEST.tsv).

From Python (copy this file into the package, e.g. src/<pkg>/store.py):

  from store import Store, child_id, setup_environment
  st = Store("results/runs/full")
  setup_environment(st)                               # before torch and friends are imported:
                                                      # their download caches go to RESULTS/cache/
  st.start(cfg_dict)                                  # refuses a different config in the same root
  for item in st.todo("model_a", all_ids):            # resumable: finished and failed ids are skipped
      try:
          st.append_view("model_a", embed(item))      # DataFrame indexed by id
      except Exception as e:
          st.log_failure(item, "model_a", e)          # one row, then keep going
  st.set_view_meta("model_a", {"checkpoint": "...", "layer": "...", "pooling": "mean"})
  with section("encode model_a", st) as s:            # one line of counts and time; an error is
      s["done"] = len(st.load_view("model_a"))         # logged as SKIPPED and the next section runs
  st.clear_claims("model_a")                          # at the start, before workers share a view:
  # in each worker: for i in st.todo("model_a", ids): if st.claim("model_a", i): ...
  # or static shards: st.todo("model_a", ids, shard=(k, n))
  out = st.fresh("figures/fig1_overview", reason="new color scale")   # archive before overwrite
  st.finish()

init and check need only the standard library. The catalog, views and cached tables need pandas
and pyarrow. Python 3.9 or later. check exits 0 when every root holds config.json, manifest.json,
only contract entries, a _meta.json per view and a SUMMARY.md per side analysis.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import hashlib
import importlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

SUBDIRS = ("tables", "views", "models", "analysis", "figures", "side", "logs")
ROOT_FILES = ("config.json", "manifest.json", "catalog.parquet")
SHARED = ("cache", "aggregate", "archived")
ARCHIVE_HEADER = "original\tarchived\tbytes\tfiles\tmoved_on\treason\tlink_left\n"
DEFAULT_PACKAGES = ("numpy", "pandas", "scipy", "sklearn", "torch", "matplotlib")
CACHE_ENV = ("HF_HOME", "TORCH_HOME", "XDG_CACHE_HOME", "MPLCONFIGDIR")


# ---------------------------------------------------------------- ids, seeds, names

def stable_seed(*parts: Any) -> int:
    """Deterministic 31-bit seed from named parts, independent of PYTHONHASHSEED."""
    h = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:8], 16) & 0x7FFFFFFF


def item_id(source: str, name: str) -> str:
    """Id of an original item: <source>/<name>."""
    return f"{source}/{name}"


def child_id(parent: str, kind: str, level: float, seed: int) -> str:
    """Id of an item derived from a parent: <parent>~<kind>@<level>#<seed>. Lineage reads off the id."""
    return f"{parent}~{kind}@{level:g}#{seed}"


def parse_child_id(cid: str) -> dict:
    """Inverse of child_id for the last derivation step; {} for an original item."""
    m = re.match(r"^(?P<parent>.+)~(?P<kind>[^~@#]+)@(?P<level>[^#]+)#(?P<seed>-?\d+)$", cid)
    if not m:
        return {}
    d = m.groupdict()
    return {"parent": d["parent"], "kind": d["kind"], "level": float(d["level"]), "seed": int(d["seed"])}


def safe_name(iid: str, limit: int = 120) -> str:
    """File name for an id: a readable stem plus 8 hex digits of its md5, so two ids never collide."""
    stem = "".join(c if c.isalnum() or c in "-_.@" else "_" for c in iid)
    return stem[:limit] + "_" + hashlib.md5(iid.encode()).hexdigest()[:8]


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")[:40] or "no-reason"


def _json_default(o: Any) -> Any:
    for attr in ("item", "tolist"):  # numpy scalars and arrays without importing numpy
        if hasattr(o, attr):
            try:
                return getattr(o, attr)()
            except Exception:
                pass
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def _sha256_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=_json_default).encode()).hexdigest()


# ---------------------------------------------------------------- environment

def package_versions(names: Iterable[str] = DEFAULT_PACKAGES) -> dict:
    out = {"python": platform.python_version()}
    for name in names:
        try:
            out[name] = str(getattr(importlib.import_module(name), "__version__", "?"))
        except Exception:
            out[name] = "missing"
    return out


def get_device() -> str:
    try:
        import torch
    except ImportError:
        return "cpu (torch not installed)"
    if torch.cuda.is_available():
        return f"cuda ({torch.cuda.get_device_name(0)})"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def git_state(path: str | Path = ".") -> dict:
    """Commit, a dirty flag and the sha256 of `git diff HEAD`, so an uncommitted run can still be traced."""
    def run(*args: str) -> str:
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True).stdout
    try:
        commit = run("rev-parse", "HEAD").strip()
    except Exception:
        return {"commit": "none", "dirty": None, "diff_sha256": None, "untracked": None}
    if not commit:
        return {"commit": "none", "dirty": None, "diff_sha256": None, "untracked": None}
    diff = run("diff", "HEAD")
    untracked = [ln for ln in run("status", "--porcelain").splitlines() if ln.startswith("??")]
    # an untracked script that produced results counts: the commit alone cannot rebuild them
    return {"commit": commit, "dirty": bool(diff or untracked), "untracked": len(untracked),
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff else None}


# ---------------------------------------------------------------- the store

class Store:
    """Everything one run profile produces lives under one root."""

    def __init__(self, root: str | Path, project_dir: str | Path = "."):
        self.root = Path(root)
        self.project_dir = Path(project_dir)
        for sub in SUBDIRS:
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        # inside RESULTS/runs/<profile>/ the shared folders sit beside runs/; elsewhere inside the root
        base = self.root.parent.parent if self.root.parent.name == "runs" else self.root
        self.cache_dir = base / "cache"
        self.archive_dir = base / "archived"
        self._t0 = time.time()

    # -- generic files
    def path(self, *parts: str) -> Path:
        p = self.root.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save_json(self, name: str, obj: Any) -> Path:
        p = self.path(name)
        p.write_text(json.dumps(obj, indent=1, default=_json_default) + "\n", encoding="utf-8")
        return p

    def load_json(self, name: str, default: Any = None) -> Any:
        p = self.root / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

    # -- start and end of a run
    def start(self, config: dict, allow_changed: bool = False) -> None:
        """Write config.json before any work. A different config in the same root is refused:
        give it its own profile, or archive the old root first."""
        old = self.load_json("config.json")
        config = json.loads(json.dumps(config, default=_json_default))  # tuples become lists, as on disk
        if old is not None and _sha256_obj(old) != _sha256_obj(config) and not allow_changed:
            changed = sorted(k for k in set(old) | set(config) if old.get(k) != config.get(k))
            raise ValueError(f"{self.root}: config differs from the saved one in {changed}; "
                             "use a new profile or archive this root first")
        self.save_json("config.json", config)
        # a resumed run is unfinished again until finish() writes a new manifest
        (self.root / "manifest.json").unlink(missing_ok=True)
        self._t0 = time.time()

    def finish(self, extra: dict | None = None, packages: Iterable[str] = DEFAULT_PACKAGES) -> dict:
        """Write manifest.json at the end. Prints a warning when the code had uncommitted changes."""
        cfg = self.load_json("config.json", {})
        items: list = []
        n_by_source: dict = {}
        if (self.root / "catalog.parquet").exists():
            cat = self.catalog()
            keep = [c for c in ("source", "parent_id", "seed", "version") if c in cat.columns]
            items = cat[keep].reset_index().to_dict("records")
            if "source" in cat.columns:
                n_by_source = {str(k): int(v) for k, v in cat["source"].value_counts().items()}
        views = sorted(p.name for p in (self.root / "views").iterdir() if p.is_dir())
        man = {
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "wall_seconds": round(time.time() - self._t0, 1),
            "config": cfg,
            "config_sha256": _sha256_obj(cfg),
            "packages": package_versions(packages),
            "platform": platform.platform(),
            "device": get_device(),
            "git": git_state(self.project_dir),
            "n_items": n_by_source,
            "items": items,
            "views": {v: self.view_meta(v) for v in views},
            "failures": len(self.failures()),
            "cache_env": getattr(self, "cache_env", {}),
        }
        if extra:
            man.update(extra)
        self.save_json("manifest.json", man)
        if man["git"].get("dirty"):
            print(f"warning: {self.root}: code had uncommitted changes or untracked files "
                  f"({man['git']['untracked']} untracked); the manifest records the diff hash; "
                  "commit before citing this run", file=sys.stderr)
        return man

    # -- catalog: one row per data instance
    def catalog(self):
        import pandas as pd
        p = self.root / "catalog.parquet"
        if not p.exists():
            return pd.DataFrame(columns=["id"]).set_index("id")
        return pd.read_parquet(p)

    def upsert_catalog(self, records: list) -> Any:
        """Insert or replace rows by id. Dicts and lists become JSON strings so each column keeps one type."""
        import pandas as pd
        if not records:
            return self.catalog()
        new = pd.DataFrame.from_records(records).set_index("id")
        old = self.catalog()
        cat = new if old.empty else pd.concat([old[~old.index.isin(new.index)], new])
        for c in cat.columns:
            if cat[c].dtype == "object":
                cat[c] = cat[c].map(lambda v: None if v is None or (isinstance(v, float) and v != v)
                                    else v if isinstance(v, str)
                                    else json.dumps(v, default=_json_default) if isinstance(v, (dict, list, tuple))
                                    else str(v))
        cat.to_parquet(self.root / "catalog.parquet")
        return cat

    # -- views: append-only outputs per representation, model or method
    def view_dir(self, view: str) -> Path:
        d = self.root / "views" / view
        d.mkdir(parents=True, exist_ok=True)
        return d

    def append_view(self, view: str, df: Any) -> None:
        """Write one new part. Earlier parts are never rewritten; a later row for the same id wins on load."""
        if df is None or len(df) == 0:
            return
        df = df.copy()
        df.index = df.index.astype(str)
        df.index.name = "id"
        df.columns = [str(c) for c in df.columns]
        n = len(list(self.view_dir(view).glob("part-*.parquet")))
        df.to_parquet(self.view_dir(view) / f"part-{n:05d}-{time.time_ns()}.parquet")

    def load_view(self, view: str) -> Any:
        import pandas as pd
        parts = sorted(self.view_dir(view).glob("part-*.parquet"))
        if not parts:
            return pd.DataFrame()
        df = pd.concat([pd.read_parquet(p) for p in parts])
        return df[~df.index.duplicated(keep="last")]

    def view_ids(self, view: str) -> set:
        import pandas as pd
        ids: set = set()
        for part in sorted(self.view_dir(view).glob("part-*.parquet")):
            ids.update(pd.read_parquet(part, columns=[]).index.astype(str))
        return ids

    def view_meta(self, view: str) -> dict:
        p = self.root / "views" / view / "_meta.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def set_view_meta(self, view: str, meta: dict) -> None:
        """How the view was made: model and version, layer, pooling, input, code version."""
        (self.view_dir(view) / "_meta.json").write_text(json.dumps(meta, indent=1, default=_json_default) + "\n",
                                                        encoding="utf-8")

    def todo(self, view: str, ids: Iterable[str], retry_failed: bool = False,
             shard: tuple | None = None) -> list:
        """Ids still to compute for a view: those already stored are skipped, and so are those that
        failed at this stage unless retry_failed is set. Running again after a crash resumes.
        shard=(k, n) keeps only the ids with stable_seed("shard", id) % n == k, so n processes can
        split one view without talking to each other."""
        ids = list(dict.fromkeys(str(i) for i in ids))
        if shard is not None:
            k, n = shard
            ids = [i for i in ids if stable_seed("shard", i) % n == k]
        done = self.view_ids(view)
        failed = set() if retry_failed else {r["id"] for r in self.failures() if r["stage"] == view}
        return [i for i in ids if i not in done and i not in failed]

    # -- claims: workers of unequal speed share one view
    def claim(self, view: str, iid: str) -> bool:
        """Claim one id for this process with an atomic file under views/<view>/.claims/. True when
        this process got it, False when another worker holds it. Unlike static shards, a fast worker
        keeps taking items while a slow one is busy."""
        d = self.view_dir(view) / ".claims"
        d.mkdir(exist_ok=True)
        try:
            os.close(os.open(str(d / safe_name(str(iid))), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return True
        except FileExistsError:
            return False

    def clear_claims(self, view: str) -> int:
        """Remove the claim files a crashed run left behind. Call once at the start of a run, before any
        worker starts; returns how many were removed."""
        d = self.root / "views" / view / ".claims"
        n = sum(1 for _ in d.iterdir()) if d.is_dir() else 0
        shutil.rmtree(d, ignore_errors=True)
        return n

    # -- failures: one row each, the run keeps going
    def log_failure(self, iid: str, stage: str, err: Any) -> None:
        msg = f"{type(err).__name__}: {err}" if isinstance(err, BaseException) else str(err)
        p = self.root / "logs" / "failures.csv"
        new = not p.exists()
        with p.open("a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["time", "stage", "id", "error"])
            w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), stage, iid, msg.replace("\n", " ")[:500]])

    def failures(self) -> list:
        p = self.root / "logs" / "failures.csv"
        if not p.exists():
            return []
        with p.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    # -- analysis tables, recomputed only when their inputs or settings change
    def cached(self, name: str, fn: Callable[[], Any], settings: Any = None, inputs: Iterable[str | Path] = ()) -> Any:
        """Return analysis/<name>.parquet, computing it with fn() when the key changed. The key hashes the
        settings and the bytes of every input file (for a view folder: every part and its _meta.json)."""
        import pandas as pd
        h = hashlib.sha256(json.dumps(settings, sort_keys=True, default=_json_default).encode())
        for inp in inputs:
            p = Path(inp)
            files = sorted(q for q in p.rglob("*") if q.is_file()) if p.is_dir() else [p]
            for f in files:
                h.update(str(f.relative_to(p) if p.is_dir() else f.name).encode())
                h.update(hashlib.sha256(f.read_bytes()).digest() if f.exists() else b"missing")
        key = h.hexdigest()
        keys = self.load_json("analysis/_keys.json", {})
        out = self.root / "analysis" / f"{name}.parquet"
        if keys.get(name) == key and out.exists():
            return pd.read_parquet(out)
        df = fn()
        df.to_parquet(out)
        keys[name] = key
        self.save_json("analysis/_keys.json", keys)
        return df

    # -- archive before overwrite
    def fresh(self, rel: str, reason: str) -> Path:
        """Return root/rel ready to be written. If it already holds anything, move it first to
        archived/<date>_<reason>/<profile>/<rel> and add a MANIFEST.tsv row. Nothing is overwritten."""
        target = self.root / rel
        if target.exists() and (target.is_file() or any(target.iterdir())):
            today = dt.date.today().isoformat()
            dest_root = self.archive_dir / f"{today}_{_slug(reason)}"
            dest = dest_root / self.root.name / rel
            k = 1
            while dest.exists():
                k += 1
                dest = dest_root / self.root.name / f"{rel}.{k}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            nbytes = sum(f.stat().st_size for f in ([target] if target.is_file() else target.rglob("*")) if f.is_file())
            nfiles = 1 if target.is_file() else sum(1 for f in target.rglob("*") if f.is_file())
            shutil.move(str(target), str(dest))
            man = dest_root / "MANIFEST.tsv"
            new = not man.exists()
            with man.open("a", encoding="utf-8") as fh:
                if new:
                    fh.write(ARCHIVE_HEADER)
                fh.write(f"{target}\t{dest}\t{nbytes}\t{nfiles}\t{today}\t{reason}\tno\n")
            print(f"archived {target} -> {dest}")
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
        return target

    def side(self, name: str, script: str, purpose: str = "") -> Path:
        """Folder for an ad hoc analysis by a development script, with a SUMMARY.md header naming the
        script, the date and the commit. Never a sibling folder of the run root."""
        d = self.root / "side" / name
        d.mkdir(parents=True, exist_ok=True)
        s = d / "SUMMARY.md"
        if not s.exists():
            g = git_state(self.project_dir)
            commit = (g["commit"] or "none")[:10] + (" + uncommitted changes" if g.get("dirty") else "")
            s.write_text(f"# {name} ({script}, {dt.date.today().isoformat()}, {commit})\n\n"
                         f"{purpose or '[what this analysis asks]'}\n\n## Facts\n\n1. [one fact per line, "
                         "each with the file that holds it]\n\n## Caveats\n\n- [what this does not show]\n",
                         encoding="utf-8")
        return d


# ---------------------------------------------------------------- fail-soft sections

@contextlib.contextmanager
def section(label: str, store: "Store | None" = None):
    """Run one notebook or pipeline section and print one line: `label: k=v, ... (12.3 s)`.
    The body fills the yielded dict with counts. On an exception the line reads
    `label: SKIPPED (<error>) (t s)`, the error goes to logs/failures.csv with id "-", and the
    next section runs. KeyboardInterrupt and SystemExit are not caught."""
    info: dict = {}
    t0 = time.perf_counter()
    try:
        yield info
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        if store is not None:
            store.log_failure("-", label, e)
        print(f"{label}: SKIPPED ({msg[:200]}) ({time.perf_counter() - t0:.1f} s)", flush=True)
        return
    extra = ", ".join(f"{k}={v}" for k, v in info.items())
    secs = f"({time.perf_counter() - t0:.1f} s)"
    print(f"{label}: {extra} {secs}" if extra else f"{label} {secs}", flush=True)


# ---------------------------------------------------------------- caches beside the results

def setup_environment(store: "Store", names: Iterable[str] = CACHE_ENV, overwrite: bool = False) -> dict:
    """Point the download caches of model and data libraries into the store's shared cache folder,
    so that a hosted runtime's downloads land beside the results and a rerun finds them.
    Call it before the first import of a library that reads these variables (torch, transformers,
    datasets, matplotlib): each reads the environment once, at import. A variable that is already
    set is kept unless overwrite is true. finish() writes the mapping to manifest.json as
    "cache_env". Returns {variable: folder}."""
    out: dict = {}
    for name in names:
        if os.environ.get(name) and not overwrite:
            out[name] = os.environ[name]
            continue
        folder = store.cache_dir / name.lower()
        folder.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(folder)
        out[name] = str(folder)
    store.cache_env = out
    return out


# ---------------------------------------------------------------- command line

def check_root(root: Path) -> list:
    problems = []
    if not root.is_dir():
        return [f"{root}: not a folder"]
    if not (root / "config.json").exists():
        problems.append(f"{root}: no config.json (written at the start of every run)")
    if not (root / "manifest.json").exists():
        problems.append(f"{root}: no manifest.json; the run did not finish, or it ended without one. "
                        "Do not cite it; resume it or archive it")
    allowed = set(SUBDIRS) | set(ROOT_FILES)
    for e in sorted(root.iterdir()):
        if e.name.startswith(".") or e.name in allowed:
            continue
        if e.suffix == ".ipynb":  # an executed notebook moved into its run root
            continue
        problems.append(f"{root}: stray entry '{e.name}'; ad hoc output belongs in side/<name>/, "
                        "shared downloads in cache/")
    views = root / "views"
    if views.is_dir():
        for v in sorted(p for p in views.iterdir() if p.is_dir()):
            if any(v.glob("part-*")) and not (v / "_meta.json").exists():
                problems.append(f"{root}: view '{v.name}' has no _meta.json saying how it was made")
    side = root / "side"
    if side.is_dir():
        for s in sorted(p for p in side.iterdir() if p.is_dir()):
            if not (s / "SUMMARY.md").exists():
                problems.append(f"{root}: side/{s.name} has no SUMMARY.md naming the script that made it")
    man = root / "manifest.json"
    if man.exists():
        try:
            g = json.loads(man.read_text(encoding="utf-8")).get("git", {})
            if g.get("dirty"):
                print(f"note: {root}: made with uncommitted changes (diff sha256 {str(g.get('diff_sha256'))[:12]})")
        except json.JSONDecodeError:
            problems.append(f"{root}: manifest.json is not valid JSON")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="create RESULTS/runs/<profile>/ and RESULTS/{cache,aggregate,archived}/")
    i.add_argument("results", type=Path)
    i.add_argument("--profile", required=True, help="run profile, e.g. quick, full, full_gpu")
    c = sub.add_parser("check", help="check run roots against the contract")
    c.add_argument("roots", nargs="+", type=Path)
    a = ap.parse_args()

    if a.cmd == "init":
        root = a.results / "runs" / a.profile
        for d in SUBDIRS:
            (root / d).mkdir(parents=True, exist_ok=True)
        for d in SHARED:
            (a.results / d).mkdir(parents=True, exist_ok=True)
        print(f"created {root}/ with {', '.join(SUBDIRS)}; shared {', '.join(SHARED)} in {a.results}/")
        return 0

    problems = []
    for r in a.roots:
        problems += check_root(r)
    for p in problems:
        print("PROBLEM:", p)
    print(f"checked {len(a.roots)} run root(s): {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
