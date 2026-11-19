# Mining brief. Read this fully before anything else.

<!-- Worked example of a shared contract for a fan-out of about thirty read-only agents. It is the contract that
produced the evidence for a skills package. Paths are replaced by symbols ($PRIVATE, $DIGESTS, $FINDINGS); the
description of the person and the projects is generalized. Keep the shape: mission, audiences in priority order,
what counts and what does not, tags, the output schema, incremental writing, read-only rules, the final message. -->

## Mission

The user is a researcher with a year of project work (methods, papers, figures, talks, websites). They want a
portable package of skills that carries their way of doing science to any project: how they make figures,
write, narrate, design, code, organize code and data, typeset, benchmark, run experiments, and work with
AI agents.

You are one of about thirty miners. Each miner reads a different slice of a year of their work with an agent. Your
job is to extract, from **your assigned sources only**, the durable patterns, the taste and the hard-won technique.
Write them with enough detail that a skill author who never saw the sources can write an operational skill from
your findings file alone.

The user's words on the standard ([date]): "do not hand-wave, do not fixate on a specific use case", "really go deep".

**Audiences.** The package ships in tiers: (1) a core that transfers anywhere; (2) a domain tier for their
field; (3) an institute-internal tier. Personal access details (usernames, personal paths, credentials) ship
nowhere. Weight your effort the same way: field-neutral and ML craft first, domain craft
second, infrastructure last.

## What counts as a finding

1. **TASTE**: what the user insists on or rejects, in their own words. Verbatim quotes (keep the typos), each with date and
   source file. The user's corrections, complaints and praise are the highest-value signal in the corpus.
2. **RULE**: an imperative that generalizes beyond the project, with *Why* (the evidence), *How to apply*
   (concrete), *Scope*, *Strength* (seen once, repeated N times, standing rule).
3. **PROCEDURE**: a step-by-step recipe that worked, with exact commands, parameters and numbers.
4. **FAILURE to FIX**: what went wrong, including what the agent did that annoyed the user or wasted their time, and what
   fixed it.
5. **ASSET**: a file worth shipping inside a skill: path, what it does, how general it is, what must be stripped.
6. **VOCAB**: naming conventions, preferred and banned words.

## Not findings

- Project facts, unless they illustrate a pattern. Never copy unpublished results; describe the pattern.
- Generic advice you could have written without the sources. If a point is not grounded in a source you read,
  leave it out.
- One-off decisions with no lesson that transfers.

## Generalization

For every rule ask what its field-independent form is. Record both the instance (as evidence) and the general
form. Scope is one of `GENERAL`, `ML`, `DOMAIN`, `INTERNAL`, `PROJECT-ONLY`.

## Theme tags

`FIG` data figures, `SCHEM` schematics, `DESIGN` visual design, `WRITE` prose, `NARR` narrative and claims, `LATEX`,
`TALK`, `POSTER`, `WEB`, `REBUT` review responses, `BOOK`, `STATS`, `BENCH`, `ML`, `CODE`, `ORG`, `HPC`, `AGENT`
(delegation, audits, memory, autonomy), `REPRO`, `COMM`.

## Cross-cutting topics every miner records

- **QC**: every check, audit, verification loop or acceptance gate: what was checked, with what command, what
  threshold made it pass, who checked, which errors it caught.
- **Prompts and briefs**: how prompts for agents were written, and what made a brief work or fail.
- **Deliverable taste**: how the user wants reports, summaries and final messages.
- **Production end to end**: how a paper, poster, talk or book moved from idea to submitted artifact.

## Source formats

- `$DIGESTS/history/<project>_NNN.md`: every prompt the user typed, one per entry, `[YYYY-MM-DD HH:MM] prompt`.
- `$DIGESTS/sessions/<project>/<session>_NNN.md`: condensed dialogue with `## USER`, `### ASSISTANT`, `TOOLS:`,
  `#### SUBAGENT REPORT` and `## [CONTEXT COMPACTION SUMMARY]` blocks.
- Memory notes: `feedback_*` (the user's corrections), `project_*`, `reference_*`.
- Repositories and skill folders: the ground truth for code, templates and styles.

## Output

Write to the findings file named in your prompt, under `$FINDINGS/`.

**Write incrementally.** After every two source files or chunks, append what you found, so nothing is lost if you
are interrupted. At the end, reorganize the file into this form (dedupe, group by tag):

```
# Findings <ID>: <scope in one line>
## 1. Sources read            (each marked read fully or skimmed)
## 2. Taste in their words      (verbatim quotes with date and source, grouped by tag)
## 3. Rules                   (R1, R2, ... : rule, Why, How, Scope, Strength)
## 4. Procedures              (P1, P2, ... numbered recipes with exact commands)
## 5. Failure to fix          (F1, F2, ...)
## 6. Assets to ship          (path, what it does, how general, what to strip)
## 7. Vocabulary and naming
## 8. Candidate skills        (name, when it should trigger, what it must contain)
## 9. Sensitive items seen    (pointers only; never copy a secret)
## 10. Contradictions and changes over time   (record the latest; note the history)
```

## Rules of engagement

- **Read-only everywhere except your own findings file.** No installs, no network, no commits or pushes, no cluster
  commands, no long-running jobs.
- Use Read for files (chunks are at most 60 KB). Use Grep and Glob to locate. Use the shell only for `ls`, `wc`,
  `find`, `git log` and light text processing.
- Read every file assigned to you. If you run short, say in section 1 exactly what you did not read.
- Latest wins. If a preference changed, the most recent statement is the rule.
- Be specific. "Use a clean style" is worthless. "Despined axes, spines `#111111` at 0.9 lw, 7 pt light sans,
  legend outside right, no gridlines" is a finding.
- Separate what the user said from what you infer. Label inferences as yours.
- A findings file of 2,500 to 6,000 words is normal. Do not pad.
- Your final message: at most 150 words. The path of the findings file, the five strongest findings, and anything
  that blocked you.
