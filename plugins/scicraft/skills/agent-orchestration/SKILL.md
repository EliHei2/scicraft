---
name: agent-orchestration
description: Runs research work with AI agents so that it survives crashes, costs what the user expects and comes back true: whether to delegate at all, sizing a fan-out, overnight and multi-day campaigns, crash and usage-limit recovery, and the report. Use this skill whenever a task might involve subagents, forks, workflows or background jobs, or the user says fan out, run 5 agents, adversarial loop, work on this overnight, don't stop until, resume the agents, my session crashed, it says completed but it isn't, stop the agents, or a deadline is close while agents run. Holds what was learned the hard way (solo unless asked, one role per agent, a script scores, every agent writes to disk as it goes, a dead workflow is never reported done, agent claims are checked) plus a read-only script listing what finished and dead agents left on disk, and state and journal templates. Prefer prompt-writing for the brief, adversarial-audit for audit content, cluster-jobs for job scripts.
---

# agent-orchestration

How to run research work with AI agents so that the work survives crashes, costs what the user expects, and
comes back true. Distilled from a year of one researcher's work with agents: code audits before cluster runs,
overnight parameter searches, a two-week unattended campaign, rebuttal and book deadlines, and many crashes
and usage limits. Most rules here exist because their absence cost hours. Where the user at hand says
otherwise, they win: write their rule into STATE.md and follow it.

> **PRIME DIRECTIVE: do the work yourself unless the user asks for agents, and when agents run, every one
> writes its findings to disk as it goes, no agent judges its own work, and nothing is called done until you
> have opened the file and re-run the check.**

Three failures cost the most. Guard against them from the start:

1. **The rebuild fleet.** Asked to sharpen a reply the author had already worked out, a session spent about
   three and a half hours on four research agents, three adversarial agents and up to eight more audit
   agents, and produced thirteen drafts. The author's points were lost: "really killed my whole points ...
   just try to polish the edges". Sections 1 and 2.
2. **Work lost and reported as finished.** On one evening a weekly usage limit killed 21 of 25 agents; the
   synthesis agents died first. In another project workflows were reported complete after dying, four times
   in one week: "you say it's completed but it didn't". Sections 5, 7 and 8.
3. **Agents confirming what they were told.** A shared preamble asserted a claim three lines above a table
   that refuted it. Six agents reported the claim back as confirmed. Sections 3 and 8.

## 0. Before starting

Collect by reading the project and the conversation. Ask only for what cannot be found, in one message:

- **What the user asked for, exactly**: agents or not, how many, which model, what time box ("don't take
  more than 10 mins", "only 5 don't go super overboard"). The size they name is the ceiling.
- **The standing rules**: the project's instruction file, memory notes, earlier briefs, the user's
  corrections in this session. A later rule overrides an earlier one.
- **What is already running**: other sessions, background jobs, cluster jobs, agents from earlier in this
  session. Never edit a tree another session is editing.
- **Constraints of the machine**: a laptop with no GPU and no data cannot run training or heavy tests ("you
  can't run anything!"). On the user's cluster, you write commands for them to paste; you do not log in.
- **The deliverable**: its path, its format, who reads it, and whether it replaces something the user has
  already seen.
- **The budget**: usage limits seen recently, and whether the user has said workflows are too costly.

For a job longer than one context window, create `STATE.md` from `assets/STATE.md` before the first launch.

## 1. Solo or fan out

- **Work solo by default.** The author's appetite for agents changed over the year: fleets in almost every
  prompt in early summer, then "running workflows is really costly ... try to figure it out your self", then
  "only 5", then one or two agents at a time. The latest standing rule is solo, or one or two agents,
  unless asked.
- **Fan out when the user asks in so many words, at the size they name, on the model they name.** "Fan out
  the ... subagents, don't do all of it in your main thread" is an order to fan out. "Make it better" is not.
- **Size by this rule, which the `adversarial-audit` skill repeats.** Work alone or with one or two agents by
  default. A size the user names is the ceiling. With no size named and a fan-out justified, use at most five
  lenses ("only 5 don't go super overboard"). Eight to thirteen lenses with one verifier per finding is the
  shape for a gate before compute only when the user asks for a full audit.
- **A fan-out pays off for independent work**: evidence gathering from separate sources, search over distinct
  hypotheses scored by a script, read-only audits with one lens each, fact checks against primary sources,
  builders checked by separate checkers. `references/fan-out-design.md` has the record of what paid off and
  what wasted.
- **Never fan out to rewrite a text the user owns.** Take their last version as the base, change only what
  is wrong or what they name, and list the changes in a few lines. Audits find errors in their version; they
  do not redesign it.
- **Under a deadline, do not spawn**, even if the user asked for agents minutes earlier. Hand over what
  builds now (section 10).
- **Launch designer or plotting agents only when the data they draw are complete.** Otherwise give each a
  hard return time and a partial-data mode that writes to a prototype folder. Three designer agents launched
  on data still being computed all missed a deadline set 25 minutes later, and the report shipped with a
  simpler script written in the main session.
- **One reviewer is often enough.** For a website, "a fleet costs more than it finds". For a final proofread
  the latest rule is one fresh agent per round, looped until a round comes back clean.
- **Test a limit; do not assume it.** A rule "no subagents until the limit resets" was written after a weekly
  limit hit; an eleven-agent workflow ran fine the next day.

## 2. One role per agent

- **Write a lens table before launching**: one row per agent with its single question, whether it may edit,
  its output path and its time box. Two agents with the same task is waste. The table template and lens sets
  that worked are in `references/fan-out-design.md`.
- **One shared brief file plus a lane prompt of three to six lines.** The brief (`BRIEF.md`, about 3 to
  10 KB) holds the rules, the format and the checks once. The lane names the scope, what the other agents
  cover ("not 3e, another agent does the trade-offs"), the files it may edit, and the output path. The brief
  itself is the job of the `prompt-writing` skill.
- **Quote the lines that bind the task into the brief**: the active short goal, the guardrail ids with their
  text, and the definition of done (these documents are defined in the sibling skill,
  `project-structure/references/governing-documents.md`). A helper agent does not read the repository unless
  told to, so a rule it was never shown does not bind it.
- **Auditors are read-only; one writer applies.** Auditors return edits as `{file, old, new}` with each
  `old` occurring exactly once. The coordinator verifies, applies, builds and re-checks. Two writers on one
  artifact is how versions diverge.
- **Choose the model per job.** The strongest model for reasoning, judging and anything the user reads; a
  cheaper model for mechanical work (running notebooks, link checks, leak scans, fixtures); fresh agents that
  have not seen the brief for audits of a deliverable. A fork inherits the parent's model, so a task wanted
  on a named model needs a fresh agent with a full brief.
- **Cap concurrency**: one lead plus at most three agents at a time, one per front, unless the user names a
  larger number.
- **Time-box every agent** ("finish within 15 minutes, fix the most serious first, log as you go") and give
  resource caps when agents compute: peak memory, disk, the interpreter path, and "check free memory and disk
  before big steps". Parallel forks once ran free disk down to 1 GB.
- **On a laptop, memory pressure eats disk.** macOS keeps swap in the same APFS container as the data, so
  parallel heavy forks ran free disk from 5.8 GB to 1.0 GB. Give each computing agent a cap (under 5 GB
  resident and under 200 MB scratch worked), one dataset at a time, and have it run `sysctl vm.swapusage` and
  `df -h /System/Volumes/Data` before each big step and wait when either is high. Watch the fleet with
  `ps -axm -o pid,rss,etime,command | head`; delete scratch environments when an agent finishes. On Linux,
  `free -h` and `df -h` play the same role (suggested, not yet tested in real work).
- **When several agents compute, write one shared engine yourself** and have them import it. Agents that
  each wrote their own estimator produced inconsistent results across panels.
- **Every agent says what it did not determine**: a confidence level, a "not determined" list and a replay
  command come back with every report.

## 3. What goes into a shared preamble

- **Facts and the question, no conclusions.** When you hand an agent a hypothesis, expect it back confirmed.
- **Diff every assertion in the preamble against the raw outputs** before fanning it out. A biased preamble
  is a data-integrity bug: six agents inherited one wrong sentence.
- **Put known corrections in, tagged "do not re-derive, do not report as a finding"**, or each agent pays to
  rediscover them. Two dead agents had independently found the same wrong parameter value.
- **Pasted output of another model, an old audit or a colleague's draft is a hint**, never a fact. The
  author said "take this with a grain of salt" at least seven times in one month.
- **Workflow scripts**: a label on every agent, a JSON schema on every agent whose output feeds code, the
  script saved to a file and launched by path, no backticks inside JavaScript template literals (a code span
  closes the literal and the launch fails), evidence bundles split into parts of about 45 KB.

## 4. Agents propose, a script scores, one judge checks

For any search (hyperparameters, thresholds, prompts, figure settings):

- **The objective is a deterministic script** with weights, hard disqualifiers and penalties written before
  the first proposal. It prints one parseable line (`EVAL_RESULT {json}`). No agent ever scores its own
  output.
- **Penalize each gaming route by name.** In the original search coverage could be gamed by merging
  everything and purity by shattering into fragments, so the objective scored 0 for any object over 3000
  units and multiplied by 0.85 when coverage exceeded 0.97.
- **Proposers get distinct hypotheses** (raise the weakest term, balance two settings, read the history and
  interpolate, a wildcard at the corners of the space) and return only the keys they change.
- **One adversarial judge** asks whether the champion is genuinely good or gaming the objective. A champion
  is promoted only if it beats the current one on the guarded objective and passes the judge.
- **The baseline is what the user already liked**; the search refines around it.
- **State on disk**: `state.json` (champion, score, baseline, cycle, history) and `history.jsonl`. Stop after
  3 cycles without improvement or at cycle 20.
- **Every round must change something visible.** "I don't see big changes between 1 and 3 ... I don't think
  your loop is efficient!" Save each round's output so the change can be checked.

`references/propose-score-judge.md` has the cycle, the objective and a ported workflow skeleton.

## 5. Persist and resume

- **Every agent writes to a real path early and incrementally.** Its brief gives the path and requires a
  section skeleton in the first tool call, then one edit per section: "A file with three sharp sections beats
  a perfect report that dies in your context."
- **Synthesis happens in the main session.** "What dies first is always the synthesis": evidence phases
  return, plan and final phases die. No synthesis agent inside a workflow.
- **If the harness blocks a subagent from writing its report file**, it returns the full findings in its
  message and the main session saves them at once.
- **Write a visible result early**, so a cutoff still leaves something to look at: "do it in a way that I
  have some pngs to look at even if you now run out of token limit".
- **Never write anything that matters only to a temporary folder.** A previous session lost a whole
  workflow's output that way. Temporary folders survive an app crash but not a reboot.
- **Long jobs keep STATE.md and a journal.** STATE.md (`assets/STATE.md`) holds done, running (ids, log
  paths), next, open, decisions, the user's rules and volatile paths. The journal (`assets/JOURNAL.md`) has one
  row per attempt, crashed ones included, with the intent written before the attempt starts. After any reset,
  read the brief and STATE.md before anything else.
- **Resume, do not restart.** Keep agent ids; after a limit resets, send each agent a short resume message
  that keeps its context and tells it not to re-run what it already prepared ("you can resume it, it used
  2.7m tokens already"). A workflow resumes by its run id within the same session only.

## 6. Long and overnight campaigns

- **Keep the language model off the critical path.** A deterministic driver advances the stages; agents run
  beside it for triage, gate decisions and writing. In the two-week design, a cheap triage agent could only
  retry or void a stage, an analyst opened gates daily, and a writer drafted from generated tables only.
- **For one night, one script**: stages `prep | smoke | sweep | eval | figures | all`, skip-if-done state
  files, fail-safe so partial results still render, a smoke on one job before any expensive sweep.
- **Chain the final step into one detached command**, so it finishes if the session dies:
  `until ! pgrep -f prep; do sleep 5; done; render_a; render_b; echo DONE`. One such chain completed four
  minutes after three sessions died on a usage limit.
- **Write gate criteria before the data arrives**: ordered criteria, inputs that do not count (aggregate
  deltas, single-row peaks, training loss), the noise floor ("a move under 2x SE is noise") and a one-command
  action. Then recommend, and wait for the user's word before an irreversible switch.
- **One namespace per variant**, never reused after a change; invalidate a sentinel when its input is newer.
- **Engineering jobs drop the ceremony**: no pre-registration documents, steward or judge agents, or planning
  files beyond the ones the brief names. Pre-registration stays for decision gates in research.

`references/long-campaigns.md` has the file set, the layered design, the gate block and the two-machine split.

## 7. After a crash or a usage limit

In this order, before re-running anything:

1. **Copy the scratchpad and task outputs out** of the temporary tree to a durable folder. They survive an
   app crash, not a reboot.
2. **Run the harvest script** on the session folder:

   ```bash
   python3 scripts/harvest_agents.py ~/.claude/projects/<slug>/<session> \
     --tasks /private/tmp/claude-<uid>/<slug>/<session>/tasks
   ```

   It is read-only. It prints the death point (a hanging tool call, an app death, a usage limit), and for
   every workflow the agents started, returned, failed and dead (started minus returned), retries sharing a
   key, whether each path the run's result names exists, and every file each agent wrote, with size and time
   or `MISSING`. Task outputs newer than the last record are flagged: those are deliveries.
3. **Harvest.** Finished agents' returns are in the run state file and the journal. Dead agents' tool trails
   survive in their transcripts (thinking is redacted on disk; the Write and Edit bodies and tool results are
   not), worth 93 to 186 kB each in one recovery. A run killed mid-way has no state file; its script is in the
   session transcript.
4. **Orphan audit**: every deliverable a run names must exist. Two were found missing five hours after a
   recovery was believed complete.
5. **Write FOLLOWUPS** (`assets/FOLLOWUPS.md`): per session the death, then items tagged `[nothing]`,
   `[needs-compute]`, `[needs-user-decision]`, `[needs-data]`, each with the exact next action, and a `RISK:`
   line.
6. **Resurrect**: resume agents by message; hand replacements their predecessors' partial files to keep and
   extend; if only the synthesis died, write it yourself from the digests.
7. **Grep the repository for temporary paths** after recovery; code that reads from a scratchpad breaks at
   the next reboot.

`references/crash-recovery.md` has the storage tiers, record shapes and the resurrection procedure.

## 8. Never report a dead workflow as complete; verify every claim

- **Report what is on disk, as counts**: "4 of 6 agents finished; 2 died at the usage limit; their partial
  files are at [paths]". A workflow status is not evidence.
- **Check the declared output path** before believing a failure or a success. A killed agent can still have
  delivered; a "completed" agent with an empty result is a token-exhaustion artifact.
- **Re-run each gate yourself.** Passed means the check, run from a clean shell, prints the value. Put the
  command and the value in STATE.md.
- **Verify every quoted number and fact at its source** before it goes into anything the user will send.
  Agents invented task facts, a probe that did not exist and a misspelled method name.
- **Treat suspiciously identical, fast or clean numbers as bugs** until proven otherwise: identical outputs
  across variants, identical memory figures, an 18-hour job reported as 12 minutes.
- **Triage every audit** into fix now, conflicts with the user's explicit instruction (keep theirs, say so),
  and decisions only the user can make (a short numbered list). Verify the audit's own claims first.
- **Freeze what is audited**: a snapshot with its sha256, or check scripts that re-run on the new version.

`references/verify-and-control.md` has the acceptance checklist and the triage table.

## 9. Controlling a running fleet

- **Propagate a new rule at once to every running agent**, verbatim, with the time and the files that
  changed ("files changed, re-read"), and save it to STATE.md or memory. When a co-author restyled two
  figures mid-run, eight of ten agents got a tailored message.
- **Stop the fleet when the author objects**, all of it, then verify nothing was touched (modification times,
  a diff against the last good state) and say so in one line. Four agents were stopped about three minutes
  after launch with exactly that check. Do the small fixes yourself.
- **Never build while agents edit the same tree.** Wait for their reports, check each log against its edits,
  build in a side folder, install only a clean build.
- **One live version of any brief.** Rename superseded briefs; a cluster agent once ran the old, broader one.

## 10. Under a deadline, and after a silence

- **Hand over what builds now, then iterate.** If the user asks mid-loop, give the current build marked "not
  final"; later fixes keep the same folder and file names.
- **Speed and accuracy are asked for together** ("faster yet don't lose accuracy"). Fill the waiting time
  with the checks: proofread the text, verify numbers, or start the next dataset behind a lock file while
  compute runs. Never drop a check to finish sooner, and say in the delivery message which checks ran.
- **Status in one sentence, about once a minute.** Four minutes of silence brought "you going?".
- **During any long research or search phase, deadline or not, post one progress line between bursts of
  tool calls**: what was found, what is next. Fifteen silent minutes of searching brought "go" and then
  "what?".
- **After an outage, a network drop or a long silence, the first message gives the state of each job in one
  line**, then work goes on: "Upload: failed, nothing reached GitHub, retrying in 8 batches. Animations:
  three of four rendered, agent restarted. Nothing is public." Check machine state yourself before asking the
  user anything: free disk (`df -h`), which agents are alive, what is deployed. The author once waited to free
  disk that `df` would have shown as 42 GB free, and restarts without a status line drew "I don't get what
  you're doing!!".
- **No helpers, long renders or research the user did not ask for**, and no explanations.
- **Time-box running agents** and tell them to fix the most serious items first, without growing the length.
- **Give a delivery a new file name** when the old file may be open on the user's machine.

## 11. Autonomy

**May be done without asking**: routine choices (record each in the Decisions block of STATE.md); keep
working without being prompted ("go", "and?" mean continue); read, search and audit; write inside folders you
created for this job; start the work the user asked for at the size they asked.

**Ask, in one bundled message while agents keep working, only for**: a budget or cap exceeded; a gate that
cannot be met; an unclear license or data-use question; a choice that changes the method's semantics (audit
items that "alter training behavior" were left for the author with a written trade-off); anything
irreversible. Mark your recommended option.

**Never, without the user's explicit word**:

- **Overwrite, rename or delete an output the user has seen, a working baseline, or any file outside the
  folders you created.** "The previous one was so good, you killed it?" Every variant gets a new name.
  Transfers are additive (no sync with delete into folders you do not own).
- **Recompute or restructure what the user has accepted.** "Do not recompute man!! we're good with tables."
- **Run what was not asked**: no training on a machine without a GPU, no logging into the user's cluster
  ("you give me the rsync and the command"), no re-running predictions when only analysis was requested.
- **Edit files another session is editing**, or send one request to two sessions. When you find faults in a
  document another session owns, hand that session or the user a table with one row per fault (what is
  printed, the remedy) and say in one line that you left the files untouched. A table of eleven faults with
  "I did not touch those files, since the other session owns them" was accepted as it stood.
- **Route file edits through the shell.** Edit and write calls give the user a reviewable change; a heredoc
  or a generated rewrite script does not. One script that replaced sixteen edits gave no reviewable diff,
  heredocs failed on the wrong working folder, and the user asked "why shell man?". The shell is for running
  programs and git.
- **Put a secret into the conversation.** Credential steps run in the user's own terminal; checks print only
  "set" or "EMPTY".
- **Push, publish or upload.**

Commands the user will paste are one line each, or one `bash <script>` line. A two-line paste without a
continuation once overwrote a 9.9 GB file. Say what success prints.

## 12. Usage limits and cost

- **Expect limits and design for them**: incremental writes, synthesis in the main session, state on disk.
  That design made one audit recoverable: five finding files existed whatever the later phases did.
- **Size to cost** by the sizing rule in section 1: the number the user named, otherwise one or two agents,
  and at most five lenses for a justified fan-out with no number.
- **When the user says to stop for cost, stop everything at once and leave it resumable.** "document what
  we did and safe-stop now!": stop every running agent, write STATE.md with what is done, what is half done
  and the paths of partial files, and reply with the one line that resumes the job. Do not start a summary
  agent to do it. Offer a stop point after each loop round so the user can end it cheaply.
- **An audit swarm can take hours and drift.** Give it a time box and a frozen target, and stop when it
  starts reporting on stale versions.
- **After a limit, resume; do not relaunch from scratch**, and check the disk first.

## 13. The report

Short enough to read on a phone, in this order:

1. **What is delivered or live**, with absolute paths and sizes. "Where did you write??" was asked more than
   ten times.
2. **Counts, then the top five, then where the rest is**: "0 critical, 2 major, 8 minor (4 need your
   decision)", then the five most important with location and exact fix, then the findings path.
3. **What changed**, one line per unit, in the user's terms.
4. **What you decided on your own**, and what needs the user's word or check (guessed readings, unverified
   names and numbers).
5. **What is not done or not checked**, plainly: "2 of 6 agents died; their lanes are unaudited".
6. **Agents still running**, each with what it is doing, or "none". An unreported live agent drew "you still
   have one subagent active, is that on purpose or is it stagnant".

Per experiment or item: kept, killed or inconclusive, with the run that would settle it. Never write a
conclusion the numbers do not support: "If v2 does not move the probe, say so plainly. That is a real and
publishable finding." A result that hurts the claim is reported with the same prominence as one that helps.
No glossary box, no bold walls, no praise, no tour of the tools.

## 14. Check before handing over

1. Run `scripts/harvest_agents.py` on the session if any agent ran in the background: no agent listed as dead
   without that being in the report, no `MISSING` file the report claims exists.
2. Open every deliverable at its path; re-run every gate and read the printed value.
3. Verify every number and fact the report states against its source file.
4. Confirm nothing the user had seen was overwritten, and nothing outside your folders changed.
5. Confirm every rule the user gave during the session reached every agent and is in STATE.md.
6. Check each finished unit against the project's `GUARDRAILS.md`, rule by rule, when the project has one.
7. Say what was not checked.

## 15. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| an eight-agent rebuild of a reply the author had worked out | "really killed my whole points ... just try to polish the edges" | the author's last version as base, minimal edits, a few lines of changes |
| fleets by default | "running workflows is really costly ... try to figure it out your self" | solo by default; the named size when asked |
| an oversized fan-out | "only 5 don't go super overboard, but deliver" | the size the user names, as a ceiling |
| a workflow reported complete after dying | "you say it's completed but it didn't it's a mistake" | N of M finished, the rest died at X, files at paths |
| synthesis agents inside workflows | "what dies first is always the synthesis" | files written early; synthesis in the main session |
| a preamble with a conclusion in it | "a biased preamble is a data-integrity bug" | facts and the question; corrections tagged "not a finding" |
| restarting dead agents from zero | "you can resume it it used 2.7m tokens already come on!" | resume by message; keep and extend partial files |
| losing the audit work | "please don't lose the audit work!" | skeleton in the first tool call, one section at a time |
| overwriting a liked output | "the previous one was so good, you killed it?" | a new name for every variant |
| editing files through the shell | "why shell man? why do you have to run things????" | the file tools for files; commands the user did not ask for go to them to paste |
| recomputing accepted results | "do not recompute man!! we're good with tables" | integrate only the new points |
| a summary metric over an obvious picture | "it's so obvious!" | look at the output before trusting the number |
| a helper fleet under deadline | declined | hand over what builds, then iterate |

## Reference files

- `references/fan-out-design.md`: where fan-outs paid off, lens tables, brief headers, the edit format, model choice, preamble hygiene, workflow scripts.
- `references/propose-score-judge.md`: the search loop, objective design with gaming penalties, state files, stop rules, a workflow skeleton.
- `references/long-campaigns.md`: files that survive resets, the layered unattended design, one-script overnight runs, gates written before the data, two-machine work, waiting on background jobs and allowlist-safe commands.
- `references/crash-recovery.md`: storage tiers, death-point signatures, journal and state record shapes, the orphan audit, FOLLOWUPS, resurrection.
- `references/verify-and-control.md`: the acceptance checklist, audit triage, propagating rules, stopping a fleet, building while agents work.
- `scripts/harvest_agents.py`: read-only list of what finished and dead agents left on disk under a session folder. Python 3.9 or later, standard library only.
- `assets/STATE.md`, `assets/JOURNAL.md`, `assets/FOLLOWUPS.md`: templates for the state file, the attempt journal and the post-crash triage.
