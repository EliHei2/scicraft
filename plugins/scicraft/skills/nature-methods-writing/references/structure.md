# Structure, closing sections and page budgets

Contents
1. Two archetypes
2. The default skeleton
3. What goes where (the empirical boundary)
4. One continuous document
5. Mandatory closing sections
6. Page-budget moves
7. The same discipline outside Nature journals

## 1. Two archetypes

A survey of about 50 Nature-family method papers (28 read in full) found two patterns.

- **A. Self-contained Methods, supplement of figures and tables.** The whole model, graph, losses, thresholds,
  hyperparameters, datasets and metrics are in Methods. The supplement holds figures and tables, often with no
  named Notes at all. This is the dominant pattern (for example Bering, scNET, STAGATE, GraphST, CellSAM, GHIST,
  Enformer, CellFM). **Default a method paper of normal scope to A.**
- **B. Thin Methods, long numbered Supplementary Methods.** AlphaFold is the example. Reserve it for systems of
  that scale.

The number of Supplementary Notes grows with the number of downstream tasks and ablations (scGPT has 12, totalVI
7), not with the size of the model. Do not build a Notes chapter the paper does not need.

## 2. The default skeleton

The order follows scVI (the model in Methods, not in Results), the economy of Cellpose 3 and the method-data
split of BIDCell. Adapt the headings; keep the order and the separations.

**Methods**

1. **Overview.** One problem-first paragraph, the task stated in one line, what the method runs upstream or
   downstream of. No dataset names.
2. **Model or graph construction.** Node, edge or architecture definitions as display equations, stated once,
   with notation inline.
3. **Model architecture.** The network in one or two sentences, the embedding or similarity definition.
4. **Loss functions.** Each term: name, one purpose clause, one equation. The combined objective as one named
   weighted sum with its weights.
5. **Training.** Optimizer, learning rate and schedule, steps or epochs, batch size, dropout, initialization,
   splits, how hyperparameters were chosen, a compact configuration block or a pointer to the hyperparameter
   Supplementary Table, compute and runtime. No dataset names.
6. **Inference.** The decision or assignment rule, thresholds, post-processing as a delta.
7. **Modeling choices.** The non-obvious decisions, each justified in one empirical sentence with a pointer to the
   robustness analysis. Underused and valuable.
8. **Evaluation and metrics.** Each metric in its own short subsection with one numbered equation. One evaluation
   protocol reused across tasks, changing only the metric.
9. **Datasets and preprocessing.** (a) The shared pipeline written once. (b) One entry per dataset with its
   stable ID, counts and panel or feature set. (c) Reference data: each reference once, with the analyses that use
   it in each role.
10. **Per-analysis matrix.** The dataset-by-analysis table (in the Supplementary Tables if it is large); prose
    gives deltas only.
11. **Settings used for other methods.** Each baseline with its version and parameters.
12. **Statistics and reproducibility**, **Data availability**, **Code availability**, **Reporting summary**
    (section 5).

**Supplementary Notes** (each cited once from Methods, and never the only home of a detail needed to reproduce
the results): loss derivations; parameter-selection heuristics and proofs; ablations and robustness; extended
metric definitions and normalization; relation to prior methods with a landscape table; software implementation
with the identifier glossary.

**Supplementary Tables**: hyperparameters, dataset manifest with accessions, per-baseline settings, software and
versions, parameter sweeps, the dataset-by-analysis matrix when it is long.

Three rules from the survey:

1. **Datasets always stay in Methods.** The strongest multi-dataset papers (Nicheformer, Geneformer, GHIST,
   scArches) put the dataset roster near the top of Methods, one named subsection per dataset.
2. **Split application case studies.** The reproducible recipe of a per-tissue or per-domain case study
   (preprocessing, labeling, the region analyzed) stays in Methods. Its interpretation moves to an extended
   analyses Note (GASTON's Notes S1 to S9 are the precedent).
3. **Every accessible Nature-family paper ends Methods with the closing sections.**

An algorithm paper often opens Methods with the architecture, then a dedicated default-settings subsection, then
evaluation (BANKSY, CellSAM).

The author's own top-level order for a combined supplement was background and related work, model, evaluation
metrics, domain analyses, the full benchmark, and software and installation at the end. It is a valid variant of
the skeleton for a benchmark-heavy paper.

## 3. What goes where (the empirical boundary)

| Content | Home | How often in the survey |
|---|---|---|
| model architecture (dimensions, forward pass, attention) | Methods | always |
| graph or edge construction, as its own subsection | Methods | always |
| loss equations, one named subsection per loss | Methods | always |
| inference, decoding, thresholds, output rule | Methods | always |
| training hyperparameters, optimizer, schedule | Methods | always |
| parameter-selection heuristics (the logic and the values) | Methods | always |
| datasets and preprocessing (roster and per-platform quality control) | Methods | always |
| metric definitions, one equation each | Methods | usual |
| statistics, data and code availability, reporting summary | Methods | always |
| loss derivations, closed-form expansions | Notes | sometimes |
| metric interpretation, robustness, caveats about thresholds | Notes | sometimes |
| ablation procedure (Methods) and its extended rationale (Note) | either | usual |
| relation to prior methods | Notes | sometimes |
| software internals (code layout, output schemas) | Notes | rare |
| background primer (for example on message passing) | Notes | rare |
| extended per-domain interpretation | Notes | sometimes |
| complexity or scalability argument | either | sometimes |

**The strict variant** ("Methods is really methods only"), which the author enforced: Methods is prose and
numbered equations; no code-font identifiers, no figure callouts, big tables in the Supplementary Tables. Key
parameter values still appear in Methods prose, early. Reproducibility holds because Methods cites the
Supplementary Tables of the same document. Use it when the brief is "exhaustive but pure Methods".

## 4. One continuous document

The author rejected splitting the supplement into `\part{Online Methods}` and `\part{Supplementary Notes}` twice
("all should be one thing"), and earlier rejected splitting the main file with `\input`. The latest form:

- One document. Each topic's procedure and its extended protocol are in the same section, the Notes material as
  clearly labeled subsections after its Methods anchor.
- The Methods-chapter firewall still applies to the procedure text; extended material marked as a Note is exempt.
- Code and command-line usage go to a software section at the end, or to a separate user guide.
- Merge with minimal change of wording ("integrate online methods and supp notes into one doc, but with minimal
  change of wording").

Ask before splitting a document the author keeps as one file, and before merging one they keep as two.

## 5. Mandatory closing sections

Nature-family Methods end with these subsections; `assets/closing-sections.tex` is the template.

- **Statistics and reproducibility**: the test, its sidedness, the statistical unit, n, the correction, the error
  bar definition, seeds, and answers to the negatives (no sample-size calculation, exclusions, randomization,
  blinding). Details in reporting-checklist.md.
- **Data availability**: every dataset with its exact accession or URL, written out as a plain URL (a hyperlink
  alone does not survive copy and paste); references and atlases with version or collection ID; source data.
- **Code availability**: the version that produced the numbers, archived with a DOI (Zenodo, Code Ocean, Software
  Heritage), the license named, and the internal tool names pinned here once. A bare GitHub link is not enough.
- **Reporting summary**: the one-sentence pointer to the Nature Portfolio Reporting Summary.

`methods_lint.py` fails when the first three are missing and warns about the fourth.

## 6. Page-budget moves

The budgets the author set for one supplement were Methods under 10 pages, Notes under 30, and the whole under 40.
The Methods budget was later raised to under 15 pages, once the "how it is computed" of the data analysis moved
back into Methods where it belongs. A budget is met by relocating and de-slopping, never by dropping a fact needed
to reproduce a result. The author's list of what must stay: "details, software versions, params, threshold,
filtering details, number of cell types".

Moves that worked, roughly in order of yield:

1. Tighten `titlesec` spacing around headings. The largest lossless gain.
2. Drop the rationale column of parameter tables.
3. Move wet-lab and imaging procedures, and secondary diagnostics, to the Notes.
4. Coarsen to about three top-level sections, with a `\subsection` only where its text runs to more than about half
   a page.
5. Turn run-in `\paragraph` heads into plain prose.
6. Cut sections that duplicate the main text ("drop 4, 5, 6 sections in method, that's going into the main
   text"), after checking that every fact in them exists in the main text.
7. Apply the five laws: a sentence without a fact goes.

Margin and line-spread tweaks move the total page count but barely move the Methods count. Count pages from the
built PDF after each move and report the count.

## 7. The same discipline outside Nature journals

The five laws, the method-data split, say-it-once, the fact inventory and its check, and author-action markers
carry over to the experimental-setup section and appendix of a conference paper, to a model card or datasheet,
and to a technical report. The register firewall is Nature-specific: a conference appendix may use code font and
figure references, and venue style files decide the closing sections (a reproducibility checklist instead of the
Reporting summary). For the structure of a machine-learning paper prefer the `ml-paper-writing` skill. Suggested,
not yet tested in real work.
