---
type: llm
focus: trace
weight: 1
---

One config file in tabfm holds the paths including the remote address me@gpu-box:/work/tabfm, and a sync script uses rsync with -u (or equivalent) and excludes .git, and never passes --delete
