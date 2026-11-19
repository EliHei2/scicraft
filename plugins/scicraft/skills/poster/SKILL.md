---
name: poster
description: Builds a conference poster from a paper as one XeLaTeX and TikZ page, laid out on an A0-proportioned design page and printed on A0, with scripted layout and printer gates. Use it whenever the user wants a poster, a poster version of a paper, a poster session, or an A0 or 100 x 130 cm print, or sends notes on a poster (text overlaps, too much text, make it professional, the printer rejected the file, fonts not embedded, the deadline for printing is Friday), even if they only say the poster. Holds the rules the author enforced: the paper's own figures and tables placed unchanged and its sentences cut, never paraphrased; the grid, type sizes at print size and the design-size arithmetic; what leaves the poster; header and footer conventions; checks by script for overlaps, smallest type at print, runts and hyphenated titles, own words, fonts, page size and file size; render and look. Prefer talk-slides for a talk, design-system for cross-media tokens, data-figures for making the plots themselves.
---

# poster

How to turn a paper into a conference poster that the author prints without rewriting it. Distilled from a
poster for a machine-learning venue built from a method paper, its camera-ready pass and the earlier
posters it replaced. Each rule comes from something the author asked for or threw out, so each carries its reason.
Refer to the person whose poster it is as the author; where they say otherwise, they win.

> **PRIME DIRECTIVE: the poster is the paper, selected and arranged.** Its figures are the paper's figure PDFs,
> its tables are the manuscript's table sources, its sentences are the paper's sentences shortened only by
> cutting. Your work is choosing and placing them, and proving by script that nothing overlaps, nothing prints
> too small and the file goes through the printer.

Three failures cost the most time. Guard against them from the first minute:

1. **Redrawing or rewriting.** The first attempt redrew the paper's diagrams in new TikZ and rewrote the abstract.
   The author was furious: "I have the most beautiful figures in the paper from tex, do not make new diagrams ...
   don't make new plots!", and the abstract was "super AI". Inventory first, place, cut (sections 1 and 2).
2. **Things lying over each other.** "make sure nothing is going over each other" was said before anything else
   about the layout. Every piece is chained to its neighbor and every box is logged and checked (sections 4 and 7).
3. **A file the printer rejects.** Figures made by matplotlib named Helvetica without embedding it, and figure
   PDFs carried superseded text hidden under their paint. Both pass a viewer and fail preflight or leak a retired
   name (section 7, gate 5).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The paper's source**: main TeX and appendix, the figure PDFs (a submission bundle's `figures/` or
  `source_assets/` folder), the manuscript's table sources, and the record files behind any number you will add.
- **The poster's frame**: size and orientation from the venue (A0 portrait, 841 x 1189 mm, is the default here;
  earlier posters of the same author were 100 x 130 cm), the print shop's file limits, the print deadline.
- **The byline as the author wants it on the poster**: author order, affiliations, who is marked as joint
  supervisor, the presenting author (underlined), contacts to print, and whether the host requires a logo.
- **Status**: is there a preprint or public code yet (decides the release line in the footer), and what is still
  unpublished and must not be shown.
- **The author's favorite figure**: the part they name as their favorite keeps its size when space runs short.

Work in a folder of its own beside the paper. Copy `assets/poster/` there and the scripts into its `tools/`:

```
poster_<venue>/
├── poster_design.tex   the design page (from assets/poster/poster_design.tex)
├── poster_A0.tex       places it on the A0 sheet: poster.pdf is what is printed
├── Makefile            make, make check, make words, make preview
├── no_photos.tex       the vector no-photos sign, built by make into the poster folder
├── figures/            the paper's figure PDFs, unchanged or cropped (record which)
├── tables/             the manuscript's table sources, unchanged
├── tools/              copies of scripts/*.py
└── departures.txt      poster sentences that depart from the paper on purpose, one per line
```

## 1. Inventory the paper and map the slots

- **List every figure PDF and table source of the paper first, then give each poster slot one of them.** The
  memory note written after the first failure says: inventory the bundle, map each slot to an existing figure,
  "and only lay out + size them".
- **Allowed changes to a figure: size, crop to the claim-bearing panels, recolor.** Nothing else. Crop with
  `\includegraphics[trim=l b r t, clip]` (non-destructive, in bp) and never cut a label: a crop that cut gene
  names off a panel was sent back ("you cut the gene names!"). Keep panels that share a label in one crop.
- **Tables go in through `\input`, unchanged.** The template's `\resultstable` wrapper turns off `table`,
  `\caption` and `\label`, so the manuscript's file is used as it is. The one edit made in real work: the
  comparator's citation number after its name, so readers find it in the poster's reference list.
- **Write the provenance block at the top of the poster source**: every asset, where it came from, and every
  departure. The template has the block; keep it current.

The ML case (a benchmark paper): the architecture figure and the training-objective figure take the method band,
the results table goes in unchanged with its rank shading, a scaling or ablation figure takes the result band.
A biology case: the overview figure, the paper's showcase figure across scales, the appendix gallery of samples.
Slot sizes and the figure-map log are in `references/content.md`.

## 2. Words

**Every sentence on the poster is the paper's own, shortened only by cutting.** "use our text copy and paste";
"your meisterwork is to select which sentences and copy paste". A paraphrase, two sentences merged, or an added
connective reads as machine-made to the author however good it is.

- **Very little text**: a short verbatim abstract, one or two key sentences per section, captions cut from the
  paper's captions. The poster is mostly figures.
- **Simple section names**: Abstract, Architecture and training, Pretraining corpus, Evaluation, Results. Section
  titles of a figure come from the paper's bold caption claims.
- **Emphasis is bold on a key phrase inside the author's sentence.** Four or five central phrases of the abstract
  get the accent (`\hi{}`), as does the method's name in the title. Nothing else is colored text.
- **Acronyms are spelled out at first use** (a departure from the paper, recorded): a reader at a poster session
  has not read the introduction.
- **Numbers are the paper's real numbers.** "for 4 use real numbers!!"; "instead of 10^9 say Billion". Each number
  has one rounding everywhere it appears on the poster.
- **Departures are listed, never hidden.** Any sentence that is not the paper's (the table key in plain language,
  an equation restated with the figure's symbols) goes into the provenance block and into `departures.txt`, which
  `own_words_poster.py` lists instead of failing.
- **Before you drop a line as "not the author's", search the paper and the author's messages for it.** In the talk
  made from the same paper, three of the author's own statements were removed as website copy and the author had to ask
  for them again.

`references/content.md` has the procedure, the matching rule of the own-words check and examples of cuts.

## 3. What leaves the poster

| Leaves | Why |
|---|---|
| new diagrams, new plots, redrawn figures | "do not make new diagrams, if anything just change color" |
| the model recipe (hyperparameters, exact loss weights, curriculum) | "keep the secret sauce"; the poster shows the idea, the data and the result |
| the paper's introduction, related work, most of the method text | the poster is mostly figures; one or two sentences per section |
| a comparator line under the table | citations sit inside the table after the method names |
| QR code and repository link while nothing is public | the footer's release line says what comes |
| a figure's text hidden under paint, a crop's hidden headers | outlined or cropped away, then checked by script (section 7) |
| unpublished results of other projects, anything still under embargo | ask (section 0) |

What never leaves: **a row, a task or a column of the results table.** The table goes in as the paper prints it,
weak entries included, with a key that says what the shading and bold mean. Choosing which figures to show is
presentation; removing what the paper reports from a table it reports is not. A visual claim in a caption ("the
structure is shared across samples") stays only if the paper measures it; otherwise the caption is neutral.

## 4. Layout

The page is designed larger than it prints, on A0 proportions, and placed on the sheet as a vector:

- **Design page 1000 x 1414.2 mm, printed on 841 x 1189 mm, so printed size = design size x 0.841.** The design
  file sets every size; `poster_A0.tex` places it with `\includepdf`, nothing rasterized. For another sheet,
  keep the 1000 mm design width, set the height to the sheet's aspect and the factor to sheet width / 1000.
- **Margins 3 cm at the sides, 2 cm top, 1.25 cm bottom; 94 cm of usable width.** Two equal columns are
  45.85 cm with a 2.3 cm gutter. Wider bands split 55.5 + 36.5 (abstract beside the key idea), 66 + 24 (a result
  figure beside its text column, 2 cm apart) or 31 + 61 (data beside the results table, 5 cm apart).
- **Type on the design page and at print:**

| Role | Design pt (size/leading) | Printed pt | Face |
|---|---|---|---|
| title | 88/98 | 74 | Helvetica Neue Bold, accent on the method's name and the coined term |
| authors | 35/42 | 29.4 | Light, presenting author underlined |
| affiliations | 23/29 | 19.3 | Light, slate |
| section title | 46/54 | 38.7 | Medium, rule below |
| abstract | 33/42.5 | 27.8 | Light, justified |
| body | 27/35 | 22.7 | Light, justified |
| caption | 25/31 | 21.0 | Light, slate |
| brace labels in math | 22/26 | 18.5 | slate |
| big numbers | 72 | 60.6 | Helvetica Neue Thin, accent |
| contacts | 22/26 | 18.5 | slate |
| references | 18/22.5 | 15.1 | slate |
| floor, checked by script | | 14 | `layout_check.py --scale 0.841 --minpt 14` |

- **One typeface, one accent, two inks.** Helvetica Neue (Light text, Medium headings, Bold title, Thin numbers);
  ink `#1A1A1A`, slate `#4A4F5A` for captions, affiliations and references; one accent (`#2B50AA` by default; set the
  host's or the paper's color) for the title word, key phrases, big numbers and the one boxed definition.
  Figures keep the paper's colors.
- **Chrome is black rules on white**: a 0.2 cm ink rule under the header and over the footer, a 0.09 cm rule
  under each section title. No boxes, cards, shadows or colored bars ("black for top and bottom like the
  [earlier] one", which replaced the orange bars of an older poster).
- **Text is fully justified** ("same length every line, like in docs") with `\hyphenpenalty=1000
  \exhyphenpenalty=1000 \emergencystretch=2em`; 5000 left loose lines and one-word last lines.
- **Math is set as in the paper**: Latin Modern Math through `unicode-math` (`mathrm=sym`,
  `Scale=MatchLowercase`), never Helvetica letters in math ("proper math typesetting"). One boxed core
  definition at most (2.2 pt accent rule, accent at 7 % fill).
- **No white holes beside figures, and the bottom columns end level.** Tune strip widths and table spacing until
  both hold; this is checked by eye (section 7).

`references/layout.md` has the TikZ chaining grammar, every spacing value, the table settings and the traps.

## 5. Header and footer

- **Header**: title in two lines broken by hand so no line holds one word; authors with superscript affiliation
  numbers, the presenting author underlined; joint supervisors marked with a dagger and the line "These authors
  jointly supervised this work."; affiliations in one paragraph, each in an `\mbox` so none breaks across lines.
  A host logo goes top right (21 cm wide on the design page) only when the host asks for one.
- **References**: a run-on paragraph above the footer rule, 18 pt design, "References" in bold ink, then
  `[n] First author et al., short name, Venue Year` in the order of first citation, inline citations `[n]` in
  slate. Datasets get a "Data:" group with the same form. Every outside picture or dataset shown has a license
  that allows the use; check it before placing it and keep the record.
- **Contacts**: one line under the references at 22 pt design: email, social handle, lab names with their
  addresses, spread with `\hfill`.
- **Bottom right**: a vector no-photos sign 2.4 cm high (`no_photos.tex`, ISO 7010 P029 layout, process red
  `#E30613` ring 1.5 mm, ink camera 1.1 mm) over a bold release line ("Preprint and code coming soon").
- **No QR code and no repository link** on the poster this came from. When the preprint is public, a link may
  replace the release line (Suggested, not yet tested in real work).

`references/footer.md` has the exact settings and the order of the pieces.

## 6. Build

Needs XeLaTeX with `fontspec`, `unicode-math`, `pdfpages`, TikZ and Latin Modern Math (TeX Live basic has them),
Helvetica Neue installed (macOS has it; elsewhere the template falls back to TeX Gyre Heros or Latin Modern Sans),
pdflatex for the sign, poppler (`pdfinfo`, `pdftotext`, `pdftoppm`, `pdffonts`), Python 3.9+ with numpy and
Pillow; PyMuPDF and the URW fonts of TeX Live for `embed_base14.py`.

```bash
cp -R <skill>/assets/poster poster_<venue> && mkdir -p poster_<venue>/tools && cp <skill>/scripts/*.py poster_<venue>/tools/
cd poster_<venue>
make                       # two xelatex passes of the design page, then poster.pdf on the A0 sheet
make check FIGS=logo,sph,f1,f2,fa,g1,g2,t6,t9 FORBID="old method name,working title"
make words PAPER=../paper/tex
make preview               # build/preview.png at 30 dpi
```

Missing figure files show as gray boxes labeled with their path, so the layout can be built before the figures
are copied. A new node needs its name in the `\foreach` list at the end of the source, or box_check never sees it.

| Script | Does |
|---|---|
| `scripts/box_check.py` | the logged boxes: overlaps, pairs closer than `--gap` cm, pieces outside the margins |
| `scripts/layout_check.py` | word boxes: text over text, type under `--minpt` at print, page size; figure labels listed apart |
| `scripts/line_breaks.py` | one-word last lines and hyphenated titles; `--dump` prints every last line |
| `scripts/own_words_poster.py` | is every poster sentence found in the paper's source, cut but not rewritten |
| `scripts/pdf_gate.py` | the print file: one page, size in mm, every font embedded, file size, forbidden strings in the text layer |
| `scripts/embed_base14.py` | embeds the Helvetica a matplotlib PDF names but does not embed, glyph positions unchanged |

## 7. Check before anything is sent

In this order (`references/checks.md` has commands, what each gate caught and the look list):

1. **Build log**: no `!` errors, no undefined references, both passes run. XeLaTeX exiting 0 proves nothing.
2. **`box_check.py --gap 0.2`**: zero overlaps, zero crowded pairs, nothing in the margins.
3. **`layout_check.py --scale 0.841 --minpt 14`** on the design PDF with the figure boxes named: zero findings in
   the poster's own text. Labels inside the paper's figures are listed apart; on the poster this came from they
   printed at 11 to 13 pt, and the camera-ready file kept them as the paper's own. Say so in the report.
4. **`line_breaks.py`**: no one-word last line, no hyphenated title; read the `--dump` once.
5. **`pdf_gate.py`** on `poster.pdf`: one page, 841 x 1189 mm, every font embedded, under the print shop's size
   limit, none of the retired names or superseded numbers in the text layer.
6. **`own_words_poster.py`**: every sentence found in the paper or listed in `departures.txt`.
7. **Render and look** at the whole page and at each band zoomed: white holes, columns that end level, labels cut
   by a crop, a marker or color a caption does not name, a figure that makes no point. A script cannot see these.
8. **Numbers**: each number on the poster traced to the paper's primary table or record, one rounding each;
   totals summed from the per-item numbers, never taken from a summary sentence.

When there is time, one independent reader checks the rendered poster against the paper. Readers report defects
with their place on the page; for a wording defect they quote the paper's sentence that should replace it or write
"needs the author's line", and never propose new prose. Once the author has approved the look and the order, the
reader brief names them as fixed. One writer applies the fixes. Errors that such an audit finds in the
paper itself go back to the paper as an errata list.

## 8. Deliver and iterate

- Deliver `poster.pdf` (the A0 file) and a PNG preview, with the gate line: "0 overlaps, 0 findings under 14 pt
  in poster text, 0 runts, every font embedded, 31.3 MB, 841 x 1189 mm" (numbers of the run at hand).
- Report what was checked and what was not (figure labels under 14 pt, anything only looked at), every departure
  from the paper's wording, and what the author must supply (byline, logo, release line).
- On notes: polish inside the approved look, never rebuild ("just try to polish the edges"). Keep each delivered
  version under its own name so a figure or a band can be brought back.
- Record each settled decision (a font, a size, a color) where the next session will read it, and do not bring a
  rejected choice back.

## 9. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| paper figures redrawn in new TikZ | "do not make new diagrams ... don't make new plots!" | the paper's figure PDFs, placed and cropped |
| a rewritten abstract | "super AI" | the paper's abstract sentences, cut |
| pieces placed by hand that touched | "make sure nothing is going over each other" | TikZ chains and `box_check.py` |
| ragged text | "same length every line, like in docs" | full justification, hyphen penalty 1000 |
| hyphen penalty 5000 | (loose lines, one-word last lines) | 1000 with emergency stretch |
| Helvetica letters in formulas | "proper math typesetting" | Latin Modern Math scaled to the x-height |
| colored header and footer bars | "black for top and bottom like the [earlier] one" | 0.2 cm black rules on white |
| a raster no-photos sign | "higher quality, more minimal, still effective" | a vector TikZ sign, 24 mm |
| matplotlib figures naming Helvetica unembedded | (printer preflight) | `embed_base14.py`, `pdffonts` gate |
| figure PDFs with superseded strings under their paint | (hidden text can be copied out) | text outlined or cropped, text-layer scan |
| powers of ten | "instead of 10^9 say Billion" | 0.0 B with the unit word below |
| long sections | "main messages only" | one or two sentences per section |

## Reference files

- `references/content.md`: the inventory and figure map, the own-words procedure and departures, numbers and claims, what leaves.
- `references/layout.md`: design-size arithmetic, the grid with every coordinate, type and spacing, math, tables, the TikZ grammar and its traps.
- `references/footer.md`: header and footer conventions, references, contacts, the sign and the release line, licenses.
- `references/checks.md`: each gate with its command and what it caught on a real poster, render and look, readers, printer and file size, the report.
