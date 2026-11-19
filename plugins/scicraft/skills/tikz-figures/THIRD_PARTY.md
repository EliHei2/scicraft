# Third-party material

## Someone else's code in this skill

None. Every file, macro, style definition, recipe and script in this folder was written
for this skill or for the author's earlier figure skills, which this one replaces. In
particular:

- `scripts/check_tikz_safety.py` was rewritten from scratch for this skill, from a list of
  the failures it must catch. An earlier version was described as adapted from another
  skill's checker; none of that version's code remains.
- The stacked-heads and residual recipes (`references/architectures.md`, sections 12 and
  13) were redrawn from scratch in this skill's grammar. Earlier versions adapted from a
  Stack Exchange answer (CC BY-SA) were removed.
- The depth and token macros (`\nnstack`, `\StackBox`, `\opstack`, `\tokenrow`) were
  rewritten for this preamble.

One set of numbers comes from a library: the nine stops of the `ramp0` to `ramp8` colors
are matplotlib's "Blues" colormap (matplotlib license, BSD-style; the colormap derives
from ColorBrewer, Apache 2.0). Color values are data, not code.

## Credited as inspiration only

Ideas and conventions learned from these sources; no file, macro or script body from them
is copied:

| Source | What was learned |
|---|---|
| Patrick-Healy/tikz-diagrams-skill (GitHub) | a static check before compiling; the render-and-inspect loop; presentation modes; the exact-versus-schematic distinction; a bounded repair loop; design gates for animations |
| fraserlove/nntikz, opentikz, janosh/diagrams (GitHub) | the vocabulary of rounded module blocks, thin sub-layer rows, token cells and offset copies for depth |
| the V-JEPA 2 paper's architecture figure | the two-rail teacher-student layout meeting at a latent loss |
| C. Bunne, *Neural Optimal Transport*, ETH Zurich, 2023 | the serif theme is modeled on its figure style; the theme is defined by measured colors and line weights (`references/themes.md`), and no macro, style or code from the book sources is used |
