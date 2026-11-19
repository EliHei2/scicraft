# Change discipline

How to make a change that does what was asked and nothing else, so the owner's scripts and numbers stay valid.

## 1. Inventory the interface first

Before the first edit, write down what callers depend on:

```bash
# flags and defaults of the reference install (the exact interpreter the owner's scripts use)
<python of the reference env> -m <pkg> --help > /tmp/help_ref.txt
<python of the reference env> -m <pkg> <subcommand> --help >> /tmp/help_ref.txt
# who calls what: the owner's scripts, notebooks and job files
grep -rn "<pkg>\.\|<command> " <scripts folder> | head -50
```

After the edit, compare:

```bash
python3 scripts/interface_diff.py --repo . --old main --paths src/<pkg>            # signatures, flags, defaults
python3 scripts/interface_diff.py --help-old /tmp/help_ref.txt --help-new /tmp/help_new.txt
```

`interface_diff.py` reads the source with `ast` and imports nothing, so it runs on a laptop without the
accelerator stack. It finds options declared through `add_argument`, `option`, `Option`, `argument`, `Argument`
and `Parameter` calls; for a command line built from function signatures (cyclopts, typer without explicit
options) the signature diff covers it. Defaults written inside help text are not compared: read those by eye.

When a flag must move (a threshold moved from the segmentation command to the export command because that is
where it takes effect), keep the old name as an alias or say so before the change. Twice a moved flag failed in
the owner's cluster command with `Unknown option: "--<flag>"`, because the flag did not exist on the branch the
command ran.

When asked "is X the same as main", answer with a concrete diff of the model path, never from memory.

**Renames.** When the user asks for a rename, do it in one change across code, command-line flags, scripts, tests
and docs, then grep for the old name and expect zero hits. A renamed flag keeps both its long form and its short
form. Touch only the folder the user named and leave every other call signature as it was. The requests that set
this: "rename everything properly in the code also in the docs... really make everything consisten", "do both
abbreviation and full name flags for the cli ... only touch that folder", "I want no changes in flags/usage ok?"

```bash
grep -rn --include='*.py' --include='*.sh' --include='*.md' '<old_name>' . | grep -v '^./.git/'   # expect nothing
```

### Command-line design for a package

From a package whose command line was rebuilt once and then kept stable across many releases:

- **One entry command, its parameters in named groups** (input and output, graph or data construction,
  prediction, model, loss), so `--help` reads as sections. Frameworks that build the command line from function
  signatures support parameter groups; use them before adding subcommands.
- **When a fixed threshold and a relative one both exist** (a shift applied to learned per-item thresholds), the
  fixed one wins and the help text of both says so.
- **Checkpoint reuse has explicit modes**, so a vocabulary mismatch is handled once, in the loader, and never by
  hand per run:

| Mode | Weights | Optimizer | Items (genes, tokens, classes) not shared with the checkpoint |
|---|---|---|---|
| `train` | fresh | fresh | the vocabulary comes from the data |
| `finetune` | loaded | fresh | shared items keep their embedding rows; new items start fresh |
| `predict` | loaded | none | the input is filtered to the checkpoint's vocabulary, and the dropped count is printed |

## 2. Reuse before you build

The owner has usually solved the problem before, in another branch, a fork, a script or a sibling repository.

```bash
git branch -a --sort=-committerdate | head -30                 # every branch, newest first
git log --all --oneline -S '<function or constant name>'        # commits that added or removed a symbol
git log --all --oneline --grep '<topic word>'                   # commits that mention it
git show <sha>:<path>                                           # read a file at an old commit
git worktree list                                               # sibling worktrees of the same repository
grep -rn '<symbol>' ../*/src 2>/dev/null                        # the owner's other checkouts
```

Report what you found and compare it with the new idea on speed and stability before choosing. Examples from the
source work: a voxel technique from an export step reused for a metric; the package's own multi-core polygon
builder chosen over a new one because it was faster; an older, more stable recovery mode chosen over the newest.

**Recovering code that only survives as bytecode.** A curated module existed only as one commit and as
`__pycache__/<name>.cpython-312.pyc`. Recover the source from git first (`git show <sha>:<path>`). If git does
not have it, the bytecode still holds names, constants and structure:

```python
# run with the same Python minor version that wrote the .pyc (here 3.12)
import marshal, dis
with open("__pycache__/<name>.cpython-312.pyc", "rb") as f:
    f.read(16)                     # header: magic, flags, and source mtime and size (or a hash)
    code = marshal.load(f)
dis.dis(code)                      # read the functions, constants and names; rebuild the source from them
```

Rebuild the source from the disassembly and check it against any surviving outputs before trusting it.

**Prefer trusted methods.** "find methods that are already used or picked by the giants and are trustable not a
random paper or github." Ask "why is this better than X?" for every new algorithm, and state the priority: in
the source work it was accuracy, then GPU speed, then memory.

**Measure before choosing.** Time candidates on a realistic slice (one tile, one batch, one shard), report the
wall time, then pick. "if gmm is lightning fast do it, if not just go with the knee/elbow one." A slow
implementation that frustrated the owner (over 5 minutes per method on 28 million rows) was replaced by a
vectorized bounding-box pass plus a KD-tree that took 6 to 24 seconds.

## 3. Minimal-diff porting

Porting means moving working code to a new place: an upstream branch, a figure repository, a cleaned module.

- The diff from the source is confined to imports, the data path and the save path.
- No renames, no new helpers, no type hints, no "clean-up", no modernized idioms. "Reuse stable idioms verbatim."
- To meet a line budget, move data preparation into a sibling script (`_prep/`) and leave the logic alone.
- Check the port against the source's output: identical files, identical numbers, or for a figure a side by side
  view. "If visually different, the diff was too large: revert and re-minimize."
- Adapted code from elsewhere is an attributed copy: say where it came from in the module docstring.

## 4. Defaults and switches

- **A new option defaults to the old behavior.** Examples from the source work: an optional z coordinate
  passthrough defaulted to `False`; a quality threshold that had been hard-coded at 20 became a parameter with
  default 20, "for no behavioural change".
- **The default path is bit-identical.** Write an equivalence test: old call, new call with the option at its
  default, same output bytes (`references/testing.md`).
- **Guard numerics with a frozen reference output.** Before the first change, store the outputs of the model or
  pipeline on fixed small inputs as a small JSON file. Every new option at its off setting reproduces it bit for
  bit. Regenerate it only for a deliberate change, and name that change in the docstring of the test that reads
  it. In the source work this oracle guarded a sampler rewrite and every ablation switch.

```python
import json, numpy as np
def forward(x, scale=1.0):                         # the shipped function; the option is off at 1.0
    return np.tanh(x * scale).sum(axis=1)
x = np.random.default_rng(0).normal(size=(4, 3))   # fixed input
ref = {"forward": forward(x).tolist()}             # written once: json.dump(ref, open("ref_forward.json", "w"))
# in the test: the off setting reproduces the stored floats exactly
assert np.array_equal(np.array(ref["forward"]), forward(x, scale=1.0))
```

- **One code path computes the objective.** Scripts, notebooks and evaluation import it and never re-derive it; a
  second copy drifts from the first without an error.
- **A default that changes results is its own change.** State it in the PR message with the size of the effect
  and file it as a separate fix.
- **Structural switches are written explicitly into every config.** Five experiment configs once differed only in
  comments and built the identical network.
- **Values whose wrong default silently voids a result have no default.** Dataset folder, reference file, memory
  budget: the script aborts when one is missing. Keep a "known-wrong assumptions" list in the plan so a corrected
  default is not reintroduced.
- **A parameter sweep uses explicit multiples of the true default**, read from the reference branch's code:
  {-2, -1, -0.5, 1, 2, 4} times the default, written out as numbers (negative values only where they mean
  something). "the default on the main was not 3 was it??? ... it's 0.05!!!"

## 5. Annotate, never filter in place

The primary output keeps every row. A decision becomes a column:

```python
# polars; the same pattern works in pandas
out = predictions.with_columns(
    (pl.col("score") >= threshold).alias("keep"),     # bool, one per row
    pl.lit(threshold).alias("threshold"),             # the value used, stored with the data
)
out.write_parquet(raw_path)                           # every row, including rejected ones
# downstream exports read the flag
table = out.filter(pl.col("keep"))
```

Per-row thresholds (one per class or gene) are stored per row the same way. Exports, aggregates and viewers
read `keep`; the raw table stays the record. "add a column ... keep true and false ... but don't filter anything
out ... as before." The threshold then lives where it takes effect, at export, and changing it needs no rerun of
the model.

A recovery or secondary assignment step is additive: it fills only rows the primary step left unassigned
(nulls) and never moves an assigned row. After it, check that every row has exactly one id and that no row was
duplicated.

Compare methods at the same decision stage. One downstream rebuild was needed because the raw argmax assignment
was compared with a baseline that was already thresholded: read the writer to see where the final decision is
applied, measure the fraction of rows below threshold, then rebuild in pipeline order.

## 6. Count what every filter removes

```python
n0 = df.height
df = df.filter(pl.col("qv") >= min_qv)
log.info("quality filter qv >= %s: %d -> %d rows (%.2f%% removed)", min_qv, n0, df.height, 100 * (1 - df.height / max(n0, 1)))
```

Log input and output counts at every filter (quality, minimum counts, margins, tiling, dedup). When an
unexpected number of rows goes missing, ask where else rows can leave before tuning anything. When comparing
methods, check that every method saw the same filters; a different pre-filter between pipelines was once the
whole "regression". A dedup asserts `before - after == withheld` on every pass. Missing results are explicit
statuses in the output, never silent drops.

## 7. Fail loudly

- **No silent fallback** when a hard requirement is missing. For a GPU method package, raise a clear error when
  the accelerator is absent; make the CPU-testable parts (readers, I/O) testable without it. Some packages in the
  source work kept CPU fallbacks by design; follow the package's existing convention, and never add a quiet one.
- **Never fix a crash by loosening the check.** The fix for a checkpoint that did not match its architecture was
  to persist the architecture and assert it on load; `strict=False` would have loaded the wrong readout.
- **Unknown config keys fail.** A loader that silently reverted misspelled keys to defaults was changed to raise.
- **A grounded feature that is silently off fails at step 0.** One run trained with a key input feature disabled.
- **Hard caps that bind are logged.** A cap documented as "never binds" truncated to exactly 400,000 points.
- **Echo the resolved config** (with git commit and seed) into the run log. "A knob outside that sed list
  silently keeps its default in every submitted job."
- **A GPU-initializing import must not block CPU work.** A package that initialized the GPU memory pool at import
  hung every CPU-side merge and stalled a workflow for 6 retries, about 9 hours. Keep CPU tools free of that
  import.
- **Log the imported module path in every job** and assert it is the checkout you shipped
  (`assert pkg.__file__.startswith(SRC)`); an editable install can shadow `PYTHONPATH`, and one figure mixed two
  code versions.
- **A script that writes results runs only from its `main()` guard.** Importing one bare script for a helper
  regenerated a banked results file and overwrote it. Put the work under `if __name__ == "__main__":`, take the
  output path from the command line, never default it to a banked file, and keep a dated copy of every banked
  result before any rerun.

## 8. Style for research code

- Correct, minimal lines for the same function, readable, in the package's existing style. "code minimally and
  humanistically, don't overdo." Match the docstring style of the repository the code goes to.
- A shape comment on every tensor line (`# (B, N, D)`), `# out-of-place` where aliasing bites.
- Docstrings give the rationale and an honest hedge; no restating the code.
- No dead code, no speculative flags, no config fields nobody reads.
- **Keep a research codebase small enough to read whole**: files under about 200 lines of code (comments and
  blank lines excluded, the owner's own limit), one backend per operation. When two backends competed, the
  deterministic and faster one stayed and the other was deleted with its code, tests and paper text together.
  An ablation is a flag that reproduces the baseline bit for bit when off.
- **Copy one function instead of importing a heavy sibling package.** When a sibling package's `__init__` pulls
  heavy dependencies, copy the function needed with a comment naming its source and version.
- Progress bars and logging in the package's own style; no banner prints.
- Optional libraries go in extras (`pip install pkg[hpo]`); the core install does not grow. "add optuna and
  wandb deps only as extras."
- Keep analysis, figure and paper code out of the package; it lives in a scripts repository or a `paper/`
  branch.
- Never put local paths, usernames or hostnames in code that goes to a shared or public repository.

## 9. Applying a reviewed fix list

When an audit or a reviewer returns a list of fixes:

- **Check each item against the method before applying it.** The owner's instruction was "with a grain of salt,
  matching code to theory": an audit item can be wrong about what the paper specifies.
- **One task per commit**, so any item can be reverted alone.
- **Keep a disposition table** next to the list:

| Item | Disposition | Detail |
|---|---|---|
| [item id] | applied | [commit] |
| [item id] | applied with a deviation | [what differs from the request, and why] |
| [item id] | rejected | [why, with the line of the method or code that settles it] |

- **The frozen reference output (section 4) must still match** after every item that claims to be numerics
  neutral.
- **A cleanup applies only numerics-neutral items** from one read-only audit's inventory, and leaves the owner's
  uncommitted edits untouched.

## 10. Files through the file tools

Read files with the read tool, search with the search tools, change them with the edit and write tools. The shell
runs programs and git. Two heredoc writes failed silently on a wrong working directory, and a sixteen-file rewrite
done in one inline Python script left no diff anyone could review: "why shell man? why do you have to run
things????" If the search tools are not loaded, say so before falling back to `grep`. Batch related edits and
commit once, with a message that lists what changed; six commits padded with status, `ls` and `grep` calls
between them were the pattern to avoid.
