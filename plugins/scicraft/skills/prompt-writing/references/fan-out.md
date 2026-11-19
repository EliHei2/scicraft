# Fan-out briefs: the shared contract, the exemplar and the lane prompts

This file is about writing the briefs for parallel agents. Deciding whether to fan out, how many agents to run,
which model, and how to merge their output belongs to `agent-orchestration`. The author's latest rule there: work
solo by default, fan out when the user asks for it in so many words, and size the fan-out as they say ("only 5,
don't go super overboard").

## The pattern

Several hundred subagent briefs followed one shape:

1. **A contract file, written once.** It sets the read-only status, the build command, the rules and the report
   format. Contract files seen: a book rules file, a polish brief, a de-AI brief, a caption brief, a figure
   brief.
2. **A lane prompt per agent**: "You are <role> of <artifact> that is <stakes: submitted tomorrow>. First read
   `<contract>` in full and follow it exactly. YOUR LANE: <scope>. Your files (edit only these): ... Output path:
   <path>.json. Deliver within about N minutes. Work fast (batch reads and greps as parallel tool calls)."

The lane prompt stays at 3 to 6 lines. It names the scope, what not to do ("NOT 3e, another agent does the
trade-offs"), the outputs and the files to read first. When the user adds something mid-run, the lead sends a
tailored message to each running agent the change affects. In one case that was 8 of 10 agents. After a shared
incident, such as a full disk, the lead sends the same message to all of them.

## What goes in the contract

From a figure contract that fed about ten agents, in this order:

1. Goal and deliverable.
2. What the agents may not do ("Do not run or re-score anything").
3. The interpreter, the paths, and where an agent may write.
4. The through-line: numbered claims that every output serves.
5. Sources of truth, newest first, with "if two sources disagree, the higher one wins".
6. `[PENDING: what]` for anything missing. Agents never invent.
7. Hard honesty rules.
8. Binding author decisions, verbatim and dated.
9. Words that must never print.
10. Voice bans.
11. Rules for the artifact type (for figures: script shape, style import, composer call, type tiers, color roles,
    the interval type, the self-check loop, reference images to learn the look from).
12. Format of captions or other attached text.
13. Fixed labels and available macros.
14. The limits of the build tools.
15. The document plan, so each agent knows what the others make.
16. The return format: "Reply in under 200 words ... every problem you found ... Do not bury problems. Longer
    notes go to `_notes/<your-name>.md`."

Contracts of about 10 KB worked. A shorter checker contract (about 3 KB) drove three checkers, because their job
was narrower.

## Build the exemplar first

Before the fan-out, the lead built the shared style module, the composer and the table helper, then one reference
output: "The figure subagents will copy it, so I'm getting it right first." Every lane prompt then gave the
exemplar's path. Agents reproduce what they are shown more faithfully than what they are told. A rule in the
contract that the exemplar breaks will lose to the exemplar.

Launch agents that depend on others (writers who cite figures and tables) only after their inputs exist, so they
can cite them.

## Distinct lanes

Give each agent a different hypothesis or lens. A lens table makes this explicit:

| Lens | Question | Allowed edits | Output |
|---|---|---|---|
| conclusions | is each conclusion the most important finding, stated with its number? | conclusion boxes only | `logs/R1.md` |
| consistency | is every number, name and attribution the same everywhere? | none (read-only) | `logs/R2.md` |
| visual | does any page show a cut label, an orphaned heading, an overflow? | none (read-only) | `logs/R3.md` |

Examples of hypothesis lanes from a parameter search: one agent per hypothesis (raise coverage, raise enrichment,
balance merges, change elongation, interpolate from the top five configs, a wildcard that maps the four corners of
the trade-off). Each agent returns "ONLY the keys you change" and stays local to the current champion ("this is
refinement, not rewrite"). A script scores the proposals and an adversarial judge checks the winner for gaming.
That loop is `agent-orchestration`.

Personas that worked for audits (one fault class each): a desk-reject proofread of references; one hostile reader
per reviewer; a chair reading the reviews; a statistics referee; a figure editor checking every figure against the
text and tables; a register editor; two art editors working at the pixel level; a terms auditor. Each brief names
the files, the persona, the fault class, what is out of scope, and the report: path, top five, an exact fix per
row with file and line.

## Read-only lanes and one writer

- Say it in capitals: "You audit and propose exact edits. You do NOT edit any file."
- Return edits as JSON `{file, old, new}` where "each `old` occurs exactly once". Record skips as `new` equal to
  `old`. The lead applies, rebuilds and re-checks.
- Start every read-only research brief with its limits: "READ-ONLY fact-finding for a manuscript. Do NOT edit
  any file, do NOT submit cluster jobs. Report findings with exact file paths and the commands and values you used
  as evidence." Give each agent its own scratch folder. Name the neighbors: "Two other agents are separately
  checking (i) ... (ii) ... do not duplicate."
- Keep producing and checking apart: checker agents re-run the builder into a temp folder and compare byte for
  byte with `cmp`. They recompute every value with their own code and import nothing from the builder. They
  re-render and compare pixels (at most 2/255, with a control showing that one dropped dot is detectable). They
  report a PASS or FAIL table per file plus a section for problems found in the surrounding text.

## Caps and slips

- Put a word cap in the lane prompt and measure each answer (`wc -w`). In one fan-out, answers came back at a
  median of 95 words and up to 165 against the cap, and the lead had to cut them.
- Ask agents to list their own rule slips. Agents reported, for example, "ran one read-only git status despite
  the no-git rule" and "this report runs past the brief's 200 words".
- Give a time box where the author gave one ("don't take more than 10 mins"; "under 15 minutes").
- Tell forks to "spawn no further agents".

## Worked example: a thirty-agent mining job

`assets/fan-out-example/` holds the contract and two lane prompts of the job that produced the evidence for this
package. About thirty agents each read a different slice of a year of sessions and wrote a findings file. Paths
and the project description are replaced with placeholders. What it shows:

- The contract states the mission, the audiences in priority order, what counts as a finding, what does not, a
  scope tag set, the output schema (ten sections), "write incrementally after every two source files", the
  read-only rules, and the final message (at most 150 words).
- Each lane prompt (`assets/fan-out-example/lane-session.md`, `assets/fan-out-example/lane-history.md`) names
  the role and the number of agents, the line "read the contract in full and follow it exactly", the slice, the
  sources in order, the output file, and a special focus of three to seven numbered items. These run to about 15
  lines, longer than the 3 to 6 of a lane in one artifact, because each slice needed its own focus list; the
  rules still live only in the contract.
- The schema has a place for what must stay out of the output (section 9, sensitive items, as pointers only). It
  also has a place for where the author changed their mind (section 10, latest wins). The skill authors who built
  this package from the findings relied on both.
- Two gaps, which `scripts/check_brief.py` reports and a second version would close. The contract has no fallback
  for an agent that cannot write files ("put the full findings in your final message"). The lane prompts do not
  name what the neighboring slices cover, so two miners could record the same episode twice. The script also
  warns that the contract quotes no guardrail or short goal. A mining job over chat logs had no governing
  documents, so the warning is expected here; a contract inside a project quotes them.
