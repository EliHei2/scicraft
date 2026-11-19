---
name: book
description: Assembles, audits and builds a book-length document (a book, a monograph, a long report) from the author's own papers, text and figures. Use it whenever the user builds a long document out of work they have already published, even without naming this skill: the table of contents, a chapter per paper, the introduction or summary, putting a paper's figures in, captions and credits, the AI-use statement, title page and required statements, an audit before delivery, the print and similarity-check PDFs, or complaints such as "you butchered my text", "you cut the labels", "this credit is wrong", "the deadline is tomorrow". Holds what an agent gets wrong here (rewriting the author's chapters, drawing or rotating figures, inventing content or credits, citing unpublished work) and ships a figure composer, edit validator, a local overlap counter against the papers, delivery checks and gated builds. For the writing loop prefer paper-writing, for audits in general adversarial-audit, for the LaTeX look latex-typesetting.
---

# book

How to turn a researcher's published and submitted papers into a book that the author recognizes as their own
and a critical reader cannot fault on provenance. Distilled from the final months of one book-length document
built from several papers, during which the author rejected four wholesale rewrites, deleted every figure the
agent drew, and then delivered a version assembled by surgery, cropping and audit. The author is the person who
shaped these rules; the user may be a different author, and where their publisher or their own rules differ,
theirs win.

> **PRIME DIRECTIVE: everything in the book comes from the author's papers, the author's own words or the
> author's figures. The agent places, checks and typesets them, and adds nothing the record does not hold.**

Three failures cost the most time. Guard against them from the first minute:

1. **Rewriting the author's text.** A request to "update against the new manuscripts" became twelve new chapter
   files with new headings and was reverted the same day ("you really butchered my beautiful text"). Compaction by
   squeezing sentences broke 112 of them. Change facts inside the author's sentences; propose anything wider as a
   plan and stop (section 3).
2. **Making or altering figures.** TikZ overviews, a subagent's re-plot, crops that cut feature names, a rotated
   page: all thrown out ("under no circumstance make diagrams/figures here on your own"). Crop, re-letter and place
   the published figures (section 5).
3. **Inventing content or credit.** A framework the papers never named, a re-ranking of the paper's table that hid
   the tasks the method wins, results written into the Introduction, a credit lifted from a paper's
   acknowledgements. Content from the papers and the brief only; credit from contribution statements only
   (sections 4 and 6).

## 0. Before starting

Collect by reading the project. Ask only for what is missing, in one message:

- **The papers**, each in its latest version: TeX source where it exists, the published PDF, supplementary
  methods and figures, the author-contribution statement, and the status of each (published, public preprint,
  under review, under revision). The latest manuscript wins on numbers, the supplement on procedure.
- **The author's own text**: any chapter drafts, a narrative or brief, an abstract they wrote, earlier versions
  they liked. A brief the author writes ("this is my main prompt for you") governs; keep a decisions file against
  it. The argument of the book lives in the project's `NARRATIVE.md` (defined in the sibling skill,
  `project-structure/references/governing-documents.md`).
- **The publisher's or institution's own documents**: author guidelines, title-page template, required
  statements, the policy on text reuse, the guidance on AI use, the delivery instructions (section 7).
- **Two or three real books of the same publisher or series**, as whole PDFs, plus a few more good ones from the field.
- **Figure sources**: the papers' figure files, extended data, posters, talk figures, with versions.
- **The bibliography** and the code repositories (for credits from history and for method descriptions).
- **Constraints**: page budget, deadline, language of the second summary, which collaborators did what.

Set up before the first edit: a snapshot folder (`_snapshots/rN_<label>_<date>/`), `GUARDRAILS.md` with the publisher's
rules, the author's rules and the ledger of allowed values (one scoreboard of numbers plus a list of retired numbers
to delete on sight), `GUIDELINES.md` for style, and `AUTHOR_DECISIONS.md` (`assets/author_decisions.md`). Show the
author the table of contents (chapter, its source paper, its one-line claim) before building.

**Survey a long incoming document before the first edit.** Outline its source, render every page into contact
sheets and list each figure placeholder with its label, caption and the number of text references to it. The list
shows which slots the author's figures must fill and which floats will be dropped.

```bash
grep -n -E '\\(documentclass|usepackage|part|chapter|section)|begin\{(figure|table|algorithm|tikzpicture)\}' main.tex
python3 <skill>/scripts/pages.py main.pdf sheet 1 40 survey_01.png   # then 41 80, and so on
```

## 1. Structure: one chapter per project, the same arc in each

`references/structure.md` has the outline, the arc table, heading examples and the length rules.

- **Introduction, one chapter per project, Discussion, appendices.** Parts only when the grouping means
  something; an exemplar's grouping copied without reason was rejected. An extension of a project is a section of
  its chapter.
- **Each project chapter follows its paper with an implicit arc:** problem statement and setup, background and
  related work (a real literature review), problem formulation and method, experimental setup, results in the
  paper's order, conclusions with limitations and future work. Chapters stay symmetric.
- **Headings name the objects, data and methods**, never the role ("Background", "Results") and never a riddle.
  Spell out abbreviations in headings. A section under about a page merges or becomes a run-in head.
- **Results are organized around the paper's figures**: one text unit per figure, opening with its message.
- **Full weight without padding.** 15 to 25 or more dense pages per project chapter; the final total was
  about 200 to 225 pages against a budget of under 200 pages without references. Measure words per page for the
  layout (463 measured against 500 assumed).
- **Boxes:** one contribution box per chapter after its opening paragraph; no generated take-home or conclusion
  boxes. Algorithm boxes are about five steps, checked against the code, or dropped.
- **Bold marks a central concept at its defining mention only**, about ten per chapter; never a clause, a number
  or a name. An earlier pass with 1 to 3 bolds per paragraph (about 640) was called senseless.

## 2. The spine, and the author's contribution first

- **One spine connects the projects** as steps: a recurring analysis rebuilt per study, shared infrastructure and
  hand-crafted analysis that show its cost, a reusable model for one operation, a reusable general
  representation, what stays open. The Summary and Introduction follow it; each project paragraph says what is
  different and the author's role.
- **No project appears out of nowhere.** Introduce it through the problem that led to it and the people the
  author joined (main institution only, years where the author wants them).
- **A chapter is about what the author did.** Center the credited analysis; the rest of the paper is one
  background section. For a framework or resource paper the chapter is about the framework and the author's
  analysis demonstrates it.
- **The Introduction carries no results of the author's own studies.** Background, mechanisms from the literature,
  the approach, data descriptions and research questions, with forward pointers. Openings come from the papers'
  introductions, never a vignette.
- **The Summary names the main experiments and conclusions from the papers' result headings**, without single
  result numbers, and keeps honesty qualifiers.
- **Frame the field before the instrument, the general category before the instance, and the finest measured unit
  as the finest**, never as "the right unit" against a straw-manned coarser one.
- **Limitations and conclusions come from each paper's own Discussion**; the Discussion ends strong and concrete.

## 3. What the agent may and may not touch

`references/author-text.md` has the full table, the integration procedure and the evidence table.

- **The author's chapters change only by surgery**: a number, a status, an attribution, a retired result, a typo,
  listed old to new with the paper's quote. Restructuring, re-titling, merging and splitting are the author's
  decisions; propose them as a plan at the narrative level and stop.
- **Text the author wrote personally (Summary, opening, aims) gets error fixes only**, and every agent brief says so.
- **No editor fan-out over the author's prose** unless the author names the file. Final-phase fixes are made in the
  main thread, visibly, and logged old to new.
- **Snapshot before every fan-out, restructure or integration**, and give the path in the first report.
- **Gate drift:** `python3 scripts/chapter_drift.py SNAPSHOT_DIR chapters --show-lost --structure`; same + near at
  least 80 %, lost at most 10 %, each lost sentence logged with its reason, no label or figure file lost unless
  listed as intended.
- **Use the papers' terms, never their sentences**, unless the author orders a verbatim version. Measure the
  overlap locally with `scripts/overlap.py` (section 8).
- **Integrating a revision the author supplies:** keep the wording; change only facts, lost content, house bans and
  earlier decisions it silently undid; flag style breaches instead of fixing them; report the verbatim share and
  what the revision reverted.
- **"Did you really integrate it?" is answered with a measurement**: new sentences, present, changed on purpose.
- **Length is cut by moving and deleting whole blocks**, never by compressing sentences.

## 4. Content from the papers and the brief only

- **No term, framework, comparison, limitation or evaluation that is not in the author's papers or brief.** When a
  term is questioned, count its occurrences in the papers; trace a suspect phrase to its origin (an earlier draft,
  an agent) before removing it everywhere. Use the field's word for shared objects and the paper's word for the
  author's.
- **Every number comes from the ledger of allowed values in `GUARDRAILS.md` or a paper.** Results tables are copied
  exactly from the submitted paper; rank statements use the paper's words. A book-only re-slicing of a results
  table ("you cut out the tasks we win in") was deleted and must not be re-added.
- **When the paper and the code disagree, the book follows the code and the discrepancy is flagged** for the
  author and the paper's ledger. Describe a method by what the code implements.
- **Two published numbers that disagree may both be right.** Read the analysis code first: when each belongs to a
  different branch (a filter applied or not), state both with their branch in the sentence. A figure and its text
  that disagree are settled by recomputing from the records, logged for the paper and listed in
  AUTHOR_DECISIONS.md (the sibling skill `integrity-audit` holds the method for claims against records). A
  detail that cannot be reconciled (a hyperparameter, a hardware list) is dropped and logged, because an
  inconsistency a reader can find costs more than the detail. A result is never dropped this way.
- **Claims survive a critical reader.** Verify every "first" against prior work and write the version that holds
  ("competitive on most tasks", not "across the benchmark"); tell the author when one of their claims does not
  hold as stated, and why.
- **Integrity (honest reporting):** a weak or mixed result stays with its number, in the chapter or the appendix;
  a result that contradicts a claim changes the claim; a control that beats the method is reported.

## 5. Figures: reuse, never redraw

`references/figures.md` has the pipeline, legibility numbers, hidden-text checks, caption forms and the license
table.

- **Never make a figure.** Crop, mask, place, resample. If none of the author's figures fits a slot, drop the float
  and say so. Every subagent brief that touches figures carries this rule word for word.
- **Crop whole panels**; keep panels that share labels together; never cut axis text, feature names, keys or scale
  bars.
- **Mask the source's panel letters and set new ones** (a, b, c) in an embedded bold sans, with space reserved.
- **Never rotate.** Upright float pages up to 150 x 215 mm; split a figure into two floats before its text prints
  below about 5.5 pt (6 pt preferred).
- **Compose at the text measure** (150 mm in the source book) with embedded rasters resampled to 450 dpi.
- **Flatten hidden text** (the source manuscript's running heads, clipped panels) and embed every font.
- **One plain source line per caption:** "Adapted from Fig. 2b of \citet{key}." when changed, "Taken from Fig. 2 of
  \citet{key}." when whole and unchanged, "Adapted from the [topic] manuscript under revision at \emph{[Journal]}."
  for the author's unpublished work, nothing for the author's own unpublished schematic. Never "Reproduced"; never
  slides, decks, posters, drafts or licenses in a caption.
- **Credit a person in a caption only for a specific panel made by their own analysis or drawing.**
- **Third-party figures need a traceable source and a compatible license**, or they go.

```bash
S=<skill>/scripts
python3 $S/gridprev.py figsrc/src/paper_fig2.pdf grid/fig2.png --step 25          # read crop boxes
cp <skill>/assets/spec_template.py figsrc/spec.py                                 # declare figures
python3 $S/compose_crops.py --spec figsrc/spec.py --out figures/ --report reports/figure_audit.json --strict
python3 $S/embed_base14.py figures/x.pdf figures/x_emb.pdf                        # if pdffonts shows "no"
pdftotext figures/fig_bench.pdf -                                                  # only visible labels
```

## 6. Credits, self-citation and references

`references/credits-citations.md` has the details and the reference-audit procedure.

- **Credits come only from the papers' contribution sections or the author's own word.** Never from
  acknowledgements, caption drafts or inference. Never expand initials. Verify figure and code credits from
  `git log`. Anything unconfirmed goes to AUTHOR_DECISIONS.md as "please confirm".
- **Collaborators' work is attributed at every mention**: chapter opening, captions, conclusions, both summaries,
  Discussion. Each contribution is credited once, in the contribution box.
- **Unpublished own work is never cited; its status is stated in words** ("under revision at [Journal]", "under
  review at [Venue Year]"). Public own work is cited for attribution only, never as evidence for a general claim.
- **Cite each claim at the claim**, one primary source, no bundles; reuse existing keys; verify new ones by DOI.
- **The reference audit** runs as read-only chunk agents of about 56 entries with OK, FIX, REPLACE_IN_TEXT or QUERY
  verdicts and a context verdict per citation; the coordinator re-verifies against Crossref and never changes a key.

## 7. Front matter: the publisher's own forms and real books

`references/front-matter.md` has the procedure, the apparatus order and the disclosure shape.

- **Find and follow the publisher's or institution's own forms.** Download every document from its author page and
  follow the
  template wording exactly; institution lines come from those documents, never from a generic class.
- **Copy front matter, contribution statements and appendix depth from two or three real books of the same
  publisher or series**, measured from their PDFs. Exemplars inform; the content justifies.
- **The AI-use disclosure states usage only**: tools, provider, models and versions, purpose per study. No sentence
  about the policy, no bibliography entry for a chatbot. Where the policy says so it sits inside the signed statement,
  with the official clauses verbatim, and it agrees with the Disclosures page and the captions.
- **The two summaries correspond exactly**; mirror every edit in the same turn.
- **The list of abbreviations is complete or absent** (`scripts/acronyms.py`, plus the text inside figures).
- **First person singular for the author's own work** where the publisher mandates it, formal register, "we" only
  with named collaborators.

## 8. Audits before delivery

`references/audit-machinery.md` has the lanes, briefs, proposal format and deadline handling; the general method
is `adversarial-audit`.

- **Run the machine checks first** (`book_checks.py` with `--bib` and `--snapshot`, `pdffonts`, raster dpi, log
  warnings) and pass the leads to lanes. Run the checker before and after every agent batch.
- **Check overlap with the author's own sources locally after every content round.** Convert every source to text
  (`pdftotext -layout`), then `python3 $S/overlap.py chapters/*.tex --sources sources/ --minspan 12 --max-share 0.7`.
  It fails on any shared run of 12 or more words; fix a hit with a one-sentence paraphrase or mark it as a quotation.
  Unpublished text never goes to an online checker.
- **Auditors are read-only lanes sharing one rules file** (`assets/auditor_rules.md`) and return exact-match
  `edits.json` proposals. One editor per file; never two waves on one file.
- **The coordinator vets every proposal** with a dry run and a review sheet, reads the source for every fact, and
  applies only error fixes to the author's text:
  ```bash
  python3 $S/apply_edits.py audit/r2/P3.json --root . --sheet audit/r2/SHEET_P3.md   # validate + sheet
  python3 $S/apply_edits.py audit/r2/P3.json --root . --skip P3-A4 --apply          # surgical edits only
  ```
- **Typography-only passes** (bold) are vetted with `check_bold.py edits.json --root .`, then read by hand.
- **Decisions only the author can make go to AUTHOR_DECISIONS.md**, short and numbered.
- **New rules from the author are broadcast verbatim to every running lane**; deadlines go in the brief and by
  message; killed agents are resumed, not relaunched.

## 9. The final build and its two twins

`references/final-build.md` has the gate list, float fixes and the delivery gate.

```bash
bash $S/build.sh main.tex $SCRATCH/b7 build/book.pdf                 # gates, then install
python3 $S/pages.py build/book.pdf count --budget 200                # pages without references
python3 $S/pages.py build/book.pdf sheet 1 30 $SCRATCH/front.png     # look
bash $S/build_print.sh main.tex print_colors.tex build_print          # print twin + color pages
bash $S/build_textonly.sh main.tex build build_textonly               # similarity-check twin
```

- **Every edit batch ends with a side build and the gate**: 0 errors, 0 undefined references and citations, 0
  overfull boxes, no "Float too large", no headheight warning, no "Rerun" after the fourth pass, 0 BibTeX warnings,
  every font embedded. Install only a clean build.
- **The print build** sets all text colors to black and keeps figure colors; report "N color, M black-and-white"
  with page numbers.
- **The text-only build** sets graphics to draft mode for the similarity check's upload limit, same text and
  pagination.

## 10. Check before anything is handed over

1. `build.sh` clean; pages total and without references; page budget.
2. `book_checks.py` zero errors, every warning inspected; `chapter_drift.py --structure` against the last snapshot
   for any chapter the agent touched; `overlap.py` with no run of 12 or more words.
3. `compose_crops.py --strict` on every changed figure; `pdftotext` of each figure prints only visible labels;
   `pdffonts` shows every font embedded.
4. Look at every changed page and figure preview, the title page, contents, Summary and chapter openings.
5. Read the captions' source lines against the figure map, and the credits against the contribution statements.
6. The print and text-only twins rebuilt from the same sources.
7. Check that no agent or background task is still running.
8. Report: what changed (one line per chapter, in the author's terms), the gate line, the open AUTHOR_DECISIONS
   items, and plainly what was not checked.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a rewrite of the author's chapters with new headings | "you really butchered my beautiful text" | fact surgeries inside the author's sentences, listed |
| editor fan-outs over the author's prose | "don't run another set of ... agents" | read-only audits, one writer, error fixes only |
| compaction by squeezing sentences | "sentences does not make any sense anymore" | moving whole blocks to the appendix |
| agent-drawn TikZ diagrams and re-plots | "under no circumstance make diagrams/figures" | the author's figures cropped and re-lettered |
| crops that cut labels | "you cut the gene names!" | whole-panel crops, shared labels kept |
| rotated and landscape figures | "please never rotate a figure" | upright floats, split when too large |
| "Reproduced", slides and licenses in captions | "no one knows about the deck" | one plain source line |
| a credit from acknowledgements | "be careful" | contribution statements and the author's word only |
| citing the author's unpublished manuscript | "do not cite our unpublished work as fact" | status in words |
| results in the Introduction | "no result should be mentioned in the introduction" | forward pointers |
| a re-sliced results table | "you cut out the tasks we win in" | the paper's table and wording |
| a framework the papers never named | "who introduced it?? I never had it!" | the papers' terms only |
| a policy sentence in the AI statement | "just state the usage!" | tools, models, purposes |
| a vignette opener | "follow the manuscript" | the paper's problem statement |
| an invented two-part grouping | "not a meaningful grouping" | one chapter per project |
| riddle headings | "I don't know exactly what that means" | headings that name the objects |
| an incomplete abbreviation list | "either do all or do none" | a list built from the printed text |
| generated conclusion boxes | "makes 0 sense, vague" | a prose conclusion from the paper's Discussion |

## Reference files

- `references/structure.md`: the outline, the arc table, headings, the spine, contribution first, Introduction and
  Discussion, length and cutting.
- `references/author-text.md`: what may be touched, snapshots, the drift gate, overlap with the source papers,
  fact-check surgeries, integrating the author's revisions and writer-agent drafts, a verbatim assembly, the last
  polish, evidence of integration.
- `references/figures.md`: the composer pipeline, legibility, hidden text and fonts, captions, credits, licenses,
  slides, the figure audit.
- `references/credits-citations.md`: credits, the contribution slot, self-citation and status, citing at the claim,
  the reference audit.
- `references/front-matter.md`: the publisher's forms, exemplar books, apparatus order, AI disclosure, summaries,
  publications page, abbreviations, epigraphs, register.
- `references/audit-machinery.md`: lanes, the rules file, proposals, vetting, collisions and deadlines, hand-off
  files.
- `references/final-build.md`: gates, looking, float fixes, the print and text-only builds, the delivery gate,
  commits.

Scripts (Python 3.9+; PyMuPDF, Pillow and numpy for the figure and page tools; pdflatex, bibtex and poppler for
the builds): `compose_crops.py`, `gridprev.py`, `strip_invisible.py`, `embed_base14.py`, `match_artwork.py`,
`apply_edits.py`, `check_bold.py`, `chapter_drift.py`, `overlap.py`, `book_checks.py`, `acronyms.py`, `pages.py`,
`count_color_pages.py`, `build.sh`, `build_print.sh`, `build_textonly.sh`. The ones that need no data answer
`--self-test`. `verbatim_corpus.py` (build, errata, check) runs a verbatim assembly (`references/author-text.md`). Assets: `assets/spec_template.py`, `assets/print_colors.tex`, `assets/auditor_rules.md`,
`assets/author_decisions.md`.
