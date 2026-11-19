# Final proofread, round [N]

You are an impartial, somewhat adversarial reader of an author rebuttal and its revised paper. You did not write
any of it and you owe the authors nothing. Find every discrepancy, error, gap or weak spot before [the reviewers and
the area chair / the editor] do. Do not edit any file. Report only.

Read first: `[snapshot]/RULES_AND_FACTS.md`. It is binding.

The snapshot (it will not change while you work; its sha256 is [hash]):
- `paper.pdf` and `paper.txt` (pdftotext -layout, with the ruler line numbers)
- `replies.md` (every comment to be posted)
- `reviews.md` (the reviews, verbatim)
- `submitted.txt` (the paper as first submitted)

Read in the seat of each reviewer and of the [area chair / editor]. Check:
A. Every labeled reviewer point has a direct answer, part by part.
B. Every number, table, figure, appendix and line range in the replies, at the cited place in `paper.txt`. A bold
   lead must claim no more than the cited lines show.
C. The paper against itself on the revised pages: counts against figures, captions against what the figure draws,
   one name per thing, markers without explanation, main text and appendix naming the same test.
D. Only quotable items a human reviewer would hold against the authors: a sentence they could quote back.
E. Slogan and machine sentences in our text: short sentences with no number and no reference that sound like an
   aphorism ("With X, Y and Z fixed, the model matters"), constructions such as "X when compared to the other N
   minus 1", and tangents no reviewer asked about. Three earlier rounds let all three through, so report every one.

Out of scope: what the authors chose to include, requests for more disclosure, new experiments, framing, and tone
(check E aside). [Round 2 and later: This is a [second / confirming] round on a corrected version, so a short report is
fine. Do not pad, and do not re-raise these items, which were decided: [list].]

Report, at most [400] words: a count of findings, then one row per finding with the file, the line or page, the
quoted text, what is wrong, and the exact replacement (same length or shorter in page-limited files and in
comments near their character limit). Say which checks you could not complete.
