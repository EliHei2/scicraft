# When to audit, how big, on which model

## The decision

Run an audit when three things hold: the work is about to cost something (compute, a submission, a release, the
trust of a reader), the work is finished enough that findings will not be stale in an hour, and there is an
independent source of truth to check against (code that runs, a paper's tables, a reference's full text, the
author's rules).

Do not run one, or run a much smaller one, when:

- **The text is the author's craft and already accepted.** The rejected rebuild: asked to sharpen a reply the author
  had worked out in a chat, the coordinator ran 4 research agents, 3 adversarial agents and a final gate, then 5 to 8
  more agents, over about 3.5 hours, through drafts v1 to v13, and added a comment nobody asked for. The author's
  points were "killed" and the result was "overwhelming". The fix took 10 minutes: a light polish of the author's last
  version and one audit per round, briefed "This is a final polish. Do NOT propose a rebuild, a new structure, new
  sections or a new style."
- **The artifact is still moving.** Auditors reported on stale versions while the text changed under them. Freeze a
  snapshot first, or wait.
- **The answer is a measurement.** "Did you really integrate the revision?" is answered by a script (a table of the
  revision's new sentences found in the current text: 178 new, 170 present, 8 changed on purpose), not by agents.
- **The user set a deadline in minutes.** Hand over a verified build first, then audit if time remains.

## Sizes that worked

| Job | Shape | Notes |
|---|---|---|
| Code about to consume compute | five finder lenses by default, 8 to 13 when the user asks for a full audit, one refute-by-default verifier per finding (two in the first audit), a completeness critic, synthesis in the main loop | 35 to 38 raw findings, 20 to 24 confirmed, 13 refuted; one round reached 43 agents and 31 confirmed findings |
| Design before a build | topic agents writing digests, then refutation critics plus a completeness critic, zero-GPU probes | verdicts SURVIVES, SURVIVES-WEAKENED, DIES |
| Claimed win before a figure | k variant formulations plus 3 to 4 lens critics (depth, circularity, statistics, domain), then a synthesizer | verdict keep, demote to illustration, or retract |
| Figure set | 4 to 6 reviewers by dimension plus logic plus fact check, ranked fixes, final regression verifier | about 10 minutes when each soundness check is one cheap agent running one script |
| Long document line edit | 7 read-only agents on disjoint chapter groups, JSON proposals, a vetting script | two rounds, about 514 edits applied |
| Reference list | chunks of about 56 entries per agent plus one style agent | 278 entries, 137 corrected |
| Literature claims | one pass over every claim about a cited work | about 290 claims checked, 50 wrong |
| Final proofread | one fresh agent per round, looped until clean | one at a time, not a fleet |
| Author's own draft | one focused audit | no rebuild, no new structure |
| Find the best candidate | candidate generators, a pre-specified deterministic screen, then adversarial judges | 74 agents, 16 of 72 survived |

## The cost history (latest wins)

- Early: "do adversarial fanout of [strongest model] subagents to harshly judge the code and improve the code. both
  in accuracy and efficiency. but don't take more than 10 mins." Fleets on nearly every request.
- Later: "look running workflows is really costly ... try to figure it out yourself", then "run fan out subagents
  only 5 don't go super overboard, but deliver this task".
- Final passes: "run the agent again and again until 0 discrepancy is detected, and make the agent really
  impartial, and a bit adversarial". This became one fresh agent per round, looped.
- Latest rule: work alone by default; fan out when the user asks, sized as asked; for proofreading, one fresh agent
  per round. Fan-outs paid off for independent evidence gathering, distinct-hypothesis search, read-only audits
  with merged edits and fact-checking. They wasted budget on rewriting a text the author owned, on synthesis
  phases that died, and on duplicate agents re-deriving a known correction.

## Process weight

An unattended research campaign used stewards, judges and pre-registration documents. A later release brief cut
this: "This job is engineering, not a campaign. No preregistration documents, no steward or judge agents." Keep the
pre-registered decision criteria for real gates (a keep or kill number written before the data arrives); drop the
ceremony for engineering jobs.

## Models and effort

- Finders and verifiers: the strongest model available, high reasoning effort.
- Scripted soundness checks: pre-write the check scripts, then run one cheap agent per script (in the figure audits
  a smaller model at low effort) that returns PASS, CAVEAT or FAIL with numbers.
- Mechanical work (link checks, leak scans, fixtures) to a cheaper model; audits to fresh agents that have not seen
  the build brief.
- A fork inherits the parent's model and context, so it cannot be the independent reader. Use a fresh agent with a
  complete brief when independence matters.
- Follow the model and count the user names in the session.

## Deadlines

- "please be fast ... ready to submit in 20 mins, if you need more effort hire more subagents but deliver please!"
  Under a deadline, hand over a verified intermediate build and commit it before launching anything else.
- Slow audit: two lanes still running after about 1.5 hours drew "taking too long". Send each running agent a hard
  deadline and a priority order: "HARD DEADLINE: you have 12 minutes from now ... strict priority order", then
  "Time is up: write your edits.json now with whatever you have and stop."
- Never kill a running agent under deadline: "don't just kill but make it faster!" Harvest what it wrote.
