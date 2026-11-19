# Layout: arithmetic, grid, type, grammar, traps

## 1. Design size and print size

The poster is drawn on a design page and scaled once, as a vector, onto the sheet:

    printed size = design size x (sheet width / design width)

| Sheet | Design page | Factor | Notes |
|---|---|---|---|
| A0 portrait, 841 x 1189 mm | 1000 x 1414.2 mm | 0.841 | the poster this came from |
| 100 x 130 cm | 1000 x 1300 mm | 1.0 | the author's earlier posters were designed at this size directly |
| A1 portrait, 594 x 841 mm | 1000 x 1415.8 mm | 0.594 | Suggested, not yet tested in real work |

To get a printed size, multiply; to choose a design size for a wanted print size, divide (14 pt at print on A0 is
16.6 pt design). Check sizes at print with `layout_check.py --scale <factor>` on the design PDF, or without
`--scale` on the printed file. A 1 pt type size is 0.3528 mm; 14 pt prints 4.9 mm tall per em.

The placement file is three lines of real work:

```latex
\usepackage[paperwidth=841mm, paperheight=1189mm, margin=0mm]{geometry}
\usepackage{pdfpages}
\includepdf[pages=1, width=841mm, height=1189mm, keepaspectratio]{build/poster_design.pdf}
```

`\includepdf` places the page as a form; text stays text and figures stay vector, so the printed file can be
searched and checked like the design file.

## 2. The grid (design cm, origin bottom left)

| Element | Value |
|---|---|
| margins | 3 cm left and right, 2 cm top, 1.25 cm bottom |
| usable width | 94 cm (x from 3 to 97) |
| title | top left at (3, 139.32), 72 cm wide, two lines |
| logo slot | top right corner at (97, 139.27), 21 cm wide |
| authors | 0.6 cm under the title; affiliations 0.45 cm under the authors |
| header rule | 0.55 cm under the affiliations, 94 cm x 0.2 cm, ink |
| first section title | 1.0 cm under the header rule |
| section title node | text height 1.22 cm, depth 0.30 cm; rule 0.3 cm under it, 0.09 cm thick |
| first piece of a section | 0.75 cm under the section title |
| between bands | 0.86 cm from the band's lowest piece to the next section title |
| two columns | 45.85 cm each, the second at +48.15 cm (gutter 2.3 cm) |
| caption under a figure pair | 0.6 cm under the lower figure |
| band 1 | abstract 55.5 cm; key idea from x = 60.5, 36.5 cm (figure 15.6 cm, 1.5 cm gap, equations 19.4 cm) |
| band 3 | figure 66 cm, text column 24 cm at 2 cm gap; gallery titles 1.0 cm below, figures 0.45 cm below titles |
| band 4 | left 31 cm; right from x = 36, 61 cm; section titles 1.3 cm apart vertically in the left column |
| footer | release line bottom right at (97, 1.3); sign 0.35 cm above it; contacts bottom left at (3, 1.3); references 0.4 cm above contacts; footer rule 0.55 cm above the highest footer piece |

## 3. Type

Sizes are in the table of SKILL.md section 4. Settings that go with them:

- Fonts through `fontspec`: `\setmainfont{Helvetica Neue}[UprightFont=* Light, BoldFont=* Medium, ItalicFont=*
  Light Italic, BoldItalicFont=* Medium Italic]`, `\newfontfamily\heavy{Helvetica Neue Bold}` for the title,
  `\newfontfamily\thin{Helvetica Neue Thin}` for big numbers. Never the `helvet` clone.
- Leading about 1.2 to 1.3 times the size (88/98, 46/54, 33/42.5, 27/35, 25/31).
- Body and captions justified; the title, authors and affiliations ragged right.
- `\frenchspacing`, `\emergencystretch=2em`, `\hyphenpenalty=1000`, `\exhyphenpenalty=1000` in every text block.
- Big numbers: a `tabular*` across the column with `@{\extracolsep{\fill}}`, the number at 72 pt Thin in the
  accent, its unit word 0.3 cm below in caption type.
- Bold (Medium) for a key phrase; accent plus bold (`\hi{}`) for four or five phrases of the abstract; italic
  only where the paper sets it.

## 4. Math

```latex
\usepackage{amsmath}
\usepackage[mathrm=sym]{unicode-math}
\setmathfont{latinmodern-math.otf}[Scale=MatchLowercase]
```

- `mathrm=sym` makes `\mathrm` use the math font, so subscripts such as `\mathcal L_{\mathrm{pred}}` match the
  paper. `Scale=MatchLowercase` sizes the math to the x-height of Helvetica Neue.
- Display sums and fractions in the paper's own form; restate an equation with other symbols only as a recorded
  departure.
- A labeled loss: `\underbrace{...}_{\lab{label}}` with `\lab` setting text at 22/26 pt in slate and a
  `\vphantom{fp}`, so every label shares one baseline; give each braced term a `\vphantom` of the tallest term.
- One boxed definition: `\fcolorbox{accent}{accent!7}` with `\fboxrule` 2.2 pt and `\fboxsep` 0.27 cm, a bold
  accent title over a `gather*`, one slate sentence under it.

## 5. Tables

- The manuscript's table through `\resultstable{width}`: it redefines `table` as empty and `\caption`, `\label` as
  no-ops inside a group, then `\input`s the file in a minipage of the strip's width.
- The manuscript's rank shading (`colortbl` cell colors) overhangs the table's right edge by about 0.2 cm; the
  poster this came from covered the overhang with a white fill in the margin. Check it on the render.
- The poster's own small tables: `booktabs`, 27/32 pt, `\arraystretch` 1.28, heavy rule 2 pt, light rule
  1.1 pt, `tabular*` to the strip's width.
- Comparator citations `\cite{n}` after the method names inside the table; `\cite` is redefined to print a slate
  `[n]`.
- The table key under the table states what each metric is and its direction, what the shading and bold mean and
  what the error after each value is.

## 6. The TikZ grammar

Everything is one `tikzpicture` with `remember picture, overlay` and 1 cm units, anchored at the page's lower left
corner (`\coordinate (O) at (current page.south west)`). Pieces are nodes with `anchor=north west, inner sep=0pt`,
each placed relative to the one above or beside it:

```latex
\node[sect, below=1.0cm of hdr, anchor=north west] (s1) {Abstract};
\rulebelow{s1}{55.5}
\node[piece, below=0.75cm of s1.south west, anchor=north west, text width=55.5cm] (abs) {\txt{\absfont}{ink}{...}};
\node[fit=(abs)(sph)(defs), inner sep=0pt] (b1) {};                 % the band's extent
\node[sect] (s3) at ($(b1.south west)+(0,-0.86)$) {Architecture and training};
```

Because each piece hangs from the previous one, a longer abstract pushes everything below it down instead of
running into it, and box_check then reports the collision with the footer. At the end, a `\foreach` over every
node name writes `BOX name x0 y0 x1 y1` (cm from the lower left) to the log for `box_check.py`.

Absolute placement on the page needs two passes of XeLaTeX (`remember picture`).

## 7. Traps met

| Symptom | Cause | Fix |
|---|---|---|
| word spaces too wide or too narrow in a text node | TikZ sets `\spaceskip` from the 10 pt font before the font switch inside a `text width` node | reset `\spaceskip=0pt\xspaceskip=0pt` inside every text block (the template's `\txt` does) |
| "Missing number, treated as zero" at the end of a table | a row starting with `[` after `\\` or `\midrule` is read as an optional length | brace the cell: `{[placeholder]}` |
| an affiliation broken over two lines for one word | line breaking inside a name list | `\mbox{}` around each affiliation, `\quad` between them |
| loose lines and one-word last lines in justified text | `\hyphenpenalty=5000` | 1000, plus `\emergencystretch=2em` |
| everything at the wrong place on the first build | `remember picture` needs the second pass | always two xelatex passes (the Makefile runs them) |
| a box_check run that misses a piece | the node's name is not in the `\foreach` list | add every new node name |
| a figure's label crosses a column edge | a crop that ends inside a label | change the trim, never cut labels |

## 8. Spacing by eye

- No white holes next to a figure: tune the text column's width or the strip width until the text runs to the
  figure's foot.
- The two bottom columns end level: tune table spacing and strip widths, not type sizes.
- The gallery the author named as favorite keeps its size; cut text elsewhere first.
