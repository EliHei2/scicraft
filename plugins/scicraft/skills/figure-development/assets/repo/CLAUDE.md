# CLAUDE.md

This repository holds the figures of [paper]. The deliverable is the rendered figure; the
standard is that every figure regenerates from tracked panel scripts, tracked small tables
and documented provenance.

## Layout

```text
assets/                 style module and palette (one source; see the data-figures skill)
code/utils/             shared helpers (save, compose, geometry); one-way: utils imports assets
code/figure_N/          one public script per panel: panel_<letter>_<name>.py, kept thin
code/figure_N/_prep/    aggregation, geometry, local copies of upstream plotting code
code/archived/          superseded scripts, still runnable; never deleted
data/figure_N/          the small tables each panel reads (TSV or JSON)
figures/figure_N/       panels/, the composed figure, and the four documents
PANEL_MAP.md            one status table for all panels
PROVENANCE.md           one row per copied or built input; canonical runs
```

Raw run outputs stay outside this repository. Only scripts in `_prep/` read them, and each
such read has a PROVENANCE row.

## Rules

1. Write the figure's one-sentence claim at the top of its NARRATIVE.md before any panel.
2. Mock up the layout from the geometry file before drawing data.
3. Reproduce a reference figure before polishing it; polish changes layout, names and units,
   never metric definitions, filtering, ranking or direction.
4. One public script per panel, drawn at its printed size in mm. The composer places panel
   PDFs at native size and draws only the panel letters. Captions live in caption.md.
5. Every plotted number is read from a table in `data/`. Nothing is typed into a script.
6. Every edit ships PNG and PDF in place; the live-text SVG on every edit once a submission set
   exists. Back up old outputs before re-composing.
7. A panel, data, asset or status change updates PANEL_MAP.md, PROVENANCE.md and the figure's
   caption.md, NARRATIVE.md and TECHNICAL_NOTES.md in the same edit. Only the sweep of reusable
   lessons into the guideline files waits for a doc sync: mark the row `Synced = -`.
8. Refactors of shared code run under the render-parity harness; any unlisted change fails.
9. Open the composed PNG before calling anything done.
10. Experiments happen outside this repository or beside the live figure as `_exp`
    variants; only what works is promoted, and the old version moves to `archived/`.
11. A figure's own NARRATIVE.md or guardrail file adds to the project's governing documents and
    never relaxes them; the project's GUARDRAILS.md wins.
12. Before a figure is shared, work through `figures/figure_N/FINAL_CHECK.md` and record the
    date and commit.
