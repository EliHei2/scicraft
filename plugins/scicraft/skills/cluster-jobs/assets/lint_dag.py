#!/usr/bin/env python3
"""lint_dag.py: check a campaign's stage graph before anything is queued.

A graph defect in an unattended campaign shows up days later as "void: attempts exhausted" or as
a stage blocked forever with a note that reads like progress. This finds those defects in a
second, on the submit host, with the standard library only (Python 3.9 or later).

It fails on:
  DUPLICATE ID         two stages with one id
  UNKNOWN DEPENDENCY   a `needs` or `smoke` entry that names no stage (ready() waits forever)
  DEPENDENCY CYCLE     a cycle over needs plus smoke (a smoke stage is a hard dependency)
  UNKNOWN GATE         a stage waits on a gate the registry does not declare
  UNREACHABLE GATE     a declared gate no stage waits on, or one whose stages can never run
                       because they sit on a cycle or below an unknown dependency
  MISSING SCRIPT       a stage's job script does not exist
  DONE DEPENDENCY      `done(` or `afterok` in a job script or a stage's extra submit options:
                       a failed upstream leaves the dependent pending forever; use ended()
                       or afterany and let the job check its upstream sentinels
  UNBRACED EXPANSION   any `$NAME` without braces in a job script. Ten stages once wrote
                       `$PANEL_s$SEED`; bash reads `$PANEL_s` as one variable, so under `set -u`
                       the job dies before its sentinel, and without it two arms write to one
                       directory. `${PANEL}_s${SEED}` cannot fail either way, so every named
                       expansion is braced.

Usage:
    lint_dag.py REGISTRY.json [--verbose]
    lint_dag.py --self-test
Exit 0 when clean, 1 on any problem.
Suggested, not yet tested in real work: reduced from a linter that guarded a campaign graph which
was built and verified but not launched; exercised here with --self-test.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile

DONE_DEP = re.compile(r"done\(|afterok")
UNBRACED = re.compile(r"\$(?![{(])([A-Za-z_][A-Za-z0-9_]*)")


def lint(registry: str, verbose: bool = False) -> list:
    dag = json.load(open(registry))
    root = os.path.dirname(os.path.abspath(registry))
    stages = dag.get("stages", [])
    gates = set(dag.get("gates", {}))
    problems = []
    ids = [s["id"] for s in stages]
    for sid in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append((sid, "DUPLICATE ID", "two stages share this id"))
    idset = set(ids)

    edges = {}
    for s in stages:
        deps = list(s.get("needs") or []) + ([s["smoke"]] if s.get("smoke") else [])
        for d in deps:
            if d not in idset:
                problems.append((s["id"], "UNKNOWN DEPENDENCY", f"{d} is not a stage id"))
        edges[s["id"]] = deps

    # cycles, by depth-first search over known edges
    color = dict.fromkeys(edges, 0)
    on_cycle = set()

    def walk(n, stack):
        color[n] = 1
        for d in edges[n]:
            if d not in edges:
                continue
            if color[d] == 1:
                cyc = stack[stack.index(d):] + [n, d] if d in stack else [n, d]
                on_cycle.update(cyc)
                problems.append((n, "DEPENDENCY CYCLE", " -> ".join(cyc)))
            elif color[d] == 0:
                walk(d, stack + [n])
        color[n] = 2

    for n in edges:
        if color[n] == 0:
            walk(n, [])

    # a stage can run only if every dependency exists, is off any cycle, and can run itself
    runnable = {}

    def can_run(n, seen=()):
        if n in runnable:
            return runnable[n]
        if n not in edges or n in on_cycle or n in seen:
            return False
        ok = all(can_run(d, seen + (n,)) for d in edges[n])
        runnable[n] = ok
        return ok

    used = {}
    for s in stages:
        g = s.get("gate")
        if g:
            used.setdefault(g, []).append(s["id"])
            if g not in gates:
                problems.append((s["id"], "UNKNOWN GATE", f"{g} is not declared under gates"))
    for g in sorted(gates):
        if g not in used:
            problems.append((g, "UNREACHABLE GATE", "declared, but no stage waits on it"))
        elif not any(can_run(sid) for sid in used[g]):
            problems.append((g, "UNREACHABLE GATE", "every stage behind it sits on a cycle or an unknown dependency"))

    for s in stages:
        extra = " ".join(str(x) for x in (s.get("resources") or {}).get("extra", []))
        if DONE_DEP.search(extra):
            problems.append((s["id"], "DONE DEPENDENCY", f"extra submit options: {extra}"))
        if not s.get("script"):
            continue
        path = os.path.join(root, s["script"])
        if not os.path.isfile(path):
            problems.append((s["id"], "MISSING SCRIPT", s["script"]))
            continue
        for no, line in enumerate(open(path, errors="replace"), 1):
            code = line.split("#", 1)[0] if not line.lstrip().startswith("#BSUB") else line
            if DONE_DEP.search(code):
                problems.append((s["id"], "DONE DEPENDENCY", f"{s['script']}:{no}: {line.strip()[:80]}"))
            for m in UNBRACED.finditer(code):
                name = m.group(1)
                problems.append((s["id"], "UNBRACED EXPANSION",
                                 f"{s['script']}:{no}: ${name}; write ${{{name}}} (or ${{NAME}}_x if the name ends earlier)"))
        if verbose:
            print(f"  checked {s['id']}: {s['script']}")
    return problems


def report(problems: list, n: int) -> int:
    print(f"lint_dag: checked {n} stage(s)")
    if not problems:
        print("LINT OK")
        return 0
    print(f"LINT FAIL: {len(problems)} problem(s)")
    for sid, kind, det in sorted(problems, key=lambda p: (p[1], p[0])):
        print(f"  {kind:<20} {sid:<16} {det}")
    return 1


def self_test() -> int:
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(os.path.join(t, "jobs"))
        open(os.path.join(t, "jobs", "ok.sh"), "w").write('set -u\necho "${ARM}_s${SEED}"\n')
        open(os.path.join(t, "jobs", "bad.sh"), "w").write('bsub -w "done(12)" < x.sh\necho $ARM_s$SEED\n')
        good = {"gates": {"G": {}}, "stages": [
            {"id": "a", "script": "jobs/ok.sh"},
            {"id": "b", "script": "jobs/ok.sh", "needs": ["a"], "gate": "G"}]}
        bad = {"gates": {"G": {}, "Gorphan": {}, "Gcyc": {}}, "stages": [
            {"id": "a", "script": "jobs/bad.sh"},
            {"id": "b", "script": "jobs/ok.sh", "needs": ["zz"], "gate": "Gnone"},
            {"id": "c", "script": "jobs/ok.sh", "needs": ["d"], "gate": "Gcyc"},
            {"id": "d", "script": "jobs/ok.sh", "smoke": "c"},
            {"id": "e", "script": "jobs/missing.sh", "gate": "G",
             "resources": {"extra": ["--dependency=afterok:5"]}},
            {"id": "e", "script": "jobs/ok.sh"}]}
        json.dump(good, open(os.path.join(t, "good.json"), "w"))
        json.dump(bad, open(os.path.join(t, "bad.json"), "w"))
        fails = []
        if lint(os.path.join(t, "good.json")):
            fails.append("a clean graph reported problems")
        kinds = {k for _, k, _ in lint(os.path.join(t, "bad.json"))}
        want = {"DUPLICATE ID", "UNKNOWN DEPENDENCY", "DEPENDENCY CYCLE", "UNKNOWN GATE",
                "UNREACHABLE GATE", "MISSING SCRIPT", "DONE DEPENDENCY", "UNBRACED EXPANSION"}
        if want - kinds:
            fails.append(f"missed: {sorted(want - kinds)}")
    if fails:
        print("SELF-TEST FAILED: " + "; ".join(fails))
        return 1
    print("SELF-TEST PASSED (clean graph passes; all eight defect kinds caught)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("registry", nargs="?", help="the stage graph (JSON)")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not a.registry:
        p.print_help()
        return 64
    probs = lint(a.registry, a.verbose)
    return report(probs, len(json.load(open(a.registry)).get("stages", [])))


if __name__ == "__main__":
    sys.exit(main())
