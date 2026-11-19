# Tests for research code

Research code fails in ways that unit tests written for web services miss: a seed that reaches nothing, a join
that is right only when no row was filtered, a metric with a dead zone, a default that moved. The template
`assets/test_research_code.py` has one runnable test of each kind below.

## 1. What to test

| Kind | The test | The failure it caught or prevents |
|---|---|---|
| shape and dtype | every public function on the empty input, one row and a typical size; output shape and dtype asserted | an output column that existed only on the success path |
| determinism | two runs with the same seed give identical bytes; a different seed changes the draw | an unordered group-by fed a seeded permutation, so `--random-seed 0` gave different scores on identical runs |
| seed reach | grep for every random source (`seed_everything`, `manual_seed`, `randperm`, `shuffle=True`, model init) and test that the seed reaches each | a package with no seeding at all; a "replicates" claim retracted |
| tiny golden values | a 3-row input with its output computed by hand or by the trusted version, committed as literals | silent changes of a formula during a refactor |
| planted structure | synthetic input with a known answer: three separated blobs give three groups; a small blob is dropped; an elongated chain stays one group | a clustering step that made every group round |
| planted fractions | for a metric, plant known fractions (0, 15, 30, 45, 55, 80% foreign signal) and scale a single feature by 10 | a "soft" variant that was not the published metric; a score that flipped past 50% |
| degenerate input | collinear points, float ids, empty groups, constant arrays, all-null scores | a confidence interval of half-width 0 at p = 0; a threshold function on a constant array |
| units | a radius in physical units on pixel coordinates | a 20 µm radius applied to pixels that scored 0.0 |
| joins | low-quality and control rows interleaved with good rows; labels shuffled; exact invariants | raw and filtered indices that coincide in clean fixtures, hiding a 0.065%-correct join |
| skewed inputs | one fixture with a heavy-tailed number of points per unit (a few units hold most points) beside the uniform one | a masking step budgeted by unit count that inverted on skewed inputs; a redraw gate then picked the inverted draw, and only an audit found it |
| default equivalence | the new option at its default reproduces the old output exactly | a "no behavior change" default that changed behavior |
| failure-path schema | the output columns are the same when a step fails or returns nothing | downstream code that crashed on the empty case |

For a training codebase, the same table reads: a forward pass on a tiny CPU config returns `(B, N, D)`; one step
at a fixed seed gives the same loss twice; every loss term on one batch matches committed values; each config
trains one step; a speedup leaves the loss trajectory identical at a fixed seed.

A budget (how many units to mask, sample or keep) is set in the quantity the model consumes (points, tokens),
never in units whose size varies; the skewed fixture is what shows the difference.

### The study's contract as tests

Before the first full run of a study, write one test per promise the analysis makes. From a study that compared
several encoders on perturbed tables:

| Promise | Test |
|---|---|
| determinism | the same seed gives the same item; a different seed gives a different one |
| parity with the reference | the port matches the reference implementation within the tolerance found by running the reference against itself |
| fixed output length | every item gives a vector of the same length, per encoder |
| the invariance the analysis relies on | it holds within its measured tolerance (row order, for a table) |
| requested equals measured | each perturbation returns its measured severity, and it matches the request within a tolerance per kind: one column for column-wise kinds, 10% for noise, 0.02 otherwise |
| resume | a rerun skips finished items and gives identical output |
| provenance | every stored view carries its provenance record, and a derived view rebuilds exactly from its parent |

The plan named five tests; cache, catalog and label checks brought the suite to eight. Inputs come from a small
generator with a seed (`toy_task(seed)`), and stores are written to the test's temporary folder.

## 2. Tests that bite

- **A test counts only if it fails without its fix.** After writing it, revert the fix (or flip a sign, drop the
  sort, join by position) and watch it go red. Two tests in the source work were decoration until this check.
- **Re-verify small fixes.** Tidy-up fixes to minor audit findings twice created a worse bug than they fixed (a
  run-killing crash, a wrecked null distribution).
- **Test the shipped expression, never a copy of it.** "if a test has to freeze the thing that varies in
  production, it is testing a different program." Give the shipped path one seam (a method) and test through it.
- **Mutation checks on signs, polarity and pairing**: swap the two inputs of a pairwise function, negate a
  weight, and confirm the test notices.
- **Name tests as claims**: `test_empty_region_is_masked_not_nan`, `test_full_model_checkpointing_is_exact`,
  `test_prediction_never_reaches_the_readout`.
- **Assert exact invariants.** A ratio bound of 0.9x passed a 0.25% offset.

## 3. Golden files and tolerances

For a refactor, a port or a release, freeze golden outputs before the first change:

- Inference: a few public inputs at two precisions (fp32 and mixed), with per-unit sums and the input checksum.
- Training: a deterministic CPU run of one batch, every loss term and per-parameter gradients, run twice to
  measure the code's distance from itself.
- Evaluation: the scores per fold.

**Tolerances are measured, never guessed**: run the reference twice (or at two precisions) and set the tolerance
from that distance. Commit the small golden tensors; keep large ones out of git with a checksum. `research-release`
has the full parity gate for a public release.

## 4. Packages that need a GPU to import

When importing the package initializes the GPU, tests on a CPU machine hang or fail. Load the module under test
with its heavy imports stubbed:

```python
import importlib.util, sys, types

def load_without_gpu(path, name, stub=("cupy", "cudf", "cuml", "rmm")):
    """Import one source file with GPU-only packages replaced by empty modules."""
    for mod in stub:
        sys.modules.setdefault(mod, types.ModuleType(mod))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

reader = load_without_gpu("src/pkg/io/reader.py", "reader")
```

Make the CPU-testable units (readers, writers, joins, thresholds) importable without the GPU stack in the first
place where the package allows it. Write merge and summary tools so they do not import the GPU package at all.

## 5. Running tests

- **On a laptop without the accelerator or the data**, write the tests and run only the CPU ones. "keep the full
  set of tests ... but do not run them" applied to GPU tests on the laptop; heavy runs go to the cluster
  (`cluster-jobs`).
- **Tests that need a heavy optional package or downloaded weights skip with a reason**, so the suite stays green
  on a laptop without them and prints a skip line where a red test would only be noise. Use a model with random
  weights for shape checks only, and train nothing in a test:

```python
import pytest

def test_encoder_output_length():
    enc_lib = pytest.importorskip("<heavy_pkg>")          # skips when the package is missing
    try:
        model = enc_lib.load_pretrained("<checkpoint>")
    except Exception as e:                                 # weights absent or not downloadable
        pytest.skip(f"checkpoint unavailable: {e}")
    assert model.embed([[0.0, 1.0]]).shape[-1] == model.dim
```

- **A fast CPU suite**: a tiny config and a synthetic store; the suites in the source work ran in about 3 minutes,
  and the release standard was under 2 minutes.
- **A gate reads the output, never only the exit code.** A build that exited 0 had produced a document without
  its bibliography.

## 6. Tests by destination

| Destination | Tests |
|---|---|
| internal feature branch | a full local suite: unit, integration, end to end where it can run |
| minimal upstream PR | none unless the maintainers ask ("add no tests please!"); keep local tests out of the PR and out of the size budget |
| public release | committed CPU tests with small golden tensors and a test that every shipped config runs one step |

This is the latest of three positions in the source work: tests written but not run (early), a full suite per
feature (mid), no tests in a minimal upstream PR (latest), with local tests kept throughout.
