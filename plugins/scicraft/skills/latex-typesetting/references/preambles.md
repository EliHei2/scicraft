# Preambles: three profiles, fonts, microtype, color, macros, shims

Read this when you start a document, restyle one, or a build breaks on a missing package.

## Contents

1. Choosing the profile
2. Profile A: venue style untouched plus a house add-on
3. Profile B: free-form book or report
4. Profile C: journal supplement
5. Fonts and math
6. Microtype, hyphenation, emergency stretch
7. One accent color
8. Macros for names, units and operators
9. Cross-references
10. Floats
11. Callout boxes
12. A minimal or foreign TeX install
13. Copying a reference document's look

## 1. Choosing the profile

| The document | Profile | Asset |
|---|---|---|
| Conference or journal paper whose venue ships a `.sty` or `.cls` (NeurIPS, ICML, ICLR, a society journal) | A | `assets/venue/` |
| Book, monograph, long technical report, anything with no imposed class | B | `assets/book/` |
| Online Methods, Supplementary Notes and Tables where the journal imposes no class | C | `assets/supplement/` |
| Preprint or arXiv version with free typography | B's font choices on `article`, or the venue look kept so the preprint matches the submission | |

Every profile expects `assets/shims.tex` beside it. `assets/revision.tex` (revision marking) and
`assets/print_colors.tex` (print copy) work with all three.

## 2. Profile A: venue style untouched plus a house add-on

- **Never edit the venue's style file and never override what it owns.** It owns geometry, type
  sizes, section heads, title block, abstract, running head, citation style. No `geometry`, no
  `\small` on the body, no switch that turns off its geometry. A self-review of an ML submission
  rated such hacks as reject-level, and two submitted papers kept the stock style.
- **Put everything else in one file, `housestyle.tex`, loaded right after the venue style.** It
  owns: the accent color and hyperref colors, a monospace that fits beside Times, microtype,
  float fractions and `flafter`, caption form, display-math rhythm, table helpers, callouts,
  theorem environments when the venue defines none, cleveref.
- **The measured exemplar.** A well-regarded ICLR paper the author studied used the stock style;
  everything that looked distinctive came from four hand-defined box environments. Distinction
  comes from the content blocks, never from the page frame.
- Main-file order (from `assets/venue/main.tex`):

```latex
\documentclass{article}
\usepackage{[venue]_conference,times}   % the venue's own line, unchanged
\input{housestyle}
```

- Inside `housestyle.tex`, `\@ifpackageloaded{hyperref}` decides whether to load hyperref or
  only set its colors, because some venue styles load it themselves.
- Main-text-only tightening for a page limit (`\tightenmaindisplays` after `\maketitle`,
  `\restoremaindisplays` before the appendix) lives in the add-on; see `page-budget.md`.

## 3. Profile B: free-form book or report

From a book rebuilt in the classic manner of Bringhurst's book design, from common packages and without a
style package (none was on the machine):

- `book` 11 pt, A4, `twoside,openright`. Measure 150 mm, text height 232 mm, inner and top
  margins 31 mm, `headheight` 13 pt, `headsep` 10 mm, `footskip` 13 mm.
- **No sidenote column.** An earlier layout with a 45 mm margin column put the front matter 21 mm
  off center, `\newgeometry` broke the margin-note package (about 78 float errors), and a fixed
  minipage killed `\vfill`. Widening the measure from 118 to 150 mm also let journal figures print
  at 83 % of their 180 mm width instead of 70 %.
- Palatino text and math with real small caps and old-style figures: `\usepackage[sc,osf]{mathpazo}`
  and `\linespread{1.06}`; monospace `\usepackage[scaled=0.86]{inconsolata}`.
- Chapter: Euler bold numeral at 66 pt in navy `1C2449`, flush right; title in letterspaced
  capitals (`\textls[160]`) at text size over a 0.5 pt rule. Section: letterspaced lowercase small
  caps. Subsection: italic. Paragraph: run-in small caps. **No level is set heavier than the one
  above it**; check `\paragraph` titles for math or macros before setting them in small caps.
- Running heads in letterspaced lowercase small caps, page number at the outer edge, no rule.
  `\runninghead{Short}` before a long `\section` sets a short head; a heading "Role: subject"
  runs as its role alone. Both exist because running heads wrapped to two lines.
- Captions small, bold label, bold claim sentence (see `tables-captions.md`); tables captioned on
  top with 6 pt skip, figures 7 pt.
- One link color `3A5BA6` for citations, references and URLs. A citation-dense book may use
  the darker shade for citations: "fifteen [citations] in its first paragraph, so the bright blue
  on every one of them reads as a wall".
- Boxes are drawn with TikZ around a savebox (a newer tcolorbox wanted a newer kernel). Keep only
  the boxes that earned a place: a "Contributions" bracket per research chapter and short numbered
  context boxes (`\begin{infobox}{box:x}{Title}`), which cannot break across pages. Section
  conclusion boxes were added and later removed for one prose Conclusions section.
- Bibliography: `natbib` `[round,authoryear,sort&compress]`, `\bibsep` 2.4 pt, small ragged-right
  font, DOIs printed as `https://doi.org/...` links.
- Front matter: `\frontchapter{Summary}` gives an unnumbered chapter that appears in the contents
  and sets running heads. Add the lists to the contents with `\phantomsection\addcontentsline`.
- `\crefalias{chapter}{appendix}` after `\appendix` so appendices print "Appendix A".
- **Number from 1 and give the appendices their own line in the contents.** The author asked
  "don't start section names from 0": in `book` or `report`, a `\section` before the first
  `\chapter` prints as 0.1, so open every numbered part with a chapter (or use `article`). A
  later round added an appendix heading to the contents so a reader finds the appendices from the
  contents page: `\cleardoublepage\phantomsection\addcontentsline{toc}{chapter}{Appendices}`
  right after `\appendix` (in `assets/book/main.tex`), or the class's own appendix-pages option.
  Check both on the rendered contents page after each build.

## 4. Profile C: journal supplement

From a Nature-family supplement where no class was imposed (`assets/supplement/main.tex`):

- `article` 10 pt, `geometry` margin 0.85 in, line spread 1.0, Computer Modern (matched math by
  default) through `lmodern`.
- Tight heads: section `1.6ex plus 0.4ex minus 0.2ex` above, `0.9ex` below; subsection
  `1.1ex plus 0.3ex minus 0.1ex` and `0.5ex`. Displays 4 pt (short 2 pt), set `\AtBeginDocument`.
- Numbered citations in order of appearance: `natbib` `[numbers,sort&compress]` with `unsrtnat`.
- `longtable` for parameter tables (`\LTpre`, `\LTpost` 0.7 em), `pdflscape` for wide ones,
  `\arraystretch` 1.14, list margins 1.45 em, links `blue!45!black`.
- `microtype` with `[expansion=false]`.
- Defaults stated once in one sentence, with `\label` at the end of the defining sentence so any
  section can point at the one definition, and a pointer to the defaults table.

## 5. Fonts and math

- **Body math must match body text.** A text-only serif over Computer Modern math looks
  unchosen. Matched choices: `mathpazo` (Palatino text and math), `newtxtext` with `newtxmath`,
  `libertinus`, Latin Modern.
- **When a venue forces Times text with CM math, keep it, and set the figures to match the
  paper.** One project's house file first chose Libertinus for matched math, then went back to
  `times` because the papers it followed were set that way and CM math is what the TikZ figures
  already embedded. Figure fonts flipped from Helvetica to the TeX default on the same day; once
  settled, write the rule down and never reintroduce the other.
- Beside Times, replace Courier: `\usepackage[scaled=0.95]{zi4}` (Inconsolata on the Times
  x-height). Courier is "far too wide beside Times".
- Posters with XeLaTeX keep paper math: `unicode-math[mathrm=sym]` and
  `\setmathfont{latinmodern-math.otf}[Scale=MatchLowercase]`. Never Helvetica letters in math.
- **Portability.** A basic TeX Live may lack Palatino (`pplr8t`) and Helvetica (`phvr8t`)
  metrics; a full or recommended install has them through `collection-fontsrecommended`. Probe
  with `kpsewhich pplr8t.tfm phvr8t.tfm` before choosing. To preview on a machine without the
  fonts, substitute Latin Modern in a throwaway copy:

```bash
sed -e 's|^\\usepackage.*{mathpazo}.*|\\usepackage{lmodern}|' -e '/helvet/d' main.tex > __preview.tex
pdflatex -interaction=nonstopmode __preview.tex && bibtex __preview; pdflatex __preview.tex; pdflatex __preview.tex
rm -f __preview.*    # after copying the PDF out
```

- `\usepackage[T1]{fontenc}` without a scalable font loads bitmap EC fonts on a basic install,
  and microtype then stops with "auto expansion is only possible with scalable fonts". Load
  `lmodern` (or the venue's font) whenever T1 is on.
- Every font in the final PDF is embedded; see `build-and-gates.md`.

## 6. Microtype, hyphenation, emergency stretch

- **Always load `microtype`.** Protrusion and expansion give even justification. Settings in use:
  book `[protrusion=true,expansion=true,final]`; venue paper `[final,tracking=false]`; supplement
  `[expansion=false]`.
- `\setlength{\emergencystretch}{1.5em}` (1.2 em in one house file) removes most overfull lines
  without visible loose ones.
- `\lefthyphenmin=2 \righthyphenmin=3` in the venue paper.
- `\babelhyphenation[english]{...}` for proper names and tokens the patterns break badly. Only
  letters and hyphens are allowed inside; a placeholder in brackets stops the build with
  "Not a letter".

## 7. One accent color

- **One accent for links, citations and box rules; everything else ink and grays.** "Restraint is
  the look; a second accent or a colour box breaks it." Used accents: muted green `26735B` with
  box fill `F2F8F5` and rule `BFD8CD`, ink `202020`, soft gray `616161` (venue paper); teal
  `228B8B` with fill `F0F8F8`; navy `1C2449` with link blue `3A5BA6` and box tint `F2F4F9`
  (book); indigo `3A3A8C` (preprint template).
- `\hypersetup{colorlinks=true,citecolor=accent,linkcolor=accent,urlcolor=accent}`.
- A box is a pale tint of the same hue with a 1.6 to 2 pt left rule, frame hidden, square corners.
- Keep a print copy one file away: `assets/print_colors.tex` maps the accent to black and box
  tints to 95 % gray, figures keep color (`build-and-gates.md`, section 6).

## 8. Macros for names, units and operators

- **Every method, model, dataset and recurring unit is a macro; never type the name raw.** A
  retired name then changes in one place. One book had to purge three retired names by hand, and
  a figure came within one `\includegraphics` of shipping one.
- `\newcommand{\method}{\textsc{MethodName}}`.
- Units: `\newcommand{\um}{\ensuremath{\,\mu\mathrm{m}}\xspace}`, or without xspace write `\um{}`
  before a following word. A final visual pass found "10 µmof the cell centroid" five times.
- Operators that appear in prose as well as math are wrapped in `\ensuremath`, because a bare
  `\GNN{}` in a sentence raises "Missing $ inserted":

```latex
\DeclareMathOperator{\GNNOP}{GNN}
\newcommand{\GNN}{\ensuremath{\GNNOP}}
\DeclareMathOperator*{\argmax}{arg\,max}
\providecommand{\Lpred}{\ensuremath{\mathcal L_{\rm pred}}}
```

## 9. Cross-references

- **Typed label prefixes and cleveref, so the noun can never drift from the float.** "The text
  says 'Table 1' from a bare `\Cref{tab:bench}` and can never drift from the float it points at."
- `\usepackage[capitalize,noabbrev]{cleveref}` after hyperref; `\crefname{algorithm}{Algorithm}{Algorithms}`,
  `\crefname{infobox}{Box}{Boxes}`.
- Prefixes: `ch: sec: subsec: fig: tab: eq: alg: box: app: def: prop: thm: lem:`.
- Without cleveref (some venue templates): `Fig.~\ref{}`, `Table~\ref{}`, `Appendix~\ref{}`.

## 10. Floats

- **A float never precedes its first mention:** `\usepackage{flafter}`.
- Fractions: `\topfraction` .9 to .95, `\bottomfraction` .6, `\textfraction` .03 to .08,
  `\floatpagefraction` .85, `topnumber` 3, `totalnumber` 4, `\textfloatsep 14pt plus3pt minus3pt`.
- `\FloatBarrier` before limitations or conclusions keeps a section's figures inside it (a
  visual pass found two figures floated past "Conclusions"). It can also strand floats on
  half-empty pages: one barrier left float pages 43 to 62 % full and cost pages. Check the page
  count and the rendered pages after adding one.
- `\raggedbottom` in long documents. Every figure is cited in the text.

## 11. Callout boxes

- **Few, one style, a left rule.** Jobs that earned a box: a contributions block and a
  one-sentence takeaway closing a dense section. A book built from papers keeps only the contribution box
  (see the sibling `book` skill). One book capped callouts at two per chapter and later removed the
  conclusion and take-home boxes. Take-home text in other long documents is quoted from the papers
  themselves, never generated.
- **Theorem statements may share the callout look.** A submitted venue paper set its propositions
  in a framed accent box while the source kept plain `\begin{proposition}[Title] ...
  \end{proposition}`. The add-on does this with one line in the preamble,
  `\boxtheorem{proposition}`, which wraps the amsthm environment in the same pale fill and accent
  rule as `insight`. Delete the line and the output is plain amsthm again, so a venue that dislikes
  it costs one line. Keep one box style for callouts and theorems.
- The add-on's `insight` and `keybox` are core LaTeX (savebox plus `\colorbox` plus a rule), so
  they compile where tcolorbox does not. With tcolorbox available the equivalent is
  `frame hidden, colback=pale, borderline west={1.8pt}{0pt}{accent}, sharp corners, fontupper=\small`.
- Inside boxes set ragged right and keep `\emergencystretch` to avoid overfull lines; give a TikZ
  box `trim left=0pt, trim right=\linewidth` so its bounding box does not overflow.
- A glossary box for readers from another field is fine in a venue paper read across fields.

## 12. A minimal or foreign TeX install

- **Shim missing packages in one place and never add `\usepackage` in a chapter.** The book
  install lacked biber, cleveref, a usable tcolorbox, csquotes, emptypage, multirow, collectbox and
  siunitx; each cost a session when met inside a chapter.
- `assets/shims.tex` loads each real package when present and otherwise defines a stand-in with
  the same interface: multirow (prints the text), csquotes (`\enquote`), siunitx (`\SI{5}{\micro\metre}`
  gives value, thin space, unit), placeins (`\FloatBarrier` written out), needspace (stand-in
  marked "Suggested, not yet tested in real work"), adjustbox `{max width=\linewidth}` (shrink only),
  cleveref (prefix-aware `\cref`).
- Input it **after hyperref**: it loads cleveref, which must follow hyperref.
- Probe what exists first: `kpsewhich multirow.sty siunitx.sty needspace.sty pplr8t.tfm`, and
  `tlmgr --usermode info <pkg>` for what a user-tree install would bring.
- A venue paper whose source must stay unmodified gets its shims from outside: a `texshim/`
  folder on TEXINPUTS (`build_latex.py --texinputs texshim`) holding one-line stand-ins
  (`\ProvidesPackage{capt-of}` plus `\providecommand\captionof...`), or `\RequirePackage{...}`
  injected on the command line. Delete the folder on a full install; the final build (Overleaf or
  the venue's checker) must not need it.
- Traps met: see `traps.md`, section 1.

## 13. Copying a reference document's look

- **Measure it; do not guess.** `pdfinfo` for page and text-block size, rendered pages side by
  side with your draft, accent colors sampled from pixels, epigraph placement from `pdftotext`.
  Get the source when it is public and quote its preamble ("verified from source, not inferred
  from the rendered PDF").
- Compare two or three variants (font size, measure in mm, margins) beside the reference page.
- Write in the preamble header which elements were copied, and justify each deviation in a
  comment. Prototype the preamble on one chapter before the full build.
- Institutional pages (title page, signed statements) come from the institution's own documents and
  the author's earlier title page, never from a template.
