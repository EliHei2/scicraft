# The parity record for work that reproduces someone else's paper

When a project re-implements published methods (baselines, an encoder, a descriptor, a benchmark protocol), keep
one status file that marks every component as exact reproduction, approximate reproduction or new extension, and
a numbered list of deviations from the papers. Template: `assets/PARITY_STATUS.md`. The pattern comes from a
tabular foundation-model study that ported several published encoders and a published dataset descriptor, kept as
two files: `PROJECT_STATUS.md` (the table) and the "Deviations from papers" section of `NOTES.md`. One file or two
both work; the status table must point to the deviations.

## The status table

| Mark | Meaning | Needs |
|---|---|---|
| **R** | exact reproduction | the same procedure as the paper or its released code, and a check against a number the authors published or released (a port that matches the library's own function to 1.7e-6; a re-implementation that reproduces the authors' released values at r = 1.0000) |
| **A** | approximate reproduction | the same idea with a documented difference in procedure: fewer training steps, a different subsample, a pooling borrowed from another paper. Each difference is a numbered deviation |
| **E** | new extension | not in any reproduced paper. Never presented as the original method |
| none | infrastructure | loaders, caches, manifests; no published reference |

Qualify a mark when it needs it: "R (code-level, re-implemented)" for a method rebuilt from the paper's definitions
because the released code has no license, "R/E" for a component that reproduces a published test and adds a new
reference. Then list what is partially implemented (with its limit and number), what is blocked (and what would
unblock it), and the next actions.

## Deviations from papers

Number them per reproduced paper. Each says what the paper or its code does, what this project does, why, and the
measured size of the difference when known. Patterns from the source project:

- **A protocol flaw in the original, fixed and stated**: the original bootstrapped before its 70/30 split, which
  leaks duplicates into the test set; the reproduction uses stratified repeated K-fold and says so.
- **The released code differs from the paper's table**: the code had 75,072 parameters and a 32-dim output against
  the table's 45,424 and 64-dim. Follow the released code (it produced the published numbers), and state the count.
- **A library silently changed a default**: a version fixed a sampling flag to one value in a pull request absent
  from its changelog, which made generated features nearly independent (mean |r| 0.025 against 0.12). Restore the
  earlier behavior, cite the pull request, and label the port "not experimentally verified" until checked.
- **A claim in your own plan was wrong**: "no pretrained weights exist" was false; five released checkpoints
  existed. Record the correction where the claim was used.
- **A possible confound**: the one encoder trained on real tables may have seen benchmark tables in pretraining.
  Name it.
- **Budget differences**: fewer steps than the original's early-stopped schedule (1,500 against up to 10,000),
  fewer subsample draws than the authors' scripts (32 or 128 against 160 to 320).

## Which side is the specification

For your own paper the methods text is the specification (`paper-map.md`). For someone else's paper, choose the
released code over the paper's table when they differ, because the code produced the published numbers, and record
the difference as a deviation. Without released code, the paper is the specification and every guess the paper
forces is a deviation.

## Verify before you port

- Re-verify every "fact" a chat or a plan asserted about the baseline (its features, its corpus, whether weights
  exist, dataset overlaps between benchmarks) by running the installed code. In the source project the chat-drafted
  plan was wrong on four such facts, including a 49-of-51 dataset overlap between two benchmarks.
- Keep "Verified APIs (version + signature)" and "Gotchas found by running the code" in the same notes file:
  hooks that must clone their tensor, output that depends on `PYTHONHASHSEED`, a precision mode that drifts 2e-3
  on one device.
- A null result in the reproduction is reported as a null.
