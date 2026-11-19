# Research questions, the plan, and the first step

## 1. The object of study

Write one sentence that names the units and the space they live in, before any question. One design document
opened: "Object of study: the space of supervised tabular learning problems, not the space of rows." Every later
choice (what a unit is, what is subsampled, what counts as a replicate) follows from that sentence.

## 2. Research questions

- **Number them and keep them visible.** One brief listed RQ1 to RQ10 under "Research questions to keep visible";
  every analysis and every figure was named after the question it answers.
- **Tie each question to an analysis, an output and a reference.** `assets/QUESTIONS.md` has one row per question:
  question, analysis (with the function or script), output (table or figure), reference or null, units and
  detectable effect, status. `scripts/check_kickoff.py` fails a question without an analysis, an output or a
  reference.
- **State hypotheses as tests, and do not presuppose them.** The brief: "Do NOT assume correlation ... We want to
  test that rather than presuppose it." Each hypothesis names the observable outcome that would falsify it.
- **State the detectable effect before correlating over few units.** With 51 datasets a correlation test detects
  |r| of about 0.38; with about 144 it detects about 0.23. "A null is informative only at n of about 144." Choose
  the corpus size from this, and report a null as a null, scoped to the setting tested (a null at one scale is not
  a null at every scale).
- **Every number has a reference it is read against**: a chance level, a same-size within-group baseline, the
  published number, the trivial floor. A distribution distance without a same-size baseline cannot be read; at
  100 against 500 items, nearest-neighbor precision and recall sat near 0.85 to 0.88 with no gap at all. The
  statistics of such comparisons belong to `distribution-comparison`.
- **Ground each question in what the data can measure.** One figure's research checked every candidate effect
  against the actual feature list before any analysis; most candidates needed features the panel did not have.
  Give research agents the real feature list as a file.

## 3. Design choices as tables

`DESIGN.md` (the layout of the document set belongs to `project-structure`) records the science as built: each
choice as a row of choice, what it is, and why it exists. The reason is one line that names the failure it
prevents: "Without this, 'real vs synthetic' is mostly 'big vs 1024 rows'." Before a classifier separates two
corpora, list the features that encode collection artifacts (size, storage type, missingness, preprocessing,
row order) and plan to strip them level by level.

## 4. The first step: minimal, with something to look at

- **Make the first step deliberately minimal and visual.** In the one-day project the author asked for "sth very
  cool in 30 mins": cheap descriptive statistics per item, then a UMAP and a PCA of all items colored by source.
  Everything else was layered on afterwards, one representation family at a time, with one plot per family plus
  one combined plot.
- **For a new model, scope a minimal sibling of the full design with one visual headline.** One project dropped
  every advanced component, froze a design spec, and defined the headline as one picture. Held-out quantitative evaluation stayed off
  the default pipeline until the picture worked.
- **Produce pictures early and save them to disk**, so a crash or a token limit still leaves something to look at:
  "do it in a way that I have some pngs to look at even if you now run out of token limit".
- **Look before trusting a metric.** "look at it" was the author's reaction
  to a clustering score that contradicted an obvious picture.
- **Gate expensive work on the cheapest measurement that could stop it.** Name the number, the threshold that
  stops the job, and report it before building. A cheap viability check showed one planned analysis axis was
  limited by the measured features, before any expensive hunt.

## 5. The order of work that held up (one day, one new field)

From the commit history and prompts of a one-day project entering a field new to the author. Times are local.

| Time | Step |
|---|---|
| 05:25 | The author pastes a chat-generated build prompt and the research brief, asks for own research |
| 05:30 | Compute limits stated (local first, a light hosted GPU, no training on the CPU) |
| by 06:04 | Inputs saved verbatim in `SPEC.md`; first commit holds the data model, preprocessing, cheap encoders, analysis and tests |
| in parallel | Literature fact check (two helper agents, spot-checked), interface verification on installed packages, one model-survey agent |
| 06:17 | Data generation with the paper-faithful overrides, real loaders, the exact baseline replication |
| 06:28 | Baselines: within-group halves, a label-free negative control |
| 07:06 | Code-faithful reimplementation with released weights; one extra model the survey recommended |
| 07:15 | Fixes found by running: hash-order patch, hooks return None, no mixed precision, fixed library profiles |
| 10:03 | Fast visual results within 30 minutes, then layering, then the shared figure |

Two things went wrong and are worth avoiding: the code after 09:52 was never committed, so the afternoon's results
came from uncommitted code, and a built archive went stale while the package kept changing. Commit with every
decision.

## 6. What to say when handing the plan over

- The claim table's corrections, first: what in the brief was wrong.
- The questions and the analysis behind each.
- The first step, what it will show, and how long it takes.
- What is unverified ([U] items) and what only the author can decide (license acceptance, compute, scope).
- If the author is unreachable, proceed on the plan and put the corrections table at the top of the report.
