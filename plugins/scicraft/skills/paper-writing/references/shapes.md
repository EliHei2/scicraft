# Shapes that worked: abstract, introduction, contribution, results paragraph, caption, opening, conclusion

Each shape below was read off text the author wrote and kept in a submitted ML paper or a
submitted biology methods paper, or off an opening rewritten eight times until accepted. Examples
here are neutral and their numbers are illustrative. Venue registers (Online Methods, ML conference
style) live in `nature-methods-writing` and `ml-paper-writing`.

## Abstract

The arc of an ML abstract that worked, in steps:

1. The world: the property of the object of study, one sentence, no specific dataset.
2. The measurement or data that captures it, with a field-scale number.
3. What current methods do and what that loses, stated as a mechanism ("[what they do], which
   [what that loses]").
4. "We introduce [concept], a [noun] that [does Y]." The concept comes before the model that
   computes it.
5. The consequence, with "therefore".
6. "To compute [concept] at [scale], we introduce [Name], a [noun] that ..."
7. Training in one sentence.
8. The result, with the comparison set named and counted ("[N] methods, including [class A],
   [class B] and [class C]"). "[N] methods of what?" is the
   question an uncounted reference class draws.
9. The bound on the result, in the same or the next sentence.
10. One robustness result.
11. One plain implication.

A biology abstract by the same author followed the same arc: current state, named failure modes,
"We introduce X, a ... that frames [task] as [reformulation]", the result with the dataset count,
one capability, one finding, the code location.

Rules: one or two headline numbers, each with what it is counted over. No adjectives on the
contribution. A bare number is decoration ("such a number? meaningless"). In a summary or
abstract of a long document, name experiments and conclusions by their section titles and leave
single result numbers out.

On revision, from six corrections in one hour on an ML abstract: give performance once, with its
comparison set, then the conceptual contrast, and do not restate the same result in several metrics.
Ablations stay out of the abstract; the one controlled swap that tests the concept itself (same
objectives, data and steps, one component exchanged) may stay, phrased as what it means. A revised
abstract is no longer than the version it replaces.

## Introduction

- **The introduction states the shape of the problem; the section that owns a result proves it.**
  No results of the authors' own in the introduction: no scores, ranks, or caveats that only make
  sense next to a result. The author's words, on finding them there: "no result should be mentioned
  in the introduction". It may name the evaluation protocol and cite it ("[protocol] on [N]
  tasks, ranked by [measure]"), and data facts such as corpus size may stay. A schematic of what something
  is may appear; a figure of how well it performs may not.
- The shape that worked in an ML paper: facts with field-scale numbers, then one bold question,
  then a short verdict sentence, then a run-in "Our contributions." with one paragraph per
  contribution (concept, model, objective, evaluation).
- The reframe sentence closes the problem paragraph: "[Task] is more accurately framed as X than
  as Y."
- Own method in an introduction is stated as a problem definition: the notation says what must be
  inferred, never how it is estimated, and one sentence names the section that carries the
  estimator. No likelihood, prior, hyperparameter or normalization constant.
- Ablations are described by their extent, with no effect sizes: "remove or replace components of
  the encoder, the input and the training objective one at a time, each against an identically
  trained control".
- The main-text statistics paragraph gives only the ranking measures and what "significant" means.
  Test names, the correction for multiple comparisons and caveats about comparators' training data go
  to the appendix with one pointer. Delete main-text sentences that state what any reader assumes.
- For an audience from another field, a terminology box defines the domain terms once.
- Zero cross-references to later sections inside motivating paragraphs; name the work, not "Part
  III".

## Opening paragraph

Eight first paragraphs were rejected before one was accepted. What held:

- First sentence about the object of study at process level: one sentence, no specific dataset,
  instrument or single system. "Do not fixate" on one example; examples come later and at the level
  of a whole field.
- Numbers in an opening are properties of the field, never one study's effect size.
- No result of the author's own (ten of ten studied exemplars agree).
- A list in prose must not read as a closed set ("just don't pretend that only [these three] are the
  available ones").
- Generalization is stated in statistical vocabulary: description, mechanism, confounded correlate,
  replication, statistical power.
- Name the human in the loop and the stages of the pipeline (acquisition, processing,
  interpretation), never its parameters.
- Define a coined term once, with all its qualifiers. Bound the work's own claim in the opening.
- Block shape for a motivating opening: phenomenon, what changed, what this work argues, one
  paragraph each; the second paragraph ends on a minimal contrast.

## Topic sentences

**Every opening and topic sentence carries a concrete fact.** Name the method, its input, its
operation, the dataset and the citation: "Tool A segments X from Y, and items are assigned by Z
[citation]". A sentence that would be equally true of any method in the field is deleted or made
specific. Two kinds were rejected in a book introduction as "super not scientific": sentences that
sort methods by a meta-property ("existing methods differ in which evidence decides ...") and
sentences that announce what a section will do. The same pass found a definition of a technology
that was also factually wrong, so check every statement about a technology or a cited paper against
the source before it stays.

## Contribution sentence

"We introduce X, a [noun] that [does Y]", with the mechanism in plain verbs and no self-praise.

> We introduce RowRetriever, a tabular classifier that attends over the k nearest training rows of
> each query instead of fitting one global decision function.

The negated half names the alternative the field actually uses, so the contrast is real. Banned on
a contribution: `principled`, `elegant`, `powerful`, `novel`, `seamless`, `comprehensive`, and
`robust` when unquantified. In a book built from papers, contributions live in labeled slots (a contribution block
per chapter), stated affirmatively and exactly once; never a sentence about what the author did not
do, and never "peer reviewed" (the venue carries it).

Devices that worked in exemplar books, for contributions that need more than one sentence (the slots
themselves belong to the sibling `book` skill): one provenance paragraph saying which
sections are original, which reworked and which figures borrowed; a deliberate non-edit note on a
reprinted chapter; author rank deciding whether a paper gets a chapter or a summary section; a
software contribution stated as a query a reader can run (for example the author's merged pull
requests, with the exclusion clause). A contested contribution takes three beats: the collaborator's
part in full, the joint part named, the author's part in one clause.

## Results paragraph

```
<subject> <measured relation>, <value> against <value> for <named comparator>,
<appositive saying who that comparator is> (<Table/Fig>).
<one robustness sentence: the conditions the result survives>
<second paragraph: mechanism, or the breakdown by condition>
```

> RowRetriever reaches the highest mean accuracy, 0.84 against 0.81 for gradient-boosted trees, the
> highest-ranked baseline (Table 1). It is ahead on 31 of the 40 datasets and significantly above 12
> of 14 comparators (adjusted p < .01), and none is significantly above it.

- Lead with the claim; the number sits inside the claim sentence with its comparator named.
- Measured relations instead of evaluative verbs: "ranks below", "is rated above X by Elo", "the
  highest-ranked published model". The author: "strong or good or bad are not scientific". "Leads"
  survives as a plain rank statement.
- A number stays only if the reader can say what it rules out: a comparator, a null, a threshold
  that changes a decision, or a consequence. "One number is decoration. Two numbers are a result."
- Count labels say what is counted: "31 of 40 datasets", never "31/40".
- Never more decimals than the claim uses.
- Statistics wording is `stats-reporting`'s job; keep one vocabulary across text, figures and
  replies.

Results sections are organized around figures: one text unit per figure, opening with that figure's
message.

## Caption

```
**<Claim title, one sentence.>** <One protocol sentence: data, filter, reference, n.>
(a) <what is drawn> <what it shows>. (b) ... <Every encoding named: colors, dashed lines, shading.>
<Statistic and error bars defined.> <One source line if adapted.>
```

> **Retrieval gains concentrate on small training sets.** Each point is one of 40 benchmark
> datasets, mean over 10 folds. (a) Accuracy gain over gradient-boosted trees against training-set
> size, log scale; the dashed line marks zero gain. (b) Gain against number of features. Error bars,
> standard deviation across folds.

- A caption that did not name a dashed line was a proofread defect. Name every encoding.
- Adapted material: "Adapted from Fig. 2b of [citation]." when cropped or changed, "Taken from Fig.
  2 of [citation]." when whole. Never "Reproduced". No mentions of slides, drafts or licenses in a
  caption (licenses go in one disclosure sentence).
- A schematic that simplifies the code says so in its caption.
- A selected example is "illustrative", and the caption says how it was selected when its local
  value differs from the dataset value.

## Conclusion and discussion

- Start from a measured fact with its number, then one concrete consequence. No anecdote, no
  meta-commentary about how things were named or treated.
- Limitations: `references/claims-and-facts.md`.
- Never end on a slogan or a forward promise.
