# Fan-out: one builder per region, figure QA with the orchestrator

A figure with four to eight independent regions over one library parallelizes well. The split of
duties is the rule: builders see only their tile and "will not catch 'the whole thing reads like a
slide'", so the figure-level judgment stays with the orchestrator. Spawning mechanics are in the
`agent-orchestration` skill.

## Before fanning out

1. Scaffold `code/` from `assets/`, set `layout.js`, and **smoke-render the master with one block or
   the placeholders**. Open the PNG and confirm the pipeline and the proportions. Never fan out on an
   unproven pipeline.
2. Write `SPEC.md` from `assets/spec_template.md`: the rules, the anti-slide list, the theme and color
   semantics, and one section per region (content, notation, crop target, data global, what is left out).
3. Put real data in `data/` through `_prep/` and record it in `PROVENANCE.md`.

## The builder brief

One agent per region, the strongest model available. Each brief carries, in this order:

- the goal: "write `regions/region_<id>.js`, defining `drawRegion_<id>(ctx, W, H, R)`";
- files to read: `SPEC.md` (its region section and the rules), `core_lib.js` and the pack it uses,
  `ref_crops/orig_<id>.png` when there is a reference, the house figures;
- the contract: only `PAL`, `FONT`, `LIB`, `SCENE` and its data global; no hex, no font strings, no
  literal sizes; never the letter or title; stay inside the rect;
- the loop: render the preview with `--check`, open the PNG beside the crop, fix the smallest defect,
  at least three times;
- the gates: `lint_regions.py regions/region_<id>.js` and `render.js ... --check` both clean;
- the return: a status line, the preview path, anything it could not match.

Builders never edit `core_lib.js`, a pack, `layout.js` or `main.js`. A missing primitive comes back as
a request; the orchestrator adds it once to the library so every region gets it.

## Orchestrator QA

After the builders return:

1. Render the master with `--check`; run `lint_regions.py` over `regions/` with `--layout` and `--main`.
2. Open the full PNG. Read it as a reader: does it read as one figure, with one flow and one palette?
3. Open each region at 2 to 3 times zoom beside its crop.
4. Fix slide tells, gray primary text, collisions, dead space, mismatched sizes. Make the smallest change.
5. Repeat until three successive looks find nothing.

## Review fan-out before calling it done

When time allows, run independent reviewers, one dimension each, on the rendered PNG: layout and
whitespace, typography tiers, clipping, science against the caption and the code, color and
redundancy. A synthesis step settles disputes against the data and the code. For checks a script can
make, write the script first and give each a cheap reviewer that returns PASS, CAVEAT or FAIL with
numbers. This caught a caption that disagreed with its figure and a title printed over a color bar.
See the `adversarial-audit` skill.

## Choosing proportions or a design

- **Judged sweep**: render N variants of a layout to separate output folders, let reviewers score each
  PNG (ratio, snugness, clipping, compactness) and a judge pick.
- **Design tournament** (used for model figures): several designers with different biases (rigorous,
  teaching, compact), weighted judges, a best-per-panel synthesis, then a QA loop until each dimension
  scores at least 8 of 10. Keep the losing candidates in `archive/`.
- **Staged sign-off with the author**: layout first, then density, then detail. Show the PNG every
  turn, make the smallest change asked, never improve several things at once.
