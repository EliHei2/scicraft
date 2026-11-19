# Paper to code map

The methods of "[paper title]" ([venue or preprint], version [N], [date]) are the specification. This file maps
every stated component to the code that implements it, the setting that controls it and the test that checks it,
and lists every place where the code makes a choice the paper leaves open, or deviates. Symbols follow the paper.
`cfg.` prefixes are config keys ([path to the config loader]). Keep it current when either side moves: a change to
an equation, a constant or a default updates this file in the same commit.

## [Section number and title, e.g. 3.1 Model]

| paper | code | setting | test |
|---|---|---|---|
| [equation in the paper's symbols, with its number, e.g. $h = \mathrm{MLP}(x)$ (eq. 1)] | `[module.function]` | `cfg.[key]` = [value] | `[tests/test_file.py::test_claim_as_sentence]` |
| [constant from Table 1, e.g. depth $L = 12$] | `[module.Class]` | `cfg.[key]` = [value] | `[test name]` |
| [a stated rule, e.g. head width $d/h = 64$] | `[module.function]` | derived in `validate()` | `[test name]` |

## [Next section, e.g. 3.2 Objective]

| paper | code | setting | test |
|---|---|---|---|
| [loss term, eq. N] | `[module.function]`; [any convention the paper leaves implicit, e.g. summed over views]. [YYYY-MM-DD] code fix: [what was wrong, what it changed, receipt file] (**paper edit: [what the text must now say]**) | `cfg.[key]` | `[test name]` |

## Choices the paper leaves open (and how the code fills them)

- **[Choice, e.g. the graph is directed].** [What the code does, the setting, and why.]
- **[Choice].** [What the code does.]

## Paper edits (open; the wording is the authors' decision)

| # | where in the paper | what the code does | proposed text | found by, date |
|---|---|---|---|---|
| E1 | [Table 1, row d_t] | [value in force and its source line] | [one sentence] | [audit or test, YYYY-MM-DD] |
| E2 | [Sec. 3.3, sentence N: typo or internal inconsistency] | [what the code follows, and why] | [one sentence] | [who, YYYY-MM-DD] |

## Ablation hooks (every switch the experiments section uses, each loaded and run one step in CI)

`[cfg.key]`, `[cfg.key]`, `[cfg.key]`. See `[configs/ablation/README.md]`.

## Corrections table (prose that disagreed with the code)

| claim | where (file:line) | truth (file:line) |
|---|---|---|
| [e.g. "mask ratio 0.75" in README] | [README.md:40] | [configs/base.yaml:12 = 0.35] |
