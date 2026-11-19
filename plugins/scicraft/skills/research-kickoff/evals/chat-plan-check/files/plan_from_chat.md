# Project plan: how realistic are synthetic tabular generators?

Generated plan. Use it as the build prompt.

## Background (facts)

1. The generator library is `minigen`. Its `Generator` turns on causal structure by default (since version 0.3), so default tables have correlated features.
2. `Generator(seed=...)` makes every table fully reproducible, also across separate processes and machines.
3. No pretrained encoder weights for minigen exist, so we will have to train our own encoder from scratch.
4. The minigen encoder maps each dataset to a 64-dimensional vector, as stated in the paper.
5. Comparing generators by dataset embeddings has been the standard approach in industry since 2024.

## Plan

- Install minigen, sample 500 tables with default settings, encode them, compare with 100 real tables.
- Train the encoder on the CPU overnight.
- Report the AUC of a logistic regression that separates real from synthetic.
