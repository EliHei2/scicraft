# Design brief: [topic in one line]

Status: DRAFT
Date: [YYYY-MM-DD]
Topic: [topic]
Repository and commit under discussion: [repo] @ [commit]. Pull before reading anything else.

## 1. The lead's questions, in their own structure

Quoted, dated, never paraphrased beyond structure. The latest message overrides earlier ones; say which.

- Q0 ([date]): "[the lead's words]"
- Q1 ([date]): "[the lead's words]"
- Q2 ([date]): "[the lead's words]"

## 2. The deliverable

[One sentence: what object ships, and through which code path it is read. For example: "the frozen table
encoder's pre-projector output, read by the linear probe of record".] Every proposal is judged by whether it
moves this object.

## 3. Hard constraints (the lead's; do not reintroduce a rejected option)

| constraint | set by, date | why |
|---|---|---|
| [method family that stays, e.g. "stay inside the joint-embedding family"] | [lead, date] | [reason] |
| [option that is banned, e.g. "no k-means anywhere"] | [lead, date] | [reason] |
| [data that stays held out] | [lead, date] | [reason] |

If evidence contradicts a constraint, argue it in one paragraph in the decision record and wait for the lead.

## 4. Fixed, free, careful

| fixed (the method as published or shipped) | free hyperparameters | careful (loss changes, large architecture changes) |
|---|---|---|
| [item] | [item] | [item: allowed only with an ablation row and the lead's sign-off] |

## 5. What exists and works

| thing | where (file:line or commit) | state |
|---|---|---|
| last working model | [commit] | [its numbers and where they are on disk] |
| config in force | [yaml path] | the yaml and the source win over every document |
| benchmark harness | [path] | frozen; changes need sign-off |

## 6. What was already settled

Link the settled-levers index. A proposal on a lever with a verdict must cite a defect in the earlier control or
be a confirmatory seed of a single-run effect. Levers absent from the index are reported as gaps.

## 7. Budget and machines

[GPU hours or days; deadline; card type and memory; what this machine can run (often: CPU probes only).]

## 8. The round

- Topics fanned out to digest agents: [list, one agent per topic].
- Probes: `probes/<name>.py` with committed `probes/<name>.out`, CPU, minutes each.
- Critics after the decisions draft: [refutation critic(s)], [completeness critic], [judge].
- Time box: [minutes per phase]. Rounds: [n]. How the result is chosen: [judge on stated metric].
- Output folder: [path]. Every agent creates its file with a section skeleton in its first tool call.

## 9. The keep or kill number

Written here before any variant is built; copied into the gates file. [metric, threshold, by when, against
which floor, on which readout.]
