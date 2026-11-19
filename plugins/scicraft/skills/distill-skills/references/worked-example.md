# Worked example: the scale of the original build

One scientist asked for a package of skills from a year of work with an AI agent. Numbers only; no content.

| Step | Numbers |
|---|---|
| the history | 15,415 prompts logged (9,425 of them counted as typed), 20 projects, 223 active days over about ten months, 2.2 GB of session transcripts, 269 memory notes |
| digests | about 6.7 MB: 47 history files (2.0 MB) and 88 session chunks (4.7 MB), at most 60 KB each; keys found in old prompts, owner told to rotate |
| first wave | 34 miners, slices of up to seven 60 KB chunks; kinds: 9 ground truth, 6 prompt history, 6 memory and logs, 11 sessions, 2 cross-cutting |
| second wave | 6 miners (the newest project twice, a field's downstream analysis, a journal campaign, two gap checks of earlier skills) and one documentation lookup |
| findings | 40 files, 328,874 words, 1,308 rules, 291 procedures, 629 failure records at the time of the count |
| skill set | 46 build briefs: core 31, ML 9, biology 5, internal 1; every brief lists all other skills as siblings |
| writers | at most 20 at once, all on the strongest model; one writer per skill; revisions from late findings and from the author's look |
| author's look | one figure skill's demo: five defects found after the writer's own look at crops up to 1,500 dpi |
| coverage pass | one auditor per findings file: 14 percent of in-scope items partly covered or missing, about 70 places where two skills disagreed; one reconciler settled them for all skills before any repair; then one gap-fill agent per skill |
| still to run when this skill was revised | one adversarial reviewer per skill, packaging, install test |

Cross-checks with the scripts of this skill, run read-only on the original workspace:
`plan_slices.py` at a 420 KB budget gives 39 slices from 36 digest sources; `tally_findings.py --totals`
on the later, larger findings set counts 1,479 rules, 310 procedures and 665 failure records (the
second-wave files had grown the set since the count above).

## The order it happened in

1. The author's request, then a map of the sources (skills, transcripts, memory, projects, history
   format) in about five minutes.
2. The extractor written and run on everything; one chunk looked at; the classifier fixed; digests
   rebuilt.
3. The mining brief and 34 launch prompts; the first wave, at most 20 at once.
4. Findings read; the skill set chosen from named requests, candidate sections and tag counts; the
   spec written as a table in the brief generator.
5. 46 build briefs generated; writers launched from a queue as slots freed, with launch notes for late
   evidence.
6. Meanwhile the second wave; its findings routed to queued briefs, running writers or revision agents.
7. The author added requests during the build (sharing, project organization, "every hard skill",
   portfolio numbers, the governing documents of the projects); each went into the state file and
   became a skill, a section or a step. The governing documents (narrative, guardrails, guidelines,
   knowledge base) lived in the repositories, and the mining of chats and memory had missed them.
8. The author looked at rendered demos and sent defects back; revisions recorded in build notes.
9. The coverage audit, then one reconciliation of every disagreement between skills, then the
   central pass of exact replacements (every changed sentence read, after one bulk replacement had
   garbled several), then one gap-fill agent per skill.
10. Planned next: adversarial review, license fixes, packaging, sharing recommendation.
