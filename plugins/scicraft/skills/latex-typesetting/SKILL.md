---
name: latex-typesetting
description: Typesets papers, books, revisions, supplements and reports in LaTeX and builds them to a PDF that passes a scripted gate. Use it whenever a task touches a .tex file's look, build or delivery, even when LaTeX is not named: "set up the preamble", "it won't compile", "citations show [?]", "we're half a page over", "mark the changes in blue", "fix the widows", "check the bib", "my coauthors need it in Word", "camera-ready is Friday". Holds three tested preamble profiles (venue style untouched plus a house add-on, book, journal supplement), font and math matching, shims for minimal installs, caption and table recipes, an out-of-tree build whose gate reads the log (errors, undefined refs, overfull boxes, fonts, rerun, page limit), page renders, page-budget moves in order of losslessness, bibliography checks, a one-color revision toggle, float renders, a Word copy for co-authors and a safe way to edit a heavily worked file. Prose goes to paper-writing or book, figures to figure-development, replies to rebuttal.
---

# latex-typesetting

How to set, build and hand over a LaTeX document so that the author finds nothing to fix in the
PDF. Distilled from a year of one researcher's typesetting: a book built from published papers, rebuilt in a
reference book's look, a machine-learning conference paper and its revision under a hard page
limit, a journal supplement, a poster and a reply document. Every rule came from a defect that
shipped or nearly shipped, so each comes with its reason. Refer to the person whose document it
is as the author; where they say otherwise, they win.

> **PRIME DIRECTIVE: no PDF leaves your hands until the gate has read the build log and you have
> looked at every page your change could touch.** A LaTeX run that exits 0 proves nothing.

Three failures cost the most time. Guard against them from the first minute:

1. **Trusting the exit code.** A shipped book PDF carried a body without its bibliography:
   every citation printed [?] and pdflatex exited 0. A three-pass build left 64 of 76
   contents page numbers wrong. Build out of tree and gate on the log (section 5), then render
   (section 6).
2. **Changing more than was asked, or the wrong file.** A revision was built on an older draft
   that shared 15.6 % of its sentences with the submitted paper. A three-hour restyle of a worked
   text came back as "super overwhelming ... just try to polish the edges". Prove the source,
   back up, edit in counted batches, tie every hunk to a request (sections 9 and 10).
3. **Fitting a limit by breaking the format or the record.** Overriding a venue's geometry or
   font size reads as a format violation; cutting a result with its number misreports. Use the
   moves of section 7 in their order.

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The document and its kind**: main `.tex`, chapter files, `.bib`, figures; venue and its style
  files (`.sty`, `.cls`, `.bst`), or "no imposed class"; page limit and what counts toward it.
- **The TeX install**: `pdflatex --version`, and `kpsewhich multirow.sty siunitx.sty cleveref.sty
  needspace.sty pplr8t.tfm phvr8t.tfm` for what is missing. Where the final build happens
  (this machine, Overleaf, the venue's checker).
- **For a revision**: the submitted PDF and the exact submitted source (editor history, tag,
  upload archive).
- **For a look to copy**: one to three reference PDFs (or their source) of the target genre.
- **Deadline and delivery**: upload limit (one venue took 50 MB), print copy needed, phone
  preview, who reads it.

Work on a copy or in a scratch build folder when others share the build; keep the source tree's
top level for what is delivered.

## 1. Pick the preamble profile

| The document | Profile | Copy from `assets/` |
|---|---|---|
| Paper for a venue that ships a style file (an ML conference, a society journal) | A: venue style unchanged plus `housestyle.tex` | `venue/main.tex`, `venue/housestyle.tex`, `shims.tex` |
| Book, monograph, long report, any free-form document | B: classic book design on `book`, Palatino | `book/main.tex`, `book/preamble.tex`, `shims.tex` |
| Online Methods and supplementary notes, no imposed class | C: `article` 10 pt, numbered citations | `supplement/main.tex`, `shims.tex` |

- **Profile A: never edit the venue's style file and never override what it owns** (geometry,
  type sizes, heads, title block, citation style). Everything the venue leaves open goes in one
  add-on loaded right after it: one accent color, a monospace that fits Times (`zi4` at 0.95),
  microtype, float placement, captions, display rhythm, table helpers, callouts, theorem
  environments, cleveref. A measured exemplar paper looked distinctive only through four box
  environments its authors defined.
- **Profile B**: 150 mm measure, symmetric margins, no sidenote column (one cost a 21 mm centering
  error and about 78 float errors); Palatino text and math `mathpazo[sc,osf]`, leading 1.06;
  navy numerals, letterspaced small-caps heads, running heads that never wrap.
- **Profile C**: margins 0.85 in, Computer Modern via `lmodern`, `natbib[numbers,sort&compress]`
  with `unsrtnat`, `microtype[expansion=false]`, `longtable` for parameter tables.
- No chapter or section file ever adds a `\usepackage`. Every package lives in the preamble.
- Copying a reference document's look: measure its PDF (page and text block with `pdfinfo`,
  rendered pages side by side, colors sampled from pixels), record in the preamble header what
  was copied, justify each deviation.

Detail for all three, with every number: `references/preambles.md`.

## 2. Fonts, math, microtype, color, names

- **Body math matches body text**: `mathpazo`, `newtx`, `libertinus`, or Latin Modern. When a
  venue sets Times text over CM math, keep it and make the figures match the paper; once a figure
  font is settled, write it down and never flip it back.
- **Always `microtype`**, plus `\setlength{\emergencystretch}{1.5em}`; hyphen minimums 2 and 3
  in venue papers; `\babelhyphenation` for names the patterns break.
- **One accent color** for links, citations and box rules; text in ink and grays. Boxes: a pale
  tint of the accent with a 1.6 to 2 pt left rule, square corners, few of them.
- **Every method, model, dataset and unit is a macro**, so a renamed thing changes in one place.
  Operators used in prose are wrapped in `\ensuremath`; a unit macro keeps the following space
  (`\um{}` or `\xspace`).
- **Typed label prefixes with cleveref** (`fig: tab: sec: eq: app: alg: box:`), so "Table 1"
  comes from `\Cref{tab:bench}` and cannot drift.
- `\usepackage[T1]{fontenc}` needs a scalable font (`lmodern` or the venue's); otherwise microtype
  stops on bitmap fonts.

## 3. A minimal or foreign TeX install

**Shim missing packages in one place.** `assets/shims.tex`, input after hyperref, loads each real
package when present and a stand-in with the same interface when absent: multirow, csquotes,
siunitx (`\SI`), placeins (`\FloatBarrier`), needspace, adjustbox `max width`, and a
prefix-aware `\cref`. On the basic TeX Live 2025 used to test this skill, siunitx, multirow,
needspace, placeins and csquotes were all missing and every profile still compiled.

- A stand-in with `#1` is defined after the conditional load with `\providecommand`, never inside
  `\IfFileExists{...}{...}` (it stops with "Illegal parameter number").
- When the source must stay unmodified (a submission), keep shims in a `texshim/` folder on
  TEXINPUTS (`build_latex.py --texinputs texshim`) and delete it on a full install.

## 4. Captions and tables

**Caption: bold claim sentence, panel key with bold letters, one source line.**

```latex
\caption[Short]{\textbf{[Claim sentence.]}
  \textbf{(a)}~[...] \textbf{(b)}~[...; the dashed line marks chance.] Adapted from Fig.~2b of \citet{key}.}
```

- Name every marker drawn (dashed line, color, band, star). Source line "Adapted from" when
  changed, "Taken from" when whole; never "Reproduced"; no slides, decks or licenses in captions.
- A table caption states what bold, underline, fills and symbols mean, the number of runs and the
  spread. **An asterisk marks significance as the caption defines it; bold marks best by value
  only when the caption says so.** Two cells lost their mark when their adjusted p missed .05.
  Rank fills are named in the caption on the same fills (`\rankkey{rankfirst}{first}`).
- The bold title states the finding with no count: "All [N] ablations lower the score, [M] of
  them significantly" was struck as "absolute AI slop"; counts go into the caption body.

**Results tables are generated from the record, never typed**:
`python3 scripts/make_table.py record.json --rank-columns 2-8 --rank-low 9 -o tab.tex` writes a
booktabs body that may change layout, never a value. The recipe it follows: `\scriptsize`,
`\tabcolsep` 2.35 pt, group rows in italics across the width instead of a category column, rank
fills `D3ECE3` / `D8EBFF` / `FDEDCE` with superscript ranks, ± SD tiny and gray, arrows for
direction in headers, `adjustbox` max width (never `\resizebox`, which also enlarges).

Numbers: `$50{,}000$`, thin space before upright units, `.58` and `$p=.002$` without leading
zero in tables, true minus. A reporting threshold applies to every result alike and is stated.
Detail: `references/tables-captions.md`.

## 5. Build and gate

```bash
python3 scripts/build_latex.py main.tex                       # build/main.pdf, then the gate
python3 scripts/build_latex.py main.tex --max-main-page 9 --max-mb 50 --publish main.pdf
```

- **Out of tree, with the build folder first on TEXINPUTS**; BibTeX inside the build folder with
  BIBINPUTS and BSTINPUTS pointing back; pdflatex until no "Rerun" (at least two passes after
  BibTeX, at most five) and **fail if it never settles**; check `%%EOF`; publish by atomic rename.
- **pdflatex and BibTeX with natbib**, never biber unless the project already depends on it.
- `scripts/latex_gate.py build/main.log` exits 1 on: LaTeX errors, a missing `.bbl`, undefined
  references or citations, multiply defined labels, overfull boxes, float too large, rerun needed,
  headheight, BibTeX errors and warnings, unembedded fonts, a page or size limit, the main-text
  end label past its page, placeholders (`??`, `NEEDS_CITATION`, `TODO`) in the PDF text.
- Put `\label{mainend}` after the last main-text sentence for every page-limited document.
- **Every edit batch ends with a build and the gate**, and chapter start pages are compared with
  the last build. Fix a new overfull line at once.

Manual equivalents, the gate table and every defect each gate caught:
`references/build-and-gates.md`.

## 6. Look at the pages

**Verify every preamble or layout change on a rendered page.** Logs missed wrapped running heads,
a box 3.9 mm short of the margin, a swallowed space after a unit, floats past the conclusions,
hidden text in a cropped figure.

```bash
python3 scripts/render_pages.py build/main.pdf png 3 7 xii --dpi 150     # by printed label
python3 scripts/render_pages.py build/main.pdf png 4 --clip 0 0 .5 .3 --dpi 300
python3 scripts/render_pages.py build/main.pdf png --sheet               # contact sheets
```

Open each PNG and look. Test a preamble change on a small probe document first. Before a long
document is handed over, run the whole-document pass (contact sheets at 45 dpi, zoom where needed,
report as `PDF page | problem | fix at file:line`). Figures: `scripts/scan_figures.py figures/
--terms "<retired names>"` for hidden text and unembedded fonts; `scripts/embed_base14.py` embeds
a figure's Helvetica.

## 7. Page budgets and stranded lines

**Measure, then take the moves in order of losslessness.** `scripts/locate_text.py main.pdf "last
words."` gives page and yMax of a sentence; `--fill` shows pages under 80 % full.

1. Layout waste: a `\FloatBarrier` stranding floats on half-empty pages, a `\clearpage` before the
   appendix, a final page holding one paragraph.
2. Main-text display tightening (`\tightenmaindisplays`: 3 pt above and below, 1 pt short),
   restored before the appendix.
3. Float geometry: `wrapfigure` at 0.43 to 0.46 `\linewidth` beside its paragraph; `\widefig`
   overhang to the right before shrinking a figure.
4. Run-in heads (`\rwpara`) in place of `\paragraph`.
5. Your own additions: caption words you wrote, pointer sentences, then float spacing.
6. Near-verbatim redundancy, kept in the section that owns the fact.
7. Method detail beyond what a reader needs, moved to the appendix.
8. Over-long background and discussion.
9. Vague sentences, deleted.

Never change the venue's geometry or font size, never shrink figure text below 4 pt at print
size, and never cut a main-text result to fit: it moves to the appendix with its number.

**No line, label or heading strands.** `\clubpenalty`, `\widowpenalty` and
`\displaywidowpenalty` at 10000; `\needspace` 9 lines before sections and 6 before subsections;
`locate_text.py --runts` lists one-word last lines of paragraphs and captions (fix with `~` or
`\mbox`); short running heads and contents entries. Detail: `references/page-budget.md`.

## 8. Bibliography

```bash
python3 scripts/bib_check.py --tex main.tex sections/*.tex --bib refs.bib          # offline
python3 scripts/bib_check.py --tex main.tex --bib refs.bib --crossref              # network, user-run
```

- **Never rename a key the text uses**, and never delete an entry silently: park uncited ones in
  a file that is not input. A 270-entry repair changed 175 entries, no key, removed nothing.
- Errors: cited key without entry, `NEEDS_CITATION` left, duplicate keys, two keys of one work in
  one `\cite` (prints "?"). Warnings: one work under two keys, missing DOI, unbraced acronyms in
  titles (sentence-casing styles lower-case them). Target: BibTeX 0 warnings.
- Verify entries against Crossref, PubMed, arXiv or bioRxiv (published since?), proceedings pages;
  resolve by title and DOI, never by key; one writer edits the `.bib`.
- Unpublished own work is never cited as evidence; it is described in words ("under revision at
  [journal]"). Detail: `references/bibliography.md`.

## 9. Revision marking

- **Prove the source first**: rebuild the submitted version and match it to the submitted PDF
  (page count, high sentence overlap) before the first edit.
- **One light blue, one switch, in every build that leaves your hands** (`assets/revision.tex`):
  `\rev{}` for changed text; a new float gets `\revfloat` and its whole caption in `\rev{}`; an old
  float only its changed words; new references through `\revbibkeys{}`. Per-round colors were
  thrown out: "just light blue whatever is different from the inital submission".
- Decide what is new against the submitted PDF. The revised paper never mentions reviewers or
  compares itself with the submission.
- Clean copy with identical line breaks:
  `build_latex.py main.tex --variant revision_clean.tex`. Detail: `references/revision.md`.
- Floats for a reply or review page: `scripts/render_floats.py main.tex --check-pdf
  build/main.pdf` crops every table and figure by label (with and without caption) and writes
  `renders/manifest.json`; the `rebuttal` skill embeds floats from it. Look at every PNG.
- Co-authors who read in Word get `scripts/latex_to_docx.py main.tex --template ref.docx`, run
  after the PDF build and `render_floats.py`: equations as PNGs at print size with their TeX as alt
  text, floats as images with captions as text. **A Word file co-authors already edit is never
  rebuilt; edit it in place.** Detail: `references/word-export.md`.

## 10. Editing a heavily worked file

1. Back up (`main.tex.pre-YYYYMMDD-label`).
2. Compile the untouched file as a baseline; stub missing packages outside the source.
3. Apply edits in themed batches with `scripts/apply_tex_edits.py batch.json` (each `old` must occur
   exactly once or the file's batch is refused; it reports changed cite keys, refs, labels and
   numbers).
4. Read the changed lines, grep for dangling references, rebuild, compare with the baseline.
5. `diff -u` the backup against the result and tie every hunk to a request.
6. Report decisions, resolved and open items, "Found but not changed", and the paths.

Polish the edges; never restyle a worked text unasked. When a requested wording contradicts the
records, write the true version, say why, and offer the change that would make the request true.
Detail: `references/safe-editing.md`.

## 11. Check before anything is handed over

In this order:

1. `build_latex.py` settles and `latex_gate.py` passes: 0 errors, 0 undefined references or
   citations, 0 overfull boxes, every font embedded, page and size limits met, main text ends on
   its page. Any gate printed "not checked" is reported as not checked.
2. `bib_check.py` offline with no errors; `--crossref` run or listed as not run.
3. `scan_figures.py` on the figure folder; `locate_text.py --runts` and `--fill`.
4. **Look**: every page your change touched, rendered; for a long document, contact sheets of
   all pages. Captions name every marker; no label is cut; no float lands after the conclusions.
5. For a revision: marked and clean builds both pass; every `\rev{}` passage
   (`extract_rev_passages.py`) maps to an edit in the list.
6. For an edited file: the diff maps hunk by hunk to the requests.
7. Hand over with the gate's state line, the pages looked at, and what was not checked. If asked
   for the PDF mid-check, send it labeled "not final".

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a build trusted on its exit code | "the run still exits 0, so the defect is invisible unless the log is read" | out-of-tree build plus a gate on the log |
| three LaTeX passes | (contents page numbers wrong after three) | passes until no "Rerun", fail otherwise |
| several revision colors | "not different colors bro, just light blue" | one blue behind one switch |
| a new float marked by its label only | "the whole caption is blue" | `\revfloat` plus the caption in `\rev{}` |
| revising the local draft | "see which one we submitted finally I don't even know anymore" | the submitted source, proven against its PDF |
| a multi-agent restyle of a worked text | "just try to polish the edges" | counted edits tied to requests |
| overriding the venue style | (rated reject-level in the author's own pre-submission verdict) | the stock style plus a house add-on |
| redrawn poster figures and a rewritten abstract | "do not make new diagrams", "super AI" | the paper's figure PDFs and sentences, cut |
| "Reproduced" in captions, mention of slides | "no one knows about the deck" | "Adapted from" or "Taken from" |
| a figure crop that cut labels | "you cut the gene names!" | shared-label panels in one crop, looked at |
| an incomplete abbreviations list | "either do all or do none!!" | a list built from the printed text, complete, or no list |
| renamed citation keys | "keep the ids that was used in the .tex main file" | keys untouched, aliases for duplicates |
| a lone word on a line | "affiliations for no reasons go to second line only for one name" | ties, `\mbox`, width fixes, a runt check |
| a section-conclusion box in every section | (removed in a later round) | one prose conclusions section |
| counts in a bold caption title | "absolute AI slop" | the finding in plain words; counts in the caption body |
| a co-authored Word file regenerated with python-docx or pandoc | (blue headings, visible "LaTeX: ..." captions; the author was furious) | that file edited in place; new Word copies built from the LaTeX source |

## Scripts

Python 3.9 or later. Standard library only, except where noted. External tools: pdflatex (or
xelatex, lualatex), bibtex, and poppler (`pdffonts`, `pdfinfo`, `pdftotext`, `pdftoppm`).

| Script | Does | Needs |
|---|---|---|
| `scripts/build_latex.py` | out-of-tree build, BibTeX, settle loop, atomic publish, variants, then the gate | TeX |
| `scripts/latex_gate.py` | reads the log, `.blg`, `.aux` and PDF; exits 1 on any gate | poppler for PDF gates |
| `scripts/render_pages.py` | pages by printed label, zoomed clips, contact sheets, float-to-page map | PyMuPDF (pdftoppm fallback) |
| `scripts/locate_text.py` | where a phrase ends on the page, page fill, one-word last lines | poppler |
| `scripts/make_table.py` | booktabs table body from a JSON record, rank fills | |
| `scripts/bib_check.py` | citation coverage, duplicates, DOIs, braces; `--crossref` online | network for `--crossref` |
| `scripts/apply_tex_edits.py` | exact-string edit batches with count checks, backup, token comparison | |
| `scripts/extract_rev_passages.py` | every `\rev{}` passage with its section and anchor | |
| `scripts/scan_figures.py` | hidden text and unembedded fonts in figure PDFs | poppler |
| `scripts/embed_base14.py` | embeds a PDF's non-embedded Helvetica with the URW clone | PyMuPDF, TeX Live URW fonts |
| `scripts/count_color_pages.py` | color and black-and-white page count for a print shop | PyMuPDF, numpy |
| `scripts/render_floats.py` | every float by label to PNG, with and without caption, plus `manifest.json` | TeX, PyMuPDF, numpy |
| `scripts/latex_to_docx.py` | Word copy from the LaTeX source on a reference template | python-docx, PyMuPDF, TeX |

## Reference files

- `references/preambles.md`: the three profiles in full, fonts and math, microtype, color,
  macros, cross-references, floats, boxes, shims, copying a reference look.
- `references/tables-captions.md`: caption anatomy and source lines, generated tables, the table
  recipe, number formatting.
- `references/build-and-gates.md`: the build by hand, every gate and what it caught, rendering,
  the whole-document visual pass, fonts and hidden text, print copy, size limits, hand-over.
- `references/page-budget.md`: measuring, the proxy for revisions, the moves in order, widows
  and orphans.
- `references/bibliography.md`: styles, offline and online checks, conventions, self-citation.
- `references/revision.md`: proving the source, the one-color toggle, the final-paper rule,
  variants, the edit list.
- `references/safe-editing.md`: the procedure for a heavily worked file and the rules around it.
- `references/traps.md`: TeX, shell and figure traps with their fixes.
- `references/word-export.md`: the Word copy for co-authors, what it holds, and the rule for a
  Word file they already edit.
