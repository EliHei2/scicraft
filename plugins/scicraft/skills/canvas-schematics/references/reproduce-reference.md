# Reproduce the reference first

When the user hands over a figure ("rebuild this", "do that", "make it like this one"), the job is
faithful reproduction first and polish second. Adapted copies drift, and "re-deriving ad-hoc is the
#1 source of rework and user frustration." If the reference came from code, find and rerun that
generator before redrawing anything.

## Procedure

1. **Measure the reference** and set the canvas to its aspect ratio, within 2 %:
   ```bash
   python3 scripts/ref_crops.py reference.png --suggest-width 1830
   ```
   Wrong proportions read as "not the same figure". A graphical abstract is usually landscape
   (about 1.4); a square canvas was one of the slide tells.
2. **Cut one crop per region** and look at each one:
   ```bash
   python3 scripts/ref_crops.py reference.png --out ref_crops a=0,0,0.55,0.42 b=0.57,0,1,0.42 \
       c1=0,0.46,0.16,1 c2=0.17,0.46,0.37,1
   python3 scripts/ref_crops.py reference.png --canvas 1830x1290    # after setting layout.js
   ```
   Boxes are fractions of width and height; a JSON file works too (`--boxes crops.json`).
3. **Set `layout.js` from the crops.** Region rects follow the reference's arrangement, uneven widths
   included (the densest stage is the widest).
4. **Reproduce the idioms**, not just the content:
   - a table drawn as solid color columns (`LIB.colorBar`), never a bordered spreadsheet;
   - a model as labeled block, arrow, block;
   - losses as small matrices in a thin dashed frame;
   - a field of view as the real crop with outlines (see `references/real-data.md`).
5. **Each region builder gets its crop as the target** (`ref_crops/orig_<id>.png`) and opens it beside
   its preview on every iteration.
6. **Deviate only where the user asked** ("make panel b real data"). Record each deviation in SPEC.md.

## When there is no reference

Name the house figures (the paper's finished data figures) and two or three published exemplars of
the same kind (for an architecture figure, I-JEPA Figure 1 or the DINOv2 overview), and copy their
density, flatness and type sizes. Show a rendered sketch early: the user judges a look, and "cannot
evaluate a description".

## A datasets-used overview

A benchmark paper often opens with one figure of the datasets it uses. The author's version went
through about ten rounds; what held:

- **One row per dataset**: a source glyph or icon, the dataset name, then a row of descriptor cells
  (rows, features, size, density, area, whatever the benchmark compares), sorted by group.
- **Color encodes the group only** (provider, platform, modality), shown by a colored bracket and
  label beside the rows. A column that repeats the group is deleted: "if you show technology with
  color no need to have that column".
- **Every cell has the same size and prints its value; opacity carries the magnitude**, scaled on
  each column's own range. The first version varied dot size, and the author asked to "change only
  their alpha". Units go in the column label ("move K and M to the column labels").
- **Text is black at a regular weight**, no bold, titles included.
- **Every descriptor comes from the provider's page.** One summary showed a density the author
  doubted ("is this density really true??") and areas the author suspected were made up; each value
  was checked against the dataset's public page. Record the page per row in `PROVENANCE.md`; the
  sibling skill `integrity-audit` holds the full fact-check procedure.
- **Export each icon** to `figN/parts/` (next section), so the same glyphs serve the slides and the
  website.

Start from `assets/region_example_overview.js` with `assets/data_example_overview.js` (fictional
values) as `data/datasets.js`; it draws the brackets, a default table glyph per row (replace it with
`drawIcon` in the data global), the cells and an opacity legend:

```bash
node render.js "preview.html?region=a&data=datasets" prev_a 898 538 regions/out --check
```

## Exporting parts

When asked for the small parts as well ("give me all small artefacts ... in a folder"), render each
icon or glyph from its own preview at the same device scale into `figN/parts/`, so it can be reused
elsewhere at print quality.
