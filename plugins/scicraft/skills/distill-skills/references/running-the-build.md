# Running the build

## The state file

A build of this size runs for hours to days and outlives the lead's context several times (context
compaction, a cleared session, a crash). `STATE.md` in the private workspace is what makes it
resumable. Template: `assets/STATE.md`. Its sections, and why each is there:

| Section | Holds | Without it |
|---|---|---|
| header | package and workspace paths, the launch line, model, agent cap | every launch re-derives paths and wording |
| what the user asked, in order | each request in their words, numbered | requests added late fall through |
| mining | done, running, second wave with the skill each feeds | miners relaunched twice or never |
| writers | done and gate-clean (with revisions), running with a timestamp, the queue in order, launch notes | lost order; late evidence missed at launch |
| after the writers | the numbered steps to finish: late findings, coverage, licenses, review, package, numbers, sharing | the end of the build improvised |
| decisions already taken | one line each, from evidence | writers re-litigate settled points |
| to tell the user at the end | secrets to rotate, integrity handling, license status, risks found on the way, where the open questions are | the most important messages forgotten after a reset |

Rules:

- **Read it first after any reset**, before any tool call that changes something.
- **Update it after every launch, every finished agent and every decision.** A state file that is an
  hour stale is worse than none, because it is trusted.
- **Keep it an index.** Under about 150 lines; detail lives in the files it names (findings, build
  notes, coverage).
- **Launch notes beside the queue**: "When launching X, add: also read findings Y (rule Z)". The note
  goes into that brief at launch.
- The state file is a working file. Delete it, or move it out of the workspace, when the package ships.

## Queue and cap

- Launch writers in an order that lets early skills serve as models: the model skill first (the one
  every brief points to), then skills that others will point to as siblings, then the rest.
- At most the agreed number at once (20 in the original build); launch from the queue as slots free.
- **One writer per skill.** Two agents editing one skill folder break it; a revision goes to the
  writer that holds the context, or to one fresh agent after the first has finished.
- **Check every writer's claim** before marking it done: the folder exists, the gate passes when you
  run it yourself, the build note exists.

## Late findings

Second-wave findings and the author's new requests arrive while writers run. Route each one, and write
the routing into the state file:

| The target skill is | Route |
|---|---|
| not yet launched | add to its brief's decisions, or a launch note |
| being written | a message to its writer |
| finished | a revision agent: the folder, the build note, the new findings, the named items |
| not in the set | a new spec row, a new brief (`make_briefs.py --only`), a place in the queue |

## Reporting to the user

The author of the history is busy and reads on a phone. Status lines are one sentence. The final
report, in this order:

1. what exists: the package path, the number of skills per plugin, the gate result for all;
2. what to do now: rotate the listed secrets (kind and date only);
3. how requests that must not become rules were handled;
4. license status and third-party pieces;
5. what was not checked or not run;
6. the open questions, collected from the build notes.

Numbers for the author's portfolio (prompts, findings, rules, skills, scripts, evals) come from
scripts (`tally_findings.py --totals`, a package stats script), never from memory.
