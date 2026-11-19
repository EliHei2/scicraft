# One source of truth for names and settings, and the contract between repositories

## One vocabulary file

- **Every id, label, direction, sweep grid and threshold comes from one module** (`vocab.py`, or a JSON file the
  code loads). Never hardcode an id or a threshold in a runner: import it. In the source benchmark repository the
  module header read: "every runner, metric wrapper, aggregator, and contract check imports these dicts so the
  method / dataset / metric IDs, labels, directions, and sweep grid can never drift between a re-run and the
  canonical scoreboard".
- **Human-readable maps are views of it.** `METHOD_MAP.md`, `DATASET_MAP.md` and `METRIC_MAP.md` were generated
  from the module, never edited beside it. The same rule held for cluster paths (one env file) and for a release's
  model id (kept in one place, so a change is one search and replace).
- **Each entry carries what a reader needs**: id, display label, paper abbreviation, direction (up or down is
  better), and the function that computes it.
- **Display names are a dict applied by the renderer**, never typed into a figure or table. Internal ids
  (`run_r0p05`, run names, hardware names) never print. A display name that is wrong in some setting is fixed
  in the dict with the reason written beside it (a vendor's name for a default method was wrong on the other
  vendors' datasets).
- **The manuscript's terminology wins.** Priority: manuscript text, then main figures, then tables, then the
  supplement. Never coin a term or a symbol the paper does not use; the author threw out an invented symbol with
  "if we don't have it leave it as is". A terminology check extracts the paper's key terms and flags synonyms in
  every other document and figure label.
- **Settings follow the same rule**: the config is the only place a hyperparameter is set; the paper map, the
  README and the methods text point to it (`paper-tests.md`).

## The contract between repositories

When results are produced in one repository and the paper or figures in another, name the hand-off file as a
contract.

- **Each repository has one deliverable and one write target.** In the source project the upstream repository owned
  "everything upstream of the figures": its deliverable was one long-format scoreboard (one row per method, dataset and
  metric; columns method, label, dataset, label, metric, label, direction, value, ci95), copied
  byte-identical into the figure repository. `results/` was its only write target.
- **A frozen reference copy** of the contract is tracked in `reference/`, and every regeneration is checked against
  it: schema, vocabulary, the complete grid, no duplicates, and the hash.
- **A legitimate change is recorded, then propagated**: refresh the reference, write the new hash and the date in
  the provenance log, and refresh the downstream copy deliberately. "Visible drift, never silent."
- **The downstream repository reads only the contract.** Raw outputs stay outside it and are read only by
  documented prep scripts; each copied file gets a provenance row in the same edit.

`scripts/verify_contract.py` is the generalized check, ported from that repository:

```bash
python3 scripts/verify_contract.py --actual results/aggregate/scoreboard.tsv \
    --reference reference/scoreboard.tsv --vocab vocab.json            # sha256; --hash md5 for the original
python3 scripts/verify_contract.py ... --allow-drift                  # schema and vocabulary only
```

It prints `OK: rows=N sha256=...` when the bytes match, `OK_SCHEMA_ONLY` when only `--allow-drift` let a value change
through, and exits 1 on a header mismatch, an unknown id, a missing or extra or duplicated grid key, or hash drift.

Provenance log row (one per contract refresh or copied input):

| file | source | hash | source date | copied on | reason |
|---|---|---|---|---|---|
| `data/figure_3/scoreboard.tsv` | upstream `results/aggregate/scoreboard.tsv` at commit [sha] | sha256 [first 12] | [date] | [date] | [what changed and why] |

## Data identity

A dataset row is defined by its bytes, not by its name or title. Check a public dataset against its source byte
for byte (the `integrity-audit` skill has the remote-zip check); labels taken from titles can carry a wrong tissue,
a wrong species or a wrong feature count into a figure. A derived output never re-enters as an input.
