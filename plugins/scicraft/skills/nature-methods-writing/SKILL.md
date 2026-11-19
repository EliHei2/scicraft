---
name: nature-methods-writing
description: Writes, restructures and de-slops the Online Methods and Supplementary Notes of a paper for a Nature-family journal, and applies the same discipline to any methods section or supplement. Use it whenever someone drafts or rewrites Methods, merges Methods with Notes, or says "reviewers said it reads like a README", "the methods are bloated", "this reads like AI", "the same dataset is described three times", "Methods is 14 pages, the limit is 10" or "resubmission Friday, fix the Methods", even unnamed. Holds the five laws (one checkable fact per sentence, say it once, method split from data), the register firewall (no code-font identifiers, no figure callouts, big tables to the supplement, no results), the fact inventory and its check, the dataset-by-analysis matrix, settings stated as run, closing sections, the reporting checklist, page-budget moves and two scripts. Prefer humanizer for sentence-level de-slop, integrity-audit to audit claims against code, ml-paper-writing for conference papers.
---

# nature-methods-writing

How to write the Methods of a computational method paper so that a reviewer reads it as a protocol: every
sentence carries a checkable fact, the method is separate from the data, each dataset's handling is stated once,
and every value is the one that was run. Distilled from the author's rounds of writing, merging, cutting and
fact-checking the Online Methods and Supplementary Notes of a method paper for a Nature-family journal, including
an audit of that text against the code and run records. Where the author of the paper at hand says otherwise,
they win; write their rule down and follow it.

> **PRIME DIRECTIVE: every sentence in Methods states a fact a reader can check, in one place only, with the
> value that was actually run.** A sentence with no fact goes. A fact stated twice keeps one home. A value the
> records do not support becomes an author action, never a guess.

Three failures cost the most time. Guard against them from the first minute:

1. **Losing or changing a fact in a restructure.** Merges and de-slop passes drop numbers that no one misses until
   a reviewer does. In one merge, a numeric diff caught two facts that lived only in deleted text. Inventory first,
   check last (sections 4 and 9).
2. **Writing a README or a figure tour.** Code-font identifiers, "as shown in Fig. 3", a hyperparameter grid and a
   sentence that the method "outperforms" the baselines turn Methods into a lab dump. The register firewall
   (section 2) blocks all four.
3. **Text that disagrees with the records.** Stating a function default as the setting, framing a run value as "[k]
   vs [j]", copying a stale configuration example. The author's words on the supplement: "From the supplementary,
   it should be reproducible. That's the point." Section 3 states every setting as run.

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The text**: the current Methods, the Supplementary Notes, the main text's own Methods paragraph, and the
  latest version the author accepted (never an earlier draft from the chat).
- **The main text**: its terms win everywhere, and its Results decide where a moved result goes.
- **The records behind every value**: the configuration written by the launcher at run time, recorded command
  lines and logs, the environment file with versions, the commit of the code that produced the numbers, the
  data accessions. A configuration example, a function default or an older draft is not a record.
- **The venue and its limits**: the journal, page budgets for Methods and supplement, whether a Reporting Summary
  applies.
- **The form**: LaTeX or Word, one continuous document or two, who else edits the file, what may not change
  (frozen sections, co-authors' wording).
- **The scope of the request**: a full restructure, a merge with minimal change of wording, or a fix of named
  facts only. A minimal-change request gets a copy with only those changes.

## 1. The five laws

Apply them to every sentence. Detail and before-and-after pairs: `references/laws-and-firewall.md` section 1.

1. **One checkable fact per sentence**: a value, a version, a threshold, an n, a named procedure or an equation.
   A sentence without one is cut.
2. **Justify only the non-obvious, once.** State the procedure and the value. Add one empirical clause only where
   a choice would surprise a reader. The author's instruction: "no philosophy or justification".
3. **Say it once.** Each definition, caveat, threshold and equation has one home; everywhere else refers to it by
   section or equation number.
4. **Hard split between method and data.** The model, training and inference sections contain no dataset name
   and no dataset-specific number. All data handling is in one Datasets and preprocessing block, with a stable
   short ID per dataset.
5. **Equations for math, parameters in a block or a Supplementary Table.** Each equation is stated once and
   numbered; the combined objective is one weighted sum with its weights. A large parameter table goes to the
   Supplementary Tables.

## 2. The register firewall

Nature's Online Methods are prose and numbered equations. Three rules separate the Methods chapter from the
Supplementary Notes, which are exempt (`references/laws-and-firewall.md` section 2):

- **R1. No code-font internal identifiers in Methods.** Write "64 bins per numeric feature", never `n_bins = 64`. The
  litmus test: if a name exists only inside your repository, it does not appear in Methods. Code font is kept for
  an invoked external library function (`sklearn.model_selection.StratifiedKFold`). Internal names go once to a
  Software implementation Note with a glossary. Your own repository or package name is replaced by a descriptive
  phrase ("the benchmark code") and pinned once, with version and DOI, in Code availability.
- **R2. No figure callouts in Methods.** No "Fig. 2a", no "Extended Data Fig. 3". Refer to sections, numbered
  equations and Supplementary Tables, and name an analysis by what it is ("mention them in terms of the analysis
  we did").
- **R3. Big tables go to the Supplementary Tables.** Hyperparameter grids, metric definitions, dataset
  inventories, notation and software versions move out and are cited. One compact configuration block for the
  defaults is the only exception. Drop the rationale column when moving a parameter table.
- **No results in Methods or Notes.** No score, rank, win or P value for the method being introduced. A result
  sentence found in Methods is moved to Results and reported to the author, never deleted silently. Published
  facts about other tools are background and may stay.
- **No document narration.** At most one orientation paragraph. No `This section describes`, no `is the single
  source for`.

## 3. State each setting as the value actually run

- **Read the value from the run records** (launch-time configuration, recorded command line, the benchmark's build
  script) and write it plainly, once: "a weight decay of 0.05". Defaults can come from class signatures while a
  shipped `config.yaml` is a stale example; check the call site, which may pass a value that differs from the
  function default.
- **Never frame a setting as a discrepancy** ("0.01 in the code default versus 0.05 in our runs"). The author
  rejected the "[k] vs [j]" framing twice: the reader needs the protocol, not the repository's history. A default
  that explains someone's failed rerun goes to the software Note as an instruction.
- **A setting that differs from the method's default is reported in the analysis that used it**, in the matrix
  row and the per-analysis prose.
- **When text and records disagree**, fix the text to the records or raise an author action. Wording may
  simplify; the records must still support it. If asked to describe a run as something the records contradict,
  state what the records show and ask whether to rerun or to change the text. Do not write it as asked.
- **A reimplemented method or metric** is marked "adapted from [ref]" with the reason (no code cited, or code that
  disagrees with the paper) and the list of differences.
- **Each metric in a suite gets one sentence on why it is not redundant**: the failure it catches that no other
  metric in the suite catches. The author asked, of a metrics Note, "for each metric, justify it a bit more ... and
  that it's not redundant". Where metrics measure on different geometry or subsets (a predicted mask, its convex
  hull or a fitted ellipse in segmentation, the full test set or a filtered subset in ML), name the one each
  uses, because a reader who reimplements the metric on the wrong one gets a different number.

## 4. The workflow

Detail for every step: `references/workflow.md`.

1. **Fact inventory.** Extract every value, version, threshold, n, equation, citation and accession from the
   sources, and add the values that live only in the records.
   `python3 scripts/fact_inventory.py old_methods.tex old_notes.tex --out facts.tsv`
2. **One home per fact.** Fill the `home` column or write an ownership table: Methods owns the formal model and
   its values; the software Note owns code layout, files and identifiers; Datasets and preprocessing owns
   per-dataset values; the Notes own derivations and extended rationale.
3. **Draft** with the five laws: problem framing in one paragraph without dataset names, numbered algorithm
   steps, one sentence listing the settings a user can change, "we" for decisions and the passive for procedure.
4. **Build the dataset-by-analysis matrix** (section 5) and cut the per-analysis prose to deltas.
5. **Humanizer pass.** Mandatory after any restructure or de-punctuation, because removing semicolons and colons
   welds clauses back together with `namely`, `rather than` and `so that`. Use the `humanizer` skill's technical
   register; read the whole document yourself for self-narration, which slice readers miss.
6. **Self-review.**
   `python3 scripts/fact_inventory.py old_methods.tex old_notes.tex --check new_supplement.tex` must lose
   nothing that is not accounted for, and `python3 scripts/methods_lint.py new_supplement.tex` must report no
   ERROR. Then read for sentences without facts and caveats repeated in other words. For a procedure the numbers
   depend on, run the regenerate-from-text test: a fresh agent implements it from the Methods alone and its output
   is compared with the reported values.
7. **Author-action markers, closed against the records.** Anything unverifiable becomes
   `\authoraction{B01}{...}` (`assets/authoraction.tex`) or, in Markdown or Word, `FILL IN (B01): ...`, never a
   guess. Then close each marker against the repository at the commit the paper names, the run logs and the data
   tables. The ones that survive are the author's decisions.

For a long supplement, give each section a drafter and a read-only fact auditor working from the ground truth.
When replacing part of a long file, draft in scratch, compile in a stub document, and splice with an md5 guard
(`references/workflow.md` section 8). A reviewer-grade audit of a finished supplement belongs to the
`integrity-audit` skill.

## 5. The dataset-by-analysis matrix

When one dataset is reused across analyses with different references, subsets or settings, prose cannot keep the
uses apart.

- **Give each dataset a stable short ID**, defined once in Datasets and preprocessing.
- **One row per (dataset, analysis) pair**, with columns for input and filters, configuration as a change from the
  default, and **the two reference roles in separate columns**: the reference that labels or scores the outputs,
  and the reference that enters the model (prior, initialization, pretraining data).
- **Shared preprocessing once, above the matrix.** The author's words: "summarize this before and not simply
  repeat for each dataset separately". Per-analysis prose states only what differs.
- **Every cell is a value from the run records**; a cell the records cannot fill gets an author action.

Machine-learning example: rows are (benchmark, analysis) pairs such as main comparison, ablation and scaling;
role 1 is the evaluation labels and metric, role 2 any pretraining or tuning data that touches the model.
Biology example: rows are (tissue section, analysis) pairs; role 1 is the cell-typing reference, role 2 the
reference that initializes the model's prior. Template: `assets/dataset-analysis-matrix.tex`.

## 6. Structure and closing sections

- **Default to self-contained Methods with a supplement of figures and tables**, the dominant pattern in about 50
  Nature-family method papers surveyed. Thin Methods with long numbered Supplementary Methods is for systems of
  AlphaFold's scale. Notes grow with downstream tasks and ablations, not with model size.
- **Order**: overview, model or graph construction, architecture, losses, training, inference, modeling choices,
  evaluation and metrics, datasets and preprocessing, the per-analysis matrix, settings used for other methods,
  then the closing sections. Datasets always stay in Methods.
- **Closing sections, mandatory**: Statistics and reproducibility, Data availability, Code availability, and the
  Reporting summary pointer. Template: `assets/closing-sections.tex`.
- **One continuous document** when the author keeps one. The author rejected a split into Online Methods and
  Supplementary Notes parts twice ("all should be one thing"). Each topic's procedure and its extended protocol
  then share a section. Ask before splitting or merging.

Skeleton, boundary table and variants: `references/structure.md`.

## 7. Reporting checklist

Answer every item, the negative ones too (`references/reporting-checklist.md`):

- exact n and what it counts, the test and its sidedness, the statistic, the spread, the correction, exact P for
  significant and non-significant results, the statistical unit per analysis;
- every package with its version, seeds and stochastic steps, compute (hardware, memory, runtime), settings used
  for other methods with versions checked against commits;
- sample-size rationale or "No statistical method was used to predetermine sample size", exclusions,
  randomization and blinding or why they do not apply;
- every accession checked to be the exact dataset used, as a plain URL; code archived with a DOI, its version and
  an OSI license (a bare GitHub link is not enough).

## 8. Page budgets

A budget is met by relocating and de-slopping, never by dropping a fact needed to reproduce a result. The budgets
the author set once were Methods under 10 pages, Notes under 30, total under 40; Methods later went to under 15
when the data-analysis recipes moved back in. What must stay, in the author's words: "details, software versions, params,
threshold, filtering details". Moves that worked, largest gain first: tighter `titlesec` heading spacing; dropping
rationale columns; wet-lab, imaging and secondary diagnostics to the Notes; about three top-level sections with a
subsection only above half a page; run-in paragraph heads turned into prose. Margins and line spread barely move
the Methods count. Report the page count from the built PDF (`references/structure.md` section 6).

## 9. Words

- **The manuscript's terms win**: main text, then main figures, then tables, then supplement. Coin nothing, and
  sweep every derived form when a term changes ("a half-converted sweep is worse than none").
- **No contest words in a two-way comparison** (`runner-up`, `winner`, `arm`, `competing method`). Tie a short
  figure label to its definition at first use. Define the unit of every quantity and the source of every set.
- **One contrast rule**: "not X but Y", "X, not Y" and "X rather than Y" are all staged contrasts. Keep one only
  when the negated half is an alternative the reader holds, at most one per section, named concretely.
- **House punctuation** in new or edited prose: no em or en dashes, no prose semicolons, no colon in the middle of
  a sentence (one or two per chapter may stay; see `humanizer`, T16). A colon before a display or a list is fine.
- **Revising the author's own text is a minimal diff**: keep their words, fix the facts they named ("keep the
  wording of the tex file as intact as possible").

The general and technical de-slop patterns are in the `humanizer` skill; the Methods-specific items are in
`references/laws-and-firewall.md` sections 4 and 5.

## 10. Check before handing over

In this order:

1. `python3 scripts/fact_inventory.py SOURCES --check DRAFT`: no lost item, or each one named in the report with
   where it went or why the records overrule it.
2. `python3 scripts/methods_lint.py DRAFT --datasets "IDS" --internal "REPO,PACKAGE" --allow-code "LIB."`: zero
   ERROR. Read every WARN. Use `--final` for the submission build, which fails on open markers.
3. Build the document twice through bibtex; the log has no undefined citation or reference and no `^!` line.
   Render the changed pages and look at them.
4. Read the whole Methods once, start to end, for self-narration, repeated caveats, terms that drift and sentences
   without a fact.
5. Trace every changed value to its record, and every remaining author action to a reason.
6. Say what was not checked: a procedure not regenerated from the text, links not opened, a build not run.

Report, short enough to read on a phone: files written; what moved where (results to Results, tables to
Supplementary Tables, identifiers to the software Note); values changed to match the records, with the record;
open author actions; what was not done.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a setting framed as "[k] vs [j]" | "as if it's [a] discrepancy" | the value run, stated once |
| Methods and Notes as two `\part`s | "all should be one thing" | one continuous document |
| justification on every line | "no philosophy or justification" | procedure and value; one clause where surprising |
| `load-bearing` and its kind | named twice as AI slop; "use proper human researcher language" | the plain fact |
| dashes, inline colons and semicolons, not-X-but-Y | "it's not a comercial work" | commas, full stops, the positive statement |
| coined terms (`footprint`, `programme`, `lineage`) | "use the terminology in the main text of paper" | the manuscript's term, swept everywhere |
| per-dataset preprocessing repeated in every analysis | "summarize this before and not simply repeat" | shared steps once, the matrix, deltas |
| analyses named by figure number | "mention them in terms of the analysis we did" | the analysis by name |
| a vague reason ("could not be used, so we built our own") | "cut to chase, really less is more" | the direct reason ("the paper cites no code") |
| a rewrite of text the author had polished | "keep the wording of the tex file as intact as possible" | a minimal diff of the named facts |
| 73 per-panel CSV files as supplementary tables | "not more than 10-15 files" | short reference tables |
| a Word file regenerated from LaTeX | "math is in tex and not proper in docx" | in-place XML edit; equation objects kept as the file has them |
| `AUTHOR ACTION` tags in co-author prose | "FILL IN, not AUTHOR ACTION" | `FILL IN (B01): ...`, the same ID in `AUTHOR_ACTIONS.md` |
| "X rather than Y" rewritten as "X, not Y" (this skill's older advice) | | both treated as staged contrast |

## Reference files

- `references/laws-and-firewall.md`: the five laws and the firewall with before-and-after pairs, settings as run,
  Methods-specific words and terms, the contrast and punctuation rules.
- `references/workflow.md`: each workflow step in detail, the ownership table, the matrix, splicing into a long
  file, fanning out, revising the author's text, Word files, the report.
- `references/structure.md`: archetypes, the default skeleton, the boundary table, one continuous document,
  closing sections, page-budget moves, other venues.
- `references/reporting-checklist.md`: the Reporting Summary items, reproducibility, study design, availability.
- `references/exemplars.md`: eight public method papers, what each is a template for, and the governing Nature
  documents.

Scripts (Python 3.9 or later, standard library only; run from the skill folder or by path):

- `scripts/methods_lint.py`: the register firewall, dashes and house punctuation, register words, repeated
  sentences and equations, open markers, closing sections, Code availability without a DOI.
- `scripts/fact_inventory.py`: the fact inventory as TSV, `--check` against a draft, `--homes` for values stated
  in more than one section.

Assets: `assets/dataset-analysis-matrix.tex` (needs booktabs, longtable, array), `assets/closing-sections.tex`,
`assets/authoraction.tex`.
