# Numbers that look too clean

A suspiciously identical, fast, smooth or low number is a bug until it is cleared. The author caught each of the
cases below by asking the obvious question.

## 1. The checklist

| What you see | Likely cause | How to clear it |
|---|---|---|
| ablation arms agree to 3 decimals | the same checkpoint loaded for several arms; the varied component is off the path that is read out | hash the checkpoint files and the output arrays per arm; check which layer is exported |
| identical SDs down a column | SD taken over head seeds of one fold, or computed once and broadcast | recompute from the per-fold scores; state in the caption what ± means |
| variants give identical pictures | outputs identical by design (the readout bypasses the varied part) or a rendering cache | compare arrays by hash, maximum absolute difference and CKA; compare PNGs pixel-wise |
| identical VRAM or time across models | the meter reads a fixed overhead or one run | read the meter's code path; rerun one model alone |
| a run many times faster than before | a fast path skipped data or ran on a subset | count items processed; compare with the previous run's count |
| a held-out curve falls smoothly forever | leakage between train and held-out units | check overlap of groups (tables, sources, donors, sections); see `ml-evaluation` for fold purity |
| a loss pinned at a constant | a trivial solution | compute what predicting zero or the mean scores (`training-diagnostics`) |
| an aggregate count that disagrees with its rows | rows enumerated but never opened counted as zero | add a coverage block; label the total a floor |
| a claim over "every method" | computed over the methods that did not crash | print coverage n per cell; refuse cells with too little coverage |
| two scorers that should differ give the same table | the same scorer called twice | diff the scorer code paths |
| a much lower score than expected | the probe or the labels | audit the probe before any claim: label quality, balance, leakage, capacity, a raw-feature probe |

`scripts/too_clean.py` runs the first, second and ninth checks on a long results table and hashes arrays for the
third.

## 2. Receipts

- Name every number's receipt in one clause: the file, the commit or the job that produced it. "The tool printed
  it" is not a receipt.
- Every quoted number traces to a committed probe output (`probes/<name>.py` with its `<name>.out`). A script
  without its output is "re-run before citing".
- Where a survey, a document or a line of prose disagrees with a results file, the file wins and the disagreement
  is recorded.
- Mark claims by status (CONFIRMED, LIKELY, SPECULATIVE) when they enter a design document.
- Join tables by ID, never by position. A memoized positional join once scored the wrong items' embeddings most of
  the time and the result was printed as science.

## 3. Reading trends

- No trend from fewer than 4 to 5 points or from the first ~10 steps. Use medians over at least 20 logged steps.
- The two-point read is most tempting when it confirms the change you just made.
- A default is not an observation. Never `.get(k, 0)` a metric and interpret the zero; assert the key or print
  `absent`.
- "0.0 loss with zero mass means 'no valid query', never 'solved'": log the mass behind every averaged term.
- Compare validation losses only within one objective, one masking distribution and one held-out set, keyed by
  the content hash of that set.

## 4. Coverage and silent subsets

- Never silently subset. Compute on all the data; a subsample used only for drawing is fine and the caption gives
  the bin or window size.
- State the coverage of every aggregate.
- Treat missing results as explicit statuses, never as dropped rows; keep floors and exclusions as named constants
  in one file.

## 5. Nulls

- A null is a finding. Report it as a null, scoped to the setting that was tested ("does not help at this context
  size", not "does not help").
- Distinguish "deferred on cost" from "refuted on mechanism".
- Do not synthesize a conclusion the numbers do not support.
