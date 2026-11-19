# CLAUDE.md

fmbench: we are building a small tabular foundation model (smalltab) and testing whether it can match tuned gradient boosting on a public suite.

## what we want

- end goal: smalltab matches or beats tuned XGBoost on the 38 classification tasks of suite v2 (mean rank over 10 seeds), with one forward pass and no per-dataset tuning. target: submission end of March.
- right now: 20-dataset pilot by Friday. need the pilot table, the seed spread, and the rank plot. if smalltab is more than 1 rank behind tuned XGBoost on the pilot we stop and rethink the prior.
- later maybe: regression tasks, a pip package, bigger context. not now.

## rules

- NEVER tune anything on the test folds. model selection uses the validation folds only. we got burned: an early table selected the checkpoint on test and the 2-point gain vanished.
- keep files under 200 lines if possible
- use type hints
- never write into /shared/tabdata, that cache belongs to the whole group. copy what you need into data/.
- prefer polars over pandas for loading
- every reported number comes from results/aggregate/*.parquet, never typed by hand. the abstract draft once had 0.861 where the table had 0.816.
- commit messages: imperative, name the decision
- the XGBoost baseline always gets its stated tuning budget (100 trials). a comparison against default XGBoost is not allowed in any table.
- do not add new dependencies without asking
- seeds: always 10 seeds, report mean and IQR

## facts

- suite v2 has 38 classification tasks, 4 of them are renamed copies of older ones (same row counts)
- XGBoost tuned with 100 trials takes about 6 GPU-hours for the whole suite on our card
- the Heron paper reports results on 33 of our 38 tasks
- our GPU box has one 24 GB card, batch 256 fits, 512 does not

## status

- loader works for all 38 tasks
- prior sampler v3 done
- pilot run: blocked, the box is down until Wednesday
- rank plot script: not started
