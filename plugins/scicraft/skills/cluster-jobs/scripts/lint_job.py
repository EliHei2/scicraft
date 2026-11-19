#!/usr/bin/env python3
"""Lint a cluster job script (LSF or SLURM) before it is handed over or submitted.

Every check below is a way a job failed on paste, died hours in, or pended forever
in real work. The resource checks are a port of the guards in a campaign submit
script (bash) to Python; the rest come from the incidents named in SKILL.md.

    python3 lint_job.py job.sh [more.sh ...] [--no-arrays] [--strict]

ERROR (exit 1):
  unfilled [placeholders], /path/to, <your...>; a laptop home path (macOS);
  `bash -n` syntax error; no wall time; no memory request; LSF job with no queue;
  LSF gmem without a unit (LSF reads it as MB); gmem and gmodel both set;
  multi-GPU job not pinned to one host; `rsync ... --delete`; a bare `python`,
  `python3` or `pip` command; a job array when --no-arrays says the site forbids them.
WARN (exit 1 only with --strict):
  no `set -u`; thread pools not capped; no PYTHONNOUSERSITE; TMPDIR not set or not
  under /tmp; GPU requested without pinning the model; a done()/afterok dependency
  written inside the job (zombie risk); no output/error log path.
INFO: notes that do not fail (shared versus exclusive GPU mode, a job array seen).

Standard library only. Python 3.9 or later. `bash` on PATH for the syntax check.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
ENV_HELPERS = ("job_env_export", "job_env.sh", "thread_env.sh")


def directives(lines: list[str], tag: str) -> list[str]:
    return [ln.strip()[len(tag):].strip() for ln in lines if ln.strip().startswith(tag)]


def body(lines: list[str]) -> list[tuple[int, str]]:
    """(line number, code) for non-comment lines, with trailing comments removed."""
    out = []
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        out.append((i, re.sub(r"\s+#\s.*$", "", ln)))
    return out


PLACEHOLDER_BODY = re.compile(r"""(?:^|[\s"'=])\[[A-Za-z][^\]\[]*\]""")
PLACEHOLDER_DIRECTIVE = re.compile(r"""[\s=":]\[[A-Za-z][^\]\[]*\]""")
LAPTOP_HOME = re.compile(r"""(^|[\s"'=])/""" + "Users" + "/")
BARE_CMD = re.compile(r"""(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+|\bexec\s+|\btime\s+|\bnohup\s+)(python3?|pip3?)(?:\s|$)""")


def lint(path: Path, no_arrays: bool) -> tuple[list[str], list[str], list[str]]:
    err: list[str] = []
    warn: list[str] = []
    info: list[str] = []
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    bsub = directives(lines, "#BSUB")
    sbatch = directives(lines, "#SBATCH")
    code = body(lines)
    code_text = "\n".join(c for _, c in code)

    if not bsub and not sbatch:
        info.append("no #BSUB or #SBATCH directives: checked as a plain launcher script")
    sched = "lsf" if bsub else ("slurm" if sbatch else "none")

    # -- placeholders and laptop paths: the commands that failed on paste
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.startswith("#BSUB") or s.startswith("#SBATCH"):
            hits = [m.group(0).strip(' ="\':') for m in PLACEHOLDER_DIRECTIVE.finditer(s)]
        elif s.startswith("#"):
            continue
        else:
            hits = [m.group(0).strip(" \"'=") for m in PLACEHOLDER_BODY.finditer(ln)]
            hits = [h for h in hits if not h.startswith("[[")]
        for h in hits:
            err.append(f"line {i}: unfilled placeholder {h}")
        if not s.startswith("#"):
            if "/path/to" in ln or re.search(r"<your[^>]*>", ln):
                err.append(f"line {i}: example path left in: {s[:80]}")
            if LAPTOP_HOME.search(ln):
                err.append(f"line {i}: a laptop home path (macOS) in a cluster job")

    # -- syntax
    if shutil.which("bash"):
        r = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        if r.returncode != 0:
            err.append("bash -n: " + (r.stderr.strip().splitlines() or ["syntax error"])[0])
    else:
        info.append("bash not found: syntax not checked")
    if not re.search(r"^\s*set\s+-[a-z]*u", text, re.M):
        warn.append("no `set -u`: an unbound variable runs as an empty string (two pasted jobs failed this way)")

    # -- resources
    if sched == "lsf":
        if not any(d.startswith("-W ") for d in bsub):
            err.append("no `#BSUB -W`: an unbounded job on a shared cluster")
        if not any(d.startswith("-M ") for d in bsub) and not any("rusage[mem=" in d for d in bsub):
            err.append("no memory request (`#BSUB -M` / rusage[mem=]): measure one unit, then ask")
        if not any(d.startswith("-q ") for d in bsub):
            err.append("no `#BSUB -q`: name the queue explicitly")
        if not any(d.startswith("-o ") for d in bsub):
            warn.append("no `#BSUB -o`: the log goes to mail or nowhere")
        gpu = " ".join(d for d in bsub if d.startswith("-gpu"))
        if gpu:
            if re.search(r"gmem=[0-9.]+(?![0-9.]*[GgMm])", gpu):
                err.append("gmem has no unit: LSF reads it as MB, so the request places on any GPU. Write gmem=<N>G")
            if "gmodel=" in gpu and "gmem=" in gpu:
                err.append("gmem and gmodel both set: they can conflict and the job may never start")
            if "gmodel=" not in gpu and not any(d.split()[:1] == ["-m"] for d in bsub):
                info.append("no GPU model or host group pinned: memory alone can land on a card that breaks the "
                            "workload. Pin by the mechanism the site documents, and check the name exists")
            if "j_exclusive=" in gpu:
                info.append("j_exclusive is set: confirm the value against the site's documented policy")
            m = re.search(r"num=(\d+)", gpu)
            if m and int(m.group(1)) > 1 and not any("span[hosts=1]" in d for d in bsub):
                err.append(f"num={m.group(1)} GPUs without span[hosts=1]: ranks land on different hosts and a "
                           "standalone rendezvous hangs at init")
        if any(re.match(r"-J\s+\S*\[\d", d) for d in bsub):
            (err if no_arrays else info).append("job array in -J: " + ("forbidden here (--no-arrays); submit a loop "
                                                "of single jobs" if no_arrays else "check the site allows arrays"))
    elif sched == "slurm":
        if not any(re.match(r"(--time|-t)[= ]", d) for d in sbatch):
            err.append("no `#SBATCH --time`: an unbounded job on a shared cluster")
        if not any(re.match(r"--mem(-per-cpu|-per-gpu)?[= ]", d) for d in sbatch):
            err.append("no `#SBATCH --mem`: measure one unit, then ask")
        if not any(re.match(r"(--partition|-p)[= ]", d) for d in sbatch):
            warn.append("no `#SBATCH --partition`: the default partition may not be the one you mean")
        if not any(re.match(r"(--output|-o)[= ]", d) for d in sbatch):
            warn.append("no `#SBATCH --output`: the log lands in the submit directory as slurm-<id>.out")
        gres = " ".join(d for d in sbatch if re.match(r"--(gres|gpus|gpus-per-node)[= ]", d))
        if gres:
            if not re.search(r"gpu:[A-Za-z]", gres) and not any(d.startswith("--constraint") for d in sbatch):
                warn.append("GPU job without a GPU type (gpu:<type>:N or --constraint): it can land on any card")
            m = re.search(r"(?:gpu(?::[A-Za-z0-9_]+)?:|--gpus(?:-per-node)?[= ])(\d+)", gres)
            if m and int(m.group(1)) > 1 and not any(re.match(r"(--nodes|-N)[= ]1\b", d) for d in sbatch):
                err.append(f"{m.group(1)} GPUs without --nodes=1: ranks can land on different hosts")
        if any(d.startswith("--array") for d in sbatch):
            (err if no_arrays else info).append("--array: " + ("forbidden here (--no-arrays); submit a loop of "
                                                "single jobs" if no_arrays else "check the site allows arrays"))

    # -- the job body
    for i, c in code:
        if re.search(r"\brsync\b[^|;]*--delete", c):
            err.append(f"line {i}: rsync --delete can wipe outputs that exist only on the cluster")
        if BARE_CMD.search(c):
            err.append(f"line {i}: bare python/pip: login shells differ; call the environment's interpreter by "
                       "absolute path (\"$PY\")")
        if re.search(r"""(-w\s+["']?done\(|--dependency[= ]afterok)""", c):
            warn.append(f"line {i}: done()/afterok dependency: if the upstream fails this waits forever; use "
                        "ended()/afterany with a completeness check, or watch for it")
    sources_env = any(h in code_text for h in ENV_HELPERS)
    if not sources_env:
        missing = [v for v in THREAD_VARS if v not in code_text]
        if missing:
            warn.append("thread pools not capped (" + ", ".join(missing) + "): 691 threads on one node tripped "
                        "the memory limit; source assets/job_env.sh")
        if "PYTHONNOUSERSITE" not in code_text:
            warn.append("no PYTHONNOUSERSITE=1: ~/.local packages can shadow the environment")
        m = re.search(r"TMPDIR=([^\s;]+)", code_text)
        if not m:
            warn.append("TMPDIR not set: keep it short and node-local (/tmp/...), socket paths cap at 108 characters")
        elif not m.group(1).strip("\"'").startswith(("/tmp", "${TMPDIR_BASE", "$TMPDIR_BASE")):
            warn.append(f"TMPDIR={m.group(1)}: keep it short and node-local (/tmp/...)")
    return err, warn, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("scripts", nargs="+", type=Path, help="job scripts to check")
    ap.add_argument("--no-arrays", action="store_true", help="the site forbids job arrays: make them an error")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    a = ap.parse_args()
    bad = 0
    for p in a.scripts:
        if not p.is_file():
            print(f"{p}: ERROR not a file")
            bad = 1
            continue
        err, warn, info = lint(p, a.no_arrays)
        for m in err:
            print(f"{p}: ERROR {m}")
        for m in warn:
            print(f"{p}: WARN  {m}")
        for m in info:
            print(f"{p}: INFO  {m}")
        verdict = "FAIL" if err or (a.strict and warn) else "PASS"
        print(f"{p}: {verdict} ({len(err)} errors, {len(warn)} warnings)")
        if verdict == "FAIL":
            bad = 1
    return bad


if __name__ == "__main__":
    sys.exit(main())
