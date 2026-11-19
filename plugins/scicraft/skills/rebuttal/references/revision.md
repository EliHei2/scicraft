# The revised paper

## 1. Prove you hold the submitted source

The folder that looks like the paper is often an older draft. In the source work the local folder held a 12-page
draft while the submission was a 9-page cut; a revision built on it ran to 13 pages and its abstract stated a different
number of tasks from the submission. A second "submitted source on disk" (a copy kept for another document) was not
the latest either. A forked agent declared the revision within the page budget because it compared against the old
draft; the revision was three pages over.

1. Find every candidate: the Overleaf project's history at the submission time (export that version), zips in the
   downloads folder, copies kept elsewhere. Extract each zip into a fresh folder; watch for file names that collide
   by case on macOS, and verify checksums.
2. Score each candidate against the submitted PDF:
   ```bash
   python3 <skill>/scripts/match_source.py submitted.pdf candidate_a/ candidate_b/ archive_c/
   python3 <skill>/scripts/match_source.py --self candidate_a/build/main.pdf candidate_a/     # calibration
   ```
   Calibration on the source work with this script: a source against its own built PDF scored 66%, the older draft
   23%. The measure used at the time (sentence match by 6-grams) gave about 70% against 15.6%. The right source
   scores near its own calibration value; a draft scores far below.
3. Rebuild the winning candidate and compare its prose lines with the submitted PDF (a line ratio of 0.949 was
   acceptable when the differences were only figure labels and glyph order). Confirm the page count and the page
   where the references start.
4. Only then edit. If no exact source exists, write the edits as a numbered list keyed to the submitted text
   (`REVISION_EDITS.md`: E1 for the main text, A1 for the appendix; each with the first words and the pdftotext line
   of the submitted sentence, the action replace, insert after or delete, and the exact `\rev{}` text) and transplant
   them onto the exported source. `rev_passages.py --out REV_PASSAGES.md` lists every marked passage with its anchor
   for this.

Keep the source unmodified for the build environment: install a missing package in user mode from the frozen TeX
archive of the year the venue uses (`tlmgr init-usertree`, then `tlmgr --usermode option repository <frozen archive
URL>` and `tlmgr --usermode install <pkg>`), or inject a shim on the command line (`TEXPRE='\RequirePackage{shim}'`
in `build_variants.sh`). For a test compile from a clean unzip, pass `-jobname`, or pdflatex writes `texput.pdf`.

## 2. Marking: one color, one switch

`assets/rev_macros.tex` holds the block; `assets/rev_example.tex` exercises every case and compiles.

```latex
\definecolor{revised}{RGB}{70,130,180}
\newif\ifrevisedcolor \revisedcolortrue
\newcommand{\rev}[1]{\ifrevisedcolor{\ifvmode\leavevmode\fi\color{revised}#1}\else#1\fi}
\newcommand{\revcap}[1]{\ifrevisedcolor{\color{revised}#1}\else#1\fi}
```

| Change | Marking |
|---|---|
| added or reworded sentence | `\rev{...}` around it |
| new table or figure | `\revcap{\caption{...}\label{...}}`, and `\rev{}` around the tabular when the table has no shading of its own; a shaded table keeps a black body |
| existing table or figure | only the changed words of its caption or cells |
| new term in an equation | `a \mathbin{\rev{+}} \rev{\lambda \mathcal{L}_{\rm new}}` |
| new bibliography entry | its key in `\rev@bibkeys` |
| punctuation fix in submitted text, a removed decoration in a figure | no color ("keep it quiet, don't make it blue because of that") |
| deletion | cannot be colored; list it in the change log (no latexdiff) |

- **Decide newness against the submitted PDF**, not the markup: `pdftotext` the submitted PDF and grep
  `(Table|Figure) [0-9]+: ` to see which floats existed.
- `\revcap` exists because `\rev` around a whole caption starts an empty paragraph in the marked copy only, which
  moved every line below it by 6 pt in the test build. `rev_pdf_check.py` catches this.
- **Round colors** (`\new` orange 214,96,0, `\newer` magenta 197,27,125) let the authors see what changed in the
  last round. They are off by default. The upload copy has one color: an Overleaf zip that compiled to the
  multi-color working copy confused co-authors and was replaced.
- A color macro swallows a space that opens its argument: `\rev{ word` prints two words run together or a blue
  space. `rev_passages.py` reports it; move the space outside.
- Grep the preamble before naming a new macro: an unused existing `\upd` clashed ("Command already defined").
- Shading inside a table: remove a single blue word inside a shaded table so its body stays uniform.

Build and check:

```bash
bash <skill>/assets/build_variants.sh main            # main.pdf (working), main_upload.pdf, main_clean.pdf
python3 <skill>/scripts/rev_pdf_check.py main_upload.pdf main_clean.pdf --allow 0,114,178
python3 <skill>/scripts/rev_passages.py . --ban <skill>/assets/banned_reply_terms.txt
```

The clean copy must have the same words in the same places as the upload copy and no text in the revision color;
the upload copy must have no text in a round color. Pass the paper's own text colors (rank tints, a method
color, white labels on dark panels) with `--allow`.

## 3. What the revised paper may say

- **It reads as the final paper.** It never mentions reviewers ("don't write that, oh, this is the answer to this
  reviewer") and holds no submitted-versus-revised table or sentence ("no trace of such comparison!! that should be
  in our general response but also just at a high level"). Grep new text for `submitted|earlier|previous|original|
  every change` and remove each comparison.
- **New text matches the measured cadence of the old.** The submitted paper had a median of 17 words per sentence,
  1% of sentences over 45 words and 0.03 semicolons per sentence; the first added text had 29, 24% and 0.39.
  "Cadence is the loudest giveaway." Split welded ", and" sentences; no inline colons, semicolons or dashes in new
  text (old text may keep them).
- **No new named concepts.** Name things concretely and define every symbol where it first appears, in the existing
  notation. The author could not tell what one newly named module was, so a reviewer could not either.
- **One name per thing, applied everywhere**: text, tables, figure labels (regenerate the figure from its code),
  the platform abstract, the replies. Check with `pdftotext` of the built PDF and of each figure PDF, the TeX, and
  the Word file. Old table files no longer `\input` still carry old labels: delete them before a source upload.
- **Uniform conditions.** One training length per study, stated once per caption.
- **Leave untouched paragraphs alone.** "It is your original text, it reads like a person wrote it ... Rewording it
  would only add blue to a part no reviewer questioned."
- **Abstract**: concept and effect, performance stated once with the comparison set named, no second metric for the
  same win, at or below the submitted length. Introduction: no results; say how the evaluation works and cite it.
  These are writing rules of the `paper-writing` skill and apply to the revision unchanged.

## 4. Page budget

- After every build: the main text must end on the limit page. `resolve_lines.py paper.pdf --pagefill 11` prints
  the last used ruler line and empty slots per page; `pdftotext -f p -l p -bbox` gives the y-maximum of the last
  line.
- Trim in this order: your caption text, your pointer sentences, float spacing, figure scale. Never the author's
  text.
- A shorter abstract pulled a paragraph with a wrapped figure onto the previous page and broke the figure. After
  each text change, render the changed pages and look; scan `pdftotext -layout` for paragraph-final lines of one
  word (a proofreader found six).
- Report the spare lines in every status message ("the main text has no spare line, so any addition has to replace
  something").

## 5. Render the floats before replies cite them

Render every float of the revised paper and look at each image before a reply cites it: each table compiled on its
own with the paper's preamble, each figure PDF to a trimmed PNG at 300 dpi, and a manifest with the float number,
its caption text and a revised flag (true when the float or its caption sits inside `\rev{}` or `\revcap{}`). The
manifest lets a checker confirm that every float a reply cites exists and that every new float is marked. The
renderer, `render_floats.py`, belongs to the sibling `latex-typesetting` skill, as does the LaTeX-to-Word builder
for co-authors (equations as PNGs at print size with their TeX as alt text). An existing co-authored Word file keeps
its equations as they are, byte for byte. When a co-author works in Word, apply the same edit pairs to their file and
highlight only the changed words, never the whole paragraph. The file keeps its styles, comments and equations, and
the count in equals the count out. `scripts/docx_highlight.py IN.docx edits.json OUT.docx` does this, prints the
counts and refuses a pair whose old text is missing or occurs twice.

## 6. Line numbers in replies

The review copy carries a ruler. Replies cite lines as tokens and `resolve_lines.py` fills them from the build:

```json
{"BENCH": ["ranks first on 9 of", "the 14 tasks"],
 "ABL":   ["Ablations.", "against an identically trained control"],
 "T_ABL": "label:tab:abl"}
```

- Phrases are searched as printed and must each lie on one printed line; choose short, unique phrases.
- `"after:<phrase>"` starts the search on that phrase's page; `"last"` takes the last hit of the end phrase.
- A passage split by a float is a list of parts and prints as two ranges.
- Re-run after every rebuild. Any change before a passage shifts it; tokens keep the replies right.
- Write "lines 463 to 464" (the joiner default), since dashes are banned in reply prose.
- When numbering of tables, figures or appendices changes, remap pointers from the `.aux` labels (`label:` tokens).

## 7. Packaging

Per round, one delivery folder and nothing stale beside it:

- `paper_revised.pdf` (upload copy, under the size limit), `paper_revised_clean.pdf`, a light copy for chat.
- `overleaf_changed_files.zip`; test it: unpack over a copy of the previous project, compile, compare with the
  delivered PDF. A whole-project zip under about 50 MB plus a separate heavy-figure zip when needed.
- `replies.md` (paste-ready), the Word file of the Markdown source, the preview. When co-authors comment in the
  Word file of the replies, rebuild it from the new Markdown with their comments carried over, and check that the
  number of comments in equals the number out (5 in, 5 out in the source round).
- `CHANGELOG.md`: exact find and replace pairs for Overleaf, old and new paragraphs for a shared document, generated
  from the same pairs as the edit script. Replay it on the snapshot; it must reproduce the new files byte for byte
  (this caught a trailing-whitespace mismatch). `scripts/changelog.py` does both:
  ```bash
  python3 <skill>/scripts/changelog.py edits.json --snapshot prebrush/ --edited source/ --out CHANGELOG.md
  ```
- `editing_bundle.zip` for anyone who edits or humanizes outside the build: the full source with the appendix, a
  Word file of the same text, the built PDF, the figures and the passage list. Check that the appendix is in it
  before sending (`references/process.md`, bundles sent out for editing).
- `NOTES.md`: every change, open points ("check the case of the reviewer ID before posting").
- Every PDF in the folder contains the final abstract string; move superseded files to `_superseded/`.
- Send with an explicit caption: "Upload THIS file as the revised paper: paper_revised.pdf".

Size: `shrink_pdf.py compress` resamples raster images. On one paper of 81 MB against a 50 MB limit, 200 dpi at
quality 80 gave 36.6 MB for upload, and 120 dpi at 76 gave 26 MB for a chat copy. `shrink_pdf.py light` stores only
pages over 3 MB as page images: a 48-page reading copy came to 2.4 MB with real text elsewhere. A system ghostscript was broken on the source machine; PyMuPDF worked. Check
`pdffonts` for unembedded fonts. Keep the full-quality master.
