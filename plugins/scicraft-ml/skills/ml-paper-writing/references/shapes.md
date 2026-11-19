# Section shapes for a machine-learning conference paper

The shapes below are the ones the author's published and submitted papers settled on after several rounds of
rejection. The running example is a fictional tabular foundation model ("the model"); a second example from
point clouds shows that the shape does not depend on the field. `assets/paper_skeleton.tex` carries each
shape with placeholders.

Contents: abstract; introduction; contributions; terminology box; related work; method; experiments;
results paragraph; ablations; limitations; appendix order; captions; headings.

## Abstract

Eleven moves, each one sentence, in this order. Concept before the model that computes it. No adjectives on
the contribution.

1. The world: "Tabular data are organized at nested levels, from cells to rows to related tables."
2. The measurement or scale, with a number: "Public repositories hold millions of tables of up to 10^7 rows."
3. The gap, stated as what is lost: "Existing foundation models serialize each table into a fixed-length
   sequence, which fixes the context to one table and discards the relation between columns."
4. "We introduce [concept], a [noun] that [does Y]."
5. The consequence, with "therefore": "The unit of prediction is therefore chosen at query time."
6. "To compute [it] at [scale], we introduce [Model], a [noun] that [mechanism in plain verbs]."
7. Training, in one sentence.
8. The result, with numbers and the comparison set named: "... against 14 methods (pretrained foundation
   models, gradient-boosted trees and per-dataset neural networks)." The author's own question to a draft
   that said only "[N] methods" was "[N] methods of what?".
9. The bound on the result ("It ranks first on classification and [k]th on regression, whereas ...").
10. A robustness result, if one exists.
11. One implication, one line.

Keep counts with their reference class and keep the abstract short: one or two result numbers. A draft that
turned the abstract into a list of placements ("second, first and first by scale") was rejected outright.
For the plain-text abstract a review platform asks for, strip LaTeX and keep the same sentences.

## Introduction

1. **Facts with numbers**, each cited. Physical or computational scales of the data type, the size of
   current corpora, the cost of the obvious approach ("10^14 pairwise interactions for one table of 10^7
   rows").
2. **What current models do**, by name, and the cost of that choice.
3. **The bold question**, one sentence: "\textbf{what should be the unit of representation for a table?}"
4. **A short verdict**, 4 to 10 words: "Yet tables have no single natural unit."
5. **The approach** in one paragraph: the concept, then the model.
6. **The evaluation**, named and cited, with no results: "We evaluate frozen representations on 12 tasks
   against 14 methods, rank them by mean rank and by Elo \citep{elo}, and ablate each component." The author:
   "no results in the introduction, just mention what is our evaluation".
7. **"Our contributions."** as a bold run-in or the `contributions` box, one short paragraph per
   contribution.

Never claim superiority before the method is introduced: "in introduction before you introduce the
background or model you use it to say it's better than other methods ... such killer mistakes".

## Contributions

Each opens "We introduce X, a <noun> that <does Y>" with the mechanism in plain verbs:
"We introduce [Model], a row-to-table encoder whose cost grows linearly with the number of rows."
State the real novelty concretely. When every part of a claim has prior work, claim the conjunction only,
and verify every "first" against the literature before the abstract is locked.

## Terminology box

For an ML venue, a paper whose application is outside ML defines the application's terms once, in a short
box in the introduction or at the start of the method: one bold term and one sentence each, at most six
terms. The author's paper for an ML venue defined six domain terms this way. After the box, the term is
used without re-definition. Use `\begin{terminology}[<Field> terms]` from `assets/ml_addon.tex`.

## Related work

Bold run-in paragraphs (`\rwpara{...}`), one per family of methods: who did what, with citations, and what
it leaves open for this data type. Cite the most important works, not the most works ("don't inflate the
references"). Say why each family matters and why this work is still needed.

## Method

1. At most one roadmap sentence ("Section 3.1 formalizes ..., Section 3.2 introduces ...").
2. The data type in general terms; the application appears as one representative instance.
3. The concept or representation, then the model, then the objective.
4. Run-in heads name components in the field's terms ("Short-range context.", "Cross-scale attention.").
5. Math "just right for a transformer paper": the losses and the core operator in the main text, proofs and
   secondary derivations in the appendix. Keep only propositions that the text references; drop unused math.
6. Implementation details readers do not need to follow the idea (an ordering trick, a kernel) go to the
   appendix.

The method section names no dataset and no dataset-specific number. The `nature-methods-writing` skill holds
the full method-versus-data split if a journal version follows.

## Experiments

Run-in paragraphs, in this order: **Pretraining data**, **Tasks**, **Comparators**, **Protocol**, then one
paragraph per result.

- Pretraining data: source, size in words ("2.1 million tables", "Billion" or "Million" in place of 10^9),
  licenses in the appendix, and whether evaluation data were held out of pretraining.
- Tasks: for each, data, label source and why it is ground truth, split unit, probe, metric. A few clean
  tasks beat many: the author capped one paper at five tasks and six comparators, with three tables.
- Comparators: published models by name and version, with where the weights came from, plus the two or
  three most-cited classical methods of the field (not a pet baseline).
- Protocol: seeds or folds, what the spread is, the test and its single correction, how the reported
  checkpoint per model size was chosen.

## Results paragraph

"<subject> <measured relation>, <value> against <value> for <comparator>, <appositive saying who that
comparator is> (<Table/Fig>)." Then one robustness sentence listing the conditions the result survives.
A second paragraph gives the mechanism or the breakdown by scale.

Example: "The model has the best mean rank, 2.1 against 4.6 for the highest-ranked published model, and
ranks first on 9 of 12 tasks (Table 1). The ranking holds under [the conditions the paper tests]."

Never give a count whose remainder invites an attack: "eight of ten significantly" became "All ten lower the
combined score, and each significantly lowers at least one task." Never drop the remainder from the record:
the per-task values stay in the table.

## Ablations

Each row removes or replaces one component of the full model, trained with the same recipe, seed and step
budget, compared at matched data seen. Labels are concrete, at most four words, "−masking" in place of
"w/o masking". The caption says exactly what each ablation changes in the model. The full model is the
reference row. Detail of the table in `tables.md`.

## Limitations

One plain opener, then a short concrete list, each item with its cause, then concrete next steps, closing
with the last bound on the evaluation:

"[Model] is a first step toward [concept], and several limitations remain. It reads single tables up to
10^6 rows, so relational databases are flattened before encoding. ... Finally, we evaluate frozen transfer
only."

Never apologize, never excuse, never hedge with a straw man. A limitation that a reviewer raised and the
paper now answers moves into the text where it is answered.

## Appendix order

The order the author set for one paper, after a reviewer-style audit found missing details:

0. Data corpus: public sources, licenses, tables of sizes.
1. Extra figures.
2. Remaining math, only items the text references, with references.
3. Model details for the reference model.
4. Pretraining: corpus, hardware, dynamics, held-out sets.
5. Transfer experiments: data, metrics, probes, run details, checkpoints, package versions.
6. Ablation protocol.

Match the detail level of top-cited papers of the venue in the last three years: exact model versions and
where they were fetched, metric definitions, training protocols, inference time, GPU type, time and memory.

## Captions

Bold claim title, one protocol sentence, then lettered panels that each say what is drawn and what it shows,
with n and the statistic defined. Name every encoding: colors, dashed lines, shading, bold, underline.
"**The model ranks first by Elo and by mean rank.** (a) Elo ratings from one Bradley-Terry fit over paired
fold-level comparisons, ... (b) ..."

## Headings

Concrete noun phrases that name the object and the operation, in the paper's terms. No riddles, metaphors,
questions, colons or invented counts. Rejected in real drafts: invented counts of the shape "One gap, two
symptoms" or "Three faces of sparsity", "ranking checks", "controls" as a heading for main results. Never
re-title the author's own sections.
