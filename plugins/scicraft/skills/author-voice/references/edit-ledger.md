# The edit ledger

Every time the author rewrites, cuts or rejects text, the change is evidence of a rule. The ledger turns that
evidence into a rule and applies it everywhere before the next section is drafted. It exists because "every
rejected pass ... has been re-rejected because the correction lived in a conversation instead of a file."

The author asked for it in plain terms: "I'm gonna rewrite this introduction part in human voice, watch and learn
exaclty what changes"; "chatgpt did a great job and cleaned up your mess, ultrathink, and learn what changed, in
text/grammer/style/flow".

## Procedure

1. **Get both versions at sentence level.** `git diff --word-diff` on the committed file, or save your version as
   `before.md` and diff it against theirs. Diff against what you last delivered, not against an older draft.
2. **Classify every change:**

| Class | What changed | Also fix |
|---|---|---|
| FACT | a number, a name, a status | the fact base |
| CLAIM | what a paragraph asserts | the outline or narrative notes |
| STRUCTURE | order, merge, split | record which shape they moved it to |
| WORD | one term for another | add a row to the terminology table |
| SYNTAX | sentence shape | record before and after verbatim |
| CUT | a deletion with nothing put back | record what kind of nothing it carried |
| HEDGE | a qualifier added or removed | the status of the evidence was wrong |

3. **Generalize.** Find two more places the rule applies. If none, log it as local. Three local fixes with the
   same shape are a rule nobody spotted.
4. **Write the entry** (format in `assets/edit_ledger_template.md`).
5. **Propagate.** Grep the whole document for siblings, fix every one, record found and fixed counts.
6. **Promote.** A durable rule moves into the governing style file; the ledger keeps the history.

## Signal words

| The author says | It means | The repair |
|---|---|---|
| "meaningless" (on a number) | the number has no comparator | add the baseline or the threshold it beats, or delete it |
| "wishy washy" | no checkable content | delete, then add evidence if the point is needed |
| "jibber jabber" | the sentence's fact is already carried by a neighbor | delete one, do not merge |
| "no one will ever understand this" | a coined heading or a metaphor | the field's term |
| "robotic", "machine written" | flow: sentences that do not set up the next one | reorder so each sentence answers the question the previous raised |
| "AI slop" | an imported pattern (a classifying sentence, a slogan, a self-titled block) | find the pattern, grep for siblings |
| a deletion with nothing put back | the strongest signal: the passage carried nothing | delete its siblings too |

## Do not

- Do not thank and move on.
- Do not fix only the sentence they fixed.
- Do not smooth their wording toward yours: "If [their] replacement reads less fluent to me, my ear is wrong."
- Do not argue in the ledger. A disagreement is a question to the author, asked once.

## Worked entries (anonymized)

```
### E04 . 2026-03-04 . WORD . Use the author's terms; never import a technical register
Trigger      "please use my terminology from my papers, I never used [that word]"
Before       "The second experiment is the falsifier for the scaling claim."
After        "The second experiment tests the scaling claim."
Generalizes  every imported word with zero hits in the corpus; grep the 30 rows of the terminology table
Propagated   9 found / 9 fixed
Law lives in TERMINOLOGY.md, row "falsifier"; gate pattern added
```

```
### E02 . 2026-03-05 . FACT . A number stays only if the reader can say what it rules out
Trigger      "such a number? meaningless, this is meaningless."
Before       "Replicates agree closely (R = 0.71)."   (invented)
After        the number moved to the results with its comparator, the abstract states the finding without it
Generalizes  every bare number in an abstract or introduction; grep [0-9]+\.[0-9]+ in those files
Propagated   6 found / 6 fixed
Law lives in STYLE.md, numbers section
```

## Learning from an accepted rewrite

When the author accepts a rewrite made elsewhere, measure the difference before and after: words, sentences,
median and p90 sentence length, numbers and citations per 1,000 words, headings. Write the rules you read off the
diff as a standard, and list separately what the rewrite lost that must be restored (a dropped qualifier, a number
that carried the argument, a mandated first person). One accepted rewrite of an introduction ran flatter than the
author's corpus (mean 16 words, p90 25, longest 43); the standard took those numbers for that register.
