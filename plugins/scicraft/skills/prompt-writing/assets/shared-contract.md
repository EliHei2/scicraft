# [Artifact]: contract for every agent. Read all of it before you start.

[One paragraph: what is being made, for whom, and the deadline. "The revised paper is submitted tomorrow."]

## 1. The operator's instructions, in their words ([date])

"[verbatim]"

Added [date]: "[verbatim]". This overrides anything earlier that conflicts with it.

Binding lines from the project's governing documents, quoted: short goal [S<n>] "[text]"; guardrails [G<n>]
"[rule text]", [G<m>] "[rule text]"; definition of done "[checks]". `GUARDRAILS.md` wins over this contract.

## 2. What you may and may not do

- [Do not run or re-score anything.] [Do not edit any file outside your lane.] [No git, no job submission.]
- Interpreter: `[command]`. Build: `[command]`. You may write only under `[folder]` and your own output path.

## 3. The through-line

Every output serves these claims, in this order:
1. [claim]
2. [claim]

## 4. Sources of truth, newest first

1. `[file]`: [what it holds]
2. `[file]`: [...]

If two sources disagree, the higher one wins. [Superseded drafts]: rejected as [off-target]. Do not build on them.
Pasted advice and older audits in `[folder]` are hints to check, not facts.

## 5. Honesty

- Every number comes from a source above. Write `[PENDING: what]` where a number is missing; never invent one.
- Every sentence is true and printed in [the source of record].
- A weak or mixed result keeps its number. It may move to [the appendix]; it does not leave the record.

## 6. Binding decisions

- [Decision, date, verbatim where possible.] Do not re-litigate.

## 7. Words and forms that must never appear

- Internal names: [list], with the reader-facing term for each: [X -> Y].
- Voice: no [em dashes, "not X but Y", slogans, glossary boxes, bold walls, middle-dot separators].
- [Domain list.]

## 8. Rules for the artifact

[For figures: the style module to import, the composer call, sizes in mm, the three type tiers in pt, color roles,
the interval type, the self-check loop (render, read the PNG, zoom crops), reference images to learn the look
from. For text: register, length per unit, citation form. Load the skill `[sibling skill]` before you start.]

The exemplar is `[path]`. Match it in look, granularity and length.

## 9. Who makes what

| Agent | Makes | Files it owns |
|---|---|---|
| [lane] | [output] | [files] |

Agents that need another agent's output start after it exists.

## 10. Report

- Create your output file with a section skeleton in your first tool call, then fill it. If you cannot write files,
  put the full findings in your final message.
- Final message: under [200] words. Every problem you found, then your rule slips (any rule above you broke). Do
  not bury problems. Longer notes go to `[folder]/_notes/<your-lane>.md`.
- Read-only lanes return proposed edits as JSON `{file, old, new}`, where each `old` occurs exactly once in its file.
  Record a skip as `new` equal to `old`. The lead applies them.
