# Size ladders and backbone swaps

## 1. Sizes

- Pre-register the sizes by order of magnitude of parameters. For example three sizes S, M and B, each
  about an order of magnitude larger than the last. The author's reason for refusing smaller stand-ins: "local test might be super misleading on such
  big models we try to have."
- Keep the input realistic on every size. No per-example subsampling in the training path below the sizes the
  model will meet; a cap on points per input was "the killer" of an earlier design.
- Vary one axis across sizes. Keep the output embedding dimension fixed ("do not add the dims, add layers ... or
  however they scale") and follow how successful families scale their transformer. Hold data, steps, objective
  and every other knob identical.
- If depth changes reach or receptive field in your architecture, hold depth fixed across the ladder and run the
  depth arms at the middle size before launching the largest one; a winner there is inherited by the largest size.
- Report for each size: parameters, samples or tokens seen, steps, and inference time.

## 2. One checkpoint per size

- One size equals one reported checkpoint. The rule that picks it is written in the pre-registration before any
  scoring: a fixed step, or the cooldown fork of a WSD schedule declared when the fork launches.
- Never best-of-seeds and never best-of-sizes. With several training seeds, the reported cell is the mean over
  seeds at the declared step.
- Leaderboards carry one representative checkpoint per size. Your own ablations and older versions stay out of the
  leaderboard.
- Selection instruments (an anchor validation set, a quick probe) are selection only and never appear in a reported
  table.
- Pre-write the fallback for an undertrained large size: "The largest model reached only N steps at the submission
  cutoff and is reported as an in-progress capacity check in the appendix, not a scaling point."

## 3. Show that pretraining helps

Plot the held-out loss and every downstream score against samples or tokens seen (not steps), one line per size,
with dashed horizontal lines for the strongest comparators per task. A curve that is suspiciously smooth or always
falling triggers the held-out check first (`references/sanity-checks.md`).

## 4. The size test

Assert the ladder in code, so that a default cannot drift. The bands and the recipe line are placeholders for
yours:

```python
def test_size_configs_load_and_share_the_recipe():
    s, m, b = (load_config(ROOT / "configs" / f"{r}.yaml") for r in ("s", "m", "b"))
    for cfg, lo, hi in ((s, S_LO, S_HI), (m, M_LO, M_HI), (b, B_LO, B_HI)):   # [your pre-registered bands]
        n = sum(p.numel() for p in build_model(cfg).parameters())
        assert lo <= n <= hi
    for cfg in (s, m, b):                       # the shared recipe: every paper constant, once
        assert cfg.model.d_out == D_OUT and cfg.train.lr_schedule == SCHEDULE   # [your paper constants]
```

- Assert parameter counts within bands, every constant from the methods table, and every derived rule recomputed
  in the test.
- Comment the assertion with why a reverted change was wrong, so it is not reintroduced. In the source project a
  paper constant had been moved on a mis-measured argument and the test comment now records the measurement.
- Change a default only through the plan of record plus a row in this test.

## 5. Backbone swaps

Purpose: separate the value of the concept (the representation, the objective, the prior) from the value of the
architecture.

- Hold fixed: representation, objective and losses, data and preprocessing, step count, seed.
- Swap only the backbone, using its authors' implementation, with parameter count within a few percent of yours.
- Compare at the same checkpoint step ("use the same step checkpoints for this").
- Tabular form: the same synthetic prior and pretraining objective with two backbones (for example a row-and-column
  attention transformer and a set encoder). A 2 x 2 of {in-context foundation model, small set encoder} x
  {trained on synthetic tables, trained on real tables} separates architecture from data source.
- Report the swap beside the main table, with what was held fixed stated in the caption.
