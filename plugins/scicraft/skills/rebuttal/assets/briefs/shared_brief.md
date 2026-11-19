# Shared brief for everyone working in `[rebuttal folder]`

Every agent brief opens with: "Read BRIEF.md first and obey it." Build one exemplar output (one table, one reply)
before any agent starts, and name it below, so that every agent copies the same form.

## Goal
[One paragraph: what the rebuttal must achieve, for which readers, in which files.]
The analyses are done. Do not run or re-score anything. [Or: the experiments listed in EXPERIMENTS.md are running;
their results arrive in results/ and slot into the places marked [PENDING: what].]

## Paths and ownership
- Work only inside `[folder]`, and only in the files your brief names. Never edit the submitted source, the records
  or anything another agent owns.
- Exemplar to copy: `[path]`.

## The through-line (from the lead author; everything serves it)
1. [The main claim, in the author's words.]
2. [The second claim.]
3. [What the new experiments show, and which reviewer asked for them.]

## Sources of truth, newest first
1. `[records: results/*.json, tables/*.tex]` (frozen [date]).
2. `[the paper as posted: paper.txt]`.
3. `[the author's notes and decisions]`.
If two sources disagree, the higher one wins. If a number exists nowhere, write `[PENDING: what]`. Never invent or
estimate a number.

## Integrity floor
- Every sentence is true and supported by the paper as posted. Every number is traced to a record and printed in the
  paper or appendix. Every quotation is verbatim.
- Results that weaken a claim stay in the record and in the appendix with their numbers. Choosing what the replies
  lead with is the author's call; changing what the records support is not allowed to anyone.
- Decisions taken after results were seen are stated where the result is reported.

## Binding decisions by the lead author
- [Names, the one statistics language, the reported comparison set and training length.]

## Words that must never print
[Internal run names, code identifiers, hardware names, internal task codes, the names of tools or models that
helped, reviewer IDs outside the reply that addresses them.]

## Voice
Lead with the claim, then the evidence, at most one reason. Short declarative sentences, one fact each, numbers over
adjectives, "we" and active voice. Say each thing once and point to its place. No dashes as punctuation, no inline
colons or semicolons in new text, no "not X but Y", no filler openers, no slogans. Keep the field's terms.

## When you finish
Reply in under 200 words: what you made, the file paths, and every problem you found (a number that disagrees between
sources, a claim you could not trace, a result that contradicts a claim). Do not bury problems. List any rule of this
brief you broke. Longer notes go to `_notes/[your name].md`.
