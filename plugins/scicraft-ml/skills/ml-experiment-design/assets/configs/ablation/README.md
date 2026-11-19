# Ablations: the validation table as configs

Every file here is a few-line override of `../base.yaml` (`base:` is deep-merged; the child wins).
Numeric sweeps need no file: `--set train.lr=1e-4`. Every file trains one real step in CI.
Protocol: [3] training seeds per arm, one config-identical replicate arm per wave as the noise unit,
comparisons at matched samples seen, differences below 3 replicate SDs printed as ties.

## The decisive experiments

| # | claim | arms | falsified if |
|---|---|---|---|
| 1 | attention across columns is needed | `base.yaml` vs `no_column_attention.yaml` | within 3 replicate SDs on every task |
| 2 | a learned readout beats a mean | `base.yaml` vs `mean_pooling.yaml` | within the noise band |
| [3] | [claim] | [arms] | [falsifier] |

## Pre-staged conditional arms

| arm | trigger | expected signature |
|---|---|---|
| [arm file or --set] | [the measured condition that launches it] | [what you expect to see if the hypothesis holds] |
