# When the result goes against the method

The evidence behind this skill includes many moments where a result went against the author's own
method and the request was to make it go the other way: find a setting or an operating point where the
method ranks higher. The same author also wrote the rule this file encodes: "for
selection you can be biased, to compute the values or stats you can't be biased", and asked, when in
doubt, "use the raw metric and compute it on this dataset".

## 1. The response that works

1. **Recompute from the raw metric.** Go back to the per-fold records, recompute the number with the
   frozen scorer, and check the run identity (`checkpoint_identity.py`) and the join. A surprising result
   is a bug candidate, in either direction: too good is as suspicious as too bad.
2. **Check the pipeline.** Normalization, the unit of replication, the n per group,
   the decision stage, the depth budget, fold leakage. If a bug is found, fix it and rerun every method,
   not only yours.
3. **If the number stands, say so plainly** with the record it comes from, and change the claim to match.
4. **Declare every post-hoc choice.** A setting chosen after seeing results is dated, labeled post hoc
   where the result is reported, and printed beside the pre-registered setting.

## 2. What the skill does not do

- It does not search settings, seeds, subsets, probes or metrics until the method wins. That is the
  creep the pre-registration in `protocol.md` guards against: peeking mid-run, renaming after relaunch,
  probe shopping, seed picking, promoting an arm, drifting the anchor set.
- It does not change a statistical test to get a smaller p, drop a weak task from a table it belongs in,
  apply a significance threshold only to unfavorable results, or move a weak result out of the record.
- It does not rarefy, subsample or rematch after the fact to make a gap appear.
- It does not exclude a comparator because it wins.

## 3. What remains the author's choice

- What to lead with, in which order, and with what emphasis, when the values are printed or plotted to
  scale.
- Which illustrative example to show, chosen by a stated rule (median score, random with a seed) and
  disclosed as illustrative.
- Which question a figure answers. A weak or mixed result goes to the appendix with its number.
- How to frame a result that holds only on a subset: scope the claim to the subset ("first on the
  reported set of N methods"), and show the strata where the method loses.

## 4. Honest forms that were used

- A null is a finding, scoped to the tested setting: "does not help at this scale", not "does not help".
- Three verdict labels: inconclusive (the measurement could not answer; say what was missing), negative
  (it answered no), dead (the measurement was degenerate). Each comes with a next action, and the
  history of reversals stays visible.
- A "dropped (honest)" list in the figure notes, each with its reason: off-message, a tiny-count
  mirage, an ordering that inverts under normalization, an effect too small.
- A "cut as fakeable" list: features or metrics removed because they could fake the result stay removed
  until new evidence.
- Weaken words after an adversarial review: "depleted", not "forbidden"; "illustrative", not
  "representative"; name what a null actually controls.
