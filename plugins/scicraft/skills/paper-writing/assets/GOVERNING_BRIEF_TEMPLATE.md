# Governing brief: [document title]

**Version** [0.1], [date]. **Written by** [the author]. Agents read this brief first and quote the
lines that bind their task. When a rule here conflicts with an older note, this brief wins; record
the conflict in the decisions log below.

## 1. Operating brief

- **Scope.** [What the agent may produce now: one section, one chapter, a figure audit. What waits for
  the author's review before the next step.]
- **Authority order.** [Which source decides what. Example: the author's explicit correction decides
  intended contribution and emphasis; the latest manuscript decides reported numbers; the analysis
  code decides what an experiment actually did; the accepted draft decides wording and headings.]
- **What agents may touch.** [Files and folders an agent may edit; files that are read-only; whether
  helper agents may edit at all or only report.]
- **Before acting.** [Recover the working state (section 5); read the relevant sources; edit the
  minimum; pass the gates in section 3; report changed files, open evidence and the next action.]

## 2. Rules per chapter or project

One block per chapter, main section or contributing project.

### [Chapter or project name]

- **Structure.** [Sections in order, each with its one claim.]
- **Terms.** [The names to use and the names that are retired.]
- **Claims allowed.** [What the evidence supports, at which status. What must not be claimed, and why.]
- **Attribution.** [Copied from the published contribution statement.]

## 3. Accuracy gates

- **Numbers.** Every number traces to the facts file in `GUARDRAILS.md`.
- **Attribution.** Every contribution sentence matches the published statement word for word.
- **Citations.** Every key exists and says what the sentence attributes to it.
- [Further gates: figures against their source panels, captions readable alone.]

## 4. Acceptance contract

For each deliverable, mark each line pass or fail from files actually inspected. A failed line is
repaired or labeled unresolved; it is never passed by adding explanatory prose.

| Gate | Pass when | Checked by |
|---|---|---|
| Science and attribution | [every number, priority claim and comparison tied to its source] | [facts file, by hand] |
| Results and figures | [every result names its experiment and panel] | [caption read alone] |
| Narrative and register | [headings and wording of the accepted draft kept] | [`drift.py delta`] |
| Limits and evidence level | [results, exploratory work and proposals kept apart] | [status tags] |
| Deliverable integrity | [files present, build clean, gate clean] | [`prose_qa.py`, build log] |

## 5. Continuation inventory

Updated at every checkpoint, so a new session resumes the work instead of restarting it.

| Task | Location or output | State (done, in progress, blocked, needs audit) | Evidence | Next action |
|---|---|---|---|---|
| [task] | [path] | [state] | [file, log or diff] | [action] |

**Open decisions for the author** (only what the papers, data, code and this brief cannot settle):

1. [decision, with the competing sources]

## Decisions log

| Id | Date | Decision | Brief item | Reason |
|---|---|---|---|---|
| D1 | [date] | [what was decided] | [section] | [why] |
