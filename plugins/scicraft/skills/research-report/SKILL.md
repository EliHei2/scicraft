---
name: research-report
description: Writes and builds the report sent to a supervisor, co-author or collaborator (a result, a reproduction, an answer about a metric or method, a status) as one offline HTML file plus a PDF, and decides what goes to co-authors in which form. Use it whenever results are written up for someone else, even when the user does not say report: "write this up for my supervisor", "an artefact I can send my prof", "is it standalone", "answer [their] question about the metric", "too much text", "this is AI slop", "send the tables to the co-authors", "put the posted replies in the internal report". It holds the accepted shape (a one-sentence answer above a three-sentence summary, one-line TL;DR with figure references, one bold sentence per section, terms defined in place, no glossary or limits box), figure rules, a builder that inlines figures and pre-renders math, a checker, the defense variant. Prefer integrity-audit to trace the evidence, data-figures for the panels, rebuttal for peer-review replies.
---

# research-report

How to write and build the report a researcher sends to someone who was not in the room: a supervisor, a
co-author, a collaborator. Distilled from reports rebuilt over many rounds of notes and from the sharing of
tables and figures with co-authors. Every
rule below is something the author asked for or threw out. Where the person at hand says otherwise, they win.

> **PRIME DIRECTIVE: a reader without context gets the answer from the first sentence, every later sentence
> carries a number or a decision, and the file opens offline with a double click.** Figures carry the argument;
> words define, state and decide.

Four failures cost the most time. Guard against them from the first minute:

1. **A report that reads as machine-made**: a glossary box and a limits box at the top, bold paragraphs set larger
   than the body, captions in fragments, 4,100 words where 2,300 had been accepted. "tooooo much text", "total AI
   slop" (sections 1 to 3).
2. **A report the reader cannot open**: figures in a separate folder, math and fonts from a CDN. "if I send it to my
   prof can [they] open with no problem?" (section 5).
3. **Wording that turns a presentation fix into an accusation**, or a claim wider than the records: one draft
   read as an admission of wrongdoing (sections 2 and 7).
4. **Sending co-authors the wrong kind of file**: dozens of per-panel CSVs uploaded where a handful of short reference
   tables were wanted. "look at the type of [their] files" (section 6).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The question, in the asker's exact words**, with who asked and when. The report answers this question and no
  other. A forwarded chat message or a challenge document is the source; copy it into the report folder.
- **The records behind every number**: result tables, run configs, logs, the commit of the code. Tracing a number
  to its code and data is `integrity-audit`'s job; this skill starts from traced numbers.
- **The manuscript's figures and its style module**, if the work belongs to a paper. Report figures look like
  them (section 3).
- **The reader and the route**: who reads it, on what device, by mail or link, and whether their institute's mail
  filter strips `.html` attachments (assume it does).
- **What the reader already uses**, when files go to co-authors: open their existing files before making yours
  (section 6).
- **The deadline**, and what may not be shown (unpublished results of others, private messages).

Work in a folder of its own that the user can find, outside any git repository unless they say otherwise:

```
<project>/<topic>_report/
├── report/     <Name>.html, <Name>.pdf          what is sent
├── figures/    every figure in the report, PNG and PDF, named as in the source
├── code/       report source (.html or .md), one plotting script per panel, the analysis scripts
├── data/       the result tables behind every figure
└── README.md   what each folder holds and how to rebuild
```

"where do you save these? save them where I can find!" Scratch folders and Downloads are copies, never the only
home.

## 1. The opening

The accepted opening, in this order and nothing else before section 1 (`references/report-shape.md` has examples
from two fields):

- **One sentence with the answer, then a paragraph that starts with a bold "Summary." and has three sentences**:
  the answer line gives the answer with its number (`<p class="answer">` in the template); the summary says what was
  measured or asked, what was done (with its size), and the answer with its number and what it means for the
  decision. "make a one sentence summary of this also on top" added the line above the summary. Written for someone
  without context: a summary dense with internal counts and names drew "no one will understand. write for someone that does not have the context".
- **A TL;DR of one-line items**, each a bold finding with its number and a figure reference that links to the
  section ("add a proper tldr with links").
- **No glossary, terms, definitions or limits box at the top.** One was added in response to "define it
  explicitly" and rejected the same day as "unnecessary and total AI slop". Define each term where it is first
  used.
- The opening fits on the first PDF page.

ML example. Answer line: "The two-stage schedule explains 1.5 of the 1.8-point gain." Summary: "The question was
whether the two-stage schedule or the larger batch explains the 1.8-point gain. We retrained both at 3 seeds with
one change at a time. The schedule accounts for 1.5 of the 1.8 points, so the paper should credit the schedule."

## 2. Sections and sentences

- **Each section opens with one short bold sentence at body size**, then plain text. "bold font and so big for such
  a long text": a bold lead had grown into a paragraph set larger than the body. Check each lead
  against the data and narrow it where it overreaches ("all scores" became "of the scores tested").
- **Every sentence carries a number or a decision.** Cut the others. `check_report.py --list-bare` lists sentences
  without a digit for you to keep (a decision) or cut.
- **Direct statements.** "X's metric could not be used, so we built our own" was replaced by what had been
  found, for example "the paper cites no code, and the public package returns an empty result on our data".
  Give the concrete reason, never a vague hedge.
- **Define every term and internal count where it is used**, in one operational sentence with its origin. "what are
  these [N]" was answered by naming them: where the [N] items come from and when they were chosen, for example
  "the [N] test prompts, chosen once before any model is scored". Explain derived counts in the same sentence,
  for example "6 seeds for each of 4 variants is 24 runs".
- **One version in the main text**: the one the paper or the decision uses. Variants and controls go to the
  appendix. "don't confuse many different versions". One meaning per term; a word that had three meanings
  ("thinning") was replaced by three words.
- **Name variants by what they are**: `<metric>_<source>`, `<metric>_nocap`, `<metric>_uniform`. "published",
  "signed" and "v2" say nothing and were thrown out.
- **State each setting as the value actually run, once**: for example "every model was trained for [k] steps".
  Never two values side by side ("[a] vs [b]"), which "makes the work look bad" and is not what happened.
- **Formulas once, in boxes; explanation in figure captions; the rest in a collapsed appendix.** "we need some
  formulas and important info boxes, other explanation should be only figure captions."
- **Name the scope of every claim**: the datasets, conditions and baseline it covers. A fold change held only for
  the excess over the baseline; a claim that clean inputs score zero was wrong (they scored small positive values).
- **Every concession carries its number, as every defense does.** A cold reader called one draft "a defence brief"
  because only the defenses had numbers. A weak or mixed result stays in the report, in the appendix if it is not
  the answer, with its number.
- **Count the main-text words every round and report the count.** Each review round adds terms and concessions;
  set a cut target per round.

## 3. Figures

The report's figures follow the manuscript (`references/figures.md`; panel making is `data-figures`):

- **Same style module and the same plotting code as the paper's accepted figures.** Figures that approximated it
  were "soooooo claude": thick bars, off-palette colors, titles in place of axis labels.
- **Shown at true size.** The builder reads each PNG's dpi and sets its width in mm (`--mm` is 4.95 px on screen and
  0.96 mm in print), so every figure shares one scale and nothing is stretched.
- **Numbered R1, R2 ... in reading order, about 10 in the main text; the rest S1, S2 ... in a supplementary
  section**, with a one-line pointer where a figure moved out. The R and S prefixes keep report figures apart from
  the paper's own numbers.
- **Full captions in full sentences**: a bold first sentence that states the figure's claim, then what each axis,
  mark and color is, n, the statistic and its spread, and which run and settings. Every mark has a legend or a
  direct label. A caption in fragments ("Open circles: no contamination. Band: ...") was "total AI slop".
- **The quantity's name on the y axis, no panel titles.** No log axis for a score whose differences matter: on
  log10 one metric "looks like it only gives 2 values"; use a linear axis with a factor (x 10^-5).
- **One run and one setting across every figure.** When the paper's run is not at hand, the caption names the run
  used.
- **Spread as median and IQR (25th to 75th percentile)**, never a confidence interval.
- **Color carries the identity of what the figure compares.** Comparing methods: metric names and y labels stay
  ink. Comparing metrics (a metric-defense report): the defended family takes the hero color, the rival family the
  rival color, the rest gray, and the y label takes its family's color. Tokens: the sibling skill
  `data-figures/references/style-tokens.md`.

## 4. Typesetting

"make the typesetting proper, it's so much AI slop style ... not random grey and different font sizes and bad
color." The template (`assets/report_template.html`) holds the look that was accepted:

- one reading column (max 960 px, text lines at most 74 characters), serif body that matches TeX math, Helvetica
  Neue headings that match the figures;
- four sizes only (28, 19, 15 and 13 px), ink for all text, one accent for links and box rules;
- dark mode by system setting; print forced to light with A4 margins 15/14/16 mm.

## 5. Build: one offline HTML plus a PDF

Mail systems block `.html` attachments, so the report travels as a PDF with the HTML beside it. Both are built
from one source by `scripts/build_report.py` (`references/build.md` has every option and the traps):

```bash
S=<skill>/scripts; R=<project>/<topic>_report
npm install --prefix ~/.cache/report-mathjax mathjax-full@3.2.2          # once, for math
python3 $S/build_report.py $R/code/report.html --out-dir $R/report --name <Name> --pdf \
    --mathjax-dir ~/.cache/report-mathjax
python3 $S/check_report.py $R/report/<Name>.html --banned <skill>/assets/banned_words.txt \
    --list-bare --pdf $R/report/<Name>.pdf --previews $R/code/pages_r01
```

The source is the template filled in (`assets/report_template.html`), a `<main>` fragment with `--head`, or
Markdown (`assets/report_template.md`; needs the `markdown` package or pandoc). The builder:

- inlines every local image as base64 at its true width;
- pre-renders `\( ... \)` and `\[ ... \]` to SVG with MathJax through node; **without node or mathjax-full it
  keeps the TeX as plain text, prints a warning, and the delivery message must say so**;
- uses system fonts and refuses to write a page that still holds `<script>`, `<link>`, `@import` or anything
  loaded from another host;
- writes `<Name>.html`, `<Name>_print.html` with every `<details>` open, and with `--pdf` the PDF from headless
  Chrome, Chromium or Edge. Without a browser it says so; print `_print.html` by hand (A4, no headers).

`--artifact` also writes a page for a hosted private link. Tell the user that only they can share that link.

An internal report that records a rebuttal holds the replies as posted, generated from the pasted files by
`scripts/posted_section.py` before each build, never copied by hand (`references/build.md`, section 5).

## 6. Where it is kept and what goes to co-authors

`references/delivery.md` has the folder sync, the message and the deposit procedure.

- **Every delivery message names the exact path** of the report folder, and the build copies the files there each
  round (only the figures the report uses).
- **Before sending co-authors files, open what they already use and match its type, granularity and count.** List
  their files with row counts and headers and write one line on what kind of thing each is (parameter table,
  dataset table with links, gene or feature list). Set the target count from them: "not more than 10-15 files".
  Stage through an explicit whitelist.
- **Tables and data are different things** ("tables are sth but data are sth else"): short reference tables in one
  place, large outputs (predictions, segmentations, checkpoints) in another, each with a manifest. No per-unit dumps
  in a table deposit and no README padding ("no readme no text just simple data").
- **What the paper shows equals what the files say.** Check every value in a deposited table against the figure or
  table it backs.
- **Each file is usable alone.** An output that holds only row indices into another table ships with that table.
- **A co-author dispute is answered who-is-right first**: the verdict, two or three bullets of evidence, other
  errors found, a reply of about four sentences ready to paste, the corrected text. A justification asked for "in
  chat" stays in chat until the user says yes to the file (`references/delivery.md`).
- **Figures a co-author will edit go as PNG, PDF and an SVG with live text** (`figure-development`), with a table of
  the plotted values beside each.

The delivery message, short enough for a phone: what is delivered with paths and sizes; whether it opens offline
and whether math is rendered; what changed, one line each; what needs their check or decision; what was not done or
is still running. No praise, no list of what is fine.

## 7. The defense report variant

When the report answers a challenge to the author's own metric, result or method. The analyses are
`integrity-audit`'s (section 11 there); this skill sets the document (`references/defence-variant.md`):

- **Restate the exact question at the top**, quoted from the challenge, and answer it first: yes or no, with "no
  reported value changes" where true.
- **Verdict on process first** (fixed before the comparison? applied to every method alike? regenerates from the
  code?), then a numbered list of text additions phrased "state more clearly" or "add this detail".
- **Evidence on known ground truth**: injected error at known doses, removal of the true errors against random
  removal. Rankings on the real outputs, never as rank changes under injected error.
- **Plain wording, every number kept.** `inflated`, `overstated`, `misreported`, `misspecified`, `conflated` and
  `hacky` are banned (`assets/banned_words.txt`, checked as whole words; a substring check flagged "assigned").
  Dropping a verb never drops the measured weakness.
- **Provenance in every label**: "our implementation of the recipe in paper X" against "the authors' package, run
  as coded", repeated in the TL;DR, the definition, every caption and the appendix.
- **Repository history in one appendix line**, with branch, commit and date.
- **Diplomatic risks go to the user before sending** (naming someone else's unpublished work; a bold box that reads as
  deflection). The user decides.

## 8. Review rounds

`references/review-rounds.md` has the briefs.

- **An outside reader**: one agent briefed as a co-author who knows the field and has never heard the internal terms
  (list them). It flags every unexplained term or number with a plain replacement.
- **Line edits return OLD to NEW pairs**, applied by a script that refuses a pair whose numbers, tags or TeX
  differ; then the `humanizer` skill on anything composed.
- **Freeze the file for each round** (record its md5), and check every finding against the source before applying
  it.

## 9. Check before anything is sent

In this order:

1. `build_report.py` ran without FAILED: no script, no outside request, every image inlined.
2. `check_report.py`: zero errors, each warning read and either fixed or kept with a reason. Report the main-text word count.
3. **Read every page of the PDF** (`--previews` writes one PNG per page and a contact sheet; use a fresh folder each
   round so stale pages are not reviewed), then every changed figure at full size.
4. **Re-verify every number and quote against the source files.** The reader will check every number: a last
   pass caught "all units, all datasets" where only some datasets had been checked.
5. Grep for phrases and figure numbers left from earlier versions.
6. Copy the files to the report folder, send the PDF with the HTML beside it, and say what was not checked.

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a glossary and a limits box at the top | "unnecessary and total AI slop" | terms defined where used |
| long text, about 4,100 words | "tooooo much text" | formulas, short boxes, captions, appendix; a word count per round |
| a bold paragraph set larger than the body | "bold font and so big for such a long text" | one short bold sentence at body size |
| a summary dense with internal counts | "no one will understand, write for someone that does not have the context" | three plain sentences |
| a separate figure folder, math from a CDN | "if I send it to my prof can [they] open with no problem?" | one offline HTML plus a PDF |
| "could not be used, so we built our own" | "really on point. cut to chase" | the concrete reason |
| two values side by side for one setting | "don't state it like that as if it's discrepancy" | the value actually run |
| "inflated", "misspecified" in the TL;DR | read as an admission of wrongdoing | "state more clearly", numbers kept |
| "published", "signed" as variant names | "make better names" | `<metric>_<source>` |
| figures that approximate the paper's | "soooooo claude" | the paper's own plotting code, true size |
| log axes on a score | "it looks like it only gives 2 values" | linear axis with a factor |
| caption fragments | "total AI slop" | full sentences |
| random gray, mixed font sizes | "so much AI slop style" | four sizes, one ink, one accent |
| dozens of per-panel CSVs for co-authors | "look at the type of [their] files" | a handful of reference tables matched to theirs |
| files only in scratch | "save them where I can find" | a project folder, path in every message |

## Reference files

- `references/report-shape.md`: the opening, sections, sentences, definitions, examples from two fields.
- `references/figures.md`: style, true size, numbering, captions, axes, figure QC.
- `references/build.md`: builder and checker options, MathJax and Chrome setup, fallbacks, the build loop, the
  posted-replies section, traps.
- `references/delivery.md`: the report folder, the delivery message, sharing and depositing files for co-authors.
- `references/defence-variant.md`: the document form of a report that answers a challenge.
- `references/review-rounds.md`: outside-reader and line-edit briefs, invariant checks, freezing a round.
