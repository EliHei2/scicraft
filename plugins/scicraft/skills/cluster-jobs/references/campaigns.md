# Unattended campaigns

The author planned to leave an agent running a campaign on the cluster for 10 to 14 days while they
worked on something else. What they asked for: "a big, accurate, but robust DAG", "self-maintained
and decision safe ... breakable, if things went wrong, smart in rerouting on queues", "handle the
cases if I run out of tokens", and for failing samples to be down-weighted or ignored with a record
kept. The design below was built and verified; it was not launched while six items for the
human were open, so its long-run behavior is untested. Its parts that ran in other projects are
marked.

## 1. The principle

**The model is never on the critical path.** About 95% of the loop is deterministic bash and
standard-library Python. The model is called on a schedule and on exceptions. If it dies, stalls,
is rate-limited or is stopped, the graph keeps advancing and the campaign still lands.

`assets/dag_driver.py` is a reduced, standard-library version of the L0 driver below (stages from
a JSON registry, a required-input check, sentinels that record input and output hashes, gates that
open only with an evidence file and numbers, `ended()` chains, STOP), and `assets/lint_dag.py`
checks the graph before launch. Both read cluster names, queues and paths from a local config the
user keeps; both pass their `--self-test`, and neither has run against a real scheduler.

## 2. The four loops

| Loop | Actor | Cadence | May do | May not do |
|---|---|---|---|---|
| L0 driver | a standard-library script, no model | every 10 min | submit, reconcile with the scheduler, mark done, write incidents | anything that needs judgment |
| L1 triage | a cheap model, headless | every 2 h and on an incident (debounced to one call per 20 min) | retry a job, void a stage, file an incident | open a gate, touch code or results |
| L2 analyst | a strong model, headless | once a day, after the overnight jobs land | read summaries, open or close gates with evidence, write the daily report | run jobs, edit results, edit the pre-registration |
| L3 writer | a strong model | once a day from the freeze date | draft text from generated tables | invent a number |

- The driver runs under the system `python3` and imports nothing outside the standard library: the
  login nodes could not import the project's NumPy. It checks this by re-running itself with `-S`.
- Triage gets a context of a few kilobytes (status, the last 30 incidents, the tails of at most 3
  failed logs), a tool allowlist (read state and logs; the scheduler's status commands; the driver),
  skills disabled, and at most 6 turns. Its whole action space is `retry`, `void`, `incident`.
- A gate opens only through a command that refuses unless `--evidence` names an existing file under
  results and `--numbers` is non-empty. "A gate decision that cannot name a file and a number is
  not a decision."
- If the analyst missed a day, the next one runs with a 48 h evidence window and a "missed day"
  section; it opens only what the evidence supports.

> **No gate is ever opened by a timeout or a default.** An unopened gate blocks, and blocking is
> safe: the subtree waits, the GPU budget is not spent, nothing wrong is published.

## 3. Three ways to keep the driver alive

| Mechanism | What it is | Survives | Does not survive |
|---|---|---|---|
| supervisor | `nohup` loop on the submit host: L0 every cycle, L1 to L3 on schedule; each tick in a subshell, `set -uo pipefail` without `-e` so one failed tick never ends it | ssh logout, a crashed tick, a failed model call | a reboot of the login node, an admin reaper |
| heartbeat | a short scheduler job that runs one driver step and submits its own successor with a delayed start (`bsub -b`, `sbatch --begin`) | a reboot, a dead supervisor | the scheduler being down; it cannot triage if compute nodes have no outbound network |
| scheduler chains | sub-graphs submitted with `ended()` dependencies | no driver alive at all | a stage whose spec must change between attempts |

The heartbeat stops itself three ways: past the campaign's end date; when the STOP file exists;
and it skips its step (still resubmitting) while the supervisor's log is fresh. "A self-resubmitting
job with no brake is how you leave something running on a shared cluster for a year."

Chains use `ended()`, never `done()`: a failed upstream leaves a `done()` dependent pending forever.
The driver's self-test greps every generated submission for `-w "done(` and fails if it finds one.

## 4. State

Small structured files, each with a size cap, so a model tick costs kilobytes:

- `state/dag.json`: per stage, status (`pending ready submitted running done void skipped
  blocked`), job id, job key, attempts, free retries, dependencies, sentinel path, gate, and the
  resource spec (queue, memory, wall, GPU model, cores). Cap 64 KB.
- `state/gates.json`: per gate, status, who decided, when, the evidence path, the numbers. Cap 8 KB.
- `state/ledger.jsonl`: append-only, one record per submission and decision. For humans and for
  GPU-hour accounting; no model reads it.
- `state/incidents.jsonl`: append-only, kind, stage, job id, detail capped at 500 characters.
  `NEEDS_HUMAN` is the page.
- `state/STOP`: its existence halts all new submissions everywhere; checked by the supervisor, the
  heartbeat and the submit wrapper independently. It kills nothing running. Only a human creates
  or removes it.
- model call transcripts kept 14 days, so a bad decision can be reconstructed.

`reconcile` is the central verb: any divergence (a job that finished while nothing watched, a
job the scheduler forgot, a sentinel that appeared during a reboot) is repaired by reading the
scheduler and the filesystem, never by guessing.

## 5. One wrapper for every submission

Every job goes through one submit script; a bare submit is a breach. It refuses:

- when STOP exists, or past the campaign window;
- a job body outside the version-controlled repository;
- destructive verbs in the body (`rsync --delete`, recursive deletes of `/`, forced pushes, killing
  all of a user's jobs);
- absolute paths outside an allowlist (with the stated limit that paths built from variables are
  invisible to it);
- a missing queue or wall time; a wall above the cap; cores or memory above the per-GPU caps scaled
  by the GPU count; a multi-GPU job without a single-host span; `gmem` with `gmodel`; `gmem` without
  a unit;
- a filesystem below its free-space floor;
- more live jobs than the concurrency cap; the hourly, daily, per-queue and GPU-hour budgets spent;
- a duplicate: same job name pending or running, or the same content hash already in the ledger.

It appends one ledger record per submission. `scripts/lint_job.py` carries the static subset of
these checks for interactive use.

## 6. Budgets

- Jobs: at least 5 and at most 25 GPU jobs a day, submitted when the cluster is least loaded, to the
  right GPU family, never to a preemptible queue.
- Model calls: a hard daily cap (16 = 12 triage + analyst + writer + 2 spares). When it is spent,
  triage is skipped first; the analyst and the writer are protected because they produce the durable
  artifacts. On any model failure, back off 5, 10, 20, 40, 80 minutes, capped at 120. A rate-limit
  message sets a cooldown until its reset time (or 6 h).
- If the model is unavailable for a whole day, the driver still advances and the analyst catches up
  the next day.

## 7. Failure semantics

| Failure | Detected by | Automatic response | Human paged |
|---|---|---|---|
| job exits | scheduler state, no sentinel | stage blocked; incident with the log tail; triage classifies and retries | at the attempt limit (void) |
| memory limit | the termination reason | retry with memory x 1.5 | after the third |
| pending forever, bad GPU string | pending longer than the timeout | kill, step down the fallback ladder, resubmit | after 2 requeues |
| dependent pending after an upstream exit | "never satisfied" | kill it, mark the subtree skipped | only if it fires (`ended()` should make it impossible) |
| supervisor dead | its log older than 3 cycles, seen by the heartbeat | heartbeat keeps stepping | yes |
| fast filesystem filling | free space below the floor | refuse stages that write there; delete nothing | below the hard floor |
| sentinel not visible yet | scheduler says done, file absent | refresh the directory, 180 s grace, incident after 2 ticks | no |
| result present, its null control absent | the stage validator | incident `NULL_MISSING`; the gate cannot open | yes |
| truncated output behind a sentinel | hash, bytes and rows stored in the sentinel | rename to `.done.bad`, count an attempt | at the limit |
| stale code on the cluster | marker grep before submit, checksum manifest of frozen code | refuse to submit | yes |
| GPU-hour budget spent | ledger total | refuse GPU submissions | yes |

"Human paged" means one line at the top of the daily report and of the daily check script, which
exits 1. No pager, no email: "The human reads one screen a day; the system's job is to put the
important line on it."

## 8. What the machine may never do

Open or close a gate outside the analyst; edit frozen model code (checksum manifest re-checked
before every job); delete anything under results, state or snapshots; kill a job that is not in its
own ledger; exceed the submission budget; run project Python on the submit host; `rsync --delete` into data, results, state or snapshot folders on the cluster (a code mirror uses it); edit the pre-registration after its tag (hash compared before every submission);
write a number into a manuscript that is not in a generated table.

## 9. Attempts and voids

A stage that exhausts its attempts is void and published as void: in the daily check, in the
report, and in the supplementary run table as attempted-and-failed with its reason. Stages that
depend only on a void stage become skipped, so the graph routes around the hole and the campaign
lands with a documented gap. Samples that keep failing are down-weighted or excluded with a record,
never silently.

The attempt journal (one row per attempt, crashes included, with an intent field) was adapted from
a public autonomous-research harness; its greedy hill-climb and its "never stop" rule were rejected
for a pre-registered campaign.

## 10. One night, one script (ran in real projects)

For an overnight run the same ideas shrink to one script the user starts before bed:

```bash
bash run_overnight.sh all        # or: prep | smoke | sweep | eval | status
```

- Stages `prep | smoke | sweep | eval | all`, each guarded by a state file
  (`.state/<stage>.done`) and skipped when done; a pre-GPU gate before the sweep.
- Fail-safe: a failed unit is skipped and recorded, so partial results still render. "do it in a
  way that I have some pngs to look at even if you now run out of token limit."
- Budget: "don't exhaust the resources please!! ultrathink the order and priorities." The most
  important units go first; the script prints what it submitted and where results land.
- In the morning: copy results to the laptop, look at the pictures first, then the tables.
- When the agent sits in a sandbox that cannot authenticate to the scheduler, it leaves a directory
  of linted job bodies and one launcher; a human runs the launcher from a normal login shell, and it
  refuses with a clear message if it finds itself inside the sandbox.
