# data/

Nothing here is tracked except this file.

- `data/raw/<name>` are symbolic links to raw stores outside the project. They are read in place and never edited. Each link has a row in `PROVENANCE.md`.
- `data/<unit>/` holds small inputs copied, summarized or wrapped from those stores (TSV, JSON). Only documented prep scripts read the raw stores; everything else reads these copies. Each copy has a row in `PROVENANCE.md`.
- Model outputs never come back in here as inputs.

To recreate the links on a new machine, set `RAW_ROOT` in `configs/paths.env` and run:

```bash
[ln -s "$RAW_ROOT/<store>" data/raw/<name>]
```
