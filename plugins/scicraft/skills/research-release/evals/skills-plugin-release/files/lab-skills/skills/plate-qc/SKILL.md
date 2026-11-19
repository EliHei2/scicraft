---
name: plate-qc
description: Checks 96-well plate-reader exports for edge effects, saturated wells and blank drift, and writes a QC table. Use whenever a user shares a plate export or asks whether a plate run is usable.
---

# plate-qc

Use this skill with Claude Code when a plate export arrives.

1. Read the export (CSV from the reader software). Our exports live in @@HOME@@/plates/exports.
2. Flag wells above 3.5 OD as saturated.
3. Compare the outer ring with the inner wells; a difference above 15% is an edge effect.
4. Questions go to @@EMAIL@@.
