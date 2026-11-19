# Agreement between two embedding spaces

Two encoders embed the same items. Do they see the same geometry? Three estimators answer different versions of
the question, and each has a trap.

## Setup

- **Same items, same order.** Inner-join the item ids across encoders and report how many each encoder lost.
  Join by id, never by position: a memoized positional join in another project scored the wrong items 89 to 99%
  of the time.
- **Subsets.** Compute everything within each meaningful group (real, synthetic; source A, source B; tissue
  type) and over the union. Report the union only beside the subsets.
- **Size cap.** Subsample to at most 600 items per subset for the permutation test, seeded, and say so.
- **Space.** Each encoder in its own analysis space (cleaned, scaled, PCA). Agreement does not need the two
  spaces to have the same dimension.

## The three estimators

| Estimator | Question | Chance or null | Trap |
|---|---|---|---|
| Spearman between distance matrices (Mantel) | do the two spaces rank pairwise distances alike? | permutation p, rows and columns permuted together, 199 to screen, 999 to report | the plain Spearman p-value treats n(n-1)/2 dependent entries as independent |
| k-NN overlap | do items keep their nearest neighbors? | k/(n-1) | read without chance it looks small; 10-NN on 100 items has chance 0.10 |
| debiased linear CKA | do the two spaces share linear structure, up to rotation and scale? | 0 for independent spaces | biased CKA is inflated in high dimension at small n |

Biased against debiased CKA between independent Gaussian matrices (simulation in the source study, n = 100):

| p | biased | debiased |
|---|---|---|
| 16 | 0.14 | 0.00 +- 0.02 |
| 32 | 0.25 | 0.00 +- 0.02 |
| 64 | 0.39 | 0.00 +- 0.02 |

`probes.py selftest` reproduces the first row (biased 0.136, debiased -0.003).

The estimator (Kornblith et al. 2019 for linear CKA; Song et al. 2012 for the unbiased HSIC):

```python
def linear_cka(X, Y, debiased=True):
    X, Y = X - X.mean(0), Y - Y.mean(0)
    K, L = X @ X.T, Y @ Y.T
    n = K.shape[0]
    def hsic(A, B):
        A, B = A.copy(), B.copy()
        np.fill_diagonal(A, 0); np.fill_diagonal(B, 0)
        return ((A * B).sum() + A.sum() * B.sum() / ((n - 1) * (n - 2))
                - 2 * (A.sum(0) @ B.sum(0)) / (n - 2)) / (n * (n - 3))
    return hsic(K, L) / np.sqrt(hsic(K, K) * hsic(L, L))
```

## Why the union lies

When two groups sit far apart in both spaces, every between-group distance is large in both, and those pairs
dominate any distance-based statistic. In the source study, agreement over the pool "is dominated by the
real/synthetic split". The fixture in `evals/agreement-mixed-union` shows the extreme case:

| subset | n | Spearman (Mantel) | p | 10-NN overlap | chance | debiased CKA |
|---|---|---|---|---|---|---|
| real | 100 | -0.08 | 0.97 | 0.102 | 0.101 | -0.002 |
| synthetic | 100 | -0.04 | 0.80 | 0.099 | 0.101 | 0.011 |
| union | 200 | 0.73 | 0.005 | 0.101 | 0.050 | 0.985 |

The two spaces share one fact (which group an item is in) and nothing else. `probes.py agree --groups` prints a
warning when the union is more than 0.2 above every subset.

## "CKA near 1"

- Use debiased CKA, a null from a shuffle-trained or label-permuted model, and a cross-check by model
  stitching.
- Name shared causes: two encoders trained on the same target, data or initialization converge partly by common
  cause. Agreement at a shared output layer was "near-tautological" for that reason.
- Convergence of representations at matching scales is a known phenomenon (SVCCA; Kornblith et al. 2019).
  Claim the mechanism the study adds, not the phenomenon.

## Few items

With 10 items there are 45 distances. Report the matrix of Spearman values, and write "indicative, not
conclusive". The source panel used it only to decide which encoder would add a new view (a pair at 0.26 added
one; a pair at 0.67 did not).

## Writing the result

State the subset, n, the estimator, its chance level or p, and the union separately. For example:

> Within real items (n = 100), distance rank correlation between the two encoders was -0.08 (Mantel p = 0.97,
> 199 permutations), 10-NN overlap 0.10 against a chance level of 0.10, and debiased CKA 0.00. Over the pooled
> real and synthetic items CKA was 0.98, which reflects the separation of the two groups that both encoders
> share.

When the user wants the pooled number alone as evidence of agreement, give the honest sentence instead and say
why. A result that contradicts the claim changes the claim.

## Running `probes.py agree`

```bash
python3 scripts/probes.py agree --a ours.npy --b baseline.npy --groups groups.txt \
  --k 10 --n-perm 999 --max-items 600 --out agreement.json
```

`groups.txt` holds one label per line in item order. Subsets under 12 items are skipped and listed.
