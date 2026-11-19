# Figure gate

For a data figure, a schematic or a composed multi-panel figure, before it is shown to anyone. How to make the
figure is in `data-figures`, `canvas-schematics`, `tikz-figures` and `figure-development`; this is the check. The
author QCs figures personally, so send the PNG or the changed pages, never only a description.

## Scripted

- **Render at final size**, PDF and PNG; read the PNG. For a figure that sits in a paper, the design width sets the
  printed type size (a 396 bp text width with the figure at 0.98 linewidth).
- **Measure every text box** after any change to label text: matplotlib `get_window_extent` on each text artist,
  pairwise overlaps, the figure bounds, the minimum gap in mm. One such check reported "no collisions and nothing
  clipped, 7.3 mm and 8.6 mm gaps to the neighboring titles"; another caught a heat-map title running into rank
  headers, a second title line hitting a tick label and a y label at the page edge.

```python
import matplotlib.text

def text_problems(fig):
    """Clipped and colliding text in a matplotlib figure. Tick labels outside the axis limits are never drawn, so
    they are left out (counting them gave false 'clipped' reports)."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    ticks, drawn = set(), []
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            for t in axis.get_major_ticks() + axis.get_minor_ticks():
                ticks.update({id(t.label1), id(t.label2)})
                if lo <= t.get_loc() <= hi:
                    drawn += [lab for lab in (t.label1, t.label2) if lab.get_visible()]
    drawn += [t for t in fig.findobj(matplotlib.text.Text) if id(t) not in ticks and t.get_visible()]
    boxes = [(t.get_text(), t.get_window_extent(r)) for t in drawn if t.get_text().strip()]
    W, H, out = fig.bbox.width, fig.bbox.height, []
    for i, (a, A) in enumerate(boxes):
        if A.x0 < 0 or A.y0 < 0 or A.x1 > W or A.y1 > H:
            out.append(f'clipped: {a}')
        out += [f'overlap: {a} | {b}' for b, B in boxes[i + 1:] if A.overlaps(B)]
    return out
```

Call it at the end of the panel script and fail the build when it returns anything. Tested on a clean 5 x 4 in
plot (no problems) and on a 2 x 1.5 in plot with a long title and two touching labels (all caught).

- **Smallest type at print size**: at least 5 pt. Rasters capped by height printed 97 to 120 mm wide on a 150 mm
  measure gave 2.2 to 4.4 pt text; the fix was composition only (width to the measure), never re-plotting.
- **Row labels on their rows**: `va="center_baseline"`; `va="center"` put row labels 0.14 to 0.18 mm above their
  rows.
- **Fonts embedded**: `pdffonts fig.pdf` shows "yes" in the emb column for every font. A matplotlib PDF that only
  names Helvetica needs it embedded before submission.
- **No number changed by a relabel**: when only labels were meant to change, prove it. Compare the `pdftotext`
  number tokens of old and new, the vector marks (PyMuPDF `page.get_drawings()`), and a registered pixel diff that
  is non-zero only inside the label boxes ("18,490 pixels changed, all inside the four label boxes"). List any
  token removed on purpose.
- **Refactor of figure code**: a render-parity harness (shipped in the sibling `figure-development` skill,
  `scripts/parity/`) takes a sha256 and a small grayscale grid of each output before, then classes each output as
  identical, identical up to encoding, changed as intended with a reason, or regressed. It catches what eyes miss.
  Number parity between paper and code is a different check (the sibling `paper-code-parity` skill).
- **Banned words absent** from the extracted text of the figure (the old name of a renamed component, coined
  labels, a statistic the paper does not use).

## With eyes

- No clipped tick, axis, method or color-bar labels; no stretching or letterboxing.
- Panel letters visible but not dominant; panel bottoms level; no appendix figure a quarter empty; no lone tile in
  a grid.
- Dense matrices readable at final size; every row block labeled ("the rows have no annotation, is it the
  intervention?").
- The names used in the manuscript, the same name for the same thing in every panel; explicit compact units.
- Rank and color direction match the metric direction; one glyph for a missing value; no labels on top of dots.
- If a color means something, a key says what; the same entity has the same color in every panel.
- Significance marked by an asterisk after the value, drawn as its own text so the number stays centered, and
  the caption says so.
- The caption describes what the figure draws now (a caption still describing a ±0.2 band after the plot moved to
  a different fit was caught by a checker). Every line style, marker and color in the figure is named in the
  caption.
- Panel titles of two to four words in standard vocabulary ("Elo rating", "Change in score by transformation");
  "ranking checks" and similar coined titles were rejected.
- Look at crops of the assembled figure, not only the standalone panel; zoom into labels by rendering crops at
  high dpi.

## Hand over

- PNG and PDF in place, plus a live-text SVG regenerated with every edit once a submission set exists (PyMuPDF
  `text_as_path=False`), because a stale SVG is what the journal receives. Before the first submission set the SVG
  may wait until the layout holds (owner: the sibling `figure-development` skill, `references/repository.md`).
- The previous outputs backed up first; variants under new names (see `handover.md`).
- Report the page size in mm, fonts and sizes used, and every number printed in the figure if it was asked for.
