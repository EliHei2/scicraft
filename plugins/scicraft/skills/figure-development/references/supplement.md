# Supplementary figures and the main-versus-supplement audit

## What a supplementary figure is for

- **It explains the mechanism behind one main-figure claim, or answers one reviewer question.
  It never re-shows the main result.** A supplement rejected as "shows nothing / it's the main
  figure" was rebuilt around a downstream consequence where both competitors fail. Name the
  parent panel or the question in the supplement's first caption line.
- **Organize it by one principle the reader already understands**: one row per mechanism, one
  figure per length scale, regime or data size. Two overlapping weak supplements that made the
  same point were merged into one.
- **It extends its parent; it does not replace the parent's metric family, granularity or
  layout.** A supplement with new metrics on a new page size was built and rejected the same
  day: "keep the metric family, keep the aesthetic, keep the three examples, only add bar plots
  and an embedding." "I don't want to introduce a new metric." A more honest new metric goes
  into the caption and the provenance notes as a documented, unplotted result, and is not
  re-added as a tile without being asked.
- **Mirror the main figure's grammar** (example tiles, bars, legend placement). One packed
  supplement was split into focused supplements that each mirrored a main figure.
- **Ship the true operating point beside any sweep.** "remake the supp figures with the real
  results, no shift." A sweep of the method's own knob is drawn as a curve and the native
  default is marked on it; a two-point "true" version (native setting against the competitor,
  zero-based) sits beside the sweep.
- **Sweep the method's knob as an additive shift on its native cutoff**, not as one fixed
  absolute threshold (a correction from the author): for example
  Delta in {-0.5, -0.25, -0.1, 0, +0.1, +0.25, +0.5}. Omit values that keep almost nothing.
  Hold labels and selected features fixed across the sweep. Sanity check that the keep-all end
  matches the competitor that keeps everything.
- **Before sweeping, assert that the native cutoff is constant within each item** (one
  threshold per class or feature; the largest within-item standard deviation of the cutoff must
  be 0). Keep an item when its score is at least its native cutoff plus Delta. Beside the
  scatter, draw a metrics strip (units, items per unit, % kept, contamination, a confidence-like
  rate) with the competitor as a dashed line. Select the run through a config dictionary passed
  as an argument, and let the composer read every number it prints from the sweep table.
- **Defend a metric with sensitivity supplements**: vary the reference, the confidence subset
  and the selection threshold, one panel each, each with the default marked. Titles name the
  quantity in plain words ("Minimum counts per unit"); the author banned "robustness" and
  "gated" from titles.
- **Show the cost at the same scale as the benefit.** Where the method wins only in a stratum,
  say so and show the excluded strata grayed below a divider with the reason.
- **A dense panel gets its own full-width row.** Split a row before shrinking it.
- **Main or supplement: decide by the claim, never by the result.** A panel that does not
  discriminate between methods leaves the main figure; its number goes to a caption sentence
  and its script stays. A weak or mixed result goes to the supplement with its number. A
  schematic that would crowd out evidence goes to the supplement unless it is Figure 1.
- **About ten striking figures carry the main text** in a long report; the rest go to a
  numbered supplement, with a one-line pointer wherever a figure moved out.

## The main-versus-supplement audit

Readers cross-check the main figure against the supplement, and a difference in the second
decimal "reads as an error". The author called this check "critical" and "water-safe".

**Rule: at the supplement's default operating point, every value equals the main figure.**

1. **One metric implementation, imported everywhere.** Never re-implement a metric per panel.
   Shared filters (for example a minimum count of 20) live in one constant.
2. **One master table is canonical.** Any metric that also appears in the master table is
   pulled from its canonical row (the default run), not from whatever sweep run the local
   analysis used. If the rest of a panel uses another run, the caption says so.
3. **Every sensitivity panel shares one y-range per metric and carries a dashed "default" line
   at the main-figure operating point.** The line's value is read from the master table, not
   typed.
4. **After any metric change, recompute the supplement defaults and diff them against the
   main values exactly** (`scripts/number_parity.py diff`, or `claims` mode for printed
   strings). In the source, a supplement differed from the main figure in the first decimal
   because a cache kept units below the main filter; the fix gated at read time.
5. **Markers, features and thresholds shown in the main figure come from the supplement's
   selection plot**, with the selection thresholds drawn and annotated there, signed correctly
   (+1 for positives, -1 for negatives, not an absolute value), and the selected items listed.
   Print beside each selection plot how many items pass each rule (for example [9] of [40]
   positives, [12] of [40] negatives). Then read the selection code and confirm it applies the
   written threshold: one pipeline took the top of a sorted score list with no cutoff at all, so
   the written rule described nothing ("we don't have any cut-off ... we just get those from
   sorted z scores right?").
6. **The main text cites the same number.** Build the manuscript-reportable numbers table in
   NARRATIVE.md (number, statistic, n, interval, source row) and list every text-to-figure
   mismatch (units, statistic names, panel counts). One audit found three: an absolute
   distance described as normalized, a peak described as a median, and panels a to c described
   as a to d.
7. **Ablation form**: the full-model row of every ablation or sweep table equals the main
   table's row for that model and setting.
