# Literature notes and interface notes

Two files under `research/`, both made from templates in `assets/`: `LITERATURE.md` for papers, benchmarks and
methods, `INTERFACES.md` for the libraries the code will call. Both are dated reference material: the libraries in
one project changed a prior's default between two minor releases, so every line carries its date and version.

## 1. Tags

Every statement carries one tag:

| Tag | Meaning | Required with it |
|---|---|---|
| [RUN] | verified by running code, or computed from a downloaded file | the command or script, and the input |
| [DOC] | read in the paper, documentation or source | URL with version, or file:line at a commit, and the date read |
| [U] | not checked, or checked and still unclear | a line in "Open uncertainties" saying what would settle it |

The project this comes from used [V] verified, [U] unverified and [C] computed; this skill folds [C] into [RUN],
because both mean "a script produced it". Estimates are written "est." and are never tagged [RUN].

- **Helper-agent statements keep their tag only after a spot check.** List the re-checked claims under
  "Provenance". A literature agent produced a citation that does not exist; another produced a wrong author for a
  real paper. Every citation is checked (see `references/exemplars-and-attribution.md`).
- **Cite only files inside the repository.** One project's interface notes pointed to verification scripts in a
  session scratch folder; they were gone after a reboot. Copy them to `research/scripts/` and cite that path.
  `scripts/check_kickoff.py` fails any note citing `/tmp`, a scratchpad or `/var/folders`.

## 2. Literature notes

Per paper or method, in this order (the template has each block):

1. **Identity.** arXiv id, version and date, or DOI checked against Crossref; authors as printed; code repository
   and commit; license; weights and their gate.
2. **Exact definitions** of what the project computes or compares against, taken from the code: each feature, loss
   term or metric with its constants and file:line. "The key item" of one note was a 70-row table giving every
   dimension of a baseline's feature vector, including that its column count includes the target column.
3. **Paper versus code** table (`references/verify-spec.md` section 4).
4. **Published results the project can re-analyze.** When the authors release result files (CSV, logs, a
   tracking-service export), download them, recompute the headline, then slice by each parameter. One re-analysis
   found 82,176 configurations at 4 levels per parameter where the paper said 6 levels and "more than 86k", and
   showed that every knob but one moved the mean score by at most 0.0003.
5. **Replication pitfalls.** Choices in the original that change the result: one baseline bootstrapped with
   replacement and then split 70/30, so duplicates landed in both train and test; it typed columns by storage
   type, so two collection artifacts became its top discriminating features; it took the first 512 rows
   unshuffled.
6. **Reading published per-item results.** Filter imputed rows (one suite had a model imputed on 15 of 51
   datasets), compare models only on the items they all ran, use a scale-free gap such as a log error ratio, and
   sanity-check the download against one headline the paper states before using it.

End the file with ranked recommendations for this project, "Open uncertainties" and "Provenance" (every source
pinned; scripts behind every [RUN]; which agent claims were re-checked).

## 3. Interface notes

**Never guess an interface: read the installed source, record version and signature, and log every surprise with
its fix.** The project's build prompt said it plainly: "Never guess an API. Inspect the installed package first."
All facts in the file are gathered before the main experiment starts.

Open the file with a verdict table of the specification's claims about the libraries, headed "read this first".
Then the environment block from `scripts/env_pins.py`, then one section per library with a version in its
heading. `env_pins.py` reads both the module's `__version__` and the distribution metadata, because one library
had no `__version__` at all (`importlib.metadata.version("<name>")` works).

Per library:

- **Signature**, copied from the installed source with every default.
- **Returns**: shapes, padding, dtypes. One generator returned labels as int64 for one prior and float32 for the
  other, and class labels that were not contiguous in 5 of 25 tables (re-encode with
  `np.unique(y, return_inverse=True)`).
- **Defaults that matter**, diffed against the published recipe and the previous version. A package default left
  two filters off that the published training script turned on, so the default generator could emit tables whose
  label was independent of the features. A trainer in the same release built its dataset with defaults, "so it
  would train v1 non-causal". Pass every flag of the published script explicitly and label any output whose port
  the library itself calls unverified, quoting the library's own caveat.
- **Determinism.** A generator without a seed argument became bit-identical (48 of 48 tests) once numpy, `random`
  and torch were seeded before each item with one worker and batch size 1. It still changed between processes,
  because it iterated over a set of strings; replacing that with `sorted(...)` made it identical for hash seeds 0,
  1, 2 and 5. Check with `scripts/hashseed_check.py`. Worker counts above 1 crashed (pickling closures) or
  deadlocked; parallelize across items in your own pool. Give each purpose a disjoint seed range (evaluation items
  from 1,000,000, training items from 11,000,000), so evaluation items never train anything.
- **Invariances measured**, each with the tolerance tests will use: row order (relative change 4.5e-7, test at
  1e-3), column order (0.18 with one ensemble member, 0.09 with four, so average members), labels, device.
- **Traps**, one line each with the fix:
  - forward hooks on a frozen model must `.detach().clone()`, because a later stage edited the hooked tensor in
    place; without the clone a label-free model showed a spurious 1.4% label effect;
  - hooks must return `None`, because a returned tensor replaces the module's output (one hook built from a lambda
    silently corrupted a test);
  - reserved token slots held placeholders of about plus or minus 100 and had to be excluded from pooling;
  - automatic mixed precision on one accelerator drifted by about 2e-3, so it was switched off and embeddings then
    agreed across CPU and GPU to 1e-6;
  - `device=None` picked the laptop GPU automatically; pass the device explicitly;
  - a model reloaded its checkpoint on every `fit` (0.3 to 0.7 s); load once per process;
  - two OpenMP runtimes in one process (torch and scikit-learn) made a gradient-boosting fit about 15 times slower
    (35 s against 2.4 s); limit that step to one OpenMP thread.
- **Timing** on the target hardware, input size stated, with before-and-after notes when something was sped up.

## 4. Installing without breaking the core

- Install heavy or conflicting packages into a scratch environment first and read what they would change.
- A package that pins an old dependency can often be installed with `--no-deps` plus its real requirements; record
  the reason beside each such line.
- On a hosted runtime, never change its core numerical packages: build a constraints file from `pip freeze` and
  install only what is missing.
- Ask the author for compute limits once, at the start. This author forbids training on the CPU ("don't run
  training of torch models on cpu"); the code raised an error unless a GPU was present or an explicit
  `allow_cpu_training=True` was passed, and tests used untrained models for shape checks only.

## 5. A fresh session resumes from the notes

When context runs short, update `NOTES.md` and `STATUS.md`, commit, and resume from those two files. The author's
build prompt put it as "update NOTES.md, commit, and tell me to /clear and say 'continue from NOTES.md'". The
notes are therefore written for a reader who saw nothing else.
