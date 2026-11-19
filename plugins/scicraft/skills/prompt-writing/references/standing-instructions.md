# Standing instructions: CLAUDE.md, memory notes, skills

Standing instructions are briefs the agent reads without being asked: the project's CLAUDE.md every turn, memory
notes when they match, skills when their description matches the task. They need the same discipline as a brief,
and they also need to stay small, because they are paid for again and again.

## Every rule has a home

| Kind of content | Home | Loaded |
|---|---|---|
| the contract of the repository and ten non-negotiables | `CLAUDE.md` | every turn |
| the argument, the goals, the invariants | `NARRATIVE.md`, `GOALS.md`, `GUARDRAILS.md`, pointed to from CLAUDE.md | when the pointer is followed; a brief quotes the lines that bind its task |
| conventions (workflow, style, concepts) | `GUIDELINES.md`, split into `guidelines/<topic>.md` past about 300 lines | when the pointer is followed |
| evidence about the field, the data and the methods | the knowledge base, `docs/kb/` with `INDEX.md` | when needed |
| a correction from the author | a memory note | when its description matches |
| a procedure done more than once | a skill | when the task matches its description |
| a number a script computes | the script's output file, never prose | |

The governing documents (`NARRATIVE.md`, `GOALS.md`, `GUARDRAILS.md`, `GUIDELINES.md`) are defined in the sibling
skill, `project-structure/references/governing-documents.md`, and the knowledge base, with its entry format and
index, in `project-structure/references/knowledge-base.md`. `GUARDRAILS.md` wins over every other document.

## CLAUDE.md as a short index

The author's preference, recorded after a long first version was rejected: "CLAUDE.md is auto-loaded into context
every turn; bloating it wastes tokens." The model the author teaches is a figures repository's CLAUDE.md of about 520
words. The counter-example is a research repository's CLAUDE.md of about 3,000 words, full of blocks marked
SUPERSEDED.

Shape (`assets/claude-md-index.md`):

1. Two sentences: what the repository is for and what standard the work meets.
2. **Repository contract**: a code block with one line per top-level path and what lives there.
3. **Pointers**: one line per governing document and per guidelines file.
4. **Non-negotiables 1 to 10**: a bold imperative and one sentence of how or why.
5. **Done checklist**: what must hold before a piece of work is called ready.

Rules for upkeep:

- Record a reversal as a dated one-liner that points at the memory note: "PARTIALLY REVERSED (<date>, user
  decision; see memory <note>)". Delete the old block.
- Mark standing operator decisions "do not re-litigate".
- Never let prose carry a number that a script computes: "never quote a corpus figure from prose, including this
  line".
- Archive stale material where it cannot mislead (`docs/kb/archive/`, a dated folder). "Everything should then be
  documented in the kb, also old stuff ... archive them, otherwise it will be misleading."

## Memory notes

A correction from the author becomes a note the same day (`assets/memory-note.md`):

```
---
name: <short-kebab-name>
description: <one line an agent can match against a task>
type: feedback | project | reference
---
<The rule, one or two sentences.>

**Why:** <the incident, with the author's words quoted and dated>.

**How to apply:** <concrete steps, numbers, file names>.

**Exception seen on <date>:** <when the rule did not hold, and what was done>.
```

Link related notes with `[[name]]`. A memory proven wrong gets a dated amendment, not a silent edit. One
blanket rule ("no subagents until the first of the month") was wrong the next day. Test a limit instead of
assuming it.

## When a procedure becomes a skill

"Made the same kind of plot twice? That's a skill waiting." From the author's teaching deck: "Trigger on the task,
not a keyword. One reference beats ten rules. Write it after the mistakes; keep it to one figure type."

Skeleton (`assets/skill-skeleton.md`): `name`; `description` (what, when, and what it is NOT for); rules; one
reference example; failures; done (acceptance). Building a package of skills from session history is
`distill-skills`; the full authoring contract of a package is that package's own guide.

## When to sync

The author's rule was stated twice and pointed in two directions; both hold, in different settings:

- **Shared docs in a batch the author triggers**: "every now and then when I'm done with big changes I'd like to say
  update docs". Keep a `Synced` flag (default `-`) in the work ledger, and on "update docs", "sync docs" or "fold X
  back", review every unsynced row and then set it to yes.
- **A lesson the author asks to record goes in now**: "add that to the skill we have for the cluster"; "add what we learned
  here and doc it in our md files".

## Agent artifacts stay out of public history

- CLAUDE.md and `.claude/` are local only (for example through `.git/info/exclude`) when the author says so.
- No assistant attribution lines in commits when the author's instructions say so ("strip off claude in the
  pushes").
- A release brief listed "traces of an assistant (CLAUDE.md, `.claude/`, attribution lines)" among what never
  reaches published files, and a leak scan with zero hits was a final gate.
