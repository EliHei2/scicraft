---
name: figure-development
description: Develops a paper's results figure from its one-sentence claim to checked final panels, in a reproducible figure repository. Use it whenever someone builds, redesigns or audits a results or supplementary figure in any field, even when not named: "make the ablation figure", "the supp doesn't match the main", "pick an example for the qualitative panel", "baseline B OOMed on two datasets", "this figure is degenerate", "camera-ready is Friday". Holds the loop (message lock, additive variants, metric lock, panels, compose, render-look-fix, adversarial review, main-versus-supplement audit, fact-check, documents), the evidence standards a comparison must meet (valid reference, stated null, identical subsampling, replication units, measured values only, failure marks, equal coverage), showcase-example hunting and disclosure, null records, and a render-parity harness. Prefer data-figures for styling, canvas-schematics or tikz-figures for diagrams, stats-reporting for test choice.
---

# figure-development

How to take a results figure from a claim to panels a co-author, a reviewer and an auditor can
check. Distilled from a long run of figure work on a benchmark paper and its revision (many
figure cycles, each with a long series of notes from the lead author). Every rule below is
something that failed without it. This skill
owns process, evidence and organization; how a plot looks belongs to `data-figures`.

> **PRIME DIRECTIVE: lock the figure's one-sentence claim first, then let it be carried only by
> numbers that were measured on the full data, under one protocol for every method, and that
> read the same everywhere they appear.**

Three failures cost the most time. Guard against them from the first hour:

1. **Panels before the message.** Figures built panel by panel were called "awful" and
   "degenerate" and rebuilt from scratch. Write the sentence, then derive the panels (section 1).
2. **An unfair comparison found after it was printed.** A "method X misses signal Y" label came
   from each method getting a different random subsample; a clean class separation came from a
   gate applied to one class only; an off-the-shelf reference was blind to the very category it
   scored. Each was retracted. Check the comparison before drawing it (section 3).
3. **The same number, two values.** A supplement read one value and the main figure another; a
   caption kept a retracted number; a re-lettered figure kept stale letters in its caption. "This
   inconsistency is not acceptable." Audit before sharing (section 7).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The claim**: the draft paragraph or the author's own sentence for this figure; the parent
  panel or reviewer question if it is a supplement.
- **The reference figures**: the figures the author accepted as the gold standard. Open them
  before building anything; a first pass that ignored them drew "this is so bad".
- **The canonical runs**: one run per method and dataset, with code commit and any non-default
  setting. Never guess a run; ask "which version is this?"
- **The master table** that every figure reads, and the one implementation of each metric.
- **The figure log** if one exists, including dead ends and locked decisions. Do not re-propose
  what is recorded as dead.
- **The venue**: column widths (89 mm and 183 mm in the source), page limits, the deadline.

Set up or adopt the repository contract (section 9). For a new figure, copy the templates;
where the repository already has a CLAUDE.md, PANEL_MAP.md or PROVENANCE.md, merge into it
instead of copying over it (`cp -n` refuses to overwrite):

```bash
cp -n <skill>/assets/repo/CLAUDE.md <skill>/assets/repo/PANEL_MAP.md <skill>/assets/repo/PROVENANCE.md <repo>/
mkdir -p <repo>/figures/figure_N && cp -n <skill>/assets/figure_docs/*.md <repo>/figures/figure_N/
cp -n <skill>/assets/FIGURE_LOG.md <skill>/assets/repo/FINAL_CHECK.md <repo>/figures/figure_N/
```

## 1. Lock the message

- **One sentence, written and dated before any panel**, at the top of `NARRATIVE.md` and the
  figure log. Include the mechanism when there is one. Name each panel's role in an arc
  (establish, mechanism, quantification, consequence). A panel with no role moves to the
  supplement or is dropped.
- **The figure's documents add to the project's and never relax them.** A figure-level
  `NARRATIVE.md` or guardrail file narrows the project's `NARRATIVE.md` and `GUARDRAILS.md`
  (defined in the sibling skill, `project-structure/references/governing-documents.md`); where
  they disagree, the project's `GUARDRAILS.md` wins.
- **Schematics never replace evidence in a main figure.** A main figure needs one real-data
  example and one quantified panel at least; a pipeline diagram goes to the supplement unless it
  is Figure 1.
- **Every quantitative panel separates the arms.** If every method scores about the same, the
  number goes into a caption sentence and the script stays as its source.
- **Introduce a category where the story reveals it**: the motivating panel shows the problem
  state, not the fix.
- **When the claim moves, re-derive the panel list**; when the author calls the figure
  "degenerate", start again from the sentence.

`references/loop.md` has the arc patterns, the claim-to-panel table for machine-learning
figures and the pacing to expect.

## 2. Build variants beside the original

- **Additive.** A redesign is `figure_N_exp` (then `exp2`, `exp3`) with its own composer, panel
  scripts and geometry file, beside the untouched original. The author picks; losers move to
  `archived/`, still runnable. Risky exploration happens outside the repository and graduates
  only when it works.
- **Reproduce the reference before polishing it.** Rerun the script that made it; never
  re-implement it from the picture. Polish changes layout, names and units, never a metric
  definition, filter, ranking or direction.
- **New options are default-off parameters** that leave every other panel byte-identical,
  proved with the render-parity harness (section 9).

## 3. Lock the metric and check the comparison

Lock each metric's definition against the benchmark's own code (file and line), with a date. A
metric that changed five times "made the author anxious"; the lock reads "do not re-tune without
the author". Offer gate choices as options with their costs, and choose before seeing the ranking.

Then hold every comparison to these standards (`references/evidence.md` has each with its
incident and its machine-learning form):

| Standard | Rule | What happened without it |
|---|---|---|
| valid reference | the reference can see the quantity measured; never your own method; purge a dropped one everywhere | a reference that missed most of one class had "no truth to recover" |
| stated null | every effect axis has a bold, labeled null; test against the matched null, not zero | "logfc vs what???" |
| units of replication | seeds, datasets, tasks or spatial blocks are the replicates; report effect sizes when every p is tiny | millions of edges gave p below 1e-70 for everything |
| identical subsampling | the same indices for every arm, or a seed derived per arm; no verdict label without an interval | a shared generator gave each method a different subsample and a false "misses" claim |
| symmetric gates | every filter and selection applies to every arm, chosen once on a neutral set | an asymmetric gate manufactured a clean separation |
| non-circular metric | a metric the model optimizes cannot crown the model; a proxy never carries the canonical name | a purity win was the model's own objective |
| measured values only | every point is read from a named file; failures carry a `failure_kind` and a red x with the cap; lines break at failures | an interpolated placeholder, OOM kills drawn as data |
| full runs only | a run on a subset or crop is a non-run, proven from the output's extent | a run that logged "All done!" covered a crop |
| one clock | one timing source for every arm | two clocks in one line ran several times apart |
| equal coverage | every method gets the same number of marks; an unrecoverable cell drops that dataset for all | a silent blank read as the hero's hidden failure |
| controls | a positive control, a negative control, and an internal control that should not move | a claimed win whose label-shuffle floor was a large share of the gap |

Run `scripts/coverage_audit.py` on any method x dataset table before it becomes a figure. It
fails on a missing cell, a value with a failure kind, a value without a source, unequal marks
and unrecorded gaps, and writes a plot table whose `segment` column tells the renderer where
lines may join.

**Integrity.** Choosing what to lead with is presentation; changing what the records support is
misreporting. A setting that differs from the default is reported where the result is. A
threshold applies to every result alike. A weak or mixed result goes to the supplement with its
number. Requests to leave things out get the honest form in `references/evidence.md` (section
14): flag the risk once, offer neutral wording, keep the record.

## 4. Choose and build panels

- **One script per panel**, at its exact printed size in mm, reading one small table, asserting
  what the caption will claim about the rows it draws, writing a pdf + png pair. Copy
  `assets/panel_template.py`. "NEVER plot multiple panels together."
- **Mock up first.** Write the geometry file (`assets/geometry.example.json`) and run:

```bash
python <skill>/scripts/mockup_layout.py figures/figure_N/geometry.json --out figures/figure_N/_mockup_layout
```

  It draws every box with its size and letter and fails on boxes off the canvas, overlaps and
  rows of mixed height. Each box's size is the figure size its panel script uses.
- **Lead with the panel that shows the claim to the eye, then quantify on the whole dataset.**
- **Add a "so what" panel** where it exists: the downstream decision the difference flips.

For a machine-learning paper the usual mapping:

| Claim | Panel |
|---|---|
| ranks first across tasks | rank per task, methods sorted by mean rank, a dot per task and a mean marker |
| each component matters | drop-one ablation, median over seeds with the interquartile range, a dashed line at the full model |
| scales | runtime or memory against size on one clock, failures as red x, lines broken at failures |
| wins a trade-off | the method's own sweep as a curve, competitors as points, the native default marked |
| better per task | paired difference forest against each baseline with bootstrap intervals; ties drawn as ties |

## 5. Showcase examples

An example is chosen, so it is a claim about the choice (`references/examples.md`):

- **Quantification is global; the example illustrates.** No per-example number when one window
  is unrepresentative.
- **Pick by a scripted, stated criterion** with a hard gate (for example: the hero shows at
  least [k] real events and no failures, the competitor at least [m] failures), render the top 7 to
  15 candidates, let independent judges score the images, record the winner, the runner-up and
  the trade-off, and back up the previous choice for instant revert.
- **The example contains the phenomenon for the hero too**, and a competitor's zero is checked
  against a different failure mode.
- **Mark your own method's failures with the same rule.** Include every item the rule selects.
- **Disclose**: "illustrative, selected for [criterion]; local value [v] against dataset value
  [V]". ML form: the median-loss example per bucket, or a seeded draw.

## 6. Compose, render, look, fix

- **The composer places panel PDFs at native size and draws only the panel letters.** Captions
  live in `caption.md`, never on the canvas. Never stretch a panel at assembly.
- **Open the composed PNG every time**, then crops at high dpi. Measure text boxes for collisions
  after any label change. `references/review.md` (section 1) has the list.
- **Notes come in bursts.** Write each into the figure log in the author's words, apply them in
  order, re-render, trace each one against the render. Sizes change by the factor named (1.2x,
  0.8x, "a tad" is about 1.1x), on exactly the elements named.
- **A surprising number is a suspected bug.** Re-derive it by an independent path before showing
  it. When numbers move between versions, show a settings diff.

## 7. Review, audit, fact-check

In this order, after the logic is right (`references/review.md`):

1. **Adversarial QA.** Several lenses (aesthetic dimensions, logic, fact-check) review the
   render, rank fixes as blocker, major, minor; apply every blocker; re-render; a final verifier
   looks for regressions. At least three rounds when the author asks for a loop. Critics re-run
   code. Record KEEP AS IS guards. The author's taste overrides the panel's verdict.
2. **Main-versus-supplement audit.** At the supplement's default operating point every value
   equals the main figure; every sensitivity panel carries a dashed default line at the
   main-figure value; the full-model row of an ablation equals the main table
   (`references/supplement.md`).
3. **Fact-check.** Every printed number traced to its table row, every stated computation
   traced to the code at the commit that produced the numbers, every panel letter in the caption
   checked after any re-lettering.

```bash
python <skill>/scripts/number_parity.py claims --canonical data/master.tsv --claims figures/figure_N/claims.tsv
python <skill>/scripts/number_parity.py diff data/figure_N/supp_defaults.tsv data/figure_N/main.tsv --key method,dataset --sig 10
```

## 8. Supplements, nulls and dead ends

- **A supplement explains the mechanism behind one main claim or answers one reviewer question.
  It never re-shows the main result**, and it extends the parent's metric family, granularity
  and look instead of replacing them (`references/supplement.md`).
- **A null is recorded, not dropped.** One line in the figure log for a small one ("DEAD END (do
  not retry): what, why"); a folder with a design written before the result and
  `assets/NEGATIVE_RESULT.md` for an analysis line. Every record ends with "do not retry unless".
  Search the records before proposing an analysis (`references/negative-results.md`).
- **Words match the evidence**: "illustrative", "attenuates", "putative", "disfavored", never a
  stronger word than the test supports.

## 9. The figure repository

`references/repository.md` has the contract. In short:

- `code/figure_N/` holds one thin script per panel and one composer; `_prep/` holds aggregation
  and geometry; `data/figure_N/` holds the small tables; raw outputs stay outside and only
  `_prep/` reads them.
- **`PANEL_MAP.md`**: one table for all panels (letter, claim role, aesthetic anchor, upstream
  source, script, output, status, Synced), with generation commands and retired forms.
- **`PROVENANCE.md`**: one row per copied or built input, the canonical runs table, the traps.
  Updated in the same edit as the copy.
- **Four documents per figure**: `caption.md`, `NARRATIVE.md`, `METHODS.md`, `TECHNICAL_NOTES.md`.
- **Deferred doc sync**: panel rows carry `Synced = -` until a sweep folds their lessons into the
  guideline files on "update docs". What waits is only the sweep of reusable lessons into the
  guideline files; the four documents update in the same edit. `scripts/docs_status.py` lists
  what is owed.
- **Every edit ships PNG and PDF in place**; the live-text SVG too once a submission SVG exists; back up old outputs first.
- **A label in a figure with no source** (a raster inside the manuscript) is repainted with
  `scripts/repaint_label.py`, which fails if any pixel outside the label boxes changed.
- **Refactors run under the render-parity harness**:

```bash
python <skill>/scripts/parity/render_all.py --repo . --units units.json --baseline
# refactor
python <skill>/scripts/parity/render_all.py --repo . --units units.json
python <skill>/scripts/parity/compare.py --snap _verify_snap --intended INTENDED_CHANGES.tsv
```

  Each output is identical, identical modulo encoding (perceptual difference below 0.004),
  changed as intended (listed with a reason), or regressed (exit 1). Registry format in
  `assets/units.example.json`; intended-changes format in `assets/repo/INTENDED_CHANGES.tsv`.

## Scripts

| Script | Does | Needs |
|---|---|---|
| `scripts/coverage_audit.py` | method x dataset coverage, failure kinds, equal marks, gaps to fetch, plot table with line segments | standard library |
| `scripts/number_parity.py` | printed numbers against the canonical table; row-wise diff of two tables at N significant digits | standard library |
| `scripts/mockup_layout.py` | layout mockup from the geometry file, with overflow, overlap and patchwork checks | matplotlib |
| `scripts/docs_status.py` | missing paths in PANEL_MAP, unnamed scripts, data without provenance, owed syncs (Suggested, not yet tested in real work) | standard library |
| `scripts/parity/render_all.py` | renders every registered unit in subprocesses and snapshots outputs | numpy, Pillow, PyMuPDF |
| `scripts/parity/compare.py` | classifies current outputs against the baseline, writes triptychs | numpy, Pillow |
| `scripts/parity/sig.py` | signatures used by the two above | numpy, Pillow, PyMuPDF |
| `scripts/repaint_label.py` | repaints a label in a source-less raster figure; fails on colored pixels in a box or any change outside the boxes; `--self-test` | numpy, Pillow |
| `assets/panel_template.py` | a panel script at true size with caption invariants asserted | matplotlib, numpy |

All run on Python 3.9 or later and answer `--help`. Install PyMuPDF with `pip install pymupdf`.

## 10. Check before anything is handed over

1. `coverage_audit.py` on every comparison table: passes, or each gap is on a fetch list in the
   report.
2. `number_parity.py claims` on every printed number, and `diff` between supplement defaults and
   the main table: zero mismatches.
3. `render_all.py` and `compare.py` if shared code changed: zero regressions.
4. `mockup_layout.py` on the final geometry; `docs_status.py`: no missing paths;
   `figures/figure_N/FINAL_CHECK.md` ticked with the date and commit.
5. **Look** at the composed PNG and at crops: clipped or overlapping text, a missing legend
   entry, internal names, a missing-value glyph, the example's frame containing what the caption
   says.
6. **Read the caption against the panels**: every letter, number, n, interval type, filter,
   selection disclosure and non-default setting.
7. **Trace every note** in the figure log against the render.
8. **Say what was not checked**: numbers that could not be traced, runs not verified as full,
   claims resting on a reference whose validity was not tested, the SVG if not regenerated.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a figure of schematics with the evidence cut | "current fig 6 is degenerate" | real examples plus quantification; the diagram in the supplement |
| a reference blind to the category scored | "it's important not to take it as ground truth" | a reference that can see the category, or each arm against its own null |
| a fold-change heatmap with no baseline | "logfc vs what???" | percentage of the random expectation, bold 100% null line |
| a verdict printed from point estimates | (a published claim found false) | all data, block bootstrap, an effect with its interval |
| silent subsampling for statistics | "do not subsample [the data] man!!" | full data; subsample for display only |
| an interpolated value shown as measured | "figure = measured values only" | a gap on a fetch list |
| hollow rings and new strips for missing values | "don't make it weird" | the established layout, gaps reported in text |
| a silent blank for one method | "each method should have 8 points" | a point or a red x in every cell |
| a supplement that repeated the main figure | "shows nothing, it's the main figure" | one mechanism or one reviewer question per supplement |
| a new metric family in a supplement | "I don't wanna introduce a new metric" | the parent's metric, extended |
| a supplement value that differed from the main | "this inconsistency is not acceptable" | one implementation, a dashed default line, a diff before sharing |
| a cherry-picked example | "if it is cherry picked then we can drop it" | a scripted hunt, judges, "illustrative" and the local against global value |
| a re-implemented reference plot | "copy-paste exactly as is" | the original script rerun, then minimal edits |
| re-typed labels in a new figure | recorded as "do not regress" | upstream labels reused from the canonical run |
| caption paragraphs on the canvas | "this is not a slide, it's a paper figure" | letters only; every detail in `caption.md` |
| a dead end proposed again | "don't re-propose it" | a record with "do not retry unless" |

## Reference files

- `references/loop.md`: each step of the loop in detail, the claim-to-panel table, pacing,
  working with the author, close-out.
- `references/evidence.md`: the evidence standards with incidents and machine-learning forms,
  requests to leave things out, the claim-audit workflow.
- `references/examples.md`: the showcase hunt, its gates, judging and disclosure.
- `references/supplement.md`: what a supplement is for and the main-versus-supplement audit.
- `references/negative-results.md`: honest negatives, null records, do-not-retry, vocabulary.
- `references/review.md`: looking at the render, adversarial QA shapes, the fact-check.
- `references/repository.md`: layout, panel scripts, geometry and composer, provenance, panel
  map, the four documents, deferred doc sync, outputs, the parity harness, source data.
