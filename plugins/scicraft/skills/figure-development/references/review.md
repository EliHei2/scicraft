# Review: looking, adversarial QA and the fact-check

Three passes, in this order, after the logic of the figure is right: "after you got the logic
right then start the adversarial aesthetics loop", and "do all of these adjustments before you
do the clean up and adversarial QA".

## 1. Look at the render yourself

Open the composed PNG every time, then crops of it rendered at high dpi. An agent that reports
"done" from a script's exit code misses what the author sees in a second. Check:

- No clipped, covered or overlapping text: the single most frequent complaint (more than 15
  times in one month). Measure it after any label change: render the panel in memory, collect
  every text artist's `get_window_extent()`, test pairwise overlaps and the figure bounds, and
  report the smallest gap in mm. In the source this caught a title running into column
  headers, a second title line hitting a tick label and a y-label at the page edge.
- No stretched or letterboxed panels; plot areas aligned across a row (align the axes boxes,
  not the boxes that include labels).
- Every color used appears in a legend; the legend sits outside the plot.
- Names are the manuscript's, never internal IDs, run names, hardware or tool names. Grep the
  PDF text for a banned-token list.
- The rank or color direction matches the metric direction.
- One missing-value glyph across the figure.
- Text actually rendered: some PDF text calls write nothing on overflow (a footnote box of
  9.5 mm silently dropped a 1,011-character footnote). Extract the PDF text and assert that the
  caption strings are present.
- Special glyphs rendered: a font without an arrow glyph printed boxes; another printed "µm"
  as a grave accent. Render-check every special character after a font switch.

Plot styling (sizes, tiers, palettes, label placement) belongs to the data-figures skill. This
pass checks that the figure carries its claim and that nothing is broken.

## 2. Adversarial QA

The author asks for it in so many words: "loop until ready for [the journal]", "adversarial
loop of at least 3 rounds", "maker, then harshly critical reviewer, then maker". The author's gate:
"just give me output if you can convince yourself that this figure is better than the original
I gave you".

**Shape that worked:** N lenses review the render, produce a ranked list of fixes (blocker,
major, minor), the maker applies every blocker, re-renders, and a final verifier looks for
regressions.

| Use | Shape in the source |
|---|---|
| aesthetic and logic review of one figure | 5 reviewers (four aesthetic dimensions plus logic plus fact-check), 15 ranked fixes, all applied, a final verifier caught 1 regression; a 5-round loop for "prettifying + logic + fact check" |
| metric choice | 10 agents: 5 propose by lens, 4 adversarial critics, 1 synthesizer |
| claim retraction | 9 agents: 5 metric or label variants, 3 lens critics, 1 synthesis |
| exemplar choice | 5 judges over 2 rounds |
| exhaustive search ("find the best X") | candidate generators fan out, a pre-specified deterministic screen, then adversarial judges, then synthesis |
| soundness checks | check scripts written first, one cheap agent per script returning PASS, CAVEAT or FAIL with numbers, about 10 minutes |

Rules for the loop:

- **Do panels one at a time when the figure is new**: "move on only if the harsh critics give
  good reviews".
- **Critics re-run code; reading prose is not enough.** One "honesty lens" flagged numbers as
  unsourced only because it could not read a binary table. Check each blocker against the data
  before acting on it.
- **Give reviewers the reference figures** (the in-repo figures the author accepted as gold
  standard), the data-figures skill and the original figure being reworked.
- **Record KEEP AS IS guards** in the figure log, so a later loop does not undo a deliberate
  choice.
- **The author's taste overrides the panel's verdict.** A review panel recommended dark example
  tiles as less "slidey"; the author demanded white, and the override was recorded so dark
  backgrounds were never reintroduced. Flag a caveat hard, once, then do what the author
  decides and keep a backup for instant revert.
- **Keep your own independent validation.** "My own validation stands independently" of what a
  workflow concludes.
- **Fan-outs die.** Spend limits, overloads and session limits killed several mid-run. Make
  them resumable (write each agent's output to a file as it lands), retry on failure, and
  finish in the main loop when the fleet is gone. Report where intermediate outputs are.
- **Under a deadline, hand over what renders now**, then iterate.

## 3. The main-versus-supplement audit

Run it after the QA loop and after any metric change. Procedure in
`references/supplement.md`; tool: `scripts/number_parity.py`.

## 4. The fact-check

Every number on the figure, in the caption and in the text is reproduced from source. One
fact-check of a figure ran as an audit followed by an adversary (18 agents) and reproduced every
bar value and every scatter coordinate exactly.

1. List every printed number with its location (`claims.tsv`: where, key, shown).
2. Check each against the canonical table (`number_parity.py claims`).
3. Check every stated fact about the computation against the code at the commit that produced
   the numbers, not the development checkout: filters, floors, caps, subsample sizes,
   denominators per method, what the plotted quantity really is (a figure that said "% cells"
   plotted % transcripts), comparator versions, resource limits.
4. Build a per-dataset matrix of stated preprocessing and parameters, and have an adversarial
   agent check it against the code.
5. Report what is wrong before editing ("tell me first, don't edit yet"). When one fact is
   wrong, audit the whole document, not only that sentence.
6. Check that every panel showing the same method ran the same configuration. In the source,
   one panel and two others used different settings of one method, so a property visible in the
   first was invisible in the others. Rerun to one configuration, or name the difference in the
   caption beside the affected panels.
7. **One term per concept across panels, caption and text.** The last QA blocker on one
   supplement was a mechanism name in one panel's header that differed from the term used in
   another panel. List each concept's term once in the figure log, then grep the panel PDFs, the
   caption and the draft for variants. A label that names an inferred mechanism needs its
   evidence on the figure; otherwise use a mechanism-neutral term with "putative".
8. Check letters: after any re-lettering, every caption and text reference to a panel letter.
9. Record the result in TECHNICAL_NOTES ("checks run") and save any corrected fact so later
   sessions never reintroduce the error.
