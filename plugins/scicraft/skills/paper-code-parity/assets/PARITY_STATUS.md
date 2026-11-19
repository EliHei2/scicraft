# Parity status: [project name]

What this repository reproduces from published work, how closely, and where it departs. A fresh reader or agent
acts on this file without opening the code. Update it in the same commit as the change it describes.

Legend: **R** exact reproduction (same procedure as the paper or its released code, checked against a number the
authors published or released) **A** approximate reproduction (same idea, a documented difference in procedure)
**E** new extension (not in any of the reproduced papers). A row with no published reference says so (`none`).

## Implemented

| component | type | where (module.function) | checked against |
|---|---|---|---|
| [e.g. the baseline's preprocessing] | R | `[data.canonical]` | [port matches the library's own function to 1.7e-6, test `test_port_matches_library`] |
| [e.g. the 70-feature descriptor, re-implemented from the paper's definitions] | R (code-level, re-implemented) | `[features.descriptor]` | [the authors' released values, r = 1.0000 on N inputs] |
| [e.g. a pretrained encoder, retrained with fewer steps] | A | `[encoders.retrain]` | [deviation 3 below] |
| [e.g. a new perturbation family] | E | `[perturb.py]` | none |
| [infrastructure: loaders, cache, manifest] | none | `[utils.py]` | none |

## Partially implemented

- [What exists, what is missing, and the limit that applies, with its number.]

## Blocked or not done

- [What, why, and what would unblock it.]

## Next actions

- [One line each.]

## Deviations from papers

Numbered per reproduced paper. Each deviation says what the paper or its code does, what this repository does,
why, and the measured size of the difference when it is known. A deviation found later is added here, never
folded silently into the code.

- **[Paper short name, component].** [Re-implemented from the documented definitions / ported from the released
  code at commit [sha] / weights from [source], license [license].] Deviations:
  1. [The paper does X; we do Y; because Z.]
  2. [The paper's protocol does X, which [named problem, e.g. leaks duplicates into the test set]; we do Y.]
  3. [The released code differs from the paper's table (the code has N parameters and a d-dim output, the table
     says M and d'); we follow the released code and state the count.]
- **[Library, component].** [Version N silently changed a default (PR or commit); we restore the earlier
  behavior. Labeled "port not experimentally verified" until checked.]
- **[A claim in our own plan or prompt that turned out wrong].** [What was claimed, what is true, the source.]

## Verified APIs (package version and signature, checked by running the code)

- **[package] [version]: `[Signature(...)]`.** [What was verified and how; any gotcha found by running it.]

## Measured runtimes

| step | input size | time | machine |
|---|---|---|---|
| [step] | [rows x features] | [seconds] | [machine, cores] |
