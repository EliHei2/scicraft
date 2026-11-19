# Narrative blocks: the contract between the argument and the prose

A narrative file is what a section must prove, written before the section exists and kept in step
with it afterwards. Together the blocks are the project's `NARRATIVE.md` (defined in the sibling
skill, `project-structure/references/governing-documents.md`); a book keeps one file per chapter
and indexes them from `NARRATIVE.md`. When file and prose disagree, the file is edited first and the prose follows.
A narrative file that describes an older draft is worse than none, because it will be trusted.

The failure it prevents: a heading is written, prose is generated against the heading, and the
prose is fluent, on topic and establishes nothing. Every density failure is downstream of that.
Meta-narration appears when a paragraph has no claim. Hedge stacking appears when a claim has no
evidence. Vague magnitude appears when nobody looked up the number. The block forces all three
decisions before a sentence is written.

The template is `assets/NARRATIVE_TEMPLATE.md`.

## The fields

| Field | Rule |
|---|---|
| Claim | One declarative sentence, quantitative or falsifiable. "This section discusses X" is a topic. |
| Without it | What breaks later if the section is cut. Written honestly, it kills sections. If nothing breaks, cut it. |
| Movement | One of the six in `references/levels.md`. |
| Evidence | One bullet per fact: fact, value with unit, provenance (file, section, table, citation), status tag. |
| Paragraph titles | One declarative sentence per paragraph, written before prose (`references/paragraph-loop.md`, T0). |
| Opens | The job of the first sentence, not the sentence. |
| Closes | What the reader now knows, one clause. |
| Must not | The specific overclaim available here, named. "Be honest" is a reminder. "[Value] is [what it measures] and no [stronger result] exists" is a Must-not. |
| Figure | The figure ID and what it must show, or none. Write the caption with the prose: in the source project an early caption caught a figure that did not show what its spec claimed. |
| Budget | Words. A ceiling. |

The chapter or paper header adds: Claim, Forced by (the wall), Hands off (the verbatim exit
sentence, written here first), Facts at risk, Sources.

## Status tags

| Tag | Means | In the prose |
|---|---|---|
| `[measured]` | a run with logged outputs | stated plainly |
| `[preliminary]` | a run with a missing control, or outputs not kept | carries its missing control in the same paragraph |
| `[unrun]` | designed, never executed | never asserted as a property; the section is titled as a specification |
| `[external]` | someone else's number | carries its attribution |
| `[cited]` | literature | cited at the claim |

"The tag decides the hedge, and no hedge is written that the tag does not license." A block with an
untagged fact is not finished.

**No fact enters a block that is not in the facts file, the manuscript, or a cited paper.** The
narrative file is where fabrication would enter undetected, because it sits upstream of every
check. Provenance is mandatory.

## Worked example (an ML paper; every number is illustrative)

```markdown
## 4.2 Retrieval gains concentrate on small training sets

**Claim.** Retrieval over training rows raises mean accuracy from 0.81 to 0.84 across 40 tabular
datasets, and the gain is largest below 1,000 training rows.

**Without it.** Section 5 argues that retrieval substitutes for data; with no size breakdown that
argument has no support.

**Movement.** Measurement

**Evidence.**
- mean accuracy, retrieval model | 0.84 | results/table1.csv row 3 | `[measured]`
- mean accuracy, gradient-boosted baseline | 0.81 | results/table1.csv row 1 | `[measured]`
- datasets where retrieval is ahead | 31 of 40 | results/per_dataset.csv | `[measured]`
- gain on datasets under 1,000 rows | +0.06 | results/by_size.csv | `[measured]`
- gain with a 10x larger index | +0.02 | one seed, no baseline rerun | `[preliminary]`
- benchmark protocol | 10 folds per dataset | cite the benchmark paper | `[cited]`

**Paragraph titles.**
1. Retrieval raises mean accuracy by three points over the baseline on the 40-dataset benchmark.
2. The gain shrinks as the training set grows and is absent above 50,000 rows.

**Opens.** States the comparison and the benchmark, with both means.
**Closes.** The reader knows where retrieval helps and where it does not.
**Must not.** Call the larger-index result an improvement: it is one seed with no rerun baseline.
Must not say "outperforms" without the 9 datasets where the baseline is ahead.
**Figure.** Fig. 3b, gain against training-set size, one point per dataset.
**Budget.** 220 words
```

The preliminary larger-index fact stays in the block. In the prose it either carries its missing
control ("from one seed, without rerunning the baseline") or it moves to the appendix with its
number. It never silently disappears and it never becomes a headline.
