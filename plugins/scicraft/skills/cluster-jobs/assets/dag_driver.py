#!/usr/bin/env python3
"""dag_driver.py: a deterministic campaign driver for a batch cluster. No model in it.

It reads a stage graph from a JSON registry, asks the scheduler what is alive, marks stages done
from verified sentinels, and submits what is ready. Running it twice submits nothing twice. Call
`step` every few minutes from a nohup supervisor loop or a self-resubmitting heartbeat job; an
agent is called only on a schedule or on an incident, and only through `retry`, `void`,
`incident` and `open-gate` (which demands an evidence file and numbers).

Standard library only, on purpose: login and submit hosts often cannot import the project's
NumPy, so this runs under the system python3 (3.9 or later).

Usage:
    dag_driver.py --config campaign.json init
    dag_driver.py --config campaign.json status
    dag_driver.py --config campaign.json step [--dry-run]
    dag_driver.py --config campaign.json open-gate G --by WHO --evidence FILE --numbers '...'
    dag_driver.py --config campaign.json close-gate G --by WHO --evidence FILE --numbers '...'
    dag_driver.py --config campaign.json void STAGE --why '...'
    dag_driver.py --config campaign.json retry STAGE --why '...' [--mem-scale 1.5]
    dag_driver.py --config campaign.json incident KIND STAGE --detail '...'
    dag_driver.py --config campaign.json chain A B C [--dry-run]
    dag_driver.py --config campaign.json seal STAGE      (called by the job itself, last)
    dag_driver.py --self-test

The config file is the user's local file (never shipped): cluster names, queues and paths live
there. Keys: registry (path to the stage graph), state_dir, scheduler (lsf, slurm or local),
job_prefix, max_attempts (default 3), pend_timeout_min (default 240), python (interpreter used in
the job wrapper to call `seal`; default python3).

The registry: {"gates": {"G1": {"desc": "..."}},
               "stages": [{"id": "S1", "script": "jobs/s1.sh", "needs": [], "gate": null,
                           "require": ["/abs/input/store"], "inputs": ["/abs/config.yaml"],
                           "outputs": ["/abs/results/s1.json"],
                           "resources": {"queue": "q", "mem_gb": 16, "wall": "4:00",
                                         "cores": 4, "gpus": 0, "extra": []}}]}

  require    paths that must exist before the stage is submitted (the first node of a graph
             lists the data store and every checkpoint the graph reads; a missing one blocks
             the stage and files an incident instead of burning a job)
  inputs     files whose sha256 the sentinel records; when one changes, the sentinel is stale,
             renamed to .done.stale, and the stage reruns
  outputs    files the job must leave non-empty; the sentinel stores their sha256 and size, and a
             truncated output renames the sentinel to .done.bad and counts an attempt
  gate       a gate id; the stage waits until the gate is opened with evidence. Nothing opens a
             gate by timeout or by default.

`state_dir/STOP` halts all new submissions. Only a human creates or removes it.
Suggested, not yet tested in real work: this is a reduced rewrite of a driver that was built and
verified for an unattended campaign but not launched; it was exercised here with --self-test and
the `local` scheduler only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

TERMINAL = {"done", "void", "skipped"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def jload(path: str, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def jdump(path: str, obj) -> None:
    """Temp file then rename: a half-written state file read by the heartbeat would look corrupt."""
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Campaign:
    def __init__(self, config: str):
        self.cfg = jload(config, None)
        if not self.cfg:
            sys.exit(f"cannot read config {config}")
        base = os.path.dirname(os.path.abspath(config))
        self.registry = os.path.join(base, self.cfg["registry"])
        self.dag = jload(self.registry, None)
        if not self.dag:
            sys.exit(f"cannot read registry {self.registry}")
        self.repo = os.path.dirname(os.path.abspath(self.registry))
        self.state = os.path.join(base, self.cfg["state_dir"])
        self.sched = self.cfg.get("scheduler", "lsf")
        self.prefix = self.cfg.get("job_prefix", "dag")
        self.max_attempts = int(self.cfg.get("max_attempts", 3))
        self.pend_s = int(self.cfg.get("pend_timeout_min", 240)) * 60
        self.python = self.cfg.get("python", "python3")
        self.config_path = os.path.abspath(config)
        p = lambda n: os.path.join(self.state, n)  # noqa: E731
        self.st_path, self.gates_path = p("dag.json"), p("gates.json")
        self.ledger, self.incidents, self.stop = p("ledger.jsonl"), p("incidents.jsonl"), p("STOP")
        self.sent_dir, self.job_dir, self.log_dir = p("sentinels"), p("jobs"), p("logs")
        self.stages = {s["id"]: s for s in self.dag["stages"]}

    # ---------------------------------------------------------------- records
    def append(self, path: str, rec: dict) -> None:
        with open(path, "a") as fh:
            fh.write(json.dumps({"ts": now(), **rec}) + "\n")

    def incident(self, kind: str, stage: str, detail: str) -> None:
        self.append(self.incidents, {"kind": kind, "stage": stage, "detail": detail[:500]})

    def sentinel(self, sid: str) -> str:
        return os.path.join(self.sent_dir, f"{sid}.done")

    # -------------------------------------------------------------- scheduler
    def live_jobs(self) -> dict:
        """job id -> state for this user's jobs. A failed query returns None: never act on it."""
        if self.sched == "local":
            return {}
        if self.sched == "lsf":
            cmd = ["bjobs", "-a", "-o", "jobid stat", "-noheader"]
        else:
            cmd = ["squeue", "-h", "-u", os.environ.get("USER", ""), "-o", "%i %T"]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        jobs = {}
        for line in out.splitlines():
            f = line.split()
            if len(f) >= 2 and f[0].isdigit():
                jobs[f[0]] = f[1]
        return jobs

    def submit(self, sid: str, wrapper: str, deps: list, dry: bool) -> str:
        r = dict(self.stages[sid].get("resources") or {})
        r.update(jload(os.path.join(self.state, "overrides.json"), {}).get(sid, {}))
        name = f"{self.prefix}-{sid}"
        log = os.path.join(self.log_dir, f"{sid}.%J" if self.sched == "lsf" else f"{sid}.%j")
        if self.sched == "lsf":
            cmd = ["bsub", "-J", name, "-o", log + ".out", "-e", log + ".err"]
            if r.get("queue"): cmd += ["-q", str(r["queue"])]
            if r.get("wall"): cmd += ["-W", str(r["wall"])]
            if r.get("mem_gb"): cmd += ["-M", f"{r['mem_gb']}G", "-R", f"rusage[mem={r['mem_gb']}G]"]
            if r.get("cores"): cmd += ["-n", str(r["cores"]), "-R", "span[hosts=1]"]
            if r.get("gpus"): cmd += ["-gpu", f"num={r['gpus']}"]
            if deps: cmd += ["-w", " && ".join(f"ended({d})" for d in deps)]
        elif self.sched == "slurm":
            cmd = ["sbatch", "--parsable", f"--job-name={name}", f"--output={log}.out", f"--error={log}.err"]
            if r.get("queue"): cmd.append(f"--partition={r['queue']}")
            if r.get("wall"): cmd.append(f"--time={r['wall']}:00")
            if r.get("mem_gb"): cmd.append(f"--mem={r['mem_gb']}G")
            if r.get("cores"): cmd.append(f"--cpus-per-task={r['cores']}")
            if r.get("gpus"): cmd.append(f"--gpus={r['gpus']}")
            if deps: cmd.append("--dependency=afterany:" + ":".join(deps))
        else:
            cmd = ["bash", wrapper]
        cmd += [str(x) for x in r.get("extra", [])]
        if self.sched != "local":
            cmd.append(wrapper)
        if dry:
            print("[dry] " + " ".join(cmd))
            return ""
        if self.sched == "lsf":
            with open(wrapper) as fh:
                out = subprocess.run(cmd[:-1], stdin=fh, capture_output=True, text=True)
            m = re.search(r"Job <(\d+)>", out.stdout)
            return m.group(1) if m else ""
        out = subprocess.run(cmd, capture_output=True, text=True)
        if self.sched == "slurm":
            return out.stdout.strip().split(";")[0] if out.returncode == 0 else ""
        return f"local-{int(time.time() * 1000)}"

    def wrapper(self, sid: str, after: list) -> str:
        """The job file: check upstream sentinels (ended() fires on failure too), run, seal."""
        s = self.stages[sid]
        os.makedirs(self.job_dir, exist_ok=True)
        lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
        for up in after:
            lines.append(f'[ -f "{self.sentinel(up)}" ] || {{ echo "upstream {up} has no sentinel"; exit 3; }}')
        lines.append(f'cd "{self.repo}"')
        lines.append(f'bash "{os.path.join(self.repo, s["script"])}"')
        lines.append(f'"{self.python}" "{os.path.abspath(__file__)}" --config "{self.config_path}" seal {sid}')
        path = os.path.join(self.job_dir, f"{sid}.sh")
        with open(path, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        return path

    # ------------------------------------------------------------- sentinels
    def seal(self, sid: str) -> int:
        s = self.stages[sid]
        outs = {}
        for o in s.get("outputs", []):
            if not (os.path.isfile(o) and os.path.getsize(o) > 0):
                print(f"SEAL REFUSED: output missing or empty: {o}")
                return 1
            outs[o] = {"sha256": sha256(o), "bytes": os.path.getsize(o)}
        ins = {i: sha256(i) for i in s.get("inputs", []) if os.path.isfile(i)}
        os.makedirs(self.sent_dir, exist_ok=True)
        jdump(self.sentinel(sid), {"stage": sid, "sealed": now(), "inputs": ins, "outputs": outs})
        print(f"sealed {sid}: {len(outs)} output(s), {len(ins)} input hash(es)")
        return 0

    def check_sentinel(self, sid: str) -> str:
        """'ok', 'none', 'bad' (output changed or truncated) or 'stale' (an input changed)."""
        path = self.sentinel(sid)
        rec = jload(path, None)
        if rec is None:
            return "none"
        for o, meta in rec.get("outputs", {}).items():
            if not os.path.isfile(o) or os.path.getsize(o) != meta["bytes"] or sha256(o) != meta["sha256"]:
                os.replace(path, path + ".bad")
                return "bad"
        for i, h in rec.get("inputs", {}).items():
            if not os.path.isfile(i) or sha256(i) != h:
                os.replace(path, path + ".stale")
                return "stale"
        return "ok"

    # ------------------------------------------------------------------ loop
    def reconcile(self, st: dict, live) -> None:
        for sid in self.stages:
            rec = st.setdefault(sid, {"status": "pending", "attempts": 0})
            if rec["status"] in ("void", "skipped"):
                continue
            verdict = self.check_sentinel(sid)
            if verdict == "ok":
                if rec["status"] != "done":
                    rec.update(status="done", finished=now())
                    self.append(self.ledger, {"kind": "DONE", "stage": sid})
                continue
            if verdict in ("bad", "stale"):
                self.incident(f"SENTINEL_{verdict.upper()}", sid, "sentinel renamed; stage reruns")
                if verdict == "bad":
                    rec["attempts"] += 1
                rec.update(status="pending", job_id=None)
            if rec["status"] == "done":
                rec["status"] = "pending"
            jid = rec.get("job_id")
            if rec["status"] not in ("submitted", "running") or not jid:
                continue
            if live is None:
                continue  # scheduler unreadable: act on nothing
            state = live.get(jid)
            if state in ("RUN", "RUNNING", "PROV", "CONFIGURING"):
                rec["status"] = "running"
            elif state in ("PEND", "PENDING"):
                if time.time() - rec.get("t0", time.time()) > self.pend_s and not rec.get("pend_flagged"):
                    rec["pend_flagged"] = True
                    self.incident("PEND_TIMEOUT", sid, f"job {jid} pending past the timeout; check the model string and the ask")
            elif self.sched != "local" and time.time() - rec.get("t0", 0) < 60:
                continue  # a read within 60 s of a submit can miss the job: never act on it
            else:  # finished, or forgotten by the scheduler, and no valid sentinel
                rec["attempts"] += 1
                rec["job_id"] = None
                if rec["attempts"] >= self.max_attempts:
                    rec.update(status="void", why=f"{rec['attempts']} attempts without a valid sentinel", finished=now())
                    self.incident("STAGE_VOID", sid, rec["why"])
                    self.append(self.ledger, {"kind": "VOID", "stage": sid, "why": rec["why"]})
                else:
                    rec["status"] = "pending"
                    self.incident("JOB_FAILED", sid, f"job {jid} ended without a sentinel; attempt {rec['attempts']}")
        # a stage that needs a void stage can never run: skip it, published with the reason
        changed = True
        while changed:
            changed = False
            for sid, s in self.stages.items():
                rec = st[sid]
                if rec["status"] not in TERMINAL and any(st[n]["status"] in ("void", "skipped") for n in s.get("needs", [])):
                    rec.update(status="skipped", why="an upstream stage is void", finished=now())
                    changed = True

    def ready(self, sid: str, st: dict, gates: dict) -> str:
        s = self.stages[sid]
        for n in s.get("needs", []):
            if st[n]["status"] != "done":
                return f"waiting on {n}"
        g = s.get("gate")
        if g and gates.get(g, {}).get("status") != "open":
            return f"gate {g} {gates.get(g, {}).get('status', 'pending')}"
        missing = [p for p in s.get("require", []) if not os.path.exists(p)]
        if missing:
            return "missing required input: " + missing[0]
        return ""

    def step(self, dry: bool) -> int:
        for d in (self.sent_dir, self.log_dir, self.job_dir):
            os.makedirs(d, exist_ok=True)
        st = jload(self.st_path, {})
        live = self.live_jobs()
        self.reconcile(st, live)
        gates = jload(self.gates_path, {})
        halted = os.path.exists(self.stop)
        if halted:
            print("STOP present: reconciling only, no submissions")
        if live is None:
            print("scheduler status unreadable: no submissions this pass" + (" (dry run lists them)" if dry else ""))
        n = 0
        for sid in self.stages:
            rec = st[sid]
            if rec["status"] in TERMINAL or rec["status"] in ("submitted", "running"):
                continue
            why = self.ready(sid, st, gates)
            if why:
                if why.startswith("missing") and rec.get("blocked_on") != why:
                    self.incident("INPUT_MISSING", sid, why)
                rec.update(status="blocked", blocked_on=why)
                continue
            rec.pop("blocked_on", None)
            if halted or (live is None and not dry):
                continue
            jid = self.submit(sid, self.wrapper(sid, []), [], dry)
            if dry:
                continue
            if not jid:
                self.incident("SUBMIT_FAILED", sid, "the scheduler returned no job id")
                continue
            rec.update(status="submitted", job_id=jid, t0=time.time())
            self.append(self.ledger, {"kind": "SUBMIT", "stage": sid, "job_id": jid})
            print(f"submitted {sid} -> {jid}")
            n += 1
        if self.sched == "local" and not dry and n:
            self.reconcile(st, {})  # local jobs ran synchronously; read their sentinels now
        if not dry:
            jdump(self.st_path, st)
        counts = {}
        for rec in st.values():
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
        print("step: " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())) + f" (submitted {n})")
        return 0

    def chain(self, ids: list, dry: bool) -> int:
        """Submit a sub-graph fixed now, with ended()/afterany dependencies. Each job checks its
        upstream sentinels itself, so a failed upstream stops the chain with a clear exit."""
        if os.path.exists(self.stop):
            print("STOP present: nothing submitted")
            return 1
        st = jload(self.st_path, {})
        jobs = {}
        for sid in ids:
            needs = [n for n in self.stages[sid].get("needs", []) if n in ids]
            deps = [jobs[n] for n in needs if jobs.get(n)]
            jid = self.submit(sid, self.wrapper(sid, needs), deps, dry)
            if dry:
                jobs[sid] = f"<id of {sid}>"
            else:
                jobs[sid] = jid
                st.setdefault(sid, {"attempts": 0}).update(status="submitted", job_id=jid, t0=time.time())
                self.append(self.ledger, {"kind": "SUBMIT", "stage": sid, "job_id": jid, "chain": True})
                print(f"chained {sid} -> {jid}")
        if not dry:
            jdump(self.st_path, st)
        return 0

    # ----------------------------------------------------------------- verbs
    def init(self) -> int:
        for d in (self.state, self.sent_dir, self.job_dir, self.log_dir):
            os.makedirs(d, exist_ok=True)
        if not os.path.exists(self.st_path):
            jdump(self.st_path, {sid: {"status": "pending", "attempts": 0} for sid in self.stages})
        if not os.path.exists(self.gates_path):
            jdump(self.gates_path, {g: {"status": "pending"} for g in self.dag.get("gates", {})})
        for f in (self.ledger, self.incidents):
            open(f, "a").close()
        print(f"initialized {self.state}: {len(self.stages)} stages, {len(self.dag.get('gates', {}))} gates")
        return 0

    def set_gate(self, g: str, status: str, by: str, evidence: str, numbers: str) -> int:
        if g not in self.dag.get("gates", {}):
            print(f"REFUSED: unknown gate {g}")
            return 1
        if not (evidence and os.path.isfile(evidence)) or not numbers.strip():
            print("REFUSED: a gate decision names an existing evidence file and its numbers")
            return 1
        gates = jload(self.gates_path, {})
        gates[g] = {"status": status, "by": by, "at": now(), "evidence": evidence, "numbers": numbers}
        jdump(self.gates_path, gates)
        self.append(self.ledger, {"kind": "GATE", "gate": g, "to": status, "by": by,
                                  "evidence": evidence, "numbers": numbers})
        print(f"gate {g} -> {status} (by {by})")
        return 0

    def status(self) -> int:
        st, gates = jload(self.st_path, {}), jload(self.gates_path, {})
        print(f"{'STAGE':<16} {'STATUS':<10} {'TRIES':<6} NOTE")
        for sid in self.stages:
            r = st.get(sid, {"status": "pending"})
            print(f"{sid:<16} {r['status']:<10} {r.get('attempts', 0):<6} {(r.get('blocked_on') or r.get('why') or '')[:60]}")
        for g in self.dag.get("gates", {}):
            print(f"gate {g}: {gates.get(g, {}).get('status', 'pending')}")
        if os.path.exists(self.stop):
            print("!! STOP is set")
        return 0


def self_test() -> int:
    """Run a four-stage campaign on the `local` scheduler in a temporary folder."""
    me = os.path.abspath(__file__)
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(os.path.join(t, "jobs"))
        os.makedirs(os.path.join(t, "out"))
        store = os.path.join(t, "store.bin")
        cfgf = os.path.join(t, "params.yaml")
        open(cfgf, "w").write("lr: 3e-4\n")
        body = {"prep": f"echo prep > {t}/out/prep.txt", "train": f"cat {cfgf} > {t}/out/train.txt",
                "eval": f"echo 0.5 > {t}/out/eval.txt", "broken": "exit 1"}
        for k, v in body.items():
            open(os.path.join(t, "jobs", f"{k}.sh"), "w").write(v + "\n")
        reg = {"gates": {"G-eval": {"desc": "train loss finite"}}, "stages": [
            {"id": "prep", "script": "jobs/prep.sh", "require": [store], "outputs": [f"{t}/out/prep.txt"]},
            {"id": "train", "script": "jobs/train.sh", "needs": ["prep"], "inputs": [cfgf],
             "outputs": [f"{t}/out/train.txt"]},
            {"id": "eval", "script": "jobs/eval.sh", "needs": ["train"], "gate": "G-eval",
             "outputs": [f"{t}/out/eval.txt"]},
            {"id": "broken", "script": "jobs/broken.sh"},
            {"id": "after_broken", "script": "jobs/eval.sh", "needs": ["broken"]}]}
        jdump(os.path.join(t, "dag.json"), reg)
        jdump(os.path.join(t, "campaign.json"), {"registry": "dag.json", "state_dir": "state",
                                                  "scheduler": "local", "job_prefix": "t", "max_attempts": 2,
                                                  "python": sys.executable})

        def run(*a):
            r = subprocess.run([sys.executable, me, "--config", os.path.join(t, "campaign.json"), *a],
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        def state():
            return jload(os.path.join(t, "state", "dag.json"), {})

        fails = []
        run("init")
        run("step")
        if state()["prep"]["status"] != "blocked":
            fails.append("prep ran without its required input")
        open(store, "w").write("x")
        run("step"); run("step"); run("step")
        s = state()
        if s["train"]["status"] != "done":
            fails.append(f"train not done: {s['train']}")
        if s["eval"]["status"] != "blocked":
            fails.append("eval ran before its gate opened")
        if s["broken"]["status"] != "void" or s["after_broken"]["status"] != "skipped":
            fails.append(f"broken not void or dependent not skipped: {s['broken']} {s['after_broken']}")
        rc, _ = run("open-gate", "G-eval", "--by", "test", "--evidence", "/nonexistent", "--numbers", "1")
        if rc == 0:
            fails.append("gate opened without an evidence file")
        rc, _ = run("open-gate", "G-eval", "--by", "test", "--evidence", f"{t}/out/train.txt", "--numbers", "loss 0.4")
        run("step")
        if rc != 0 or state()["eval"]["status"] != "done":
            fails.append("eval did not run after the gate opened")
        open(cfgf, "w").write("lr: 1e-4\n")
        _, out = run("step")
        if not os.path.exists(os.path.join(t, "state", "sentinels", "train.done.stale")):
            fails.append("changed input did not stale the sentinel")
        open(os.path.join(t, "state", "STOP"), "w").close()
        os.remove(os.path.join(t, "state", "sentinels", "prep.done"))
        _, out = run("step")
        if "submitted prep" in out:
            fails.append("STOP did not halt submissions")
        rc, out = run("chain", "prep", "train", "--dry-run")
        if rc == 0:
            fails.append("chain ignored STOP")
    if fails:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(fails))
        return 1
    print("SELF-TEST PASSED (required inputs, chain of needs, gate refusal without evidence, gate open,"
          " void and skip, stale sentinel on a changed input, STOP)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--config", help="the local campaign config (JSON)")
    p.add_argument("--self-test", action="store_true", help="run the built-in test and exit")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("init"); sub.add_parser("status")
    ps = sub.add_parser("step"); ps.add_argument("--dry-run", action="store_true")
    for nm in ("open-gate", "close-gate"):
        g = sub.add_parser(nm); g.add_argument("gate"); g.add_argument("--by", required=True)
        g.add_argument("--evidence", required=True); g.add_argument("--numbers", required=True)
    v = sub.add_parser("void"); v.add_argument("stage"); v.add_argument("--why", required=True)
    r = sub.add_parser("retry"); r.add_argument("stage"); r.add_argument("--why", required=True)
    r.add_argument("--mem-scale", type=float)
    i = sub.add_parser("incident"); i.add_argument("kind"); i.add_argument("stage")
    i.add_argument("--detail", required=True)
    c = sub.add_parser("chain"); c.add_argument("stages", nargs="+"); c.add_argument("--dry-run", action="store_true")
    sl = sub.add_parser("seal"); sl.add_argument("stage")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not a.config or not a.cmd:
        p.print_help()
        return 64
    cp = Campaign(a.config)
    if a.cmd == "init": return cp.init()
    if a.cmd == "status": return cp.status()
    if a.cmd == "step": return cp.step(a.dry_run)
    if a.cmd == "seal": return cp.seal(a.stage)
    if a.cmd == "chain": return cp.chain(a.stages, a.dry_run)
    if a.cmd in ("open-gate", "close-gate"):
        return cp.set_gate(a.gate, "open" if a.cmd == "open-gate" else "closed", a.by, a.evidence, a.numbers)
    if a.cmd == "incident":
        cp.incident(a.kind, a.stage, a.detail); print(f"filed {a.kind} on {a.stage}"); return 0
    st = jload(cp.st_path, {})
    if a.stage not in cp.stages:
        print(f"unknown stage {a.stage}"); return 1
    rec = st.setdefault(a.stage, {"attempts": 0})
    if a.cmd == "void":
        rec.update(status="void", why=a.why, finished=now())
        cp.append(cp.ledger, {"kind": "VOID", "stage": a.stage, "why": a.why})
    else:  # retry: a spent stage changes something, or retrying would fail the same way
        if rec.get("attempts", 0) >= cp.max_attempts and not a.mem_scale:
            print(f"REFUSED: {a.stage} spent its attempts; give a resource change (--mem-scale)"); return 1
        if a.mem_scale:  # recorded in state/overrides.json; the registry stays as written
            ovp = os.path.join(cp.state, "overrides.json")
            ov = jload(ovp, {})
            cur = ov.get(a.stage, {}).get("mem_gb") or (cp.stages[a.stage].get("resources") or {}).get("mem_gb", 8)
            ov.setdefault(a.stage, {})["mem_gb"] = int(float(cur) * a.mem_scale + 0.999)
            jdump(ovp, ov)
        rec.update(status="pending", attempts=0, job_id=None)
        rec.pop("why", None)
        cp.append(cp.ledger, {"kind": "RETRY", "stage": a.stage, "why": a.why, "mem_scale": a.mem_scale})
    jdump(cp.st_path, st)
    print(f"{a.cmd} {a.stage}: {a.why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
