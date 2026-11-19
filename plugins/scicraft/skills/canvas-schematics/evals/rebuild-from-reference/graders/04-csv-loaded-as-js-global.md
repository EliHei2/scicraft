---
type: llm
focus: trace
weight: 1
---

The points of cells.csv reach the page through a generated .js file that assigns a window global (for example window.PANEL_B = ...), and no file in fig_overview calls fetch.
