# Figure [N] technical notes

How to rebuild this figure on a new machine, and what was checked. Newest decision first.

## Deliverables

| File | Made by | Role |
|---|---|---|
| `figures/figure_[N]/figure_[N].{pdf,png}` | `code/figure_[N]/_compose_figure_[N].py` | main figure |
| `final_figures_svgs/Figure_[N].svg` | live-text PDF to SVG conversion | journal upload |

## External prerequisites

| Path (relative to a named root) | Size | What it is | Read by |
|---|---|---|---|
| `RESULTS/[...]` | [GB] | [raw per-item outputs] | `_prep/[build].py` |

## Environment

[Interpreter and version, packages with versions, any script that needs its own environment.]

## Run order

1. `python code/figure_[N]/_prep/[build].py` ([minutes]; cache-first, `--force` recomputes)
2. panels, then the composer (PANEL_MAP.md has the exact list)

## Decisions (dated, newest first)

- [date] LOCKED: [decision]. Supersedes [earlier decision]. Reason: [ ].
- [date] DEAD END (do not retry): [what was tried], [why it failed], [scripts kept at ...].
- [date] KEEP AS IS: [deliberate choice a reviewer pass might undo], [reason].

## Checks run

- [date] render-parity: [n] outputs identical, [n] changed as intended.
- [date] main against supplement: every default value equal at [n] digits.
- [date] fact-check: every printed number traced to its table row.

## Quirks

[Fonts, glyphs, path depths, byte stability, anything that broke once.]
