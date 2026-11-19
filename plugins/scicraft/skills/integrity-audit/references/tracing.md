# Tracing a number to its code and run

Commands and procedures behind SKILL.md sections 2 to 5. The lead example is a model-comparison table in a machine
learning paper ("accuracy, mean over seeds, per benchmark dataset"); the same steps traced a segmentation
benchmark's contamination metric and a Methods supplement.

## 1. Find the code that ran

1. Record each repository's state:
   ```bash
   git -C <repo> remote -v
   git -C <repo> rev-parse HEAD
   GIT_TERMINAL_PROMPT=0 git ls-remote <url>          # every branch and tag on the host
   git -C <repo> fetch origin <branch> --depth=1       # the released branch, not the local one
   ```
2. Find every copy of the implementation, then which copies are identical:
   ```bash
   grep -rlE "def (compute_<metric>|<metric>_fast)" <roots>
   md5 -q <each file>                                  # or: md5sum; run as a background job on large trees
   ```
   Locate a scoring module by md5 and size across clones, then pick the commit the benchmark ran (one audit
   identified it by its exact byte size).
3. Read the reproducibility bundle if one exists: README, run map (each figure value to a run), metric map (each
   metric name to its code), the gathered build scripts. If none exists, build one beside the paper before the
   audit closes, from the templates in `assets/reproducibility_bundle/`: `README.md` (paper version, code commit,
   master table, one rerun command with its expected output), `RUN_MAP.md` (each figure value to its run and
   output path), `METRIC_MAP.md` (each metric name to its code file, commit and settings as run) and `inputs.tsv`
   (per dataset and method, the exact input files and run-time parameters). The next challenge then starts from
   the bundle, not from the logs. Write input paths relative to the bundle or as public accessions, never as home or cluster paths.
4. Load the master table the figures read. Pivot the published values by method and dataset.
5. Read the recorded command lines and configs of the actual runs (an inputs table, the builder's invocation of
   the evaluation). They give the run-time parameters.

## 2. Find where the defaults come from

| Trap | Check | Seen |
|---|---|---|
| a config file nobody loads | `grep -rn "config.yaml" --include=*.py .`; no hit means it is an example | the CLI built defaults by parsing class signatures with `ast` |
| the function default | read the call site: `grep -rn "fit(" ...` and read the arguments passed | caller passed `max_iter=250`, the function default was 100 |
| a metric with no argument from the CLI | it falls back to the function default; read it | one metric got neither floor nor cap from the CLI, so it ran with the function's own values |
| names built at run time | grep the parts: `grep -rn "_scores" ...` and `grep -rn "f\"{" ...` | a literal grep missed `f"{col}_scores"` |
| a stale per-dataset setting in the text | the figure's provenance note names the run ID; read that run's config | a per-dataset config carried as current had changed |
| the project's own notes | never a source of truth for a paper claim | top-level notes repeated a claim from an earlier version of the method |

Machine-learning forms of the same traps: an `argparse` default overridden in the launch script; a Hydra or YAML
config whose key the training code never reads; a seed list in the paper that differs from the sweep file; an
evaluation that silently truncates the split (`max_samples`, `limit_val_batches`); a learning-rate schedule whose
warmup the scheduler ignores. Each is settled by the launch command and the logged config of the run that
produced the table, never by the repository's defaults.

## 3. Trace the claim through the code path

For a claim about what the method does (for example "the encoder is pretrained on dataset X"):

1. Write down the claim verbatim with its location (document version, line).
2. Fetch the released branch at a named commit.
3. Follow the code path the claim implies. Does X ever reach training or initialization? Write what the code does
   (here: the encoder started from random weights; X was used only for evaluation).
4. Pull the run commands from logs and harness records; confirm them against the scored outputs (for example, that every
   default run was launched with no extra flags).
5. List every derived fact the trace surfaced: encoder details, graph defaults, removed features, bugs found (an
   off-by-one in an index mapping), wrong dataset labels, the run ID behind each figure.
6. Correct the text, or flag it. Whether to change the code instead is the author's call; say so.
7. Save the fact to the project's memory or notes as a hard fact, so later sessions do not reintroduce the claim.
   Note where the project's own notes are wrong for this paper.

## 4. The branch, commit and date table

Every statement about "the code" names its state. When the public code changes during an audit:

| | old head | new head | side branch |
|---|---|---|---|
| commit | `<sha>` | `<sha>` | `<sha>` |
| metric function identical to the run | yes/no | yes/no | yes/no |
| CLI defaults | ... | ... | ... |
| other functions that differ | ... | ... | ... |
| date made public | ... | ... | ... |

Run `git ls-remote origin <branch>` immediately before writing the current head.

## 5. The repro wrapper

`repro/repro_metrics.py` imports the original functions at the run's commit and calls them with the run's
arguments. Its header states the definition as run: unit floor, cap, feature universe, label or typing source,
the input filter, the commit. It never edits the imported code.

```python
"""Recompute <metric> exactly as the benchmark ran it.
code: <repo>@<sha> (<file>, <bytes> bytes, md5 <md5>)
settings as run: <arg>=<value> (from <launch script or log line>), ...
"""
import sys; sys.path.insert(0, "<checkout at sha>")
from <package>.<module> import <metric_fn>          # the original, unmodified
```

Gate before using it on anything new: it reproduces N of N published values. Report "exact N/N" or list the
misses with their class. Mark what cannot be reproduced locally and leave it out; do not approximate it.

The same gate applies to any new harness: the first output of an exploration or evaluation script is a
reproduction of a documented number ("reproduces the documented baseline exactly"), before it decides anything.

## 6. Probing a definition until the digits match

When the code that made a number is unknown or gone:

1. List the candidate definitions: per-unit mean or pooled; label source; floor; filter; which split.
2. Compute each. Compare with the published value at 3 to 4 decimals.
3. Record the parameter that matched, and how close the others came. A floor of one value matched a heatmap to
   every digit; the other matched an older aggregate, which explained where the older number came from.
4. Check fairness with the matched definition: does any method get a different floor or label source? (One
   method's labels existed only for units above a size cutoff.) Rerun all methods with one recipe.
5. Write "not reproducible" for values nothing matches, with what was tried.

## 7. Mismatch classes and the exactness ledger

Recompute with the unmodified code, then classify every published value:

- **exact**: relative error ≤ about 1e-12. Note bit-exact values separately.
- **printed precision**: equal at the printed digits.
- **(a) setting**: the run used a setting the text does not state. In one audit every match needed one such
  setting. Write the setting as run and the sentence that states it.
- **(b) code**: the numbers came from other code. Go to section 8.
- **(c) data**: other input (a quality filter one method's input carried, a version, a subset).
- **not reproducible**.

`EXACTNESS.md`, one block per figure or table:

```
## Table 2
exact (≤1e-12): 46/48 cells
printed precision: 2/48 (rows X, Y; third decimal)
differs: none
not reproducible: none
settings as run, not stated in the text: <arg>=<value> (source: <log line>)
open: <anything still unexplained, marked UNCONFIRMED with the suspected cause>
```

A suspected library-version change is marked UNCONFIRMED until shown. Ship with the ledger; do not keep chasing a
residual difference the author did not ask about.

## 8. Recovering code from bytecode

When the numbers came from code that has since changed and only compiled files remain:

1. Find `__pycache__/<module>.cpython-3XX.pyc` beside the current source or shim. Confirm it is the run's: the
   header records the source size, and a runtime warning in the benchmark log names a line number that must match.
2. **Copy it before anything else.** Never import the live package under the matching Python: that recompiles the
   source and overwrites the `.pyc`, the only copy.
3. Load the copy without the source:
   ```python
   import importlib.machinery, importlib.util, sys, types
   sys.modules.setdefault("<parent>", types.ModuleType("<parent>"))       # stub the parent package
   loader = importlib.machinery.SourcelessFileLoader("<parent>.<mod>", "copy/<mod>.cpython-311.pyc")
   spec = importlib.util.spec_from_loader(loader.name, loader)
   mod = importlib.util.module_from_spec(spec); loader.exec_module(mod)
   ```
4. Find the matching source in git history (another branch, an older commit). Remove later additions.
5. Verify identity: compile the candidate under the same Python minor version and compare every code object,
   recursively, on `co_code`, `co_consts`, `co_names` and the line table (`co_linetable` on 3.10 and later), plus
   the file's md5 after writing the `.pyc`. Gate: zero differences (one recovery matched every one of 141 code
   objects).
   ```python
   import marshal
   def load(p):
       with open(p, "rb") as f:
           f.read(16)                      # header: magic, flags, mtime or hash, source size
           return marshal.load(f)
   def walk(c):
       yield c
       for k in c.co_consts:
           if hasattr(k, "co_code"):
               yield from walk(k)
   def same(a, b):
       fields = ("co_code", "co_names", "co_varnames", "co_linetable" if hasattr(a, "co_linetable") else "co_lnotab")
       ka = [k for k in a.co_consts if not hasattr(k, "co_code")]
       kb = [k for k in b.co_consts if not hasattr(k, "co_code")]
       return all(getattr(a, f) == getattr(b, f) for f in fields) and ka == kb
   A, B = list(walk(load("run.pyc"))), list(walk(compile(open("candidate.py").read(), "<mod>.py", "exec")))
   print(len(A), len(B), sum(not same(x, y) for x, y in zip(A, B)))
   ```
   A code object compiled from source carries the filename you pass; compare with the same name or ignore
   `co_filename`.
6. Pin an environment with the matching Python (`uv venv --python 3.11` plus named package versions). Port the
   original tests and run them against a stub package root (the real submodules plus an empty top-level
   `__init__` in place of a GPU-only one): `PYTHONPATH=stubroot venv/bin/python -m pytest`.
7. Reproduce the published values with the recovered code to ≤ 1e-12.

The loader in step 3 and the comparison in step 5 were written for this skill and run on a toy module (an
identical candidate gave 0 differences, one changed default gave 1). Suggested, not yet tested in real work: the
original recovery used a session script that was not preserved.

## 9. Releasing exactly the code that ran

"make sure you just pushed ... the exact metric we had here ... no new stuff or correction. the results in the big
benchmark should be reproducible 1:1"

1. Clone the remote into scratch and branch from the release branch.
2. Extract files from a ref with braces: `git show "${B}:path/file.py" > out.py`. In zsh, `$B:s` is read as a
   substitution modifier, and the redirect had already truncated the file.
3. Strip every function absent from the run's bytecode. Verify zero differences across all code objects, the file
   size and the line number of a known runtime warning.
4. Tests in a pinned environment (step 6 above). Install optional dependencies `pyproject.toml` declares.
5. `git status --short` and `git diff --stat`: only the intended files changed. The remote tip has not moved since
   the fetch.
6. Commit, push fast-forward only. Never force.
7. Download the raw file back from the host (`curl -sL <raw url>`) and verify it against the `.pyc` again.
8. Run the public entry point end to end on one full benchmark row. Function identity is not enough: one release
   passed it and still could not run the CLI, because the branch's data loader was older. Disclose the rerun recipe
   (metric file from one commit, loader from another). Porting the loader was not authorized, so it was left.
9. An exact-code release pushes the code unchanged. CLI defaults change only when the author decides, and the
   release note says so; otherwise give the run value in the rerun instruction (`--min-<unit> <value>`) as the
   benchmark setting.
10. Write a note naming branch, commit, date and what the release does and does not reproduce.

## 10. Results tables from logs

When a table is assembled from many runs (runtime, memory, scores):

- Regenerate it from a tracked script that also writes an audit file (`RESOURCE_AUDIT.md`), one row per source
  log.
- One clock for every method (scheduler accounting). Two clocks in one line (an internal timer and the scheduler
  wall clock) were 1.9 to 6.6 times apart.
- Never read time from undated log stamps: they wrap at 24 h, and runtimes came out exactly 24 h and 48 h short.
- A `failure_kind` column: OOM, TIMEOUT, SUBSET, NOT_ATTEMPTED. An OOM kill is not a measurement. A stale
  `--dry-run` log is not a run.
- Keep a "verified, do not re-check" list so the audit is not repeated.
