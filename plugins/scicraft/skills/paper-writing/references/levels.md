# The four levels: contents, narrative, text, edit

Work descends. A level is never entered while the level above it is unsettled. Most defects in a
long document are level-n problems attacked at level n+1, which is why a paragraph gets rewritten
five times and still reads wrong: the section had no claim. In the project this came from, three
passes on one chapter were rejected in a row, each fixing the previous defect and adding the next
(conversational headings, then abstract-noun subjects, then editorial sentences), because the unit
of work was the section and the level above had never been settled.

## Contents

| | |
|---|---|
| Decides | how the problem is cut up: which sections exist, in what order, what forces each transition |
| Artifact | a spine file: one line per unit with its one-sentence claim, the limit that forces it, and the verbatim handoff sentence; plus the build file and the page or word budget |
| Test | the wall test for every adjacent pair (below), and the four contents tests |
| Stop when | the build file, the spine and every narrative file agree, and the reason for each change is written next to it "so it is not undone by someone reverting to an earlier convention" |

**The wall test.** For every adjacent pair, name what the earlier unit could not do that the later
one does. If the answer is "and then we also did X", the transition is a list, and the contents are
wrong. A transition is one of three kinds: forced (the wall is named), licensed (declared as a
change of topic, once), or a list (forbidden). Write both sides of every seam in one place, the
spine, and copy the handoff sentence into the prose from there. Never write "this paper moves from
X to Y".

**The four contents tests.**

1. Claim. Every unit states one claim no other unit states. Same claim twice: merge. No claim: cut,
   do not shorten.
2. Wall. The transition into it is forced or licensed.
3. Service. A unit that serves no later unit is cut, "however interesting".
4. Evidence. A claim that rests only on unrun experiments is a specification, and is titled as one
   ("Towards ...", "Proposed ...").

**Split and merge.** Split when a unit must hold two claims at once or mixes more than two
movement shapes. Merge when two claims paraphrase each other, or when a unit exists only to hold
background; background lives at first use.

**Selection.** A paragraph or section survives only if deleting it leaves a later one unsupported.
Budgets are ceilings, not quotas. A unit under budget means a missing claim, and the repair is
evidence, never sentences. The author's words: "don't force 40 pages, but really hammer it home".
Hammering it home means more evidence per claim and fewer claims, never repetition.

**Page estimate before promising pages.** pages = ceil(w / wpp) + 1.5 c + 0.7 f, for w words, c
chapter openers and f figures. Measure wpp on the real layout first: one book layout measured 463
words per page against 500 assumed, and an estimate of 23 pages delivered 30 because openers and
figures had been modeled as free. `prose_qa.py --wpp` uses this formula.

## Narrative

| | |
|---|---|
| Decides | what each section establishes, on what evidence, in what movement, before any prose |
| Artifact | one narrative file per chapter (paper: one per main section), one block per section, paragraph titles inside each block; template in `assets/NARRATIVE_TEMPLATE.md`, rules in `references/narrative-blocks.md` |
| Test | the file reads alone as an argument: a stranger can say what each section proves and what it costs |
| Stop when | every block has a claim sentence, every fact a status tag and a provenance, every paragraph a title, and the author has seen the blocks |

## Text

| | |
|---|---|
| Decides | the prose: paragraph architecture, sentence order, words |
| Artifact | the manuscript files |
| Test | the paragraph audit (`references/paragraph-loop.md`) and `scripts/prose_qa.py` |
| Stop when | every paragraph passed three rounds, the cut pass brought the word count down, the gate is clean, and every number traces to the facts file |

## Edit

| | |
|---|---|
| Decides | nothing new: the author rewrites, the agent records |
| Artifact | the edit ledger (`assets/EDIT_LEDGER_TEMPLATE.md`), procedure in `references/intake-and-revision.md` |
| Test | every change is classified, generalized, written down and propagated |
| Stop when | the ledger entry exists, its siblings are fixed across the document, and the durable rule is in the governing file |

## The loop per section

```
1  READ       facts at risk, the sources the block names, the edit ledger
2  NARRATE    write or update the block. Stop. Show it. Do not draft against an unagreed block.
3  DRAFT      prose to the block, one paragraph at a time (paragraph loop)
4  CUT        15 to 25 percent fewer words, same facts. Run prose_qa.py.
5  HAND       give it to the author
5b INTAKE     text arrived from outside the loop: measure before reading (intake-and-revision.md)
6  DIFF       the author rewrites; diff at sentence level
7  LEDGER     write every change as a rule, both versions verbatim
8  PROPAGATE  apply the rule backwards to every section already drafted
```

Step 8 is what makes the loop converge. A rule learned at chapter 11 that is not applied to
chapters 1 to 10 will be re-learned at chapter 12.

**Two checkpoints per section**: show the block before drafting, show the draft before cutting. A
wrong claim costs one message to fix at level 2 and a rewrite at level 3.

## The six movements

Name the movement in the block before drafting. It fixes paragraph order, which is where most
rewriting cost sits. A section that is none of these is usually two sections.

| Movement | Paragraph skeleton | Typical use |
|---|---|---|
| Knot | 1 the operation and the scale where it breaks, with the number. 2 the obvious fix and the mechanism by which it fails, one sentence each. 3 what was done: mechanism, not praise. 4 the cost, quantified, and what it does not fix. | an engineering decision (sharded training, a memory limit) |
| Reformulation | 1 the standard framing, in the field's words. 2 the class of thing it cannot represent (the whole paragraph's work). 3 the new framing, object types named. 4 what becomes computable. | casting a task as retrieval, as link prediction |
| Measurement | 1 the question and why this data discriminates. 2 the design, including what was withheld from which method ("withholding is the credibility"). 3 the number in apposition with its comparator. 4 what it rules out, plus one flat limitation. | every results section |
| Construction | 1 the object and its purpose. 2 the definition, notation once. 3 the properties, each with its consequence. 4 the cost (compute, memory, an assumption, an unimplemented piece). | a method section, a data model |
| Landscape | 1 the axis that separates the methods. 2 per family: mechanism in one line and its documented weakness, cited. 3 the gap, stated as the requirement the next unit meets. | related work |
| Concession | 1 the limit, bare declarative. 2 its mechanism. 3 what it does and does not invalidate (narrow it; an overbroad concession is also false). 4 the measurement that would settle it. | limitations |

Related work follows the Landscape movement: organize prior work by the inductive bias or failure
each family buys, never by chronology, and only after your own formulation is stated. The form that
works: "some models X (e.g. A, B) while others Y (e.g. C, D)". The form that fails: "several methods
exist but they have limitations".

**Positioning briefs: one read-only agent per work, all sharing one common brief.** When a document
holds several works (a book, a paper with two contributions), research the landscape of each with
its own agent. Each writes six sections: a short landscape by method family; three gaps; the work's
claims pressure-tested (the strongest counterargument, then the wording that survives it); the
author's own wording for each claim, quoted; the handoff to the next unit; defects in the
bibliography. New references are verified on Crossref or Europe PMC before use. In the source work
four such agents also surfaced mismatches between papers and their code, and wrong venues in the
bibliography. Common brief: `assets/POSITIONING_BRIEF_TEMPLATE.md`. Use the output for the
introduction and related work only, and stop when the related work in hand is enough (the author
narrowed the scope: "related work we have there is enough"). A generic prompt template the user
pastes (the source began from eight "act as an elite research methodologist" prompts copied from
social media) is rewritten into the common brief, never run as given.

## The narrative audit (when the story itself is in doubt)

Read every unit's heading, opening, closing and handoff plus the facts file. Produce: the central
claim as the evidence supports it; a proposition chain (number, proposition, evidence, status
measured/preliminary/unrun) and where it breaks; each joint graded holds, licensed or does not
hold; the strongest version of each repair with drafted sentences; the contents the evidence
supports (title, single claim, handoff, tagged NEW, CUT, MERGE, MOVE, RETITLE). Lessons from the
one full audit on record:

- The stated cause must be the historical cause. A handoff that reconstructs a choice never made
  is caught by anyone who reads the methods.
- A gap is not a mandate. Your method winning one comparison does not force the next section.
- A preview section that gives every headline number destroys every later wall.
- A strong section with no upstream proposition requiring it reads as a diary.
- Do not end a part on a plan or a budget.
- "An admitted gap is not a defect; an unadmitted one is."
- Look for the single experiment on data already held that repairs two joints.
