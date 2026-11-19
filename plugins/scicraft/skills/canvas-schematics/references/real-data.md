# Real data, real code and honest geometry

A schematic earns trust when its structures come from the thing it describes. Two failures drove
these rules: a concept figure whose partition was not the one the code builds, and a tree drawn by hand
that the author dismissed as arbitrary. A third: slide formulas that did not match what the code
computes.

## Data as a JS global

`file://` pages cannot `fetch`. A `_prep/` script writes each dataset as a script that sets a global:

```python
# code/_prep/build_panel_b.py  (Python, any data library)
import json
pts = load_window(path, x0, y0, size)          # crop of the real data, about 1,000 points
payload = {"source": str(path), "window": [x0, y0, size], "pts": pts}
open("code/data/panel_b.js", "w").write("window.PANEL_B = " + json.dumps(payload) + ";\n")
```

```html
<script src="data/panel_b.js"></script>   <!-- before the region files -->
```

- **Keep a panel to about 1,000 points.** More reads as noise at print size and slows the render.
- **Normalize coordinates to [0, 1]** in `_prep/` and map them into the region rect in JS.
- **One point field, nested crops.** Zoom levels crop the same field; never re-sample per level, and
  do not thin displayed points if a neighborhood shown is computed on the full set.
- **Choose the shown window honestly**: rank candidate windows by the property the panel must show and
  check that the dramatic one is not an artifact. Rank with the renderer's own functions.
- `PROVENANCE.md` gets one row per data file: source path or accession, window, date, script.

## Generate structure from the real code

When a figure shows a partition, a graph, a tree, a mask or a neighborhood that a method computes,
generate it with that method:

1. A `_prep/gen_<panel>.py` imports the real function, runs it on a fixed-seed synthetic or real
   input, and writes `data/gen_<panel>.js` plus the numbers the figure shows (`facts.json`).
2. Use two inputs where legibility differs: a "hero" set of about 230 points for density panels and a
   "toy" set of about 50 points where every node must be readable.
3. The region draws from the global and never adjusts the geometry by hand.

## Make the schematic match the implementation

- **Write the caption and SPEC.md first** and depict the mechanism correctly before any polish. Keep
  a list of mechanism traps in "trap, then correct depiction" form in SPEC.md.
- **Derive every formula from the code**, not from memory or a summary; asked "how exactly do you
  compute it?", the answer is the line of code. Check sign, normalization, which terms are summed,
  and which inputs are detached.
- **Let a blind reader compare.** One agent that has not seen the drawing's intent reads the code and
  the rendered figure and lists every mismatch. "It should be a 1:1 match."
- State in SPEC.md what the figure leaves out (a capping step, a schedule), so the omission is a choice.

## Exact versus schematic

- **Quantitative geometry comes from equations or data.** A curve, a distribution or a coordinate drawn
  to look measured must be measured.
- **Illustrative geometry gets no exact-looking ticks, fits or values** and is marked "schematic" or
  "illustrative" in the caption.
- **No measured results in a concept schematic.** Numbers belong in the data figures, where they are
  traceable. A number that does appear (a dataset size, a count of layers) comes from the paper.
- **The visual equals the reported number.** When a schematic shows a quantity per object (a fraction
  colored per cell), the color encodes exactly the per-object value that is aggregated in the text.
- **Emphasis by color, size or order only where the values are printed or drawn to scale.**
