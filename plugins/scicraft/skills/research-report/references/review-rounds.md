# Review rounds

A report sent to a supervisor gets read cold. Before it goes, have it read cold by agents that each look for one
kind of failure, and apply their findings through a script that cannot change a number. The procedure for running
adversarial agents in general is `adversarial-audit`; this file holds the two briefs that mattered for reports.

## 1. Freeze the round

Record the md5 of the source before launching readers. Readers return edits against that version; if the file
changed, their edits are checked against the current file before use. Agents that audited a moving file produced
edits that no longer matched.

## 2. The outside reader

One agent, briefed as:

> You are a co-author or supervisor who knows <field> in general and has NOT followed this work. You have never
> heard of: <list every internal term, run name, variant label and count>. Read <file> from the top. For every
> term, number or claim you could not explain to a colleague, return: the exact text, why it is unclear, and a
> plain replacement. Cite the data file behind any number you question. Do not edit the file.

What it caught in the source report: the summary never said which claim it answered; an over-broad claim; a
contradiction between two sections; three undefined internal terms; an unexplained derived count; a dataset
never described; which run had been recomputed.

Apply the fixes without restructuring the document, and tell the user which fix you declined because it could not
be verified.

## 3. Line edits with invariants

For a language pass over a long report:

1. Rewrite one caption yourself as the target voice and include it in the brief.
2. Split the source at section boundaries into three or four slices.
3. Brief one editor per slice: "harsh copy editor; change no fact; return edits, do not edit the file", output a
   JSON list of `{"original": ..., "replacement": ...}`.
4. Apply with a script that, for each pair, checks: the original occurs exactly once and inside the slice; pairs
   do not overlap; the multiset of numbers (`re.findall(r"\d+(?:\.\d+)?", s)`) is the same before and after; HTML
   tags, TeX and symbols (>= x 10^ µ %) are unchanged; no em dash, banned word or "not X but Y" is introduced. Pairs
   already applied are skipped, so the script can run twice. After all pairs, check the whole file's numbers and
   tags again.
5. Editors also report factual inconsistencies they notice. Check each against the figure or the script before
   changing anything: one caption claimed more draws than the figure showed; another
   flag was rejected because the script header named the commit.

One such pass made 106 edits and changed no number.

## 4. Other lenses

When there is time: a hostile fact-checker who plays the person who raised the question; a terminology auditor who
lists every term with its meanings across the document; a figure-legend reader. Every reader returns OLD to NEW
pairs plus a check that each OLD occurs once. Verify each MUST-FIX against the data with a one-line check before
applying it, and list the rejected points with the reason.

Under a deadline, start no new readers. Ship what builds, name what was not reviewed, and iterate.
