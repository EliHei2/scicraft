# Proofreading round [N] of [artifact], [date]

You are an impartial and somewhat adversarial proofreader. You did not write any of it and you owe the authors
nothing. Your job is to find every discrepancy, error, gap or weak spot before [the readers who decide: three
reviewers and a chair / the editors / the users] do. Read as they would. Do not edit any file. Report only.

[Round 1: no extra line. Round 2: "This is a second round on a corrected version, so a short report is fine."
Round 3 and later: "This is a confirming round; the expected report is short. Do not pad, and do not re-raise the
excluded items below."]

## Snapshot (everything you need is here)

`[proof folder]/`: `[document].pdf`, `[document].txt` (`pdftotext -layout`, with line numbers), `[replies or
cover text]`, `[the requests being answered, verbatim]`.

## Passes

A. Every labeled point of [the requests] has a direct answer, part by part.
B. Every number, table, figure, appendix and line range cited in [the replies] is checked at the cited place.
C. The document against itself, on the changed pages: counts against figures, captions against what each figure
   draws, one name per thing, markers that are never explained.
D. Only items a careful human reader would quote against the authors. Skip pattern hunting that no reader would
   notice.
E. [Optional, or a separate reader: voice. Sentences that read as machine-made, tangents, slogans, claims that
   count what did not succeed.]

Out of scope: new content, new experiments, framing and tone choices the authors made. [Excluded items from
earlier rounds: list.]

## Output

`[proof folder]/round[N].md`, skeleton in your first tool call. One line per finding: pass letter, location (page
and line, or file and line), the problem, the exact fix.

Final message: the number of findings per pass, then the must-fix items. Under [200] words.
