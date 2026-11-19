# Reproducibility bundle: [paper short title]

Everything a reader or auditor needs to go from a number in the paper to the run and the code that made it.

- Paper version: [file name], md5 [md5], dated [YYYY-MM-DD]
- Code: [repository URL], branch [branch], commit [sha], made public [YYYY-MM-DD]
- Results table every figure reads: [path to the master table], md5 [md5]

## Read in this order

1. `RUN_MAP.md`: each figure or table value to the run and output path that produced it.
2. `METRIC_MAP.md`: each metric name to its code file, commit and settings as run.
3. `inputs.tsv`: per dataset and method, the exact input files and run-time parameters.

## Rerun one value

```bash
[the exact command for one row, with every non-default setting written out]
```

Expected output: [the value it must print], to [n] decimals.

## Not covered

[values that cannot be regenerated from this bundle, with the reason, or "none"]
