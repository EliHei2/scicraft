## 4 Results

### 4.1 Benchmark

Across the 24 classification datasets our model wins against all five baselines (BH q < 0.05 for every
comparison, paired Wilcoxon over the 10 outer folds of each dataset). It beats XGBoost (q = 0.000333), CatBoost
(q = 0.001125), the MLP (q = 0.000025) and kNN (q = 0.000005). Against TabBase the gain is smaller but still
significant (p = 0.034†). Mean accuracy is 0.842 ± 0.031.

† unadjusted, added after pre-registration.

**Figure 3 caption.** Accuracy per method. Bars show the mean over datasets, whiskers show 95% bootstrap
intervals. Stars mark significance.

### 4.2 Ablations

Removing attention or pretraining gives a clearly detectable drop in accuracy (Holm-adjusted p = 0.0024 and
p = 0.0055). Removing row shuffling also hurts (Holm-adjusted p = 0.048). The effect of removing feature tokens is
undetectable (Holm-adjusted p = 0.063), the small-context variant is insignificant and label smoothing is
invariant (p = 0.62). Overall the ablation results remain mixed but support the design.

**Figure 4 caption.** Change in accuracy when one component is removed (mean over folds, whiskers 99% CI).
