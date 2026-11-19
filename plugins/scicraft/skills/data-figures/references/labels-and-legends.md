# Labels, titles and legends

## Titles

- One short line naming the plotted quantity in plain words, or no title when the y label says it: "if you have
  informative y label you don't need a title." "titles are too long ... make it clear one thing and go."
- Example of a fix: "Change in score after each input transformation" became "Change in score by transformation".
- No jargon of the project in titles ("robustness", "gated" were banned: "use proper terminology that people
  understand"). Qualifiers in parentheses ("(raw)"), never after a dash.
- Per-panel statistics in the form `accuracy = .81, n = 12`: an equals sign, commas between.
- A figure-level title, when the venue wants one: at most 6 words, explanatory, never vague.
- Titles go left-aligned on the baseline of the panel letter (`S.title(fig, s)`: x 3.8 mm, 4.2 mm below the top;
  the composer's letter sits at x 0.3 mm on the same baseline). `ax.set_title` centers on an offset axes and a long
  title clipped the figure's right edge; center on the grid with `fig.text` if centering is wanted.

## Names and units

- **Only manuscript names print.** Keep one display-name dict per paper and apply it in the renderer. Banned on any
  figure: internal IDs and run names, task codes, hardware and scheduler words, AI-tool names, tool or brand names
  of the pipeline, a vendor name for data from another vendor. Grep the PDF text: `check_panel.py --ban words.txt`.
- **Name axes concretely.** "RNA density" was rejected as meaningless and became the counts of the named gene. The ML
  analog: "performance" becomes "balanced accuracy".
- **Name variants by the parameter changed, with units and rounded values**, sorted numerically, the default marked:
  "dropout 0.5", "context 4k tokens (default)".
- **Units compact and in the label**: `No. samples (M)` with ticks 50/100/200 (not `50M` on each tick), `×10³
  contacts`, `#neighbors`, "K pairs". One unit per metric across axis, subtitle and caption (a fraction
  from 0 to 1 or a percentage, never both; the latest decision wins).
- **Show counts when the reader will ask "how much"**; a "% of peak" axis read as hand-waving.
- House numbers: `.642`, true minus, `S.num(x, d, sign=True)` for signed values.

## Direct labels

Two placers, both in `figstyle.py`:

- **`S.compass_place`** for small scatters (the final choice for the main trade-off scatter): each label's nearest
  edge sits a fixed `radius_pt=4.5` from its marker, in the best of 12 directions. No leader lines. Placement order
  is hero first. Deterministic. Hard obstacles, each kept `clear_pt=0.8` pt away: every marker, every label already
  placed, the axes frame, and every rectangle passed in `obstacles` (data units). **Error bars count as obstacles**:
  pass each whisker as `(x, lo, x, hi)`; `tradeoff_scatter` does this for its x and y whiskers. If no direction is
  free, the least bad one is taken: give the panel more room (wider axes, more headroom with `pad_frac`) and look.
  In the demo, eight labeled points with whiskers needed `pad_frac=0.16` in a 44 by 23 mm axes.
- **`S.repel_labels`** for dense clouds (volcano plots): adjustText 1.x. Create texts at their points with a white
  1.6 pt halo; pass ALL highlighted points as `x=`, `y=` obstacles and each label's own point as `target_x`,
  `target_y`; `force_text=(0.5, 0.9)`, `force_static=(0.4, 0.7)`, `force_pull=(0.005, 0.005)`,
  `expand=(1.5, 1.8)`, `prevent_crossings=True`, `ensure_inside_axes=True`, `iter_lim=600`, `min_arrow_len=3`;
  leaders `arrowstyle="-"`, `#9AA1AA`, 0.3 pt, alpha 0.75, `shrinkA=1`, `shrinkB=2`. Leave about 1.2 times headroom
  above capped clusters.
- Never hand-place labels one by one and never hand-roll a force loop: "it's been 1000 times where you put the
  labels or points so weirdly, look how it's implemented and just do it!!"
- Leaders thin and short: "the pointers in volcano plots are just soooo long", "the pointers are so solid". The
  label should be neither too far nor too close: a fixed gap, the direction free.
- adjustText results depend on font metrics: the same scatter switched to Computer Modern put a label beside the
  wrong point. After a font change, look again at 2 to 3 times zoom.
- Label only the significant or extreme points of a dense cloud; list all selected items in the caption.
- A label never sits on a dot, a whisker or a line, and never covers a title.

## Legends

- **Outside the plot area, always.** "legend never inside plot!!" Below or to the right, left-aligned to the panel it
  describes, no wider than it.
- **One legend per figure for a recurring series** (`S.legend_mm(fig, entries, x_mm, y_mm, ncol)`), placed where it
  keys the most panels; a legend strip between two rows can key both. Split legends by what they explain and put
  each under its tiles, in one legend font.
- Circle markers, not squares. A mask glyph in a legend is a real irregular shape.
- Entries in the order of the marks (stacked bars top to bottom).
- Every color used appears in a key: "you have a pinkish color ... not in the legend".
- A category legend lists only the classes present in the tiles it keys. Classes below a stated share of drawn items
  are dropped (0.05% in the source), and the caption gives that threshold.
- Where a legend would crowd, color the category names in the titles instead.
- A discrete parameter gets a discrete legend; the default is starred and labeled "0.05 (default)".
- In a composer legend with uneven labels, advance x by each entry's measured width (`font.text_length`), not a
  fixed pitch.

## Glyph coverage

- Helvetica Neue lacks the arrows U+2191 and U+2193 and Greek letters: use the mathtext arrows of the style module
  (`S.ARROW_UP`, `S.ARROW_DOWN`, `S.ARROW_RIGHT`, `S.ARROW_LEFT`) and ASCII ("aSMA"), or mathtext Greek.

## Direction marks

- A direction mark says which way is better and must point that way **on the page**. A y label is rotated 90
  degrees: `S.ARROW_UP` typed into it points left on the page (found in review of the demo).
- Use `S.label_dir(ax, "median score", "up")` for a y label (it writes a right arrow, which reads as up once
  rotated) and `S.label_dir(ax, "latency (ms)", "left", axis="x")` for an x label. In a horizontal title an up
  arrow is correct as typed.
- The direction of the color ramp and of the rank must match the mark.
- Computer Modern maps the micro sign to a grave accent ("µm" printed as "`m"): write `$\mu$m`.
- Check every special glyph by rendering it after a font switch; matplotlib warns about missing glyphs in its log.
- Guard `pd.isna(x)` before formatting a table value into a label: an empty cell printed "nan".
