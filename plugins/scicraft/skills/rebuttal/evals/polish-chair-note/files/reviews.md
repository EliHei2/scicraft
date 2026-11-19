# Reviews (copied from the forum, 3 reviewers)

## Reviewer Xq7P (rating 4: borderline reject)

Strengths: The idea of pretraining one encoder on many molecule collections is interesting and the paper is clearly written. The benchmark covers many tasks.

W1. The paper reports averages only. It is not clear on how many tasks the encoder is actually better than GraphFM, and on which tasks it is worse.
W2. The ablations are run with a small model and short training, so it is unclear whether the components matter at full scale.
Q1. How do the results change when scaffolds seen in pretraining are excluded from the test sets?

## Reviewer Lm2T (rating 6: weak accept)

Strengths: Strong empirical results and a useful public benchmark.

W1. The comparison with GraphFM is not fully fair because GraphFM was pretrained on fewer molecules.
Q1. What is the inference cost compared to the baselines?

## Reviewer Rk9D (rating 6: weak accept)

Strengths: Well motivated, convincing ablations of the attention design.

W1. Please report results with more than one random seed.
