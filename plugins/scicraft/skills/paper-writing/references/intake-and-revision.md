# Intake, the author's text, revisions and the edit ledger

## Whose text is it

| Text | House style applies? | What the agent does |
|---|---|---|
| drafted by the agent in this loop | yes | fix it, audit it, gate it |
| written or accepted by the author | no | place it; fix only errors (fact, number, pointer, citation key, hard limit); record any other deviation in a header and say so once |
| from outside the loop (a collaborator's draft, another model's rewrite, a zip) | not before intake | measure it before reading it (below); the author decides what changes |

**Text the author supplies is theirs. Place it; never improve it.** Asked to "replace the
introduction with the text in this package and apply our style", an agent merged a 9,786-word file
onto the house style, every edit defensible, and produced "a chapter [they] did not write and had not
asked for". The tell: **a request to place a file has produced a rewrite.** If following an
instruction means rewriting more than moving, the instruction has been misread. Ask, or paste and
annotate. Check after placing:

```bash
diff <(sed -n '/\\section/,$p' sections/intro.tex) supplied_intro.tex   # empty except documented key fixes and floats
```

**Once the author has humanized a text, the wording is frozen.** Change it only for an error, a
number, a pointer or a hard limit, never "for bettering it". When a polished text from the author is
not followed word for word, list every deviation with its reason. When the author's sentences read
less fluent to you than yours, "my ear is wrong". Keep the author's roughness: a uniform finish is
itself a machine signal; fix typos the author would fix and leave their constructions alone.

## Intake of text written outside the loop

A package's own self-audit is evidence about intent, never about the text, and a clean compile is
not a clean chapter. One package shipped a true self-audit and "LaTeX compile: successful. Undefined
citation warnings: 0." It was 2.03 times the accepted length, 98 percent of the rejected length,
carried 87 blocking gate hits against 1 in the accepted version, and 28 absent citation keys, nine
of them duplicates of works already cited.

```
a PASTE     the supplied file is the section, byte for byte
b EXCEPT    two mechanical edits only: citation keys that break the build or double-print an existing
            work; float environments if a figure plan was supplied. No sentence added, moved or
            rewritten, including around a float.
c MEASURE   against the LAST ACCEPTED version, never the repository:
              python3 scripts/measure.py accepted.tex incoming.tex [--rejected rejected.tex]
              python3 scripts/prose_qa.py incoming.tex --facts GUARDRAILS.md --terms TERMS.txt
            a row closer to the rejected version than to the accepted one is a regression
d KEYS      resolve every citation key by title and author
e NUMBERS   every numeral against the facts file
f HEADER    a comment at the top: "what this section does NOT yet carry", one line per deviation,
            RECORDED, NOT FIXED. Check by name what a replacement drops: required pronoun, frozen
            sentences (prose_qa.py --frozen), the figure plan, the argument-carrying numbers, every
            honesty statement, especially a negative result.
g HAND BACK say it once. The author decides. Every row is decided on its own; a package is never
            adopted or refused whole.
```

What an incoming text gains is usually a distinction that makes a later claim sayable, rarely better
sentences. Example of such a distinction: a method that uses a reference as a prior may not be
validated by agreement with that same reference.

When a whole section is replaced, list beforehand, by name, what lives in no single section (frozen
naming sentences, the mandated pronoun, the figure program, certified numbers, honesty statements)
and check each afterwards. One introduction replacement dropped all five while the gate passed.

## A new version of the science: fact updates inside the author's sentences

"Update against the new version" means old value to new value inside the existing sentences, listed.
Never a restructure, new headings or an editor fan-out over the author's prose. A "really update the
works" request once produced twelve new chapter files, new titles and a fan-out of editor agents; it
was rejected whole and restored byte for byte from a snapshot.

1. Snapshot before touching anything, and give the snapshot path in the first report:
   `python3 scripts/drift.py snap --snap _snapshots/r1_<date> sections/*.tex`.
2. Restructuring is level 1 and the author's call: show it as a plan and stop.
3. Apply one-sentence surgeries. Log each as `{file, old, new, source_quote}`.
4. Where the science under a part changed, rewrite the technical paragraphs inside the author's
   skeleton and touch the narrative one sentence at a time.
5. Verify: `drift.py delta` (how much changed; one round that replaced 37 to 90 percent of the
   author's sentences cost a whole extra round), `drift.py new --max-new-numbers N` (only the
   intended numbers changed), the gate, the build.
6. No humanizing pass over the author's text unless they name the file. In the final phase, fix only
   the obvious mistakes, in the main thread, visibly.

## The edit ledger

Every correction by the author is diffed, classified, generalized, written down and propagated
before the next section is drafted. "Every rejected pass ... has been re-rejected because the
correction lived in a conversation instead of a file." Template: `assets/EDIT_LEDGER_TEMPLATE.md`.

1. **Get both versions at sentence granularity**: `git diff`, or save your version to a scratch file
   and diff.
2. **Classify every change.**

| Class | What changed | What to fix besides the line |
|---|---|---|
| FACT | a number, comparator, status, attribution | the facts file |
| CLAIM | what the sentence asserts | the narrative block |
| STRUCTURE | order of sentences or paragraphs, a split or merge | record which movement it moved to |
| WORD | a noun or verb swapped | add a row to the terms file |
| SYNTAX | clause order, a sentence split or joined | record before and after verbatim |
| CUT | deleted with nothing put back | record what kind of nothing it carried |
| HEDGE | a qualifier added or removed | the status tag in the block was wrong |
| PROCESS | how the work is done | the governing notes |

3. **Generalize.** Find two more places the change applies. If none, log it as `local`: "three local
   fixes with the same shape are a rule nobody spotted".
4. **Write the entry**, both versions verbatim. A paraphrase of what the author wrote is useless as
   evidence.
5. **Propagate.** Grep the whole document, fix every instance, record the counts.
6. **Promote** a durable rule into the governing file (facts, terms, narrative, gate). "The ledger is
   the log; the craft documents are the law."

Don'ts: do not thank and move on; do not fix only the sentence the author fixed; do not smooth their
wording toward yours; do not argue in the ledger.

Signal words: "meaningless" means a number with no comparator. "Wishy washy" means no checkable
content; the repair is deletion, then evidence, never rewording. "No one will ever understand this"
means a heading or a metaphor; use the field's term. A deletion with nothing put back is the
strongest signal.

When the author accepts a rewrite made elsewhere (by a colleague or another model), measure the diff
and write a standard from it: a table of versions, the rules read off the diff, and the losses to
restore listed separately. "learn what changed, in text/grammar/style/flow".

## Trimming to a page budget

A page budget is met by moving and deleting whole blocks, never by rewording. The brief given to a
trimming agent, in the author's lesson: "[their] sentences are [theirs]. You trim by DELETING and MOVING. You
do not write."

- MOVE: a whole float with label and caption, or a whole procedural paragraph with its run-in head,
  verbatim into `appendix/moved_from_<stem>.tex`, in original order.
- DELETE: the second and third statement of a caveat, signposts, recaps, sentences restating a
  number already in a caption or table, paragraphs reprising the conclusion, redundant glosses.
- KEEP: opening and handoff (may lose sentences, never reworded), contribution blocks, author-action
  markers, equations the text reasons about, claim-carrying floats, inbound labels, every number a
  remaining sentence depends on.
- Forbidden: any new or reworded sentence or heading (except a connective of at most eight words,
  logged with its line), changing numbers, citations or labels.
- Order: floats, then procedural paragraphs, then redundancy. One page is about 520 words, one
  figure or 0.6 of a table at the layout measured; measure yours. "Reach the target and stop; do not
  overshoot by more than one page."
- Verify: `drift.py new --snap <snapshot> <file> --moved appendix/moved_from_<stem>.tex
  --allow-connectives` reports 0 new sentences and 0 new numbers, brace balance 0; every
  cross-reference target still defined.
- Report per section, under 350 words: words before and after, words moved, floats moved, paragraphs
  moved and deleted (by their first six words), connectives added, what was kept despite its cost.
- Assemble: after the trim, gather the moved files into one appendix, in manuscript order, each under
  a heading naming the unit it came from, input the result once from the main file, then rebuild. In the source work a short script did this
  after every trim; the port is `scripts/assemble_moved.py`, which also fails on a duplicate label (a
  float copied instead of moved) or a reference with no target:

```bash
python3 scripts/assemble_moved.py --moved-dir appendix --order order.txt --titles titles.tsv \
        --top section --out appendix/moved.tex --tex-root .     # --top chapter for a book
```
