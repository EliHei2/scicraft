# notes for results section (me, rough)

- benchmark: 40 OpenML classification datasets, 10 folds each, accuracy averaged over folds then datasets
- main claim: retrieval helps, mostly on small data
- stats: wilcoxon signed-rank over datasets vs GBT, p = 0.003 (BH adjusted across the 4 comparisons). vs TabTransformer p=0.02, vs TabMLP p=0.004, vs kNN p<0.001
- GBT is ahead on 9 datasets, all of them > 10k rows
- tried a 10x bigger index (augmented with synthetic rows) on 5 datasets, one seed, got about +0.02 more. didnt rerun GBT on those. maybe mention??
- cost: 12 ms per query on one A100 vs 0.4 for GBT
- Fig 3: (a) gain vs train size scatter, (b) per-dataset accuracy RowRetriever vs GBT
