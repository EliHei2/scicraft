# Hunting and disclosing a showcase example

A showcase example is the one window, image, prompt, document or field of view that lets a
reader see the effect with their own eyes. It is chosen, so it is a claim about the choice.
The procedure below ran at least eight times in the source work, for qualitative panels in a
benchmark paper. The rules hold for any field: a qualitative failure case beside a benchmark
table, a sample generation beside an FID curve, a retrieved neighbor beside a recall number.

## The rules

- **The quantification is always global; the example only illustrates.** "whatever you show
  in bars and stats it should be global." "You can show a subset, but show statistics from the
  whole" dataset. No per-tile number on an example whose single window is unrepresentative.
- **Pick by a stated, scripted criterion, never by eye from the best cases.** A search that
  ranks candidates on the criterion returns the best available option every time; a search
  with hard thresholds can return nothing. Rank with the renderer's own functions, because the
  space the scorer sees and the space the reader sees can differ.
- **The example must contain the phenomenon it claims, for the hero too.** One gallery window
  had zero events for the hero, so "keeps them unobstructed" was meaningless. A competitor's
  zero came from a different failure (it had fused the items), so it was misleading. A
  dramatic window was rejected because the hero was also messy there: no contrast.
- **Desirable properties can be anti-correlated.** A perfectly clean hero existed only in
  sparse windows, while dense windows showed the real effect at a lower contrast. Choose the
  best simultaneous satisfier and state the trade-off.
- **Mark failures of your own method with the same rule as everyone else's.** "don't cheat"
  was said about an example where the competitor's failures were marked and comparable hero
  failures were not.
- **Include everything in the frame that the rule selects**, not only the items that flatter.
  Every item of the selected kinds inside the window is drawn, removed by the method or not.
- **Representative or illustrative, said plainly.** Prefer a window near the dataset median
  of the score ("closest to the run-wide median", then nudged for framing within a small
  tolerance) when the claim is typical behavior. When the window was picked for a strong
  signal, the caption says "illustrative", names the criterion, and gives the local value
  against the dataset value ("local value about four times the section value").
- **Lay a qualitative comparison out as columns that read left to right**: the raw input, then
  the ground truth or a reference built without any compared method, then each method in the
  paper's order. Every column shows the identical input items, and only the method's own layer
  changes between columns. In the source, fixed anchor points stayed identical in all three
  method columns and only the method-dependent graph changed. ML form: input, label, model A,
  model B on the same example.
- **The overview and every zoom read the same items.** A zoom panel once drew different items
  from the overview it claimed to enlarge. Render a larger window and crop; check every
  connector lands on the same box.
- **Validate the features an example is built around.** "1000% sure these are confident
  markers, not expressed in other cells" became three independent evidence streams plus
  adversarial skeptics; several candidates were rejected as not specific, and the rejections
  were recorded.
- **"Pick better examples" comes with a criterion**: ask for it if it is missing. Typical
  criteria in the source: hero good and competitors bad on the claimed axis; a structure
  that is textbook-clean; a mechanism the author describes literally ("[the two interacting
  items] side by side, and the other method's [outputs] run over each other").

## The procedure

1. **Write `find_<thing>_example.py`.** Scan the whole dataset with a composite score. Each
   term encodes one property: the coherence of the structure, proper unit sizes, hero clean,
   rival failing, an incident worth a zoom. Make one term a hard gate (for example: hero has
   at least [k] real events and no failures; the competitor at least [m] failures). Log every
   parameter.
2. **Run a cheap viability check first.** Before an expensive hunt, confirm that the features
   the criterion needs exist in the data at all; one hunt was proven field-limited in minutes.
3. **Render previews of the top 7 to 15 candidates** to `data/<fig>/_<name>_candidates/` with
   a `_candidates.json` index. Use a lean renderer that skips heavy layers if memory is tight.
   For the author's review, one page per category, rows are candidates, columns are methods
   or parameter levels, in one multi-page PDF; the author picks by ID.
4. **Judge.** Fan out judges that read the PNGs (five lenses, or three judges per candidate,
   then a synthesizer). Record the mean score, the winner, the runner-up as a ready fallback
   and the trade-off between them.
5. **Apply the winner. Back up the previous choice as JSON** so a revert takes seconds. Delete
   the candidate scratch.
6. **Write the caption**: "illustrative", the criterion, the local against global caveat, and
   that every quantitative panel uses the whole dataset.
7. **Record rejected candidates with the reason** ("do not re-propose") in the figure log.

## Machine-learning forms

| Situation | Stated rule |
|---|---|
| qualitative failure cases beside a benchmark | the median-loss example per bucket, or a seeded random draw per bucket |
| sample generations | a fixed seed list written before sampling; no regeneration until it looks good |
| retrieval or nearest-neighbor examples | queries drawn at random from the eval split with a stated seed |
| "where the baseline fails" | the gate requires the baseline's failure to be a real error, not a refusal or empty output |
