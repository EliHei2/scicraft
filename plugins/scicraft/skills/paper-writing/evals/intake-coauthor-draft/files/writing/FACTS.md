# FACTS

**Authority.** results/main_table.csv, run of 2026-10-02. Where the draft and the table disagree, the table wins.

## Scoreboard

| Label | Value | Unit | Comparator | Source | Status |
|---|---|---|---|---|---|
| main-acc | 0.842 | mean accuracy, 40 datasets | 0.811 for XGBoost | results/main_table.csv | measured |
| ahead | 31 of 40 | datasets ahead of XGBoost | | results/main_table.csv | measured |
| cost | 12 | ms per query, one GPU | 0.4 for XGBoost | results/timing.csv | measured |

## Required statements

- XGBoost is ahead on 9 of the 40 datasets, all above 10,000 training rows.

## Retired

- `0.79` mean accuracy from the old 30-dataset split, superseded on 2026-10-02
