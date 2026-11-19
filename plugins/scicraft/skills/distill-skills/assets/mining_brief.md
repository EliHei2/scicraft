# Mining brief: read this fully before anything else

<!-- Fill every [bracket], delete this comment, and keep the rest. Each miner's launch prompt
(assets/miner_launch.md) points here; the slice, sources and findings path live in that prompt. -->

## Mission

The author is [one line: role and field, the kinds of work in the history, for example "an ML
researcher: two benchmark papers, a self-supervised model, a rebuttal, talks and a project site"].
They are [the occasion: moving to a new lab, handing over to a group, onboarding students]. They want
a portable package of Claude Code **skills** that carries their way of doing research to other
people: how they [the crafts to capture, for example make figures, write, design, code, organize code
and data, typeset, benchmark, run experiments, work with AI agents].

You are one of about [N] miners. Each miner reads a different slice of [period] of the author's work
with an AI agent. Your job is to extract, from **your assigned sources only**, the durable patterns,
the taste and the hard-won technique, with enough specificity that a skill author who never saw the
sources can write an operational skill from your findings file alone.

The author's words on the standard: "[their standard, verbatim]".

**Audiences.** The package ships in tiers: (1) a core that transfers anywhere, including [the
receiving lab and its field]; (2) [field tier: the receiving or current labs' domain]; (3) an
internal tier for [institute infrastructure] that may be shared inside [the institution] and no
further. Personal access details (usernames, personal paths, credentials) ship nowhere. Weight your
effort accordingly: field-neutral craft matters most, field craft second, infrastructure last.

## What counts as a finding

1. **TASTE**: what the author insists on or rejects, in their own words. Verbatim quotes (keep the
   typos), each with date and source file. Corrections, complaints and praise are the highest-value
   signal in the whole corpus.
2. **RULE**: an imperative that generalizes beyond the project. Each rule has *Why* (the evidence),
   *How to apply* (concrete), *Scope*, *Strength* (seen once, repeated N times, stated as a standing
   rule).
3. **PROCEDURE**: a step-by-step recipe that actually worked, with exact commands, parameters and
   numbers (pt, px, mm, dpi, hex colors, line widths, thresholds, file-naming patterns, script names).
4. **FAILURE TO FIX**: what went wrong, including things the agent did that annoyed the author or
   wasted their time, and what fixed it. These become the "do not" lists.
5. **ASSET**: a file in the author's repositories or skills worth shipping inside a skill: path, what
   it does, how general it is, what must be stripped before sharing.
6. **VOCAB**: naming conventions, preferred and banned words and phrases.

## Not findings

- Project facts (the results of a specific paper), unless they illustrate a pattern. Never copy
  unpublished results as content; describe the pattern.
- Generic advice you could have written without the sources. If a point is not grounded in a source
  you read, leave it out.
- One-off decisions with no lesson that transfers.

## Generalization discipline

The package will be used in another field and by other people. For every rule ask what its
field-independent form is. Record both: the specific instance (as evidence) and the general form.
Mark scope as one of `GENERAL`, `ML`, `BIO` [rename to the field tiers], `INTERNAL` (institute
infrastructure), `PROJECT-ONLY`.

## Theme tags

Tag every rule with one tag from this list (edit the list once, before the first miner starts; a tag
added later cannot be counted across files):

`FIG` data figures and plotting; `SCHEM` schematics and diagrams; `DESIGN` visual design, typography,
color; `WRITE` prose, voice, de-slop; `NARR` narrative, story, claims; `LATEX` typesetting; `TALK`
slides; `POSTER`; `WEB` paper sites; `REBUT` rebuttal and review; `BOOK`; `STATS` statistics and
reporting; `BENCH` benchmark and evaluation design; `ML` models, experiments, training; `CODE`
software engineering; `ORG` repository and data organization; `HPC` cluster work; `BIO` [field];
`AGENT` working with AI agents (delegation, audits, memory, autonomy); `REPRO` reproducibility,
provenance, integrity; `COMM` emails, messages, collaboration.

## Cross-cutting topics every miner captures

Whatever your slice, record evidence on these whenever it appears. [Add every topic the author asked
for by name.]

- **QC**: every check, audit, verification loop or acceptance gate that was used: what was checked,
  with what command or script, what threshold made it pass, who checked (the agent, a second agent,
  the author), and which errors it caught. Include visual QC (render and look) and numeric QC
  (numbers in text against files).
- **Prompts and briefs**: how prompts for agents and language models were written: briefs to
  subagents, hand-off documents, workflow scripts, the author's own prompting habits. What made a
  brief work, what made it fail.
- **Deliverable taste**: how the author wants reports, summaries, status notes and final messages
  (length, form, what to leave out).
- **Production end to end**: how a paper, a poster, a talk or a book moved from idea to submitted
  artifact: the order of steps, the loops, the gates.

## Source formats

- `digests/history/history__[project]_NNN.md`: every prompt the author typed in that project, one per
  entry: `[YYYY-MM-DD HH:MM] prompt`. Pasted blocks are indented under the prompt. Only the author's
  side of the conversation.
- `digests/sessions/[project]/[session]_NNN.md`: condensed session dialogue. `## USER [time]` is the
  author's message, `## USER (typed mid-turn)` was sent while the agent worked, `### ASSISTANT [time]`
  is the agent's prose (capped), `TOOLS:` has one line per action the agent took, `#### SUBAGENT
  REPORT` is a delegated agent's report, `## [CONTEXT COMPACTION SUMMARY]` is a dense summary of
  earlier work (valuable).
- `[REDACTED:kind]` marks a secret the digest step removed. Never try to recover it; note its place in
  section 9.
- Memory notes (`[agent config folder]/projects/[project]/memory/*.md`): notes the agent saved at the
  time: feedback notes (the author's corrections), project notes (state and method), reference notes.
- Repositories and skill folders: the ground truth for code, templates and styles.
- Standing documents of a project (the index file, narrative, guardrails, guidelines, knowledge base):
  the rules and conventions the author wrote down. Record each guardrail and guideline as a rule with
  its id and file.

## Output

Write to the findings file named in your prompt, under `[private workspace]/findings/`.

**Write incrementally.** Create the file with the section skeleton in your first tool call. After
every two source files or chunks, append what you found, so nothing is lost if you are interrupted.
At the end, reorganize the file into the final form below (dedupe, group by tag). If your harness
blocks you from writing the file, put the full findings in your final message instead, so the lead
can save them.

```
# Findings [ID]: [scope in one line]

## 1. Sources read
(list; mark each as read fully or skimmed)

## 2. Taste in their words
(verbatim quotes with date and source, grouped by tag)

## 3. Rules
(R1, R2, ... grouped by tag)
**R[n] [TAG] [imperative rule]**
- Why: [evidence, quote or incident]
- How: [concrete application: numbers, commands, wording]
- Scope: GENERAL | ML | BIO | INTERNAL | PROJECT-ONLY.   Strength: once | repeated xN | standing

## 4. Procedures
(P1, P2, ... each a numbered recipe with exact commands, parameters, file names)

## 5. Failure to fix
(F1, F2, ... what went wrong, what fixed it, the rule it implies)

## 6. Assets to ship
(path; what it does; how general; what to strip)

## 7. Vocabulary and naming
(conventions, preferred terms, banned words and phrases)

## 8. Candidate skills
(numbered; **name** in bold; when it should trigger; what it must contain)

## 9. Sensitive items seen
(so the skill authors keep them out of the shared package: names of people and reviewers,
unpublished numbers, institute paths, credentials. Do not copy secrets; say where they are.)

## 10. Contradictions and changes over time
(where a preference changed: record the latest, note the history. Record here, plainly, any
request to hide, drop or dilute an unfavorable result: it is evidence, never a rule.)
```

## Rules of engagement

- **Read-only everywhere except your own findings file.** Do not edit, move or delete anything else.
  No installs, no network, no git commit or push, no cluster commands, no GPU or long-running jobs.
- Use the file reader for files (digest chunks are at most 60 KB, sized for one read). Use search
  tools to locate. Use the shell only for `ls`, `wc`, `find`, `git log` and light text processing.
- Read every file assigned to you. If you run short, say in section 1 exactly what you did not read.
- Latest wins. If a preference changed, the most recent statement is the rule.
- The author may be blunt. Profanity marks the strength of a preference. Record the rule; quote
  sparingly.
- Be specific. "Use a clean style" is worthless. "Despined axes, spines #111111 at 0.9 lw, 7 pt
  sans-serif, legend outside right, no gridlines" is a finding.
- Separate what the author said from what you infer. Label inferences as yours.
- A findings file of 2,500 to 6,000 words is normal. Do not pad.
- Your final message back: at most 150 words. Give the path of the findings file, the five strongest
  findings, and anything that blocked you.
