# notes for the paper (weft)

- weft = pretrained encoder for tables. one embedding per cell, row and table embeddings are attention pooling over cell embeddings, so you pick the unit (cell / row / table) at query time
- main thing people do now: serialize the table into a fixed length token sequence (truncate at 512 cells) or fit a model per dataset (gbdt). serialization throws away column structure and caps context
- corpus: 1.8 million public tables from open data portals, 4.1 billion cells total. largest table 9.6 million rows
- encoder: column-wise attention inside each row then row-wise attention across rows, cost linear in number of rows (no full attention over all cells)
- training: masked cell prediction in embedding space with an EMA target encoder (JEPA style, cite i-jepa)
- eval: frozen embeddings, linear probe, 12 downstream tasks (8 classification, 4 regression), 5 seeds, compare 14 other methods = 5 pretrained tabular foundation models, 6 gbdt / per-dataset neural nets fit on each task, 3 simple baselines (mean imputation + logistic/linear, PCA of raw features, random-init encoder)
- ranking: mean rank over tasks + Elo from paired per-seed comparisons (cite elo)
- results are in results.csv
- weakness: regression tasks, there gbdt fit per dataset is usually better
- our motivating application is hospital EHR tables but we don't want the paper to be an EHR paper
- venue: ICLR, double blind
