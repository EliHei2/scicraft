# STATE: [job in one line]

Brief: [path to the brief this job follows]. Read the brief and this file before anything else after a reset.
Last updated: [YYYY-MM-DD HH:MM, time zone] by [session or agent name]

## Done

<!-- One line each, newest last. Name the output path and the check that passed, with its printed value. -->
- [YYYY-MM-DD] [unit]: [output path]. Gate: [command] printed [value] (threshold [value]).

## Running

<!-- Everything that can still change the disk: agents, background jobs, cluster jobs. -->
| What | Id | Started | Writes to | Log | Expected end |
|---|---|---|---|---|---|
| [agent / job name] | [agent id, job id, PID] | [time] | [output path] | [log path] | [time] |

## Next

1. [the single next action, as a command or a file to write]
2. [then]

## Open

<!-- Questions only the user can answer. Each with your recommendation and what it blocks. -->
- [question] Recommended: [choice], because [reason]. Blocks: [unit].

## Decisions

<!-- Routine choices made without asking, one line each, so the user can overturn them later. -->
- [YYYY-MM-DD] [choice] because [reason]. Reversible by [how].

## Rules from the user

<!-- Verbatim, dated. A later rule overrides an earlier one; strike the old one, do not delete it. -->
- [YYYY-MM-DD HH:MM] "[the user's words]"

## Proposals

<!-- Ideas outside the brief's scope. They go here, never into code, until the user says yes. -->
- [idea]: [why it might help], [what it would cost].

## Volatile

<!-- What exists only in a place that a crash or reboot can wipe: temp folders, scratchpads, unpushed
commits, ignored results. Move each to a durable path as soon as it matters. -->
- [path]: [what it holds]. Move to [durable path] by [when].
