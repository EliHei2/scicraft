# The lens catalog

One lens is one fault class with one question. Each finder gets one lens, its own output path and, usually, no
edit rights. Write the lens table before launching:

| Lens | Question | Allowed edits | Output |
|---|---|---|---|
| [name] | [one question the finder answers] | none | audit/rN/[name].json |

## Code before compute (training, evaluation, data pipelines)

| Lens | Question | What it caught |
|---|---|---|
| Math and loss floors | For every loss term, what does a trivial predictor score (predict zero, predict the mean, marginal entropy)? Does the logged loss sit at that floor? | a loss pinned at exactly 0.5/d for every variant: a dead objective that made five architectures indistinguishable |
| Indexing and alignment | Do rows, ids and positions stay aligned through every join, sort and concatenation? | a positional column paste after a join that attached ids to the wrong rows |
| Masking and leakage | Can any test information reach training: shared units across folds, normalization fit on all data, selection on test scores? | masking budgeted by count that inverted on skewed inputs; uniform test inputs had hidden it |
| Config and guards | Does every config key reach the code? Do misspelled or removed keys fail loudly? Does every guard distinguish the cases it exists for? | a loader that silently reverted misspelled keys to defaults; a hash guard stored but never asserted; a removed key still present in all 7 configs, which the new unknown-key guard then made unloadable |
| Train and eval in the same regime | Are caps, frames and preprocessing parameters persisted in the checkpoint and asserted at load? | an evaluation stream with no size cap where training was capped |
| Supervision on the shipped layer | Do the loss, the regularizer and the tripwire attach to the layer that is shipped? | a regularizer on the read-out while the shipped layer got no direct loss and collapsed |
| Evaluation and metric | Does the metric separate a known-good run from a known-bad one? Is the probe target independent of the representation? | a metric near zero for good and bad runs alike; labels derived from the embedding being scored, which reversed the sign of a result |
| Experiment validity | Does each comparison change one factor? Is there a trained null, a second seed, the cheapest baseline? | a five-arm ladder in which every arm shared the one parameter the experiment was meant to vary |
| Efficiency | Where does the time go, measured? | thread oversubscription (about 80 threads on 10 cores) as the dominant cost, ahead of the model |
| Minimality | What can be deleted without changing a result? | features cut as "fake-able" and kept out until evidence |
| Precedent | What do working published systems do here, verified from primary sources? | a design that was "the outlier" in stacking components no working system combined |

`ml-experiment-design`, `ml-evaluation` and `training-diagnostics` hold the content behind these lenses; the
audit only asks the question.

## A design before it is built

- **Refutation, one critic per mechanism.** "A mechanism that could learn X has not survived." The refuter of one
  design found its premise contradicted by a committed probe that neither design document cited (grep count 0).
- **Completeness.** What was never tested, which arm is missing.
- **Precedent and cost.** The single cheap measurement that could stop the whole build, named first.
- **Red, black and white hat** in turn on one proposal: attack, worst case, strongest case.

`research-design-review` covers the design review itself.

## A data figure

- Layout and whitespace; type sizes against the print minimum; clipping; color and redundancy.
- Science against caption: does the caption claim more than the table? ("visually near-identical" deferred to a
  table that said the agreement was at chance.)
- Fact check: every plotted value reproduced from source. One harsh fact-check reproduced every bar value and
  coordinate of two panels exactly.
- Main against supplement: the same run, the same labels, the same floors across panels.
- Agents see only their tile and "will not catch 'the whole thing reads like a slide'": one reader looks at the
  whole figure.

`figure-development` and `data-figures` hold the figure rules.

## A paper, book or report

| Lens | Question |
|---|---|
| Facts | Every number, dataset, unit and comparison matches the source; denominators exact |
| References | Each entry correct (authors, venue, DOI); each citing sentence supported by the cited work; primary source rather than a summary of it |
| Consistency | Counts against figures, captions against what the figure draws, one name per thing, the same test named in main text and appendix |
| Claims | Absolute words ("first", "only", "every", "nothing") searched for counterexamples in the document itself |
| Attribution | Every credit from the author or a contributions section, never inferred |
| Voice | Machine-made sentences, slogans, tangents; read as a reader, not as a checker |
| Terminology | Terms with more than one meaning; one term with more than one name |
| The referee's seat | "only quotable items a human reviewer would hold against the authors" |
| Outsider | Can someone from another field follow the opening? |

What round 1 of one final proofread caught: a citation on the wrong sentence, a promised "full ranking" missing
from the appendix, a core count that did not add up, main text and appendix naming different tests, a caption that
did not name a dashed line, one target with two names, an italic unit. Round 2 found 15 more items, mostly bold
lead sentences claiming more than the cited lines showed.

Personas that caught different errors from one shared brief: a cold read by a senior reader, a line editor, a
hostile fact-checker in the role of a competitor who could not reproduce the result, a terminology auditor, and an
outsider comprehension test. The terminology auditor caught a word with three meanings.

## A reply to reviewers

Two independent lenses per reply, then a reviser:

1. **Facts.** Every number and claim in the reply is printed in the paper at the cited place.
2. **The reviewer in person.** Coverage: list every sentence of the review that states a weakness, a number, a doubt
   or a question, and put in `uncovered` each one the reply does not answer head-on within the first two sentences.
   Persuasion: where would you stay unconvinced, and which printed result would convince you?

`rebuttal` covers the reply itself.

## A release

Fresh agents that have not seen the build brief: a newcomer who installs from the README and finishes one task, a
break-it pass, a leak scan with zero hits, consistency from a clean clone, and numbers traced to files. Fix every
stumble rather than explaining it away. `research-release` covers the release.

## Sweeping a class

When one instance is caught, the next lens is that pattern across the whole artifact: "find such patterns by an
adversarial audit subagent and really fix all of these". When one plotted point is doubted, re-check the others.
