---
name: paper-writing
description: Writes a research paper, book chapter or any long scientific document with an agent, from the table of contents to final prose, through a four-level loop (contents, narrative, text, edit) that settles each claim before a sentence exists. Use it whenever someone asks to draft, restructure or revise a paper section, an abstract, an introduction, a results paragraph, a caption or headings; says "this reads like AI", "the numbers don't match", "update the paper to the new results"; hands over a collaborator's or another model's rewrite; or must cut to a page limit before a deadline. Holds the narrative-block format with fact-status tags, the paragraph loop with three ordered audit rounds, shapes that worked for abstracts, contributions, results and captions, the heading and term rules, a facts file with retired numbers, intake of outside text, and a runnable prose gate. Use author-voice for voice measurement, humanizer for pattern de-slopping, nature-methods-writing or ml-paper-writing for venue register.
---

# paper-writing

How to write a long scientific document with an agent so that the author keeps it, distilled from a
year of writing a book built from published papers, an ML conference paper with its revision, and a
biology methods paper. Almost every rule here comes from a draft the author rejected, a correction
that had to be made twice, or a check that failed silently. Where the author of the document at hand
says otherwise, they win: record their rule in the edit ledger (section 7) and follow it.

> **PRIME DIRECTIVE: no sentence is written before its claim is agreed, and no claim carries a fact
> that is not in the facts file with its status.** Prose generated against a heading is fluent, on
> topic, and establishes nothing.

Three failures cost the most time. Guard against them from the first minute:

1. **Drafting against a heading.** Meta-narration, hedge stacks and vague magnitudes are all
   downstream of a section that had no claim. Settle contents and narrative first (sections 1 and 2).
2. **Rewriting the author's text.** A request to place or update a file that produced a rewrite,
   new headings or an editor fan-out was rejected whole, more than once: "you really butchered my
   beautiful text". The author's sentences are theirs (section 7).
3. **Losing a correction.** A rule that lives in the conversation is re-learned at the next
   chapter. Every change the author makes goes into the ledger and is propagated backwards
   (section 7).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The author's texts**: published papers, the submitted or latest manuscript, supplementary
  methods, their earlier drafts. The best methods or results page they wrote is the register
  target; read one page of it before drafting.
- **The records behind every number**: result tables, logs, the analysis code. These become the
  facts file (section 5).
- **The author's governing brief**, if they wrote one. It overrides earlier rules; keep a decisions
  log against it (D1, D2, ...) and pass it word for word to any helper agent. When the author wants
  to write one, offer `assets/GOVERNING_BRIEF_TEMPLATE.md` for them to fill (operating brief, rules
  per chapter, accuracy gates, acceptance contract, continuation inventory). The author writes it;
  the agent keeps the decisions log and audits the deliverable against it (section 9).
- **The project's governing documents**: `NARRATIVE.md` (the argument) and `GUARDRAILS.md` (the
  invariants), defined in the sibling skill, `project-structure/references/governing-documents.md`.
  In a writing project the narrative blocks (section 2) are `NARRATIVE.md`, and the facts file
  (section 5) is the ledger of allowed values in `GUARDRAILS.md`.
- **The venue**: page or word limit, format, deadline, and whether text is submitted (punctuation
  fixes only) or in revision (changes marked in one color).
- **What may be said**: unpublished results, results under review, attribution from the published
  contribution statements.

Set up beside the manuscript, never inside a build folder (this layout gathers the files the source
project kept in several places; suggested, not yet tested in real work as one folder):

```
NARRATIVE.md        the narrative blocks (assets/NARRATIVE_TEMPLATE.md), or an index of writing/narrative/
GUARDRAILS.md       the facts file: every number the document may state, plus the Retired list
                    (sections from assets/FACTS_TEMPLATE.md)
writing/
├── SPINE.md        one line per unit: claim, the wall that forces it, the verbatim handoff
├── narrative/      one file per chapter, for a book or any document too long for one NARRATIVE.md
├── sources/        raw text of every source: manuscripts as text, numbered briefs, the bibliography key list
├── TERMS.txt       banned and renamed terms for the gate (assets/TERMS_TEMPLATE.txt)
├── FROZEN.txt      sentences the author fixed verbatim, one per line
├── EDIT_LEDGER.md  every correction, as a rule (assets/EDIT_LEDGER_TEMPLATE.md)
└── _snapshots/     a copy before every pass that touches prose
```

## 1. Contents

Decide how the problem is cut up before anything else. Detail: `references/levels.md`.

- **The wall test for every adjacent pair**: name what the earlier unit could not do that the later
  one does. "And then we also did X" is a list, and the contents are wrong.
- **One claim per unit, stated nowhere else.** Same claim twice: merge. No claim: cut, not shorten.
  A unit that serves no later unit is cut "however interesting". A claim resting only on unrun
  experiments is a specification and is titled as one.
- **Budgets are ceilings.** A paragraph survives only if deleting it leaves a later one unsupported.
  A unit under budget is missing a claim; the repair is evidence, never sentences.
- **Estimate pages before promising them**: ceil(words / wpp) + 1.5 per chapter opener + 0.7 per
  figure, with wpp measured on the real layout (463 measured against 500 assumed in one book).
- Done when the build file, the spine and the narrative files agree, with the reason for each change
  written down.

## 2. Narrative blocks

One block per section, written before prose and shown to the author. The blocks are the project's
`NARRATIVE.md`. Template: `assets/NARRATIVE_TEMPLATE.md`; rules and a worked ML example:
`references/narrative-blocks.md`.

- **The claim is one declarative sentence, quantitative or falsifiable.** "This section discusses
  X" is a topic.
- **Without it**: what breaks later if the section is cut. If nothing breaks, cut it.
- **Movement**: Knot, Reformulation, Measurement, Construction, Landscape or Concession. It fixes the
  paragraph order (skeletons in `references/levels.md`).
- **Every fact carries a provenance and a status tag**, and the tag decides the hedge:

| Tag | Means | In the prose |
|---|---|---|
| `[measured]` | a run with logged outputs | stated plainly |
| `[preliminary]` | a missing control or discarded outputs | carries its missing control in the same paragraph |
| `[unrun]` | designed, never executed | never asserted as a property |
| `[external]` | someone else's number | attributed |
| `[cited]` | literature | cited at the claim |

- **Must not** names the specific overclaim available in this section, not a general reminder.
- **Paragraph titles**: one declarative sentence per paragraph, inside the block, before any prose.
- When file and prose disagree, edit the file first. A narrative file describing an older draft is
  worse than none.

## 3. The paragraph loop

The unit of work is one paragraph. Detail and a worked example: `references/paragraph-loop.md`.

```
0 TITLE    the paragraph's one message, as a sentence. Needs "and": two paragraphs. None: no paragraph.
1 DRAFT    one paragraph
2 ROUND 1  smooth      each sentence raises the question the next answers
3 ROUND 2  clear       one checkable fact per sentence; every quantity present; heading names content
4 ROUND 3  scientific  subjects that exist; no sentence about the document; the register of the field
5 NEXT
```

- **The rounds run in this order.** Round 3 is the one most often used as a substitute for the other
  two, and a paragraph can be flawless in register while carrying no argument.
- **A sentence carrying no number, threshold, named tool, mechanism, decision or falsifiable claim is
  deleted, not rewritten.** Two sentences with one fact: delete one.
- **A number stays only if the reader can say what it rules out.** "One number is decoration. Two
  numbers are a result." In motivating prose keep a number only when it is the argument.
- **Output per paragraph**: a table of sentence, fact carried, verdict. A failing paragraph is
  rewritten and re-audited, not patched.
- **The cut pass is separate**: 15 to 25 percent fewer words, same facts, no new fact or citation.
  A pass that lengthens has failed. Cut whole items, never connective tissue until sentences break.

## 4. Shapes that worked

Read `references/shapes.md` before writing any of these. In short:

| Unit | Shape |
|---|---|
| Abstract | the world; the measurement; what current methods lose, as a mechanism; "We introduce [concept], a ..."; consequence; "we introduce [Name], a ..."; training in one sentence; result with the comparison set counted ("[N] methods, including ..."); its bound; one robustness result; one implication |
| Introduction | facts with field-scale numbers; one question; a short verdict; "Our contributions." one paragraph each. No results of the authors' own: name the evaluation and cite it |
| Contribution | "We introduce X, a [noun] that [does Y]", mechanism in plain verbs, no adjectives on it |
| Results paragraph | claim with its number inside, against a named comparator with an appositive, then the pointer; one robustness sentence; mechanism next. "0.84 against 0.81 for gradient-boosted trees, the highest-ranked baseline (Table 1)" |
| Caption | bold claim title; one protocol sentence; lettered panels saying what is drawn and what it shows; every encoding named; n and statistic defined |
| Opening paragraph | the object of study at process level, no single dataset; field-scale numbers only; no own result |
| Conclusion | a measured fact with its number, then one concrete consequence |

## 5. Facts, claims and limitations

Detail: `references/claims-and-facts.md`.

- **One facts file holds every number the document may state**, with value, unit, comparator,
  source location and status, and an authority order between sources. It is the ledger of allowed
  values in the project's `GUARDRAILS.md`; a project that already keeps a separate `FACTS.md` may
  keep it, since `--facts` reads any Markdown file with a Retired heading. "Numbers that appear nowhere
  are not hedged; they are deleted."
- **The Retired list** holds superseded values and removed names, "delete on sight", and the gate
  fails on them (`--facts`).
- **Bound each claim in the sentence that makes it**: claim, then "whereas" plus the measured
  counter-fact. Every caveat has a named cause; uncertainty is a number or a missing control, never
  an adverb.
- **Declare every asymmetry in a comparison and print the number that beats you.**
- **Limitations**: one plain opener, a short list with one cause each, concrete next steps; each
  caveat stated once; taken from the paper's own discussion, never invented. Delete "honestly".
- **Integrity.** Choosing what to lead with is presentation; changing what the records support is
  misreporting. A contradicting result changes the claim. A weak or negative result goes to the
  appendix with its number and diagnosis, never out of the record. A reporting threshold applies to
  every result alike and is stated. When asked to leave a result out, write the honest form.
- **Citations**: at the claim, one fundamental source, no clumps. A missing source is
  `\citep{NEEDS_CITATION_shortdesc}`, which fails the gate; never an invented key. Never cite your
  own unpublished work as evidence.

## 6. Headings and terms

Detail and the full rejected list: `references/headings-and-terms.md`.

- **Every heading is concrete, scientific, self-contained, one idea**: a noun phrase or a claim that
  a figure in that section proves. Test: could it sit over a section of a Nature Methods paper
  without a reviewer querying it?
- Banned shapes: riddle, question or fragment, metaphor for a noun, abstraction with no object,
  invented count ("three symptoms"), non-standard term, a colon or comma (an unsplit heading), a
  fourth level.
- **Never re-title the author's sections.**
- **One name per concept** in text, figures, tables, replies and site. Reuse an existing term before
  inventing one; take the noun from the paper the sentence cites; define or cite every term at first
  use.
- **A rename erases the old name everywhere, "as if it never existed"**: prose, captions, table rows,
  figure labels, data keys readers see, LaTeX labels. Add the old name to `TERMS.txt` so the gate
  fails if it returns, and run `prose_qa.py <figure scripts> --ext .py --terms TERMS.txt --terms-only`
  over the code that draws reader-facing labels.

## 7. The author's text, outside text and the ledger

Detail: `references/intake-and-revision.md`.

- **Text the author wrote or accepted is placed, never improved.** Fix only errors (fact, number,
  pointer, citation key, hard limit); record other deviations in a header and say so once. If
  placing a file turns into rewriting it, stop and ask.
- **Text from outside the loop is measured before it is read**: paste byte for byte, then
  `scripts/measure.py accepted.tex incoming.tex` and the gate, keys by title and author, numbers
  against the facts file, a header of what it does not yet carry. "Recorded, not fixed." Its own
  self-audit and clean compile are not evidence about the text.
- **A new manuscript version means fact updates inside existing sentences**, old to new, listed.
  Snapshot first (`scripts/drift.py snap`) and give the path in the first report. A restructure is
  the author's call, shown as a plan.
- **No editing fan-out over the author's prose** unless they ask for it on a named file. Auditors
  report; one writer changes the text.
- **The ledger**: diff at sentence level, classify (FACT, CLAIM, STRUCTURE, WORD, SYNTAX, CUT,
  HEDGE, PROCESS), generalize to two more places, write both versions verbatim, propagate across the
  document, promote durable rules into the facts, terms or narrative files.
- **Trimming to a page budget moves and deletes whole blocks and never rewords**;
  `drift.py new --moved ...` must show 0 new sentences and 0 new numbers. Then
  `assemble_moved.py` gathers the moved files into one appendix and checks that every label is
  unique and every reference resolves.

## 8. Scripts

Python 3.9 or later, standard library only. Run from the skill folder or copy into the project.

| Script | Does |
|---|---|
| `scripts/prose_qa.py` | the gate: ban greps, sentences about the document, colons and semicolons, Markdown left in `.tex`, headings, unresolved markers, retired values (`--facts`), banned terms (`--terms`), frozen sentences (`--frozen`), word budget and page estimate (`--budget`, `--wpp`); `--terms-only` for figure scripts and site copy; `--self-test` plants one defect per check |
| `scripts/drift.py` | `snap` a snapshot; `delta` percent of words changed since it; `new` new sentences, new numbers and brace balance since it |
| `scripts/assemble_moved.py` | after a trim: one appendix from the `moved_from_<stem>.tex` files in manuscript order, each under a heading naming its source; checks duplicate labels and undefined references; `--self-test` |
| `scripts/measure.py` | intake measurement of incoming text against the last accepted version (and a rejected one): length, paragraphs, sentence lengths, cadence, citations, numerals, bold, cross-references, first person. The rows are the source project's; the script is new (suggested, not yet tested in real work) |

```bash
S=<skill>/scripts
python3 $S/prose_qa.py --self-test
python3 $S/prose_qa.py sections/ --draft --facts GUARDRAILS.md --terms writing/TERMS.txt
python3 $S/drift.py snap --snap writing/_snapshots/r1_<date> sections/*.tex
python3 $S/drift.py delta --snap writing/_snapshots/r1_<date> sections/*.tex
python3 $S/measure.py accepted/intro.tex incoming/intro.tex
python3 $S/prose_qa.py sections/ --facts GUARDRAILS.md --terms writing/TERMS.txt \
        --frozen writing/FROZEN.txt --budget 9000 --wpp 463
python3 $S/assemble_moved.py --moved-dir appendix --order writing/order.txt --top section \
        --out appendix/moved.tex --tex-root .
```

## 9. Check before anything is handed over

In this order (`references/qa-gate.md`):

1. `prose_qa.py` without `--draft`, with `--facts`, `--terms` and `--frozen`: clean, or each
   remaining hit named in the report with the reason (for example, the author's own sentence).
2. For a pass over existing text: `drift.py delta` and `drift.py new` against the snapshot; the
   numbers changed are exactly the ones meant to change.
3. Build until the log has no "Rerun" (the sibling `latex-typesetting` skill's `build_latex.py`
   does this out of tree and fails if it never settles) and read the log: no undefined citations or
   references, no "??" or "(?)" in the PDF. A fixed number of passes once left 64 of 76 contents
   page numbers wrong.
4. **Every number traces to the facts file**, checked by hand against the block's evidence list.
   Every status tag is honored in the prose.
5. **Read every heading and every paragraph you drafted** against the audit tests. The gate cannot
   see a metaphor heading, a subject that does not exist, a gap in the chain, or a number without a
   comparator.
6. Trace the ledger: every correction the author made is applied everywhere it applies.
7. **When the author wrote a governing brief, audit the deliverable against it**: one row per brief
   item, met or not met, with the file and line that shows it. Do the audit read-only, then fix in
   the main thread. The author's instruction: "do a strict adversarial yet constructive audit so
   everything that is in the brief is satisfied". Report unmet items plainly.
8. Report: what was drafted or changed, one line per section; the snapshot path; what the gate
   reported and what was left with a reason; numbers or readings you had to guess; open
   `[AUTHOR ACTION]` items; what was not checked.

When there is time, let one fresh reader at a time attack the draft with one lens (a journal editor
hunting sentences whose only content is that something matters; a referee hunting unsourced
claims and numbers absent from the facts file). They report; one writer changes the text. Rule on
every conflict between readers and write the ruling down. Output format and staging:
`references/qa-gate.md`, "Two-reader review".

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| prose drafted against headings | "wishy washy" | a narrative block with a claim sentence first |
| a whole section drafted, then audited | "generate one paragraph by one paragraph" | the paragraph loop with three ordered rounds |
| a bare number in an abstract | "such a number? meaningless" | a number with its comparator, or no number |
| clever headings ("the hinge", "Function follows position") | "no one will ever understand this" | concrete noun phrases in the field's terms |
| machine vocabulary ("symptom", "falsifiers") | "use my terminology from my papers" | the author's and the field's words, grepped by the gate |
| results in the introduction | "no result should be mentioned in the introduction" | the evaluation named and cited; results where they are owned |
| a rebuild of the author's chapters with new titles | "the titles were so nice and human now you made it all AI slop" | fact updates inside the author's sentences, from a snapshot |
| a supplied file merged onto the house style | "I told you to literally copy-paste" | paste byte for byte, record deviations in a header |
| an opening built on one example | "DO NOT fixate!" | the object of study at process level |
| random facts in the opening | "write like a scientist!" | field-scale numbers that carry the argument |
| a heavy agent rewrite | "do simple small surgeries" | one-sentence surgeries, logged old to new |
| editor fan-outs over the author's prose | "just fix the obvious mistakes" | auditors that report; one writer, in the main thread |
| a renamed variant left in a table | "as if it never existed" | the old name erased everywhere and banned in the gate |
| invented limitations and frameworks | "for limitations do not come up with new stuff" | limitations from the paper's own discussion |
| evaluative words ("strongest", "wins") | "strong or good or bad are not scientific" | measured relations ("ranks below", "the highest-ranked") |
| "less is more" applied by squeezing sentences | "you butchered them" | whole blocks moved or deleted, wording untouched |
| a gate that always printed ok | (found by planting a defect) | `prose_qa.py --self-test` |

## Reference files

- `references/levels.md`: the four levels with artifact, test and stop condition; contents tests; the six movements and their paragraph skeletons; positioning briefs for related work; the narrative audit.
- `references/narrative-blocks.md`: every block field, the status tags, and a worked ML block.
- `references/paragraph-loop.md`: tests T0 to T7, the three rounds, the audit table, a worked paragraph, the cut pass.
- `references/shapes.md`: abstract, introduction, opening, contribution, results paragraph, caption and conclusion, with examples.
- `references/headings-and-terms.md`: the heading rule with rejected examples, term discipline, the rename procedure.
- `references/claims-and-facts.md`: bounding claims, limitations, integrity, the facts file and retired list, manuscript versions, citations.
- `references/intake-and-revision.md`: whose text it is, intake of outside text, version updates, the edit ledger, trimming.
- `references/qa-gate.md`: what the gate checks and cannot check, extending it safely, the LaTeX pre-flight, the two-reader review.
