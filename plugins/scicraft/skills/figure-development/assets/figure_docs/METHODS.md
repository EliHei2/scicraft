# Figure [N] methods

Internal record of how every panel is computed and drawn. The manuscript's Methods section is
written from this file in prose and math (see the nature-methods-writing skill); code names
stay here.

## Metrics

| Metric | Formula | Direction | Implementation (file:function) | Filters and floors |
|---|---|---|---|---|
| [name as printed] | [definition] | [higher is better] | `[module.py:function]` | [min counts, caps, subsample sizes] |

## Comparison protocol

- Methods and runs: [canonical run per method, from PROVENANCE.md].
- Reference: [what the methods are scored against, and why it can see the quantity measured].
- Null: [what "no effect" means, how it is computed, what it controls and what it does not].
- Units of replication: [seeds, datasets, spatial blocks], n = [ ].
- Subsampling: [none; or identical indices for every method, seed [ ]].

## Per panel

| Panel | Script | Reads | Size (mm) | Notes |
|---|---|---|---|---|
| a | `code/figure_[N]/panel_a_[name].py` | `data/figure_[N]/[table].tsv` | [60 x 40] | [ ] |
