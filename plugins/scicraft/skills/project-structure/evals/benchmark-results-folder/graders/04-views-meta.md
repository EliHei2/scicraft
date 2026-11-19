---
type: llm
focus: trace
weight: 1
---

Each model's outputs go to their own folder in the run root, written append-only (new part files, never rewriting earlier ones), and each such folder has a metadata file saying how the outputs were made
