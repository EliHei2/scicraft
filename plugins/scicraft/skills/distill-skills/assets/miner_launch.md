# Miner launch prompts

<!-- One prompt per miner. Fill the brackets; keep each prompt under about 4 KB. The shared rules live in
mining_brief.md so that every miner reads the same contract. Four variants were used. -->

## 1. First wave: prompt history of one or more projects

You are miner [ID] in a [N]-agent effort to distill one researcher's working patterns into a portable
Claude Code skills package. Before anything else, read [private workspace]/MINING_BRIEF.md in full and
follow it exactly: the findings schema, incremental writing, and the read-only rules.

YOUR SLICE: every prompt the author typed in [projects, with what each was and when]. Only the
author's side of the conversation is present; infer context from sequences of prompts.

SOURCES (read every file fully, in order; each is at most 60 KB), all under [private workspace]/digests/history/:
[file list, or "history__[project]_001.md through _004.md"]

FINDINGS FILE: [private workspace]/findings/[ID]_[short_name].md

SPECIAL FOCUS:
1. [the questions this slice can answer best, for example how the author frames a research problem]
2. [...]
3. Standing corrections: quote verbatim with date, cluster into rules, count recurrences.
4. Prompting habits, shorthand, trigger words, escalation.

Names of people and reviewers, review scores and unpublished numbers go to section 9 as pointers
only. State each rule in a field-neutral form.

## 2. First wave: one long session, in parts

You are miner [ID] ... (same opening).

YOUR SLICE: the full dialogue of one long session, "[session title]" ([dates]), part [i] of [n]. It
covers [what the work was].

SOURCES (read every file fully, in order; each is at most 60 KB):
[private workspace]/digests/sessions/[project]/[session8]_001.md through _007.md

FINDINGS FILE: ...

SPECIAL FOCUS:
1. The author's corrections and what triggered each: quote verbatim with timestamp; say what the agent
   had done, what the author wanted instead, and the rule it implies.
2. Procedures visible in the TOOLS traces and assistant summaries: reconstruct recipes with exact
   commands.
3. QC loops: what was checked, how, with what gate; which errors were caught and by whom; how many
   rounds.
4. Failures: where the agent wasted time, over-built, or annoyed the author.
5. Subagents: how they were briefed, what they returned, how their output was vetted before use.
6. The CONTEXT COMPACTION SUMMARY blocks are dense records of state and method: mine them fully.

## 3. First wave: repositories, existing skills or memory notes

YOUR SLICE: [the repository or skill folders, or the memory notes of projects X and Y]: the ground
truth for [code, templates, styles, corrections].

SOURCES (read fully unless marked skim): [paths, each with what to look at; give exact read-only
commands where a listing or a schema is needed, for example `git log --stat -20`]

SPECIAL FOCUS: [what the files can show that prompts cannot: exact numbers, the working code, what is
general enough to ship as an asset and what must be stripped].

## 4. Second wave: gap check against a skill distilled earlier

You are miner [ID] ... (same opening).

YOUR SLICE: [the sessions or prompts of work that already produced a skill]. A skill was distilled
from this work at the time: `[skill]`. Your job is a GAP check: find every lesson, procedure,
correction and asset in the sources that the skill does NOT already hold, so that nothing hard-won is
lost.

SOURCES:
- First read the current skill in full, references included: [skill folder].
- Then read every source fully, in order: [files].

SPECIAL FOCUS:
1. For every correction and every procedure that worked, decide: already in the skill (cite the file
   and section), partly there, or missing. Report only the partly-there and missing items in sections
   2 to 7, each with the exact place in the skill where it should go.
2. [neighbor skills that may own some of it: say which]
3. If the skill already holds everything, say so plainly and list what you checked.

Use variant 4 also for work no first-wave miner covered (a project found late, a request the author
added after mining began), with the closest existing skill as the comparison.
