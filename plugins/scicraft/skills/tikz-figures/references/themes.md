# Themes, fonts and the palette

One preamble (`assets/preamble.tex`) serves every figure. Two switches at its top set the
look; every color and style keeps the same name in both themes, so a body written once
compiles in either.

**Contents**
1. The two switches
2. Choosing the theme and the font
3. Palette by role, both themes
4. Rules for using color
5. Line weights and text sizes
6. Renamed tokens (from the two older skills)
7. Adding a theme

---

## 1. The two switches

```latex
\providecommand*{\figtheme}{minimal}   % minimal | serif
\providecommand*{\figfamily}{auto}     % auto | sans | serif | cm
```

Edit the two lines in the copied preamble, or set them per build without editing:

```bash
pdflatex "\def\figtheme{serif}\input{fig.tex}"
pdflatex "\def\figfamily{cm}\input{fig.tex}"
python3 scripts/render_figure.py fig.tex --theme serif     # same, plus the checks
```

| `\figfamily` | Loads | `\figfont` (used by every style) | Use when |
|---|---|---|---|
| `auto` | the theme's own | as below | the default |
| `sans` | `helvet` + `sansmath` + `\sfdefault` | `\sffamily\sansmath` | the minimal theme; any sans-bodied host |
| `serif` | `mathpazo` (Palatino text and math) | `\rmfamily` | the serif theme; a Palatino host (book, report) |
| `cm` | `lmodern` (Computer Modern shapes, vector) | `\rmfamily` | a venue paper whose body math is Computer Modern |

Every style in the preamble sets `font=\figfont...`, so a snippet never names a family. In
a snippet that needs its own font size write `font=\figfont\figL`, never `\sffamily`.

**The bug this fixes.** The older serif-default preamble loaded `mathpazo` without
`sansmath`, while its `base` style still said `font=\sffamily\sansmath`. Every `[base]`
figure then died with `Undefined control sequence \tikz@textfont ->\sffamily \sansmath`.
The font command is now defined by the switch, so it always exists.

**Known limit of sans math.** `sansmath` sets Latin letters and digits in sans, but
lowercase Greek still comes from Computer Modern italic (`pdffonts` shows `CMMI`). This is
expected; it is how the minimal-theme figures have always looked. Uppercase Greek is a
different matter: `sansmath` takes it from the T1 Helvetica clone, which has none, so
`$\Phi$` printed as a black box with no error in the log. The preamble now takes
uppercase Greek from Computer Modern sans. Look for black boxes in every PNG anyway.

## 2. Choosing the theme and the font

- **The minimal theme is the default for machine-learning figures.** Sans text and math,
  four tones, flat shapes, near-zero text. The author called their own figure in this look
  "the best I made myself" and asked for every later figure to follow it.
- **The serif theme matches a serif-bodied host.** A book or report set in Palatino, or a
  co-author's figures already drawn in this look. It keeps black structure, a blue family
  and one warm red contrast. It is defined here only by measurements: the colors of the
  serif column in section 3, operator boxes with 1.3 pt black outlines and 4.5 pt corner
  radius, a 1.6 pt black spine arrow, 0.5 pt gray field and trajectory strokes, 0.7 pt
  gray support arrows. It is modeled on the figure style of a published monograph, credited in
  `THIRD_PARTY.md`; no code from it is used.
- **Match the figure's math to the paper's math.** When a venue fixes Times text with
  Computer Modern math, set `\figfamily{cm}` so figure math and body math agree. In one
  submission the figures went from Helvetica to the TeX default font on the same day for
  this reason, and that was final. This was the author's most recent paper, so for a
  venue submission with Computer Modern math `cm` is the rule, not an option.
- **Decide once, record it, never flip back.** A font that changes between morning and
  evening costs a round of rework on every figure. Write the choice in the project's
  notes and keep every figure of the paper on it.
- **Match a figure set, not a single figure.** A new figure takes the theme of the
  paper's other figures, including figures drawn in other tools (a canvas schematic or a
  matplotlib panel in Helvetica Neue reads as sans).

## 3. Palette by role, both themes

| Token | minimal (default) | serif | Role |
|---|---|---|---|
| `ink` | `#1A1A1A` | `#000000` | text, outlines, axis spines, primary arrows |
| `slate` | `#5A5F6B` | `#5A5F6B` | secondary text, faint arrows, braces |
| `annot` | `#9AA0AB` | `#7E7E7E` | glosses, support arrows, vector fields, trajectories |
| `mist` | `#9AA0AB` | `#9AA0AB` | faint structure, gridlines, tree edges |
| `cloud` | `#E7E9EE` | `#DEDEDE` | generic block fill |
| `cloudPale` | `cloud!55!white` | `cloud!55!white` | faded back copies in a stack |
| `paper` | `#FFFFFF` | `#FFFFFF` | halos, operator fills |
| `accent` | `#2B50AA` | `#2B50AA` | the protagonist: the model, "ours", focal points, visible tokens |
| `accentL` | `#9EBEE0` | `#A7BED3` | soft fills, halos, density tint, the accent block |
| `accentMd` | `= accent` | `#6078B8` | target dots in a source/target pair |
| `accentBox` | `= ramp3` | `#9FC1E0` | the one special module in an operator pipeline |
| `navy` | `#1A254B` | `#1A254B` | deepest ink: source dots, the highlighted path, heading ink |
| `contrast` | `#B8860B` mustard gold | `#F2545B` red | the ONE contrast: held-out, target, masked, "other" |
| `contrastL` | `#E8D6A0` | `contrast!30!white` | fill of the contrast (mask tokens) |
| `mapfill` | `#C9CED6` | `#8C90A4` | tall "map" box fill |
| `truth` | `#CBCBCC` | `#CBCBCC` | observed or data layer, drawn under the prediction |
| `link` | `= accent` | `#5774BC` | an in-figure citation, the only colored text |
| `ramp0` to `ramp8` | matplotlib Blues | same | depth, time, ordinal index, density, energy |
| `c1` to `c4` | accent, contrast, slate, accentL | same names | categorical series, in this order |

Ramp stops (RGB): 247,251,255; 222,235,247; 198,219,239; 158,202,225; 107,174,214;
66,146,198; 33,113,181; 8,81,156; 8,48,107. The preamble also defines the pgfplots
colormap `ramp` from them and makes it the default colormap.

## 4. Rules for using color

- **One accent, one meaning.** `accent` is the thing the reader should care about;
  `contrast` is its one foil. Everything structural (boxes, arrows, axes, frames) is gray
  or ink. If a third saturated hue appears, delete it. Six saturated colors in one figure
  means the figure has failed.
- **The contrast keeps its meaning in every figure of the paper.** In the minimal theme
  gold means held-out, target or masked everywhere. Recolor a diverging map onto the
  blue ramp so gold is not spent on a colormap.
- **An ordinal index is a lightness ramp, never a categorical series.** Time steps,
  depths and stages take `navy!28` to `navy!100` or `ramp1` to `ramp8`. A categorical
  palette on an ordinal axis tells the reader the steps are unrelated kinds.
- **Style is the second channel.** Solid = observed, dashed = predicted, dash dot =
  extrapolated, saturation plus width = mass. At most three edge relations in one figure;
  more goes into a legend keyed by line style.
- **At most three series per axis.** More series become facets (a `groupplot` row).
- **Data points stay neutral in an architecture figure.** The model is the subject; a
  rainbow of points pulls the eye away from it.
- **Emphasis by color only where the values are printed or plotted to scale.** Making a
  baseline "look pale" is allowed only where it is pale in the numbers.
- **No gradients by default.** Radial shading (`\shade`) is allowed for one density blob
  as an exception, never on boxes. No drop shadows: depth is an offset faded copy.

## 5. Line weights and text sizes

| Element | Weight |
|---|---|
| vector-field arrows, trajectory strands | 0.5 pt gray |
| frustum (dashed zoom connector) | 0.4 pt `ink!45` dashed |
| general lines (`base`), blocks, axes | 0.6 to 0.9 pt |
| operator boxes (`opbox`) | 1.3 pt black |
| the spine arrow (`spine`) | 1.6 pt black |
| arrowheads | Stealth, about 2.2 x 1.8 mm |

Text: three tiers and a panel letter. In a figure built at its printed width,
`\figL` (7 pt) for titles and block names, `\figM` (6 pt) for labels, `\figS` (5 pt) for ticks and tags,
nothing under 5 pt after any scaling, and the bold lowercase panel letter at 8 pt (`\figLetter`). A subtitle is a
lighter weight, never a fourth size. If a label does not fit, give it more room or
shorten it; do not shrink it.

## 6. Renamed tokens (from the two older skills)

The two skills this one replaces used colliding names: `inkblue` was `#2B59C3` in one and
`#1A254B` in the other, and `cbRed` was red in one and an alias of gold in the other. The
chip style `token` (a labeled box taking a fill) collided with the token cell `token` (a
small square in a sequence). Old figures port with this table:

| Old | New |
|---|---|
| `inkblue` (protagonist blue) | `accent` |
| `inkblue` (deepest navy, minimal skill), `cbNavy`, `cbTraj` | `navy` |
| `inkblueL`, `bblue`, `cbBlueLt`, `tealL` | `accentL` |
| `bblueD`, `cbBlue` | `accent` |
| `cbBlueMd` | `accentMd` |
| `bmustardD`, `cbRed`, `cbPink`, `coral`, `otred`, `amber` | `contrast` |
| `bmustard`, `coralL`, `otsalmon` | `contrastL` |
| `cbInk` | `ink` |
| `cbAnnot` | `annot` |
| `cbTruth`, `truegrey` | `truth` |
| `cbFillGrey` / `cbFillGreyPale` | `cloud` / `cloudPale` |
| `cbCombBlue` / `cbSlate` | `accentBox` / `mapfill` |
| `cbLink` | `link` |
| `cbBl0` to `cbBl8` | `ramp0` to `ramp8` |
| `teal`, `violet` (third and fourth categories) | `accentL`, `slate` |
| style `token` with a fill argument | `chip` |
| `cbbox`, `cbboxaccent`, `cbboxmap`, `\cbstack`, `cbfront` | `opbox`, `opbox accent`, `opbox map`, `\opstack`, `opfront` |
| `cbflow`, `cbtransport` / `cbagg` / `cbfield` | `spine` / `agg` / `field` |
| `cbtraj` / `cbtrajhi` / `cbnote` / `cbpanel` / `cbeq` | `traj` / `trajhi` / `note` / `panel` / `eq` |
| taxonomic pastels `tf*` with the `taxon` style | removed (see SKILL.md, section 11) |

## 7. Adding a theme

A theme is one more branch in the palette block: define every token of section 3 under a
new `\ifx\fig@theme...` test, and nothing else. Do not add style definitions per theme;
the styles read the tokens. Compile the test body of section 1 of `workflow_qa.md` in
every theme before using it, and look at both PNGs side by side.
