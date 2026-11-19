# Replies, messages and prose

For text that leaves as text: a reply to reviewers, a cover letter, a message to a supervisor, release notes, a
paragraph pasted into a shared document. How to write it is in `rebuttal`, `paper-writing`, `author-voice` and
`humanizer`; statistics wording is in `stats-reporting`. This is the gate.

## Scripted

- **Count what the platform counts.** Characters per comment against the limit (5,000 on an OpenReview-style
  venue; the final replies sat at 4,900 to 4,990), after every edit. Six characters over led to a two-word trim.
- **Count the pieces.** One general comment plus exactly one per reviewer. Six comments for three reviewers drew
  "why do we have total of 5 instead of 4".
- **Quotations verbatim.** Every quoted sentence (a reviewer, a guideline, the paper) matched character for
  character against its source file.
- **Every number in the text found at its source.** "All 90 numbers in the replies are found in the blue PDF" was
  the gate of one round. A number that is not in the built document either comes from a record you can name or is
  removed. Full number and claim audits: `integrity-audit`.
- **Every cited line, page, table and appendix resolved** in the built PDF, after the last rebuild (see
  `checklist-latex.md`).
- **Banned strings**, one list file per project: the author's banned words, old names of renamed things, and
  punctuation the house style bans. One reply style banned em and en dashes, semicolons and colons inside sentences,
  enforced by script:

```bash
grep -nE '—|–|;' replies.md
grep -nE '[a-z]: [a-z]' replies.md            # a colon inside a sentence
grep -niE -f banned.txt replies.md
```

- **Nothing added or dropped by a polish.** Before and after a humanizer or wording pass: the multiset of number
  tokens is unchanged, the set of citation and reference keys is unchanged in both directions, and the text grew by
  about 3 to 5% (a shorter text after a de-slop pass means facts were deleted). `text_drift.py before after --show`
  lists every sentence that moved.

```bash
python3 -c "import re,sys,collections as c; a,b=[c.Counter(re.findall(r'\d+(?:\.\d+)?',open(f).read())) for f in sys.argv[1:3]]; print('lost',a-b,'added',b-a)" before.md after.md
```

## Read

- **Every term defined or cited at first use.** A probe, a test, a statistic, an abbreviation. A terms audit of one
  paper found 49 undefined or late-defined terms.
- **One name per thing**, the field's term, the one the earlier version used. Keep a banned-variants list and grep
  it.
- **Counts say what they count**: "[k] of [n] subsets", "higher median than a method on a task, [k] of [n]", never a
  bare "[k]/[n]".
- **Claims as strong as their evidence**: the bold lead sentence of each answer states exactly what the cited
  lines show; a statement true under one metric and false under another is deleted.
- **Every exclusion and exception checked in the records** before it is printed.
- **A message to a person** reads as the author's own: short first-person paragraphs, no headings or lettered
  options, at most three plain questions, the word count checked before it is shown (about 450 words was the
  target for a message to supervisors).
- **The author's own worked-out draft** was polished, not rebuilt: only what is wrong or named changed, and the
  changes are listed. Compare against their last version (`text_drift.py`).

## Hand over

The paste-ready text in a file (a plain Word file with the Markdown typed literally, plus a `.md`), the character
count per piece, the posting order when it matters (public reply first, the private note within minutes, the
answer to the other reviewer last), and what to check on the platform before posting.
