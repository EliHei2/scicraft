# Generator-driven geometry and deterministic randomness

Any tree, partition, graph, point cloud, density, trajectory or embedding that stands for
what a method computes is produced by the method's own code and emitted as TikZ. A
figure built this way cannot misstate the method, and it rebuilds identically.

**Contents**
1. Why: what went wrong without it
2. The pattern: gen_<figure>.py
3. The shipped generators
4. Two datasets: a hero set and a toy set
5. Deterministic randomness
6. Emitting TikZ that compiles
7. facts.json: the numbers the figure shows
8. When the real code cannot run here

---

## 1. Why: what went wrong without it

- A concept figure carried a hand-drawn tree ("some random tree") and a hand-drawn
  partition that did not match what the code computes. Both were replaced by geometry
  generated from the real backend.
- A zoom cascade re-sampled points per level; the clump in one frame had no relation to
  the next. One field with nested crops fixed it.
- A scatter used `rand` without a seed and moved on every compile, so two versions of the
  same figure disagreed.
- A sphere graticule computed in an inline `\foreach` failed with "Unknown operator 'a'";
  computed in Python and emitted to a file, it compiled.

## 2. The pattern: gen_<figure>.py

```
figures/<figure>/
├── gen_<figure>.py     imports the real function, runs it on a fixed-seed input
├── frag/               frag_*.tex written by the generator (coordinates only)
├── facts.json          every number the figure shows or depends on
├── body.tex            frames, labels, connectors; \input{frag/...} while iterating
└── <figure>.tex        preamble + body with fragments inlined: the delivered file
```

1. Import the backend function (the partitioner, the tokenizer, the graph builder, the
   sampler). Do not reimplement it for the figure: a reimplementation drifts from the
   code the paper describes. If the package import pulls heavy dependencies, copy the one
   function out with a comment naming its source and version.
2. Run it on a fixed-seed synthetic input, or on a small real sample chosen by a stated
   rule (scan by rank, check that the dramatic case is not an artifact).
3. Write coordinates in a local frame (`[-1,1]^2` is the convention here) so a fragment
   drops into `\begin{scope}[shift=(..), x=..cm, y=..cm]`.
4. Write `facts.json` beside the fragments.
5. Build panels one at a time, as a narrative, and look at each before the next.

The emitters in `scripts/tikz_emit.py` (`points`, `rects`, `segments`, `smooth_cycle`,
`tree`, `write_frag`, `write_facts`) are importable:

```python
import sys; sys.path.insert(0, "path/to/skill/scripts")
from tikz_emit import points, rects, tree, write_frag, write_facts
from mymethod.partition import build_tree          # the real backend
cells, nodes, edges = build_tree(xy, capacity=4)   # your function's own output
write_frag(Path("frag/partition.tex"), rects(cells, "celledge") + points(xy, "ptdot", 0.9))
```

## 3. The shipped generators

| Script | Produces | Run |
|---|---|---|
| `scripts/density_zoom.py` | a four-level zoom: KDE bands, density window, points, kNN ego ball, from one field; `facts.json`; a self-contained `fig.tex` | `python3 scripts/density_zoom.py --out zoom/ --preamble assets/preamble.tex` |
| `scripts/tikz_emit.py` | the emitter library, and a worked example: an adaptive quadtree on a seeded toy set, drawn as the partition and as its tree with one address traced | `python3 scripts/tikz_emit.py --out frags/ --preamble assets/preamble.tex` |

In the quadtree example, `build_partition()` is a stand-in: replace it with an import of
the method's own partition function and keep the emitters. Both scripts take `--seed`,
print what they built, and exit non-zero when a check fails (`density_zoom.py` fails if
any neighbor of the ego falls outside the last frame).

## 4. Two datasets: a hero set and a toy set

Use two inputs when a figure has both dense and legible panels: a "hero" set (about 230
points in the original figure) for density panels, and a "toy" set (about 50 points) for
trees and addresses a reader must be able to follow node by node. Both are seeded and
both are named in `facts.json`.

## 5. Deterministic randomness

- **In Python:** `numpy.random.default_rng(seed)` or `random.Random(seed)`, the seed a
  command-line argument with a default, and the seed written to `facts.json`.
- **In TikZ:** `\pgfmathsetseed{N}` before every loop that uses `rand` or `rnd`. A loop
  that must produce the same jitter for several panels sets the seed inside the panel
  (`\pgfmathsetseed{\k*97+\j}`). The safety script warns when `rand` appears without a
  seed.
- **Prefer coordinates over runtime randomness** for a figure that will be kept: emit the
  points once from Python. PGF's generator can change between TeX versions; a file of
  coordinates cannot.
- **The same cloud perturbed, never a new cloud.** In an animation or a before-after pair,
  seed once and perturb the same base pattern.
- **In a canvas or JavaScript figure** the same rule holds with a seeded generator; see
  `canvas-schematics`.

## 6. Emitting TikZ that compiles

- `plot[smooth cycle, tension=0.6] coordinates {(x,y) (x,y) ...}`: points separated by
  spaces. Joining them with `--` fails with "Cannot parse this coordinate".
- Three decimals are enough at figure scale and keep files small.
- Draw density bands lightest first and the core last.
- Keep dot radii in pt (`circle (0.8pt)`) so they do not scale with the frame; keep paths
  in frame units so they do.
- Compute anything with `and` in it (ellipse radii, per-point sizes) in Python.
- Emit style names from the preamble (`ptdot`, `celledge`, `tnint`, `tnleaf`, `tedge`,
  `tpath`, `tnpath`, `egoring`, `egospoke`), never
  raw hex colors, so the theme switch still applies.

## 7. facts.json: the numbers the figure shows

Every number drawn in the figure or quoted in its caption (point counts, k, a radius,
depth, number of leaves, a selection rule) is read from `facts.json`, never retyped.
Before hand-over, compare each number in the caption and in the figure with the file.
Where a showcase example was selected (an ego point, a window, a sample), record the rule
and the candidates it was chosen from.

## 8. When the real code cannot run here

If the backend needs hardware or data that are not available (a cluster, a GPU, a large
private dataset), run the generator where it can run, commit the fragments and
`facts.json`, and build the figure from those files. Say in the hand-over which
fragments were generated where. Never substitute hand-drawn geometry and present it as
the method's output; if it must be hand-drawn, it is schematic and is marked so.
