# Final build: gates, the print build and the text-only build

Every edit batch ends with a side build and a gate; the delivery adds two extra builds. The commands below are
the shipped scripts; they need pdflatex and bibtex (natbib), poppler's `pdfinfo` and `pdffonts`, and Python with
PyMuPDF and numpy for the counters.

## 1. Side build and gate

```bash
bash scripts/build.sh main.tex $SCRATCH/b7                    # build and gate only
bash scripts/build.sh main.tex $SCRATCH/b7 build/book.pdf   # install only when every gate is zero
```

pdflatex, bibtex, then three more pdflatex passes (four in all). The gate counts must all be zero: LaTeX errors,
undefined references and citations, multiply defined labels, Overfull boxes, "Float too large", "too small"
(headheight), "Rerun to get" after the last pass, BibTeX warnings, non-embedded fonts. Three passes once left 64 of
76 contents and list-of-figures page numbers wrong; the fourth pass and the Rerun gate fixed it. The general build
that passes until the log has no "Rerun" (at most five passes) is `build_latex.py` in the sibling skill
`latex-typesetting`.

- **Measure "pages without references" from the PDF** after every build, because float changes move it by
  several pages: `python3 scripts/pages.py build/book.pdf count --budget 200` finds the bibliography's first page
  from the outline (or from the first lines of each page) and reports the pages before it, exiting 1 over the
  budget. If appendices follow the bibliography, add their pages by hand. By hand:
  `for p in $(seq N -1 1); do pdftotext -f $p -l $p book.pdf - | head -3; done`.
- **Build into a side folder, install by copy-then-rename.** The installed PDF never shows a half-built state, and
  building is safe while agents work.
- **Report the gate in every hand-over:** "builds cleanly at N pages (M without references), 0 errors, 0
  undefined references, 0 overfull boxes, fonts embedded", then the commit, then "not pushed".
- **`make` can say "built" without recompiling;** the log is then from an earlier build. Check timestamps.
- **A grep that correctly finds nothing returns exit 1** and stops an `&&` chain; an empty zsh glob aborts the
  command. In zsh `${PIPESTATUS[0]}` is empty, so a failed command piped into `tee` reads as success. In zsh
  `echo ====` fails, because a word that starts with `=` is expanded as a command path; print separators as
  `'----'`. `set -- $r` does not split a string into words in zsh either; use `${=r}` or an array.
- **Keep scratch builds from filling the disk.** Builds failed twice on a full disk:
  `find $SCRATCH -name '*.pdf' -size +20M -delete`.
- **Verify any preamble change in a small probe first:** copy the preamble lines into `t.tex`, add sample boxes,
  compile, render, look. Chapters never add `\usepackage`; missing packages get a shim in the preamble.

## 2. Look at what changed

A gate cannot see a figure that drifted to the end of its chapter, a caption printed over text or a near-empty
last page.

```bash
python3 scripts/pages.py build/book.pdf render $SCRATCH/look 70 41 42 xii   # by printed page label
python3 scripts/pages.py build/book.pdf figs                                # figure number -> page
python3 scripts/pages.py build/book.pdf sheet 35 50 $SCRATCH/intro.png      # contact sheet
```

After each major install look at the pages that carry the argument: title page, contents, Summary, chapter
openings with contribution boxes, every changed figure page. Zoom into a region with `pdftoppm -r 300 -x 0 -y 0
-W 500 -H 150 -png`.

Float and layout fixes that worked:

| Symptom | Fix |
|---|---|
| a half-empty float page adds two pages | `[!tbp]` to `[!t]` (LaTeX tries float pages before top placement) |
| figures stranded on 43 to 62 % full float pages | remove the `\FloatBarrier` that forced them |
| all figures of a chapter drift to its end | restore placement next to the first citation; check `.lof` pages against citation pages after any float change |
| Float too large after a longer caption | shrink the `\includegraphics` width (128 to 116 mm) |
| wrapfigure caption printed over body text | raise the reserved line count (`[17]` to `[19]`) |
| two-line running head, headheight warning | `\section[short]{long}` |
| contents page numbers overflow | widen `\@pnumwidth` |
| appendix references print "Section B.5" | `\crefalias{section}{appendix}`, `\crefalias{subsection}{appendix}` |
| a chapter's last page holds one paragraph | trim the last few lines, or move a float |
| version strings print "vo.2.o" | lining figures for version strings (old-style figures break them) |
| an overfull TOC title | `\section[short]{long}` or discretionary hyphens in the short title |

A layout fix is accepted only after a page count and a look; a `\FloatBarrier` added to keep figures in their
section cost pages.

## 3. The print build

"Make a print version of the build, everything black and white other than the figures, and tell me exactly how
many pages are colored."

```bash
cp assets/print_colors.tex print_colors.tex      # then name your preamble's colors in it
bash scripts/build_print.sh main.tex print_colors.tex build_print
```

`build_print.sh` writes a temporary `main_print.tex` that inputs the color overrides just before
`\begin{document}`, builds it through the same gates, and runs `count_color_pages.py`: a page is a color page when
more than 12 pixels at 60 dpi have chroma above 28 of 255. In a test document the screen build had 6 color pages
of 9 (links, headings, a tinted box) and the print build 1 (the figure page).

- A color that must survive in print (a ranked results table) is declared with `\providecolor` in the preamble and
  left out of the overrides.
- Cross-check: every color page carries a figure caption or the kept table, every figure page was caught, and the
  front matter is all black and white. Report "N color, M black-and-white" with the printed page numbers.

## 4. The text-only build for a similarity check

Similarity checkers cap uploads (25 MB in the source work, against a 100 MB book). Image downsampling with
PyMuPDF and Ghostscript was tried first and failed; draft mode works:

```bash
bash scripts/build_textonly.sh main.tex build build_textonly
```

It inputs the book with `\PassOptionsToPackage{draft}{graphicx}`, reuses the full build's aux, bbl, toc, lof, lot
and loa, runs pdflatex twice, and checks that the page count equals the full build's. Result in the source work:
about 1 MB, same text and pagination, figures as empty frames. Regenerate it after every final build. It is also
the reason hidden text in figures matters: the similarity check reads the full PDF's text layer if it gets it.

## 5. A preview under an upload cap

To send a phone preview under a 30 MiB cap: PyMuPDF `doc.rewrite_images(dpi_threshold=130, dpi_target=110,
quality=70)` then `doc.save(out, garbage=3, deflate=True)`. Do not use `clean=True` (it broke a Pattern resource).
A 150 dpi target was still 64 MB. If needed, split by chapter from the PDF outline.

## 6. Renaming the title

Grep the title macros, `pdftitle`, the signed statement and any echo in the Introduction or Summary. Edit all, rebuild,
check the old string is absent from the PDF text, and render the title page (letter-spaced capitals do not extract
as words) and the signed statement.

## 7. Delivery gate

In this order, each one stated in the report:

1. `bash scripts/build.sh` clean; page count with and without references; page budget met.
2. `python3 scripts/book_checks.py chapters/*.tex front/*.tex --intro <intro file> --unpublished <keys> --bib
   <bib files> --snapshot <last snapshot>`: zero errors, every warning inspected and classed legitimate or fixed
   (epigraphs and acknowledgements are exempt). `scripts/overlap.py` with no shared run of 12 or more words.
3. Fonts embedded; no hidden text in figures (`pdftotext` of each figure file).
4. Front matter against the publisher's template word for word; the signed statement matches the title verbatim;
   the AI statement agrees across the signed statement, Disclosures and captions; the two summaries correspond.
5. Abbreviations against usage; `AUTHOR ACTION`, `NEEDS_CITATION`, `??` absent from the PDF text. Repeated words
   (`grep -nE '\b([A-Za-z]+) \1\b'`) and "a" or "an" before the wrong sound (`book_checks.py` warns on both);
   check each hit by hand, because a doubled word can be correct in the second-language summary.
6. External links checked (399 links in the source work), PDF title and author metadata, a Contents bookmark.
7. The print build with its color count, and the text-only build under the upload cap.
8. `AUTHOR_DECISIONS.md` current; say plainly what was not checked.

## 8. Commit and push

Read the repository's commit conventions first; some authors want commits free of AI attribution, with agent
files excluded through `.git/info/exclude` rather than a committed `.gitignore`. One commit for an accumulated tree,
with a message that says it was committed from an accumulated working tree and describes what the diff shows.
Exclude build PDFs, zips, local snapshots, staged third-party sources and unpublished source dumps; check staged
sizes (nothing over 50 MB, never over 100 MB), and grep the staged list for every excluded pattern
(`git diff --cached --name-only | grep -E '\.pdf$|_snapshots/|figsrc/src/'` must print nothing). A commit message
written through a heredoc needs a blank line after the subject, or the body becomes part of the subject; on a
commit that is not pushed, fix it with `git commit --amend`. Always ask before pushing. A push of about 150 MB needed
`git -c http.version=HTTP/1.1 -c http.postBuffer=524288000 push origin main`.
