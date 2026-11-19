# Style tokens

Every number the house style uses, with where it came from. `assets/figstyle.py` implements all of them; change a
token there, never in a panel script.

## Page widths

| Venue | Width | Constant |
|---|---|---|
| Nature, single column | 89 mm | `WIDTH_MM["nature-single"]` |
| Nature, double column | 183 mm | `WIDTH_MM["nature-double"]` |
| ICLR and NeurIPS text width (5.5 in) | 139.7 mm | `iclr-text`, `neurips-text` |
| ICML column and text (3.25 in, 6.75 in) | 82.5 mm, 171.5 mm | `icml-column`, `icml-text` |
| A4 with 2.2 cm margins (6.5 in) | 165.1 mm | `a4-text` |

The ICML values are the venue's published column widths; they were not used in the source work. Check the current
style file of any venue before the first panel.

## Text

| Role | Size at print | Weight |
|---|---|---|
| panel letter | 8 pt by default; one size per paper across data, schematic and TikZ figures; a venue that specifies another size wins, and a paper may choose up to 10.5 pt once for all its figures | bold lowercase, no period |
| title | 7 pt | regular |
| axis label, category label | 6 pt | light |
| tick, annotation, legend, in-cell value | 5 pt | light |
| floor for any text | 5 pt | |
| in-cell heatmap value in a very dense matrix | down to 3.3 pt, never lower | |

- Scale the tiers together (`S.apply(scale=1.1)`; one figure ran at 7.7/6.6/5.72 pt). A ratio change (titles twice
  the cell text) means changing the tier values, never multiplying literals in a script: literals such as `1.1*` and
  `+0.5` multiplied into a mess and overflowed narrow panels in a figure that took about 40 tweaks.
- Count tiers in the composed figure, not in the script settings. `check_panel.py` counts them.
- All text in print figures is `#000000`. Spines and ticks `#111111`. A hero label may take the hero color; a white
  label sits on a dark heatmap cell. No other colored or gray text. A dark gray such as `#222222` stays only for web
  and slide text where the sibling `design-system` skill says so per medium; an older paper module used it for
  print, and the newer modules replaced it with pure black.
- Color carries the identity of whatever the figure compares. When methods are compared, metric names and y labels
  stay ink. When metrics are the compared items (a report that defends one metric against another), the defended
  metric family takes the hero color, the rival family the rival color, the rest gray, and the y label takes its
  family color.

## Fonts

| Host document | `S.apply(font=...)` | Stack |
|---|---|---|
| sans default, Nature, most ML venues with a sans figure style | `helvetica` | Helvetica Neue, Helvetica, Arial, Liberation Sans, Nimbus Sans, DejaVu Sans |
| default LaTeX, figure text matching `\sffamily` | `cm-sans` | cmss10 (ships with matplotlib) |
| default LaTeX, figure text matching the serif body | `cm-serif` | cmr10 |
| a Palatino-like serif body | `serif` | TeX Gyre Pagella, Palatino, Palatino Linotype, Book Antiqua, DejaVu Serif |

- The env var `FIGSTYLE_FONT` sets the default for every panel of a project.
- macOS: the module registers `/System/Library/Fonts/HelveticaNeue.ttc`. matplotlib reads only the first face of a
  collection, so bold is extracted once with fontTools into `~/.cache/figstyle/HelveticaNeue-Bold.ttf`
  (`S.bold_font(size)`). The same limitation means a `light` weight request renders the first face of the
  collection; check the rendered weight once on your machine.
- Linux or a cluster: Helvetica Neue is absent; the stack falls to Arial, Liberation Sans or Nimbus Sans. Install
  one of them, or the PDF will name DejaVu Sans and `check_panel.py` fails it.
- Computer Modern: no U+2212 minus (the module turns on mathtext for tick labels), the micro sign prints as a grave
  accent (write `$\mu$m`), and there is no bold cmss face (bold labels render regular; pass the composer a bold font
  file of the host with `--letter-font`).
- Mathtext follows the body face (`mathtext.fontset custom`). Sans math is about 70% of why a figure reads as a
  modern ML paper rather than default LaTeX.
- In a LaTeX-typeset table panel beside Helvetica Neue panels, use xelatex with `fontspec` and
  `\setmainfont{Helvetica Neue}`, not `helvet` (a Nimbus clone that looks foreign); the setup is in the sibling `design-system` skill, `references/tokens-by-medium.md` (LaTeX row).

## Lines and marks

| Element | Value |
|---|---|
| spine, compact panels | 0.5 pt, `#111111` |
| tick, compact panels | width 0.4 pt, length 1.8 pt, outward, pad 1.4 pt |
| spine and tick, large panels | 0.9 pt; width 0.9 pt, length 3.4 pt |
| data line | 0.8 pt default; heavier (1.0 pt) only for a series that is not a compared method |
| guide line, heatmap grid | 0.3 to 0.4 pt, `#D1D1D6` (light gray, not white, so a white cell still reads as a cell) |
| faint bar y-grid (optional) | 0.38 pt, `#E6E8EB` |
| zero line | 0.35 to 0.4 pt, `#111111` |
| reference line from the hero bar | 0.6 to 0.9 pt, dash (2.4, 1.8), `#9AA1AA` |
| trade-off diagonal | 0.5 pt, dash (2, 1.6), alpha 0.25 |
| error bar | 0.5 pt, cap 1.3 pt (bars, `#111111`) or 1.0 pt (scatter, `#9AA1AA`) |
| leader line | 0.3 pt, `#9AA1AA`, alpha 0.75 |
| label halo | white stroke 1.6 pt |
| scatter marker | one size for every compared method (`s=16` in the template); white edge 0.4 pt |
| bar width | about a third of the slot or less (0.34 in `method_bars`) |

## Color roles

| Role | Hex | Use |
|---|---|---|
| `HERO` | `#0072B2` | the method the paper is about |
| `HERO_ALT` | `#0A3D66` | a second read-out of the hero; diamond marker |
| `HERO_PRIOR` | `#8DBEDD` | an earlier version of the hero; open marker |
| `RIVAL` | `#E69F00` | the strongest comparator |
| `OTHER` | `#A8A8AD` | every other comparator ("context, never a competitor colour") |
| `BASELINE` | `#6E6E73` | untrained twin, random or trivial baseline |
| `CLAIM`, `AGAINST`, `NOCLAIM` | `#0072B2`, `#D55E00`, `#C7C7CC` | ablation marks: claim holds (filled), finding against (filled), no claim (open) |
| `FAIL` | `#D6321E` | the one saturated red: a run that did not complete |
| `BAND` | `#EFEFF1` | seed-to-seed noise band; also an n/a cell |
| `MISSING_FACE`, `MISSING_EDGE`, hatch | `#DDDDDD`, `#888888`, `//` | missing heatmap cells; one missing-value glyph per figure |
| `UNLABELLED` | `#9A9AA0` | unlabeled items, distinct from the ground color |

- `OKABE_ITO`: `#0072B2 #E69F00 #009E73 #CC79A7 #56B4E9 #D55E00 #F0E442 #000000` for further compared series.
- Grouping metadata (datasets, platforms, batches) uses a cool pastel family (`METADATA_PASTEL`) on icons, brackets
  and labels only. A sweep ramp was once moved from amber to lemon because an amber ramp read as the rival's color
  at tile size: check every new palette against the method colors.
- Red means one thing per figure. In the source figures it meant removed, failed or forbidden; a category that
  clashed with it was recolored.
- Use method colors only where method identity is the encoding (lines, markers, legends), never on heatmap row
  labels.
- Valence (expected or unexpected effect) is shown with pale background bands, never with green and red bars.
- **Keep the category colors of a paper in one file**: a dict from canonical label to hex, an alias map that
  resolves every spelling in the data to a canonical label, and one lookup that every panel and supplement calls.
  The lookup returns a neutral `#666666` for an unknown label, so a typo shows on the render instead of borrowing a
  hue; unlabeled items take `UNLABELLED`. A shared lookup was introduced so that one label's color "is identical
  everywhere" across a main figure and its supplements.
  `assets/figstyle.py` ships the empty tables `CATEGORY` and `ALIASES` and the lookup `category_color()`: fill the
  tables once per paper.
- **Tint an icon or glyph by flooding its silhouette with the color at alpha 1.0.** Lowering alpha by luminance
  (`alpha *= 1 - k * luminance`) washed the icons out.

## Ramps

| Name | Stops | Use |
|---|---|---|
| `RANK5` | `#F1F6FF #C7DCFF #8FB9FF #4D97FF #003FBD` | rank heatmaps, discrete steps, best darkest |
| `MUTED5` | `#E8F0F7 #CFDEEB #A6BFD7 #7099BD #4A7CA8` | a calmer single-hue alternative |
| `DIVERGING` | `#0A84FF` (0), `#7DB9FF` (.30), `#D6E8FF` (.43), white (.50), `#FFD9D6` (.57), `#FF8C84` (.70), `#FF3B30` (1) | signed values with a wide white plateau; values printed |
| `DELTA` | `#2166AC #F7F7F7 #D55E00` | the alternative: a schematic matrix drawn without values, or a figure where red already means something else; blue to orange is near iso-luminant and reads flat with values printed |
| `SWEEP_BLUE` | `#C7DCEC` to `#1B4773`, six steps | an ordered parameter sweep |
| `SWEEP_LEMON` | `#F7EDA8` to `#8C7800` | a second sweep family |

- Signed values use `DIVERGING` by default ("red blue apple palette, with median at white"), values printed. Never red
  and green.
- Use `TwoSlopeNorm(vmin=data min, vcenter=meaningful baseline, vmax=data max)` with `DIVERGING`: the full ramp is
  used and white still means "no change". `vmin=0` when no cell reaches 0 wastes the dark end.
- Re-pick the white-text threshold after any change of map or norm (`S.text_color_for(c, threshold=...)`; 0.45 for
  the red end after the plateau was widened).
- Color bars sit outside the matrix and their ends are labeled with words (`best`/`worst`, or the two directions
  in their own end colors).

## Output

| Item | Value |
|---|---|
| panel PNG | 600 dpi |
| composed PNG | 600 dpi (320 dpi was used for one large figure) |
| PDF page | exactly the figure size: `bbox_inches=None`, `pad_inches=0` |
| ground | transparent (`savefig.transparent True`, `figure.facecolor "none"`), which prints as white; never dark in print; axes face white only inside heatmaps |
| fonts | `pdf.fonttype 42`, `ps.fonttype 42` |
| SVG | `svg.fonttype "none"` for panels; composed figures through `compose.py` (PyMuPDF with live text) |
| number format | `S.num(.642)` gives `.642`; true minus U+2212; `sign=True` adds `+` |
