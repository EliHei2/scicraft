# Tests that assert what the paper states

A paper constant written only in a config is one edit away from drifting. A paper constant asserted in a test is
a failing build. Template: `assets/example/test_paper_constants.py`.

## What to assert

- **Every constant of the paper's hyperparameter table**, read from the config the code actually loads, in one
  dict that cites the table. The source project's size test asserted parameter counts within bands, every Table 1
  constant, and the derived rules, with comments citing the paper-map line and why a reverted change was wrong.
- **Derived rules, recomputed in the test** from their inputs (a width that must divide, a number of levels that
  follows from two sizes, a schedule length). A second literal copy of the derived value tests nothing.
- **Stated settings that are easy to lose**: "no weight decay on embeddings", "one optimizer step over both
  views", "the deployed encoder is the online encoder". A setting the paper states is a test, not a comment.
- **Exact identities** the method relies on, verified numerically: two formulations that must agree (a per-view
  backward against the joint objective, a checkpointed forward against the plain one) to a stated tolerance.
- **Published numbers you reproduce**: a self-test that recomputes a published row or the published ranks at the
  printed precision. In the source project the scoring pipeline was accepted only after it reproduced a published
  row within the stated spread of the published value, and the table builder carried a `--selftest` that
  reproduced the paper's printed mean ranks.

## How to write them so they bite

- **Test the shipped expression, never a copy of it.** "If a test has to freeze the thing that varies in
  production, it is testing a different program." A coverage test that monkeypatched the varying part could not
  fail while the feature was worse than what it replaced. Give the shipped path a seam (one method) that a test can
  call.
- **Run entry points, do not read them.** Every config in the ablation folder loads, builds and takes one real
  training step on CPU with a tiny config: "a config that cannot train cannot be merged". In the source project
  five arm configs differed only in comments and built the identical network, and an ablation wave ablated the
  wrong (default) objective; both are caught by loading and diffing.
- **A test counts only after you have seen it fail.** Change the constant, or revert the fix, run, watch it go red,
  restore. In the source project two new tests added during a tidy-up were decoration and passed either way. "A
  test that does not bite is worse than none."
- **Name tests as claims**: `test_per_view_backward_equals_the_joint_objective`,
  `test_empty_region_is_masked_not_nan`, `test_config_matches_paper_table_1`. When the claim changes, rename the
  test; a test named after an overturned claim keeps the old claim alive.
- **New mechanisms are switches whose default is the current behavior**, and an equivalence test proves the
  default path is bit-identical. Then a paper row stays reproducible while the code grows.
- **Keep the suite fast**: a tiny CPU config and a synthetic store; the source project's 80-file suite ran in about
  3 minutes.

## Configuration as one source of truth

- Typed config (dataclasses) with a `validate()` that derives dependent values and raises on impossible
  combinations; pinning a derived value warns.
- Write structural switches explicitly into every config file. Leaving them to dataclass defaults let every run
  in the source project train silently on a fraction of its input features.
- Echo the resolved config into the run log and the result record, with the code commit. A knob that a launcher
  does not pass keeps its default silently: "a silent-null generator".
- Comment every knob with its paper symbol, its reason and its ablation arms. Change defaults through the plan
  of record plus a test.

Wider config and test design belongs to the `research-code` and `ml-experiment-design` skills; this file holds only
what ties the code to the paper.
