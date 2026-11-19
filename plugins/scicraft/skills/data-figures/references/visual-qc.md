# Visual QC

"Plausible isn't correct. A clean, tidy figure is the failure that survives review." Run the scripted gates first,
then look, then let someone else look.

## Scripted gates

```bash
python3 scripts/check_panel.py figures/fig2/panels/*.pdf --figure figures/fig2/fig2.pdf --figure-width 183 --ban banned.txt
pdffonts figures/fig2/fig2.pdf          # every font: emb yes, type TrueType or CID TrueType
```

`check_panel.py` fails a PDF on: for files given with `--figure`, a page size other than `--figure-width` and
`--figure-height` (panels keep their own sizes); a Type 3 font (set `pdf.fonttype 42`);
an unembedded font; a DejaVu fallback (register the house font, or `--allow-dejavu` when a math symbol needs it);
text under 5 pt; more than 4 text sizes besides the letter size (4 warns); gray text; text off the page; overlapping
horizontal text; a banned word. It lists colored text as warnings, to be confirmed as hero labels.

It cannot see a label lying on a dot or a whisker, overlaps of rotated text, meaning, or color roles.

For a plotted value, assert in the panel script (ranks are permutations, n is equal across methods, an interval
excludes zero where the label says so) and diff captions against the master table.

## The look list

Open the composed PNG, then render crops of every dense region at 900 to 1200 dpi:

```bash
python3 -c "import fitz; p=fitz.open('fig.pdf')[0]; mm=72/25.4; \
p.get_pixmap(dpi=1200, clip=fitz.Rect(80*mm, 0, 139*mm, 44*mm)).save('zoom.png')"
```

Check, in this order:

1. Nothing clipped: tick labels, axis labels, method names, color-bar labels, letters, the top of a bar or whisker.
2. No label on a dot, whisker or line; leaders short and thin.
3. Direction arrows point the right way on the page: "higher is better" points up, also inside a rotated y label.
4. Grid: row heights equal, plot areas aligned, titles centered or left-aligned consistently, letters one size and
   close to their panels but not on content.
5. Text: three sizes, all black, nothing below 5 pt in print, no prose, no internal names.
6. Legends outside the plots, every color keyed, legend order equal to mark order.
7. Color: method colors unchanged from the other figures, red used for one meaning, rank and color direction
   matching the metric direction, no metadata palette colliding with method colors.
8. Encoding: bars from zero, spread named, compared methods equal in weight, failures marked, gaps empty.
9. Space: no dead margins, no crammed legends, dense matrices readable at print size.
10. Side by side with the reference figures at the same scale.
11. Inspect crops after assembly, not only the standalone panel: the composer can change what is visible.

## When a figure must be right: the review loop

The author specifies it as maker, then a harsh reviewer acting as a journal editor, then maker again, for at least
3 rounds (5 rounds for "prettifying + logic + fact check"):

- Get the logic right first (data, metric, claim), then run the aesthetic rounds. Do all requested adjustments
  before clean-up and review.
- One reviewer per lens, each reading the composed PNG: layout and white space, typography tiers, clipping, science
  against the caption, color, redundancy. A synthesis step removes duplicates and settles disputes against the
  data. Reviewers that only see one tile will not catch "the whole thing reads like a slide": the orchestrator
  checks the figure as a whole.
- For soundness, pre-write each check as a script and let a cheap agent run it and return PASS, CAVEAT or FAIL with
  the numbers. This downgraded a headline p value to an honest relative claim in about 10 minutes.
- Gate: hand over only what you can argue is better than the reference figure.
- Write the review down: checked by script, found and fixed, kept and flagged, results against the narrative shown.
  A written review once caught single- and two-seed composites mixed, bars that disagreed with the caption's
  estimator, and a caption broader than its evidence.

The sibling skills `qc` and `adversarial-audit` hold the general review machinery.

## Proportions by judged sweep

For a geometry choice (cell size against height, panel aspect), render N variants into separate folders, let a
reviewer read each PNG and score ratio, snugness, clipping and compactness, and let a judge pick. It beat serial
guessing.

## Render parity for refactors

Before moving panels onto shared code, snapshot every output; after, classify each one:

- per output: sha256, a 96 by 96 grayscale grid of the PDF rasterized at 110 dpi, and the PDF page size;
- classes: identical, identical apart from encoding (mean absolute difference below 0.004), changed as intended
  (listed with a one-line reason in an intended-changes file), regressed (exit 1);
- each unit rendered in its own subprocess so rcParams state cannot leak between panels;
- always a full render before comparing (a filtered run silently skipped a composer);
- baseline, current and difference written side by side for a look.

It caught a commit that had deleted a module still imported by two panels. The harness ships in the sibling `figure-development` skill (`scripts/parity/`);
the sibling `paper-code-parity` covers number parity.

## Before saying "done"

Say what was not checked: rotated-label overlaps, color-blind safety of any color outside the shipped palette,
how the SVG behaves in the co-author's editor, and any number not traced to the master table.
