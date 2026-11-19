# Calibration on data with a known answer

Run the battery where you know the answer before you run it where you do not. `scripts/simulate.py`
draws N reference items from a standard Gaussian in d dimensions and M candidate items that are
identical, shifted along one axis, or contracted on every axis, and runs the same code as `twosample.py`.

```bash
python3 scripts/simulate.py --selftest                                  # 14 known answers, about 100 s
python3 scripts/simulate.py --n-ref 80 --n-cand 400 --dim 24 --reps 20  # your own sizes
python3 scripts/simulate.py --scenarios null --reps 200 --no-c2st       # false-positive rate only
```

## Tables measured here (N=100 reference, M=500 candidate, 10 runs, 200 permutations, alpha 0.05)

d = 16 [sim]:

| scenario | linear AUC | forest AUC | energy rej. | MMD rej. | energy z | precision | recall | density | coverage | out of support |
|---|---|---|---|---|---|---|---|---|---|---|
| identical | 0.507 | 0.497 | 0.0 | 0.0 | 0.15 | 0.890 | 0.884 | 0.969 | 0.968 | 0.050 |
| shift 0.5 SD | 0.588 | 0.570 | 0.9 | 0.9 | 3.36 | 0.861 | 0.893 | 0.927 | 0.956 | 0.054 |
| shift 1 SD | 0.739 | 0.693 | 1.0 | 1.0 | 11.98 | 0.847 | 0.843 | 0.904 | 0.941 | 0.066 |
| contraction ×0.85 | 0.511 | 0.616 | 0.8 | 0.9 | 2.94 | 0.973 | 0.675 | 1.772 | 0.991 | 0.250 |
| contraction ×0.7 | 0.513 | 0.826 | 1.0 | 1.0 | 15.89 | 0.999 | 0.341 | 3.219 | 0.999 | 0.597 |
| contraction ×0.5 | 0.529 | 0.975 | 1.0 | 1.0 | 66.98 | 1.000 | 0.039 | 6.369 | 1.000 | 0.963 |

d = 32 [sim]:

| scenario | linear AUC | forest AUC | energy rej. | MMD rej. | energy z | precision | recall | density | coverage | out of support |
|---|---|---|---|---|---|---|---|---|---|---|
| identical | 0.506 | 0.502 | 0.3 | 0.3 | 0.33 | 0.840 | 0.855 | 0.982 | 0.975 | 0.052 |
| shift 0.5 SD | 0.573 | 0.544 | 0.6 | 0.6 | 2.43 | 0.833 | 0.868 | 0.878 | 0.958 | 0.040 |
| shift 1 SD | 0.708 | 0.664 | 1.0 | 1.0 | 8.33 | 0.832 | 0.834 | 0.917 | 0.957 | 0.075 |
| contraction ×0.85 | 0.514 | 0.668 | 1.0 | 1.0 | 4.68 | 0.983 | 0.505 | 2.605 | 0.999 | 0.363 |
| contraction ×0.7 | 0.467 | 0.887 | 1.0 | 1.0 | 21.73 | 0.999 | 0.124 | 6.029 | 1.000 | 0.829 |
| contraction ×0.5 | 0.519 | 0.993 | 1.0 | 1.0 | 93.26 | 1.000 | 0.001 | 13.317 | 1.000 | 0.998 |

PRDC columns are at matched sizes (candidate subsampled to 100, 3 draws per run); the analytic coverage
null at 100 against 100 with k = 5 is 0.971.

The 0.3 false-positive rate in the d = 32 identical row is chance in 10 runs. A follow-up with 400 runs
per dimension gave 0.053, 0.045 and 0.058 at d = 2, 16 and 32, and 30 runs at d = 16 gave 0.033 [sim].
A rejection rate needs about 200 runs before it can be read.

## How the numbers compare with the source project

The source project's own simulations (30 to 50 runs, N=100 against M=500) agreed on every point checked
[lit]: linear AUC 0.49 to 0.51 and forest 0.84 and 0.90 at ×0.7; energy and MMD 1.00 for contractions;
precision and recall 0.88/0.87 (d=16) and 0.85/0.80 (d=32) under no difference; recall 0.31 and 0.08
with density 3.3 and 6.1 at ×0.7. Small differences (forest 0.83 against 0.84 at d=16) are run-to-run
spread.

## What the self-test asserts

1. No difference: linear and forest AUC within 0.40 to 0.60; energy rejection at most 0.34 in 6 runs;
   out-of-support share at most 0.15; precision and recall below 0.95; simulated coverage within 0.05 of
   the analytic null.
2. Contraction ×0.7: linear AUC below 0.60; forest AUC above 0.70; energy and MMD reject in every run;
   recall below the no-difference recall; density above 1.5.
3. Shift 1 SD: energy and MMD reject in every run; linear AUC above 0.65.

Passed 14 of 14 on Python 3.10, numpy 2.2.6, scipy 1.15.3, scikit-learn 1.7.1 [ran].

## When your regime differs

Rerun the grid at your N, M and d before reading a real result. Gaussian clouds are the easy case: with
heavy tails, clusters or discrete features, expect wider no-difference bands. That last sentence is a
caution, Suggested, not yet tested in real work.
