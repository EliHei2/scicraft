# Recovering after a crash or a usage limit

Distilled from recoveries after an app crash, a machine crash, a weekly usage limit that killed 21 of 25
agents in one evening, and several session limits. The paths are Claude Code internals as observed in 2026.
They may move; check the layout once with `ls` before trusting this file.

## 1. Two storage tiers

| Tier | Holds | Survives |
|---|---|---|
| `<tmp>/claude-<uid>/<project-slug>/<session>/` (on macOS under `/private/tmp`) | `scratchpad/`, `tasks/*.output` of background commands and agents | a crash of the app, a usage limit; **not a reboot** |
| `~/.claude/projects/<project-slug>/` | `<session>.jsonl` transcript; `<session>/workflows/wf_*.json`; `<session>/workflows/scripts/*.js`; `<session>/subagents/...` | everything |

**First move after any death: copy the scratchpad out**, before anything else, to a durable folder such as
`~/.claude/projects/<project-slug>/recovered/<date>-crash/`. One recovery saved 115 MB this way: 304 census
files and seven evidence bundles that existed nowhere else.

## 2. Find the death point

```bash
python3 <skill>/scripts/harvest_agents.py ~/.claude/projects/<slug>/<session> \
  --tasks /private/tmp/claude-<uid>/<slug>/<session>/tasks > recovered/harvest_<session>.txt
```

The script diffs the transcript's tool calls against their results and reads the tail:

| Signature | Meaning |
|---|---|
| a tool call with no result at the end | the session died inside that call |
| no hanging call, trailing queue-operation records | the app died; the user was queueing messages into an app that was gone |
| "You've hit your session limit" in a workflow's `logs` | a usage limit; running agents keep their partial files |
| a task output newer than the last record | a background job finished after the session ended: a delivery |

The last tool call of one dead session had already returned the number it spent the night hunting. Read the
tail before re-running anything.

## 3. Record shapes

- **Journal** `<session>/subagents/workflows/wf_*/journal.jsonl`: `{"type":"launched"}`,
  `{"type":"started","key","agentId","label","phase"}`, `{"type":"result","key","agentId","result"}` (the
  field is `result`, not `value`), `{"type":"failed","key","agentId"}`. Older journals carry no `label`;
  recover the lens from the first user message of the agent's transcript.
- **Started minus returned is exactly the set of agents that died.**
- **Retries share a key.** Several `started` records with one key and different agent ids are attempts at one
  task; read them oldest first. Later attempts are usually shorter.
- **Run state** `<session>/workflows/wf_*.json`: `status`, `result` (with `digest`: the concatenated return
  values of finished agents), `logs` (which agents failed and why), `script` (the whole workflow source with
  every agent's prompt). It is written only when a run finishes, even when every agent inside failed.
- **A run killed mid-way leaves no state file and no script.** The script survives only in the transcript:
  the `tool_use` block with `name == "Workflow"`, field `input.script`. The `workflows/scripts/` folder holds
  only finished runs, so its absence proves nothing.
- **Agent transcripts** `agent-<id>.jsonl` (with `agent-<id>.meta.json`; `finished: true` when it ended).
  Thinking blocks are redacted on disk: the text is empty and only a signature remains. The tool trail
  survives and is enough: every Write and Edit target with its body, every shell command, every tool result
  (where probe output and config reads live). Dead agents yielded 93 to 186 kB of usable material each.
- **Task notifications** in the session transcript carry the full result payload of finished background
  agents, sometimes richer than what was shown in the chat, and sometimes an earlier, better run that a later
  resume overwrote.

## 4. The orphan audit

A campaign is not recovered because some of it was. For every run state file, pull `result` and check that
each path it names exists (`harvest_agents.py` prints `MISSING (orphan)`). Two lost deliverables, one of them
seven agents times about 44 kB of finished research, were found this way five hours after the recovery was
believed complete. `"final": null` plus limit lines in `logs` is the signature of a run whose evidence
returned and whose synthesis died.

## 5. Write FOLLOWUPS before acting

Fill `assets/FOLLOWUPS.md`, one block per session: start and end, topic, the exact last record, and numbered
items tagged `[nothing]`, `[needs-compute]`, `[needs-user-decision]` or `[needs-data]`, each with `->` and the
exact next action, plus a `RISK:` line for what lives only in volatile places. Correct a dead session's own
closing diagnosis when it was wrong. Then do the `[nothing]` items and send the user the rest in one message.

## 6. Resurrect, do not restart

- **Same session, agent still known**: resume it with a short message that keeps its context ("Resume your
  [task] from where you stopped; the limit has reset. Same rules. Do not re-run the scripts you already
  prepared."). Nine agents killed together at a session limit were resumed this way.
- **Same session, workflow**: stop it and resume from its run id, so cached agents are reused. Resuming a run
  works within the session that started it, not across sessions.
- **New session**: hand the replacement its predecessor's partial files and surviving probe scripts, and tell
  it to keep and extend them, never overwrite. Four of six dead agents had already written a skeleton or a
  full verdict table; those files were the starting point.
- **Only the synthesis died**: write it yourself from the digests. "Writing it myself from the digests is what
  won." Or spawn one writer per lost deliverable with the digest split into parts of about 45 KB.
- Fold the corrections the dead agents found into the replacement's preamble.
- Rerun a cached workflow so that only the dead agents run again, when the harness supports it.

## 7. After the recovery

- Grep the repository for hard-coded temporary paths (`grep -rn "/private/tmp/claude-" .`). A manifest
  builder once read its inputs straight from a dead session's scratchpad and would have become unregenerable
  at the next reboot.
- Check derived files for freshness. An agent re-ran a corpus script during a session and the manifest's hash
  changed under the main session.
- Record the incident and its lesson where the next session will read it (memory note, STATE.md).
