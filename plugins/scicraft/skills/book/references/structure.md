# Structure, spine and density

How a book built from the author's papers is laid out, how the projects connect, and how long it gets. Every
rule here was set by the author after a structure was rejected.

## The outline that held

```
Front matter (the publisher's order, see front-matter.md)
1  Introduction            the field, the problem, the approach, research questions; no results
2  Project A               one chapter per project, each with the same implicit arc
3  Project B
4  Project C               an extension of a project is a section of its chapter, never its own chapter
5  Discussion              strong, concrete, from the papers' own Discussions
Appendices A to C          one per project: parameters, schedules, preprocessing, implementation-only boxes
Bibliography
```

What was rejected on the way, in order: a 443-page structure with invented background chapters; a 50-page
skeleton ("this is a muscle!!!"); parts I to VI; one part per chapter; a two-part grouping copied from an exemplar
("not a meaningful grouping"); one project split over three chapters while another had one ("unify this");
an extension of a project as its own chapter ("be normal!"). The final form is the outline above.

- **Parts only when the grouping means something.** Copying an exemplar's grouping does not justify it; the content
  has to. When in doubt, drop the parts.
- **Symmetric chapters.** Every project gets one chapter with sections and subsections inside it. If one project
  is a chapter, all are.
- **A background chapter is dissolved** into each project's related-work section, where it serves a question.

## The implicit arc inside each project chapter

The order of a research paper, with headings that name the content and never the role:

| Step | Holds | Example heading for an ML project |
|---|---|---|
| 1 Problem statement and setup | the scientific problem as the paper's introduction states it; the experiment that frames the work when one does | "Prediction on small tables without retraining" |
| 2 Background and related work | a literature review of what one could have done, by method family, each with what it does | "Gradient-boosted trees, meta-learned priors and in-context learners" |
| 3 Problem formulation and method | the formal problem, the method in the paper's notation, small algorithm boxes | "A transformer trained on synthetic tables for in-context prediction" |
| 4 Experimental setup | data, splits, baselines, metrics | "Benchmark suites, splits and compared methods" |
| 5 Results in the paper's order | one text unit per figure, opening with that figure's message | "Accuracy against tuned baselines across suites" |
| 6 Conclusions, limitations, future work | measured fact first, limitations from the paper's own Discussion | "What the benchmark settles and what it leaves open" |

- **Headings name objects, data and methods.** "Problem statement", "Background" and "Results" as literal labels
  were rejected ("drop from title literal namings like background ... but make it implicitly obvious"). An
  instance of the accepted kind (illustrative): "The cost of tuning a model for every dataset". Rejected kinds,
  in stand-in wording with the author's reaction: "tuning as an inference problem" ("I don't know exactly what
  that means"), "reusable computation" ("just say reusable features or reusable representations"), "three views
  of one table" ("literally mention it"), "Five block types and one shared index" ("AI slop"). No colons, no questions, no math in
  headings. Spell out abbreviations in headings, contents and list-of-figures entries.
- **The paper's key noun goes into the headings.** If the paper is a benchmark, "benchmark" and "metrics" appear.
- **A section under about a page** merges into its neighbor or becomes a `\paragraph{}` run-in head. Print the
  outline with the page span of each section from the `.toc` before deciding.
- **Sectioning stops at x.y.** A fourth level (`\subsubsection` with numbering off) is typographically
  indistinguishable from the level above and buys nothing.
- **Heading sizes never invert between levels.** Copy the hierarchy of the exemplar book.
- **A heading pass** (four agents by chapter group in the source work, prose untouched): print the outline with
  page spans, extract the source papers' section headings as a reference, follow their order but word every
  heading afresh, because a copied heading counts as overlap in a similarity check. The concreteness rule holds at
  every level, run-in heads included. After the pass the `\label` count must match the last commit, and
  `chapter_drift.py --structure` must show the prose unchanged apart from the headings. Running heads fit one line.
- **Algorithm boxes are small**, about five steps, checked line by line against the code and the paper, or
  dropped. Name an algorithm by what the code implements: a method named after a published algorithm whose state
  variables the code does not have was renamed to "resembles X".
- **Boxes.** The latest decision (the final line-edit brief and its delivery checks): a contribution box (a
  left-rule box) after each chapter's opening paragraph, and no take-home or conclusion boxes in a book built from papers.
  Generated conclusion boxes drew "what kind of ... is this??"; take-homes that were kept for a while quoted the
  papers' result headings, never the agent's own lines, and were removed at the end as repetitive. Other long
  documents may use a takeaway box quoted from the source paper, never generated.
- **Results chapters are organized around their figures.** Each figure gets a paragraph (or a subsection) that
  opens with its message, taken from the paper and its supplementary notes, and cites panel letters ("Fig. 4.1b").

## The spine that connects the projects

A book of several papers needs one argument that makes each project the next step. The field-neutral form of
the spine that held:

1. a recurring analysis is rebuilt by hand for every study;
2. shared infrastructure and expert hand-crafted analysis show its value and its cost;
3. a reusable model for one recurring operation;
4. a reusable general representation;
5. what stays open.

For a machine-learning book the same shape reads, for example: hand-tuned pipelines per dataset, a shared
benchmark that exposes their cost, a model for one operation (say, imputation), a pretrained representation
reused across tasks, open problems.

- **Each project paragraph in the Introduction and Summary says what is different and the author's role.**
- **Projects never appear out of nowhere.** Introduce each through the problem that led to it and the people the
  author joined: the problem met, then the group, then the project. Where the author asks for it, give years and
  each collaborator's main institution only (never department lines: "you overdid"). Keep the science science.
- **Keep separate works separate.** Two contributions of different kinds go in separate chapters, and passages that
  lump them as shared motivation are removed ("not the same class, separate"). Each chapter ends on its own paper's
  point.
- **Say what the instrument records, then what the pipeline infers.** Describe a modality by its raw measurement
  (molecules with positions, spectra, reads, logged events, stain images), never by a unit a later step derived
  from it (cells, peaks, genes, sessions). Name the step that produced the derived unit and cite the vendor's or
  the field's default pipeline for it, so the reader sees that the table every analysis starts from is the output
  of an imperfect inference. A "cells by genes" description of a subcellular measurement was rejected as
  hand-waving.
- **Frame the field before the instrument or platform.** Lead with the scientific domain; introduce the
  measurement as the best current means with its concrete advantages and a named comparator.
- **Say the general category first and the specific instance second** ("the finest-scale measurement, which on
  this platform is each detected molecule").
- **Do not straw-man the coarser abstraction.** "Transcript is the finest!", not "the cell is the wrong unit". The
  argument is that pooling into a predefined unit before learning loses information, and that the unit can be
  chosen at query time. ML form: a row-level representation keeps the finest resolution and leaves aggregation to
  the user; it does not prove that group-level models are wrong.

## Contribution first

- **A chapter is about what the author did.** Chapters allocated by the paper's section order buried the
  author's share ("point is my contribution ... just connect it lightly to others"). Center the chapter on the
  author's credited analysis and give the rest of the paper one background section.
- **Exception for a framework or resource paper:** the chapter is about the framework, and the author's
  analysis is the demonstration of where its tools are used.
- **For a collaboration**, state (a) the main project's aim and team, (b) the author's role plainly in the
  opening and wherever the work appears, (c) the author's contribution step by step with each step's purpose.
  A chapter on a collaboration that grew toward the collaborators' results (1.7k to 3.2k words) was cut back to
  the author's share.
- **The Summary carries the spine**, the main experiments and conclusions taken from the papers' result section
  titles, and no single result numbers. Honesty qualifiers stay ("while dedicated models remained stronger on
  several endpoints").

## The Introduction and the Discussion

- **The Introduction reports no results of the author's own studies.** Keep the background, the problem told
  through mechanisms cited from the literature, the approach, data descriptions (corpus size) and the research
  questions, with forward pointers ("Chapter 4 tests this with a benchmark of ..."). A problem-illustration figure
  may stay with a neutral title. `book_checks.py --intro` flags result verbs.
- **State the scope once, early: the data type the book treats, then what carries over.** For example, "the
  methods target one assay type; most of them, and most of the challenges, apply to the wider class of spatially
  resolved measurements" (ML form: "the models target small tabular datasets; the evaluation protocol applies to
  any supervised benchmark"). The author asked for this after the Introduction read as if it covered only one
  platform. The scope sentence promises no result.
- **Rewriting an Introduction with a writer agent** (the third attempt, the one that held): the agent drafts in
  scratch and returns the draft, a claims file (each claim with its source file:line) and a figure plan that uses
  only existing figures. The coordinator merges the author's own opening verbatim, then compares draft and current
  text for labels kept and missing, citation keys, house bans and new numbers (`chapter_drift.py --structure`,
  `book_checks.py`) before installing. After installing, fix cross-references in the other chapters, build, look
  at a contact sheet, then run the result-verb check.
- **Openings come from the papers.** No vignettes, field-of-view scene setting or rhetorical devices; one such
  opener, prescribed by the agent's own decisions file, drew "the most stupid way of beginning". The first
  paragraph of the book is a gist of the whole book, at the level of a field; fixing on one example drew
  about fifteen rejections in a day.
- **The Discussion ends strong and concrete.** Anchor on each paper's own Discussion. Limitations restate and
  expand those Discussions and add only the obvious. State the field's open problem precisely. Name future
  experiments with citations.
- **Reception evidence is collected, then the claim is worded to it.** Read-only research agents return one row per
  item as `fact | source | bib key`: citation counts from more than one index, the reviews that cite the work and
  what they cite it for, packages that depend on it, pipelines that wrap it. Every new entry is fetched by DOI
  from Crossref. "Widely adopted, with tools that build on it" held where "the standard" did not. A priority claim
  is checked the same way: a metric the author's team was said to have introduced had been defined earlier by
  others, and the book credits them.

## Length and density

- **Full weight, no padding.** Each project chapter is dense LaTeX of 15 to 25 or more pages with equations,
  citations and figures. The total target moved from 100 to 150 to "under 200 pages excluding references"; the
  final build was about 200 to 225 pages. A short part means a missing claim; repair it with evidence, never with
  sentences.
- **Measure words per page for the actual layout.** 500 was assumed, 463 was measured. Estimate pages before
  promising them: pages = ceil(w / words_per_page) + 1.5 c + 0.7 f, for w words, c chapter openers, f figures.
- **Compare with exemplars of the same layout class.** Page counts from the PDF outline (front, main, appendix,
  references) of the exemplar books, against their median.
- **Cutting to a budget (P11 order):** layout first (a `\FloatBarrier` that stranded figures on 43 to 62 % full
  float pages cost pages; removing it saved them), then move procedural paragraphs and secondary floats verbatim to
  the appendix, then delete restatements (keep each fact in the chapter that owns it and cross-reference it
  elsewhere), then over-long background, then vague sentences (delete, do not rephrase). Keep every main-text
  result with its number, controls and limits, every label and figure. One trimming pass went 249 to 240 pages
  this way.
- **Never compress sentences.** Compaction by squeezing produced unreadable sentences ("your compaction has
  butchered the nice text"); four repair audits fixed 112 of them. After any length pass, run a "does every
  sentence read on its own" check and restore the author's pre-compaction wording from the snapshot.
- **Word caps need a drift floor.** Caps alone forced cutting the author's own sentences (kept-verbatim share fell
  from 73 % to 46 % in one chapter).
- **Moving detail to the appendix:** one agent per chapter-appendix pair; cut each block by exact start and end
  text, check it appears once in the appendix and nowhere in the chapter, move its labels with it, leave a
  one-sentence pointer. Move parameters, schedules, preprocessing filters, comparator settings,
  implementation-only algorithm boxes and architecture tables. Results, figures and the main results table stay.
- **Methods detail matches the best exemplar of the same publisher or series.** The exemplar listed frameworks only, so
  software version numbers were dropped (which also removed an impossible package combination). Default: list
  frameworks as the exemplar does and cite the source paper's methods, where versions are pinned; never print a
  version the papers do not record. (Author to confirm: one record of the same days took versions from the latest
  supplementary methods.)
