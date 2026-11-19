# Digest: [question this digest answers]

Agent: [role]. Repository: [repo] @ [commit]. Date: [YYYY-MM-DD].
Primary sources: [arXiv IDs or DOIs, each with version], [official code repository @ commit].
All quotes are verbatim from the primary source; section, equation, table and figure numbers are the papers' own.
Tags: [V] verified (I opened the source on [date]; link given), [U] unverified, [C] computed by me from a
downloaded file (method stated). Self-flag every LIKELY cell so it is re-checked before it enters a manuscript.

## 0. Bottom line

| what | mechanism | role here | measured effect in the source (table or figure) | tag |
|---|---|---|---|---|
| [model or method] | [what it does] | [adopt / adapt / reject] | [number, Table n] | [V] |

## Corrections to the brief

[Where the brief or a chat-generated plan states something the sources contradict. Asked for, so here they are.]

## 1 to n. Per sub-question

[One section per question in the brief. Quote, then say what it means for this design.]

## Probes

[Each probe imports the repository's own functions by file path, runs on CPU, and has its `.out` committed.]
| probe | what it measures | `.out` |
|---|---|---|

## The decision

[The exact code shape: module, function, config key, default equal to current behavior.]

**What it should do, so it can be falsified:** [the measurable before and after, on a probe through the
deliverable].

## Arguing against my own recommendation

[The strongest objection, stated as its best advocate would.]

## The runner-up, and why it lost

## Claim ledger

| claim | source (paper section, eq., or probe) | tag |
|---|---|---|
