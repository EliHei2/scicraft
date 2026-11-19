# FOLLOWUPS after [crash, usage limit, app death] on [YYYY-MM-DD]

Sessions: [N]. Scratchpads copied to: [durable path]. Harvest report: [path to harvest_agents.py output].

Tags: `[nothing]` the agent can do it now; `[needs-compute]` needs the cluster or a GPU machine;
`[needs-user-decision]` only the user can decide; `[needs-data]` input is missing. Every item ends with
`->` and the exact next action. `RISK:` names what lives only in a volatile place.

---

SESSION [session id]   [start, UTC] -> [end, UTC]
TOPIC : [what the session was doing, one or two sentences]
DEATH : [exact last record: type, tool, time; app death, usage limit or tool hang, from the harvest report]
CORRECTS: [if the dead session's own closing diagnosis was wrong, the correction; else "none"]
  1. [nothing] [what is unfinished and what survives of it, with paths]
      -> [exact next action: a command, a file to write, an agent to resume with its id]
  2. [needs-user-decision] [the decision]
      -> [the options, with your recommendation]
  3. [needs-compute] [what must run elsewhere]
      -> [one-line command or `bash <script>` line for the user to paste]
  RISK: [paths that exist only in temp folders, unpushed commits, ignored result folders]

---

SESSION [next session id] ...
