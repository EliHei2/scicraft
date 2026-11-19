---
name: ml-paper-writing
description: Writes, rewrites and checks machine-learning papers for venues such as NeurIPS, ICML and ICLR, from abstract to limitations and appendix. Use it whenever someone drafts or edits an ML method paper, its abstract, introduction, contributions, related work, method, experiments, results table, ablation table or limitations, or says "make this sound like a real ICLR paper", "this reads like AI", "we are over the page limit", "submission is Friday", "check the anonymity", even when the skill is not named. Holds the voice (claim, mechanism, at most one reason) and its hard bans, the preserve contract with scripts proving no number or citation moved, section shapes that held up, framing around the general data type, tables with raw values and stated spread, a terminology box, a house add-on that leaves the venue style untouched, page-limit fitting and an anonymity scan. Prefer paper-writing for the drafting loop, humanizer for general de-slop, rebuttal for replies to reviewers.
---

# ml-paper-writing

How to write a machine-learning conference paper so that its author submits it without rewriting it and a
reviewer finds nothing to query in its form. Distilled from a year of the author's ML papers: a
self-supervised point-set encoder paper, a foundation-model paper for an ICLR-style venue with its revision,
and the skill the author first wrote for this register. Each rule is something they asked for or threw out, with its
reason. Where the author of the paper at hand says otherwise, they win.

> **PRIME DIRECTIVE: every sentence states one claim about the general data type, with its mechanism or its
> number, in the paper's own terms, and nothing the venue or the author has already settled is changed.**
> The venue owns the template. The author owns their sentences. The records own the numbers.

The failure to fear is a paper that reads as generated: dashes, staged contrasts, slogan sentences,
"strongest", vague titles, results in the introduction, a ± nobody defined. A reviewer or the author spots it
in one paragraph and stops trusting the rest. The author called it "AI slop" and "such killer mistakes".

Three failures cost the most time. Guard against them from the first minute:

1. **Rewriting what was settled.** Changing the author's humanized sentences, re-titling their sections or
   touching the venue style. "keep text and style as I gave you, I worked hard to make it human, please
   change only if you must" (sections 3 and 7).
2. **Losing a fact in a style pass.** A dropped citation, a changed number, a deleted caveat. Edits for style
   are read for style, so these slip through by eye (section 3).
3. **Framing on the home application.** Writing about one dataset or domain instead of the data type, or
   claiming superiority before the method is introduced. The author's correction: the home domain is just
   an example (section 1).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The venue, its year and its style package**, downloaded from the official author guide; the page limit
  for that year; whether review is double-blind; the platform's PDF size limit.
- **The latest version of the manuscript.** Check which file is current before editing (a revision once
  started on an older draft that shared 15.6% of its sentences with the submitted one).
- **The records**: the result files and tables every number must come from. No number is typed from memory.
- **The author's own texts** and which parts they have already humanized (frozen, section 3).
- **One to three exemplar papers** they want the paper to resemble (section 9).
- **The terms**: the coined concept, the field's established terms, code names that must not reach the paper.
- **Identifying strings** for the anonymity scan (names, affiliations, project names), kept in a file outside
  the repository.

State the plan before any change wider than a sentence. Work on a copy: `cp main.tex main.before.tex`.

## 1. Frame around the general data type

Detail in `references/framing-and-terms.md`.

- **Define the data type first, by the conjunction of properties that makes it hard.** The application is one
  representative instance. A tabular foundation model is framed on tables (heterogeneous columns, no natural
  order, ten to ten million rows), not on the benchmark suite; a point-set encoder on irregular, nested
  point fields, not on the application it was built for.
- **Domain words only inside the domain section.** General sections say element, feature, region, group.
- **Never claim the method is better before it is introduced.** The introduction names the evaluation and
  reports no result.
- **State concrete novelties, each tied to the component that provides it.** When every part of the claim has
  prior work, claim the conjunction. Verify every "first" before the abstract is locked.
- **Do not straw-man the abstraction the field uses.** Claim what the representation keeps; never that the
  common unit is wrong.
- **Benchmark claims only where results exist.** Other domains are discussed, not claimed.
- **Theory goes to the appendix unless the main argument needs it.** A separation or optimality result
  without a complete proof is a conjecture, never a theorem. Every value in a worked example comes from a
  computation that was run: a theorem witness with made-up values was deleted on sight.

## 2. Voice and hard bans

The register of I-JEPA, GraphSAGE, Graphormer and DINO: declarative, concrete, motivation first. Detail,
cadence numbers and before/after pairs in `references/voice-and-bans.md`.

- **Claim, then mechanism, then at most one reason.** Justify only what would surprise a reader.
- **"We" for decisions, present tense for what the method does, past tense for what was observed.**
- **One idea per sentence, main verb in the first eight words.** Break sentences of three clauses or 60 words.
- **Move between sentences by repeating the noun**, not with "Moreover", "Furthermore", "Additionally".
- **Measured relations, never evaluative words.** "ranks first by mean rank", "is rated above X by Elo",
  "the highest-ranked published model". "strong or good or bad are not scientific".
- **Bound a claim in the sentence that makes it, and give the bound a cause** ("whereas models trained on
  single tables rank higher on their own task"). New text never uses `leads`, `wins` or `falls behind`
  (owner: `stats-reporting/references/vocabulary.md`); a sentence the author wrote with one and a named
  measure stays as written.
- **Define or cite every term, probe, test and statistic at first use.** "[N] methods of what?"
- **No sense verbs for models** ("sees", "knows"): "receives ... as input".

Hard bans, deleted on sight:

| Ban | Fix |
|---|---|
| em dash, spaced en dash (`---`, ` -- `) | comma, parentheses, two sentences; ranges keep `12--18` |
| "not X but Y", "X, not Y" as a habit; "X rather than Y" when Y was never a candidate or two sit back to back | state Y; "X rather than Y" with Y a real candidate stays, positive half first (owner: `humanizer`) |
| triads for rhythm, slogan sentences ("X is the point.") | the plain fact |
| filler openers (`Importantly`, `Notably`, `Note that`), `in order to` | delete; "to" |
| self-praise (`principled`, `elegant`, `powerful`, `novel`, `seamless`) | cut |
| vague magnitude where a number exists | the number |
| "couple" for more than two | bind, join |
| inline colons and semicolons in new prose | two sentences; a colon before a display stays (one or two per chapter may stay; see `humanizer`, T16) |
| `·`, `×`, pipes between phrases; daggers in tables | a comma; one caption sentence |
| code words (`w/o`, `A3`, `max_rows`) | human names (`−masking`, "the 12M model") |
| self-narration ("This section presents") | delete; one roadmap sentence per paper |

Run the `humanizer` skill after any pass that removed punctuation: a de-punctuation pass once welded clauses
together with "namely", "rather than", "so that".

## 3. The preserve contract

- **Change prose only.** Every `\cite`, `\ref`, `\cref`, `\eqref`, numbered equation, macro, defined symbol and
  number survives byte for byte. Never rename a citation key.
- **Prove it.** `preserve_diff.py BEFORE AFTER` compares the multisets of numbers, citation keys, labels and
  references, the equation count, duplicate sentences and the word count. A pass in this register lengthens
  the text by 3 to 5 percent; a shorter result usually means facts were lost.
- **The author's humanized text is frozen.** Change it only for an error, a number, a pointer, a hard limit
  or an explicit order, and list each change with its reason. Never re-title the author's sections.
- **In submitted text, punctuation fixes only.** Rewording belongs to the revision (the `rebuttal` skill marks
  it in one color).
- **Polish, do not rebuild.** One-sentence surgeries logged old to new. A three-hour multi-agent rebuild of a
  text the author had worked out was rejected as "super overwhelming".
- **One hand writes the prose**, so the paper keeps one voice even when other work fans out.
- **Gaps become `[AUTHOR ACTION: ...]` markers**, never invented content; close each against the records.

## 4. Section shapes

Templates with placeholders in `assets/paper_skeleton.tex`; full shapes and examples in
`references/shapes.md`.

| Section | Shape | It fails when |
|---|---|---|
| Abstract | world, measurement with a number, gap as what is lost, "We introduce [concept]", consequence, "we introduce [Model], a [noun] that [mechanism]", training, result with the comparison set named, its bound, one implication | it lists placements, or counts lack their class ("[N] methods") |
| Introduction | facts with numbers, what current models do and what it costs, the **bold question**, a 4 to 10 word verdict, the approach, the evaluation without results, **Our contributions.** | it reports results or claims superiority early |
| Contributions | one short paragraph each: "We introduce X, a <noun> that <does Y>" | adjectives stand in for mechanisms |
| Related work | bold run-in per family: who did what, what it leaves open | references are inflated |
| Method | one roadmap sentence at most; data type, concept, model, objective; losses and core operator in the main text | it names datasets or carries unused math |
| Experiments | run-in paragraphs **Pretraining data**, **Tasks**, **Comparators**, **Protocol**, then one per result | a task lacks its label source, split or metric |
| Results paragraph | "<subject> <measured relation>, <value> against <value> for <comparator>, <who that is> (Table N)", then the conditions it survives | it uses "leads", "wins", "falls behind" |
| Limitations | "[Model] is a first step toward [concept], and several limitations remain.", each with its cause, next steps, "Finally, ..." | it apologizes or hedges with a straw man |
| Appendix | data and licenses, figures, referenced math, model details, pretraining, transfer experiments, ablation protocol | a detail top papers report is missing |

Captions open with a bold claim sentence, then one protocol sentence, then lettered panels; every encoding
is named. Headings are concrete noun phrases in the paper's terms, with no colon, question or invented count
(a heading of the shape "Three faces of sparsity" was rejected).

## 5. Terms and the terminology box

- **One name per thing, the field's established term over an invented one**, used in prose, captions, tables,
  figures and replies. Ask the author to choose between plausible terms, recommendation first.
- **A rename reaches every variant**; a half-converted sweep is worse than none.
- **The coined concept in italic at its introduction**, in full every time after.
- **A terminology box** defines the application's terms once for ML readers: one bold term and one sentence
  each, at most six (`\begin{terminology}` in `assets/ml_addon.tex`).
- **A glossary maps code names to paper names**; grep the manuscript for the code side before hand-over.

## 6. Tables

The `ml-evaluation` skill computes the numbers; `references/tables.md` sets them.

- **One main results table with all tasks and all methods**; detail tables in the appendix.
- **Rows grouped by family with italic group rows**, the proposed method last as "(ours)"; columns named as
  tasks a stranger can read.
- **Raw metric values with their spread, and the caption says what ± is** ("mean over 5 seeds followed by the
  standard deviation across seeds"). Never normalize away the units.
- **Column definitions under the table or in the caption**: data, label source, split, probe, metric,
  direction, in standard terms.
- **One checkpoint per model size**, chosen by one fixed rule stated in the appendix. Own ablations and older
  versions stay out of the leaderboard.
- **Ablations**: one change per row against a matched, trained control; labels "−component", at most four
  words; the caption says what each change does to the model.
- **Bold and underline declared in the caption**; asterisks for significance after the correction; no
  daggers, crosses or red.
- **A companion data table beside the results table**: pretraining corpus rows, a rule, evaluation rows;
  totals in bold in "Billion" and "Million"; the total seen by the shipped model.
- **Tables are generated from records**, never typed (`latex-typesetting` has the generator).

Integrity: choosing what to lead with is presentation; changing what the records support is misreporting.
A weak or mixed result stays in the record with its number, in the main table if it belongs to the task set,
in the appendix otherwise. A threshold for what is printed applies to every row alike and is stated. A
setting that differs is stated where the result is.

## 7. The venue style and the house add-on

- **Never touch the venue's style file.** No `geometry`, no font-size change, no geometry switch, no edits to
  the `.sty`. The author's pre-submission verdict file called such changes reject-level.
- **A house add-on owns only what the venue leaves open**: one accent color for links and callout rules, the
  contributions and terminology callouts, table helpers, run-in heads, main-text display tightening.
  `assets/ml_addon.tex` is loaded after the venue package:

  ```latex
  \usepackage{[venue]_conference,times}   % the venue's package, unmodified
  \input{ml_addon}
  ```

- **Macros for every method name and recurring operator**, so a rename is one line.
- **Typography beyond this** (preprint fonts, shims for a minimal TeX, print variants, the build gate) is the
  `latex-typesetting` skill. The free-form Palatino preamble of the original skill applies to preprints only.

## 8. Page limit and anonymity

Detail in `references/venue-and-submission.md`.

- **Measure the overrun before cutting.** `\label{mainend}` after the last counted sentence, then
  `page_budget.py` reports its page, words per section and the overrun in words (820 words per full
  ICLR-style page; measure your venue).
- **Moves, in order**: detail to the appendix with a pointer; cut words by the voice rules, never facts;
  `\tightenmaindisplays` in the main text only; small figures beside their paragraph at 0.43 to 0.46
  `\linewidth`; run-in heads; wide figures overhang right only, never the line-number margin.
- **Never shrink fonts, margins or figure labels.**
- **Anonymity**: anonymous author block, final switch off, no acknowledgements or funding, own work cited in
  the third person, unpublished own work never cited as evidence, anonymous code links, no names in PDF
  metadata or in the text layer of figure PDFs. `anon_check.py` scans sources, PDF and figures.
- **Review the paper as the venue's referee before submission**, from `assets/self_review_template.md`:
  issues ranked P1 (would sink the paper), P2, P3, each with one action; a novelty table against the three
  closest papers; venue fit; scores on the venue's form; the single most valuable action. Fix every P1
  before anything cosmetic.

## 9. Follow a named exemplar

Detail in `references/exemplars.md`.

- **Name the exemplar instead of describing taste.** Voice from I-JEPA, GraphSAGE and DINO; detail level from
  the most-cited papers of the venue in the last three years; typesetting from one to three recent accepted
  papers at the venue, measured from their source.
- **Record what was copied** at the top of the add-on, with each deviation justified. The venue style still
  wins.
- **When output looks wrong, compare it with the exemplar side by side** before changing anything else.

## 10. Scripts

Python 3.9 or later, standard library only. `pdfinfo` and `pdftotext` (poppler) are used when present.

| Script | Does |
|---|---|
| `ml_paper_check.py` | bans, separators, daggers, headings, numbers in the introduction, missing contributions, `w/o` and undefined ± in tables, code words, markers; `--self-test` proves every check fires |
| `preserve_diff.py` | numbers, citation keys, labels, references, equations, duplicates and length before and after a pass |
| `anon_check.py` | author block, final switch, acknowledgements, first-person self-reference, identifying links, names in sources, PDF text, metadata and figure text layers |
| `page_budget.py` | page of `\label{mainend}` against the limit, words per section, overrun in words |
| `textprep.py` | shared prose extraction used by `preserve_diff.py` |

```bash
S=<skill>/scripts
python3 $S/ml_paper_check.py main.tex
python3 $S/preserve_diff.py main.before.tex main.tex
python3 $S/anon_check.py . --pdf build/main.pdf --figures figures --names ~/private/names.txt
python3 $S/page_budget.py build/main.aux --limit 9 --tex main.tex --pdf build/main.pdf
```

## 11. Check before anything is handed over

1. `ml_paper_check.py`: zero FAIL; every warning read and either fixed or explained.
2. `preserve_diff.py` against the snapshot: no number, key, label or equation moved.
3. Full build, then gate on the log: zero errors, zero undefined references or citations, zero overfull
   boxes, every font embedded, PDF under the platform limit (`latex-typesetting`).
4. `page_budget.py`: the main text ends on or before the limit.
5. `anon_check.py` for a blind submission, with the names file.
6. Diff the venue `.sty` against the downloaded original: identical.
7. Render the pages and look: tables, callouts, floats next to their text, no one-word last lines.
8. Read the whole paper once yourself, top to bottom, for self-narration and term drift; slice readers miss
   both.
9. Report: files and paths, what changed (one line per section, in the author's terms), what you decided on
   your own, what needs the author's word (`[AUTHOR ACTION]` markers, guessed readings), and what was not
   checked.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| `--` and em dashes | "drop `--` ai signature!" | commas, parentheses, two sentences |
| "not X but Y" | "write like a human, look up top LeCun or Bengio or Leskovec papers" | Y stated plainly |
| vague section titles | "these titles are super non-scientific" | concrete noun phrases |
| results in the introduction | "no results in the introduction, just mention what is our evaluation" | the evaluation protocol, cited |
| superiority before the method | "such killer mistakes" | the method first, the claim in the experiments |
| "strongest", "wins" | "strong or good or bad are not scientific" | measured relations |
| an undefined probe | "every single thing should be clearly introduced, or cited" | definition or citation at first use |
| "[N] methods" | "[N] methods of what?" | the count with its classes |
| daggers in an ablation table | "clear AI slop flag" | uniform settings, one caption sentence |
| `·` between phrases | "please never use AI slop like `·` in between things" | a comma or a sentence |
| inline colons and semicolons in new text | "drop extreme use of `--` and inline `:` and `;`" | two sentences |
| an unlabeled ± | "add in the table what's the +- (for real, what is it?)" | the spread named in the caption |
| normalized scores | "give me the actual values of the metrics computed" | raw values |
| "floor", "ms/cell" | "use standard terms, and give proper definitions in the captions" | column definitions |
| many checkpoints in the leaderboard | "only have rep (best checkpoint) per s/b/m" | one per size, by a stated rule |
| "couple" for four | "couple is for 2" | bind, join |
| the home domain as the frame | "it's just an example" | the general data type |
| a rewritten, humanized text | "you really butchered my beautiful text" | one-sentence surgeries |
| a Word-like look | "the font looks like word" | the official venue style plus a small add-on |

## Reference files

- `references/voice-and-bans.md`: positive rules, cadence, the ban table, neutral before/after pairs, the
  preserve contract, verification commands.
- `references/shapes.md`: abstract, introduction, contributions, terminology box, related work, method,
  experiments, results, ablations, limitations, appendix order, captions, headings.
- `references/framing-and-terms.md`: the general data type, novelty claims, one name per thing, code names.
- `references/tables.md`: main results table, column definitions, spread, checkpoints, ablations, marks,
  LaTeX recipe, integrity.
- `references/venue-and-submission.md`: venue style, the add-on, macros, versions, page fitting, anonymity,
  the build.
- `references/exemplars.md`: choosing and copying a named exemplar.
- `assets/ml_addon.tex`: the house add-on. `assets/paper_skeleton.tex` and `assets/refs.bib`: a compiling
  skeleton with every shape. `assets/self_review_template.md`: the referee self-review, filled before
  submission.
