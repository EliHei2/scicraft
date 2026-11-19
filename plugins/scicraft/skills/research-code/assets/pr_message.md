<!--
PR message template. Save one file per branch outside the repository (for example
../pr-descriptions/<branch>.md) and do not commit it. Delete these comments before use.
Rules: 3 to 5 short paragraphs, no headings, no tag on the left, no dashes as punctuation, every
identifier in backticks, the outputs specified, defaults stated. The first commit message on the
branch carries the same text.
-->
Adds `[command or function]` [one sentence: what it does for the user]. [One sentence: why, with the
issue or the measured problem, for example "the reader dropped [N]% of rows without a message".]

`[command] [positional args] [--flag VALUE]` writes `[output file]` with columns `[col_a]` ([type],
[meaning]), `[col_b]` ([type], [meaning]) and `[keep]` (bool, [rule that sets it]). [Coordinate space,
units or `obs` keys if the consumer needs them.] Names follow `[consumer]`'s spec: [the one rule that
matters, for example how an id-column clash is resolved].

Defaults leave current output unchanged: `[--new-flag]` defaults to `[value]`, which reproduces the
previous behavior. `[--opt-in-flag]` turns on [what]. [If a default does change results: say so here,
with the size of the change, and file it as a separate fix.]

Not in this PR: [what is deliberately left for later, one sentence]. Review: `[path/to/main_file.py]`.

No new dependencies. Closes #[N].
