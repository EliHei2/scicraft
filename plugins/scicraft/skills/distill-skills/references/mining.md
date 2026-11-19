# Mining: slices, miners, the second wave

## Slices

The original build had 34 first-wave slices, named by source kind:

| Code | Count | Source | Typical size |
|---|---|---|---|
| A | 9 | existing skills, repositories, style files, the author's design and writing corpus | a few folders, read with listings and targeted reads |
| H | 6 | prompt history, one to three projects each | 4 to 7 history chunks |
| K | 6 | memory notes and figure logs of one or two projects | dozens of short notes |
| S | 11 | long sessions, one per slice or one part of a long one ("part 1 of 4") | 1 to 7 session chunks |
| T | 1 | one writing system across a repository and its sessions | mixed |
| X | 1 | one theme across everything (briefs, agents, standing instructions) | greps across all digests plus named files |

Second wave: 6 more (two on the newest project, one on a field's downstream analysis, one on a journal
revision campaign, two gap checks of sessions that had produced skills), plus one documentation lookup
on distribution options.

- **Budget.** At most about 420 KB of digest per slice (seven 60 KB chunks). Findings files of 2,500 to
  6,000 words came back from slices of that size.
  `python3 scripts/plan_slices.py [ws]/digests --budget-kb 420 --json [ws]/slices.json` packs history
  and session chunks: sources of the same kind and project share a slice while they fit, a longer
  source is split into consecutive parts. On the original digests (about 6.6 MB) it gives 39 slices.
  Suggested, not yet tested in real work: the original slices were planned by hand from `INDEX.md`.
- **Hand-plan the rest.** Memory notes, repositories and existing skills are not digests. Plan them by
  what they can show that prompts cannot: exact numbers, the working code, templates.
- **List every project's standing documents and give them to a miner**: the index file, the narrative,
  the guardrails, the guidelines and the knowledge base (defined in the sibling skill,
  `project-structure/references/governing-documents.md`). In this package's own build the slices
  covered chats and memory, the governing documents in the repositories were missed, and they were
  added only when the author asked for them.
- **Cross-cutting slices** are worth one or two miners: a theme that shows up a little in every
  project (how briefs were written, how reports were wanted) is invisible to a miner of one project.
- **Weight by audience.** In the original build the receiving lab was machine-learning first, so the
  ML research prompts got their own slice with a long special focus, and institute infrastructure got
  the least.

## The launch

1. Write the shared contract once: `assets/mining_brief.md`, every bracket filled.
2. **Audit the contract before the fan-out.** A shared preamble with one wrong claim is confirmed by
   every agent that reads it (seen in another campaign of the author's: six agents "confirmed" a false
   statement from their preamble). Read it against the sources once.
3. One launch prompt per miner from `assets/miner_launch.md`: miner ID, slice, sources in reading order,
   findings path, special focus, and the privacy line.
4. Launch on the model and at the count the author named; at most 20 at once in the original build.
   Record each launch in the state file.

## While miners run

- **Each miner writes a skeleton first** and appends after every two chunks, so a miner that dies keeps
  its partial file. If a harness blocks subagents from writing report files, the miner returns the
  findings in its message and the lead saves them.
- **A "completed" with an empty result is not a result.** Check the findings file: it exists, has all
  ten sections, has rules, and section 1 lists what was not read. `scripts/tally_findings.py` flags a
  file with zero rules.
- **Read the five strongest findings in each report** and write anything that changes the plan (a
  project nobody covered, a new named request) into the state file at once.
- **Resurrect, do not restart.** A miner that died mid-slice gets a successor with its partial file
  ("keep and extend") and the list of chunks it had not read.

## The second wave

Two kinds of gap. Launch both after the first-wave findings are read.

1. **Uncovered work.** Compare the projects and sessions in `INDEX.md` with the slices. A project that
   appeared late, or one the author named after mining began, gets a slice.
2. **Gap checks of earlier skills.** Where a skill was distilled during the work itself (a deck skill
   written right after a talk), its sessions were never mined against it. The gap miner reads the
   current skill with every reference file first, then every chunk of the sessions, and reports only
   partly-there and missing items, each with its target file and section (variant 4 of the launch
   prompts). In the original build two such checks fed revisions of three skills.

Second-wave findings arrive while writers run. Route each one: to a skill not yet launched, add it to
that brief's decisions; to a skill being written, message its writer; to a finished skill, a revision
agent with the build note and the new findings.

## Findings that matter most downstream

| Section | Used for |
|---|---|
| 2 the author's words | the thrown-out table and the quotes that carry rules |
| 3 rules with tag, scope, strength | the skill set (tag counts) and the rules themselves |
| 4 procedures | references and scripts |
| 6 assets | what to port; the writer's "existing material" list |
| 8 candidate skills | the skill set (counts across files) |
| 9 sensitive items | the forbidden-terms files; the rotate list |
| 10 contradictions | latest-wins decisions in the briefs; integrity requests to encode honestly |
