# EDIT LEDGER: [author], [document]

The log of every change the author made to text written for them, with the rule it teaches. Newest entry at the
bottom. A durable rule is promoted into [STYLE.md or the governing style file]; the ledger keeps the history.

Classes: FACT, CLAIM, STRUCTURE, WORD, SYNTAX, CUT, HEDGE.

## Procedure for each entry

1. Diff the author's version against what was delivered, at sentence level.
2. Classify every change.
3. Find two more places the rule applies, or mark it `local`.
4. Write the entry below.
5. Grep the whole document for siblings, fix each, record the counts.
6. Promote the rule if it is durable.

## Entries

### E01 . [YYYY-MM-DD] . [CLASS] . [one-line rule]
**Trigger** [the author's words, verbatim]
**Before** [what was written for them]
**After** [what they wrote or required]
**Generalizes to** [the class of text, and how to find its siblings: a grep pattern where possible]
**Propagated** [n found / n fixed, or pending]
**Law lives in** [the file and section that now carries the rule]

### E02 . [YYYY-MM-DD] . [CLASS] . [one-line rule]
**Trigger** [...]
**Before** [...]
**After** [...]
**Generalizes to** [...]
**Propagated** [...]
**Law lives in** [...]

## Gate patterns collected from the ledger

```
[pattern]    # E[nn]: [what it catches]
```
