# Print math: px to mm to pt

A schematic is read on paper at the size the journal prints it. Every size in the figure is
chosen for that printed size, and the canvas is laid out so the arithmetic is trivial.

## The contract

| Quantity | Value | Why |
|---|---|---|
| layout scale | 10 logical px = 1 mm | font px map straight to pt; 1830 px is a 183 mm double column |
| 1 pt | 25.4 / 72 mm = 0.35278 mm = 3.528 px | |
| device scale `S` | 3 | the PNG gets 30 px per mm, about 760 dpi |
| widths in evidence | 183 mm double column (1830 px), 89 mm single column (890 px) | Nature sizes; for another venue read `\the\textwidth` from its template and use that |
| PDF page | exactly W/10 x H/10 mm | Chrome rounds to its own unit, so expect up to 0.1 mm more |

## Text tiers

Three tiers plus the panel letter, from the cross-skill figure law (7, 6 and 5 pt with a 5 pt floor).

| Tier | pt | px at 10 px/mm | `FONT` key | Holds |
|---|---|---|---|---|
| panel letter | 8 (one size per paper, up to 10.5) | 29 | `LETTER` | bold lowercase, no period, drawn by the master only |
| L1 | 7 | 25 | `L1` | panel titles, all panels one size |
| L2 | 6 | 21 | `L2` | block and group labels, math |
| L3 | 5 | 18 | `L3`, `FLOOR` | annotations, legends, ticks, subscripts |

- **Nothing goes under 18 px.** The two source libraries said "L3 = 17.6 px (5 pt)" in a comment and
  used 17 px (4.8 pt) in the code, and the letter at 28 px was 7.9 pt. The shipped library uses 18 and
  29, and `LIB.math` keeps subscripts at the floor (`LIB.subSize`), so set math at L2 or L1.
- **One panel letter size per paper**, the same in data, schematic and TikZ figures: 8 pt by default
  (29 px is the nearest px above it). A venue's own letter size wins; a paper may choose up to
  10.5 pt (37 px) once for all its figures. The sibling skill `data-figures` owns this rule
  (`data-figures/references/style-tokens.md`).
- **A subtitle is a lighter weight of a tier** (`FONT.light`), never a fourth size.
- **If text does not fit, give the panel more area or shorten the text.** The rule that came out of
  about 40 small tweaks to one figure: titles of a set share one size; shorten the text, do not shrink
  it. A label that clips is shortened before any font is touched.
- **Glyph coverage**: Helvetica Neue lacks the arrows and Greek letters on some systems. Draw arrows as
  paths, write Greek as a word or set it in the math face, and look at the render.

## Another canvas width

When a canvas is not at 10 px/mm (an inherited template, a website figure), compute the floor:

```
px per mm = W_px / P_mm
min px    = pt x 0.35278 x W_px / P_mm
```

```bash
python3 scripts/print_maths.py --width-px 3200 --width-mm 180 --px 18 75
```

On a 3200 px canvas printed at 180 mm, 1 px is 0.05625 mm and the 5 pt floor is 32 px. Text set at
18 px there printed at 2.9 pt and was called "terrible, tiny text". The repair at the time raised
every font to 75 px (12 pt); that 12 pt rule is obsolete and the 5 pt floor replaces it. Before
resizing an inherited figure, write a table of every element class with its old and new size
(fonts, line widths, dot radii, gaps) and change them together.

## Line weights and marks at 10 px/mm

Measured from the two source libraries; keep them unless the house figures differ.

| Mark | Value |
|---|---|
| block border | 1.6 px, `PAL.line` `#3a3f47`, radius 3 |
| forward arrow | 2.0 px, head 3.4 x lw |
| soft flow arrow between stages | `PAL.flow` `#999` (`#bbb` was too faint in print) |
| EMA arrow | 1.6 px, dash [6, 5], head 7 |
| leader line | 1.0 px, `PAL.leader` `#9aa0a6` |
| cell outline / white halo | 2.4 px / 8 to 9 px |
| molecule dot | radius 3.0 everywhere, white halo 1.3 px |
| mask | dash [8, 6], 2.5 px; error mask `PAL.err`, dash [5, 4], 2.2 to 2.4 px |

## Placing the PDF

Include the PDF at its natural size (`\includegraphics{figure.pdf}`). Scaling it to `\textwidth`
scales every font by textwidth / (W/10 mm). If the figure must be another width, change `CANVAS.W`
and relayout; two panels scaled independently came out with "different font sizes / different heights".

## Resolution

The PDF holds the canvas as a raster at device scale (30 px per mm at `S = 3`), so it is sharp in
print but its text is not live. When a venue or a co-author needs editable text or a true vector
file, draw the figure with the `tikz-figures` skill instead.
