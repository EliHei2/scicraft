# Adversarial readers for long documents

A chapter, a full paper or a long report is too much for one careful pass in one sitting. The method that held
up: fresh-context readers each take one disjoint slice and return edits as data; one writer checks and applies
them by script. In one technical report, four readers returned 106 edits and no number changed. On a methods
chapter, the same kind of pass surfaced four factual errors as a side effect (a miscounted step list, two
sentences contradicting each other about one reference, a wrong axis name, a justification against an
alternative that was never a candidate), because rewriting a sentence forces someone to read it.

## When not to use readers

- **On the author's own prose that they asked you to keep.** A pass of twelve humanizing editors over an
  author's chapters was undone by a byte-exact restore from the snapshot; the author's words were "do simple
  small surgeries". For the author's text, make one-sentence edits yourself and list each one (SKILL.md
  section 5).
- **Under a deadline.** Hand over what is done; do not start helpers the user did not ask for.
- **To make up for not reading.** Readers miss self-narration (pattern T8) almost entirely, so you read the whole
  document yourself in any case.

## Setup

1. Snapshot the file and run the counts: `frame_density.py` for the before numbers, and keep the snapshot for
   `preserve_diff.py`.
2. Rewrite one paragraph yourself in the target voice. It goes into every brief as the model.
3. Split the document into disjoint slices at section boundaries, by line range. Four slices of a 15- to 20-page
   report worked. Record each slice's line range: `apply_readers.py --lines` rejects an edit that matches outside
   it.
4. Give each reader the brief below, its slice and line range, and the paths of the rule files
   (`references/patterns-general.md`, `references/register-technical.md`, and the voice sample if there is one).
   Readers get the text and the rules, never your reasoning about what is wrong with it.

## The reader brief

Copy it and fill the brackets.

```
You are a harsh adversarial copy editor for [document type], reading lines [A]-[B] of [file].
Find every sentence that reads as machine-written, using the patterns in [rule files], and propose a
sentence-level fix. Model voice: [the paragraph rewritten by the coordinator, or the writer's sample].

Rules:
- You return edits. You do not edit the file.
- Keep every number, unit, version, equation, citation key, label and reference exactly as written.
- Add no fact, name, number, citation or claim. If a fix needs a detail the text does not have, leave
  the sentence and report it as a FLAG.
- Add no em dash, no spaced dash, no semicolon and no mid-sentence colon. Add no "not X but Y",
  "X, not Y" or "rather than".
- Edit sentences, not paragraphs. Do not reorder paragraphs or change headings.
- Keep a caveat that names its cause. Do not soften or strengthen any claim.
- ORIGINAL must be copied exactly from the file and long enough to occur exactly once in it.

Write a JSON list to [slice]_edits.tmp.json, then rename it to [slice]_edits.json when complete:
[{"ORIGINAL": "...", "REPLACE": "...", "WHY": "pattern number and one phrase"}]
Report factual problems you notice (a count that does not match a list, two sentences that contradict
each other, a caption that does not match its figure) as entries {"FLAG": "...", "WHERE": "line N"}.
Finish within [minutes] minutes.
```

A hard limit of 8 minutes per reader was used on a chapter-scale pass. The temporary name matters: in one pass
the applier ran one second after a reader wrote its first draft. `apply_readers.py` skips entries without
ORIGINAL and REPLACE, so FLAG entries can share the file.

## Apply

```bash
S=<skill>/scripts
python3 $S/apply_readers.py draft.tex slice_1_edits.json --lines 1-240 --dry-run    # read the rejects first
python3 $S/apply_readers.py draft.tex slice_1_edits.json --lines 1-240
python3 $S/preserve_diff.py draft.before.tex draft.tex
python3 $S/frame_density.py draft.tex
```

- **Exact-once matching.** An ORIGINAL that occurs zero times or twice is rejected, never applied to the first hit.
  A rejected edit is fixed by hand or dropped. Running the applier again is safe: edits already in the file are
  reported as applied.
- **One writer.** Only the coordinator applies edits. Decline an edit that contradicts the author's explicit
  wishes or the voice sample, and an edit that only changes taste.
- **Verify every FLAG against the source** (the figure, the table, the script, the run record) before changing a
  fact. In one pass a caption described an average over five draws where the figure showed a single draw; that was
  a real error. In
  the same pass a reader's doubt about which code produced a table was rejected, because the script header named
  the commit. A fact is changed only on evidence, and the report says what changed and why.
- Then read the whole document top to bottom yourself, for self-narration and for paragraph-scale tells.
