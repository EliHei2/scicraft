# The figure repository contract

The earlier plotting work in the source project was "scattered, mixed older aesthetics, and
embedded data prep inside plotting logic". The repository below replaced it. Its order of
construction is worth copying: the documentation contract first, then per-figure work, then
consolidation of shared code under a render-parity harness.

## Contents

1. Layout
2. One script per panel
3. Geometry, mockup, composer
4. Data and provenance
5. The panel map
6. The four documents per figure
7. Deferred doc sync
8. Outputs
9. The render-parity harness
10. Source data and deposits

## 1. Layout

```text
assets/                style module, palette (one source each)
code/utils/            shared helpers; one-way dependency: utils imports assets, never the reverse
code/figure_N/         panel_<letter>_<name>.py, supp_<topic>.py, _compose_figure_N.py
code/figure_N/_prep/   build_*.py and compute_*.py (raw outputs to small tables), geometry,
                       local copies of upstream plotting code, _explore/ for discovery scripts
code/archived/         superseded scripts, still runnable
data/figure_N/         small TSV or JSON tables the panels read
figures/figure_N/      panels/, the composed figure, caption.md and the three other documents
PANEL_MAP.md           one status table for all panels
PROVENANCE.md          one row per copied or built input; canonical runs; traps
```

`assets/repo/CLAUDE.md` holds the contract as a file to drop in the repository root. Keep the
set of documents small and non-redundant: "keep minimal set of .md files, no nested
redundancy"; detail goes to sub-files that CLAUDE.md points to.

- **Raw outputs stay outside.** Only `_prep/` scripts read them, each read has a PROVENANCE row,
  and anything needed at render time is copied, summarized or wrapped first. "All figure
  production should be self-contained here, no referencing to external locations": icons and
  reference images are copied in as assets.
- **Large intermediates are untracked and regenerable; the small derived tables are the
  artifact.** A crash once wiped a scratch folder with two versions of a script and a 2.2 GB
  frame; the cache outside scratch survived. Port any script that produced a shipped number
  from scratch into `_prep/` the same day.
- **Prep steps that take minutes are cache-first.** Each writes its small table once; a rerun
  reads that table unless the step is called with `--force`. Panels and supplements then rebuild
  in seconds, and every recompute is a deliberate act that shows in the command history.
- **A panel never depends on a cache it cannot rebuild.** Its loader regenerates a missing cache
  by calling the `_prep/` script that wrote it. Deleting one cache file once broke a dependent
  supplementary figure, and the break showed only at composition.
- **Exploration happens outside the repository, or beside the live figure as `_exp`.** Only
  what works graduates. Old versions move to `archived/` and are never deleted ("archive in the
  same folder the unused stuff"); they stay runnable as the source of caption numbers.
- **On a case-insensitive file system, never aggregate into a name that differs only in case.**
  `cat part_C3.jsonl > part_c3.jsonl` appended a file to itself until the disk filled at 12 GB.

## 2. One script per panel

- **"NEVER plot multiple panels together."** Each panel is its own script with its own pdf and
  png output, kept thin (the source capped them at about 150 lines, with a docstring ending
  `Adapted from: <path>`). Aggregation and long plotting code live in `_prep/`. Extract a
  single subpanel from an upstream multi-panel script instead of calling the whole thing.
- **Port upstream scripts by date.** Only scripts from about the last month count as style
  references, because older ones carry retired looks; schematics are exempt. Record the chosen
  source in the panel docstring (`Adapted from:`) and in the PANEL_MAP row.
- **The panel script asserts what the caption claims** about the rows it draws (a label, a
  sign, an equal seed set) before drawing. `assets/panel_template.py` is the shape.
- **Variants are selected by an argument or environment variable, never by a copied script.**
- **Reproduce before polishing.** When an upstream render is the ground truth, regenerate it
  first: as a subprocess wrapper of the upstream script, as a polished local copy in `_prep/`,
  or as a verbatim asset copy. Polish may change layout, names and units. It may not change a
  metric definition, a filter, a ranking or a direction.
- **Add options to shared renderers as default-off parameters** that leave every existing
  panel byte-identical; prove it with the harness. To retune a shared renderer for one panel
  without editing it, wrap it in `_prep/render_*.py` and patch there.
- **One renderer per chart form per paper.** Two different bar implementations in one figure
  family stopped reading one-to-one and were unified.

## 3. Geometry, mockup, composer

- **One geometry file per figure is the single source** of canvas size (89 mm single column,
  183 mm double column), letter band (4.5 mm in the source), row tops and every panel's x, y, w
  and h. Panels and composer both read it, so they never drift.
- **Mock up first.** `scripts/mockup_layout.py` draws a labeled box per panel on the exact
  canvas, with letters, and checks overflow, overlaps and patchwork rows. Settle shared rows,
  full-width rows and aspect ratios before drawing data.
- **Author each panel at its exact printed size.** "make the panels from the first place so
  that they have those proportions"; "do not rescale panels only for the main figure". Save
  with no tight bounding box, so the PDF page size equals the figure size; a tight box changed
  page sizes and the composer misplaced panels.
- **The composer places panel PDFs at native size and draws only the panel letters**, last, so
  no opaque panel paints over them. With PyMuPDF: a new page of the canvas size in points,
  `page.show_pdf_page(rect_mm, src, 0, keep_proportion=True)` per panel, letters, then
  `doc.save(path, garbage=4, deflate=True)` and a 320 to 600 dpi pixmap for the PNG. A missing
  panel prints a warning and is skipped. Captions never go on the canvas: "composer now draws
  only panel letters; on-canvas caption paragraphs removed".
- **A panel lifted from a report PDF keeps its outlines and is registered to the data.** The
  redaction that removes neighboring artwork also removes the vector polygons inside the area.
  The redaction is one full-page pass in PyMuPDF: `add_redact_annot(rect, fill=False)` on each
  area, then `apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
  graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED, text=fitz.PDF_REDACT_TEXT_REMOVE)`; the
  `REMOVE_IF_TOUCHED` mode would also delete axes and crop boxes that only touch the area. The sibling
  `book` skill ships a composer built on these calls (`book/scripts/compose_crops.py`).
  Read them with `page.get_drawings()` before redacting and draw them back afterwards with
  `Shape.draw_polyline`. When the lifted panel is laid over raw data, register the page frame
  to the raw frame: match the drawn polygons to the raw centroids, fit the transform, and
  report the share of polygons that lands within a stated distance of its centroid. A crop that
  does not register is not the data its caption names.
- **Note which composer is canonical.** A standalone composer went stale after a panel was
  resized inside the combined figure.
- **Write down the regeneration order** (prep, panels, composer) and the render-size contract
  between panel scripts and composer in PANEL_MAP.

## 4. Data and provenance

- **One canonical run per method and dataset, in a registry** (the "Canonical runs" table in
  `assets/repo/PROVENANCE.md`). Never pick a run by guessing; ask "which version is this?"
  before computing. Reuse upstream derived labels (cell types, clusters, embeddings) and never
  recompute them in a new figure; the author's anger at a re-typing was recorded as "do not
  regress", and the old typing script was retired. Before using a new run, check what the
  sibling figures use and flag any inconsistency.
- **Every copied or built file gets a PROVENANCE row in the same edit**: file, builder, source,
  source date, rows, date.
- **Name the traps**: files that share a name with the canonical table but hold an older
  recompute.
- **A side table overrides base keys explicitly.** A first-match lookup over a plain concat
  silently kept a superseded value.
- **Verify every join numerically.** A dataframe join reordered rows and a positional column
  paste attached ids to the wrong items, so a method "looked broken". After a join, assert row
  counts and a physically meaningful invariant (distance to the assigned center, identical key
  columns). Refuse a lossy join.
- **Find a number's provenance by reproducing it** to three or four digits, probing candidate
  definitions until the digits match; record the parameter that matched, or write "not
  reproducible". The first output of any new evaluation script is a known number reproduced
  exactly.
- **Verify a public dataset's identity byte for byte** against the public bundle (a small
  member file fetched by HTTP range request), not by its title. This catches a mislabeled sample
  or a wrong feature count before it is printed on a panel.
- **Re-read user-editable constants every session.** The author edited color constants at the
  top of a composer and renamed them between sessions.

## 5. The panel map

`assets/repo/PANEL_MAP.md` is the template. One table across all figures, no nested maps.

- Columns: Panel (displayed letter), Name, Claim role, Aesthetic anchor (the reference figure
  it copies), Upstream source, Script, Output, Status (draft or final), Synced (- or yes),
  Notes.
- Per figure: a layout graph, the composition block in mm, the generation commands in order,
  QA notes, and "retired, do not re-add" lines with reasons.
- Displayed letters often differ from file stems; the map keeps the mapping.
- Update it in the same edit as any panel, data or status change. `scripts/docs_status.py`
  lists rows whose paths are missing, scripts the map never names, data without provenance and
  owed syncs.

## 6. The four documents per figure

Hand-written, under `figures/figure_N/`, templates in `assets/figure_docs/`:

| Document | Holds |
|---|---|
| `caption.md` | the public caption: bold claim sentence; data and filter once; per panel what is shown, how it is computed, n, error-bar type, data source, color key; selection disclosures; nulls in place; source-data index |
| `NARRATIVE.md` | the locked claim, the arc, per panel Claim, Contrast, Magnitude and Takeaway (each claim with its number), results against the claim, the manuscript-reportable numbers table |
| `METHODS.md` | formulas, implementation file and function, filters and floors, the comparison protocol, per-panel size and script index |
| `TECHNICAL_NOTES.md` | the reproducibility manual: deliverables, external prerequisites with sizes, environment, run order, dated decisions (LOCKED, DEAD END, KEEP AS IS), checks run, quirks |

The caption carries "every detail: what's shown, how it's computed, very specific", including
exactly where the data are downloaded from. Proofread every cited number and path against the
rendered panels and the tables. A stale caption after a panel swap or a letter change was a
recurring bug.

A multi-session figure also keeps a log (`assets/FIGURE_LOG.md`): newest section on top, dated,
with LOCKED blocks that say what they supersede, dead ends, rejected items with reasons, open
questions for the author, and the doc sync owed.

## 7. Deferred doc sync

**The figure's own documents never wait.** The caption, `NARRATIVE.md` and `TECHNICAL_NOTES.md`
of the figure being edited change in the same edit as the panel: a new filter, threshold, n,
color key, panel letter or default goes into all three before the render is shown. After several
edits the author asked "did you update all relevant md files for this plot?", and a stale caption
was a recurring bug.

Folding a panel's reusable lessons into the project's guideline files on every edit would make
those files churn faster than figures. Only that sweep is deferred:

- A new or changed panel row gets `Synced = -`. The figure log lists what each document owes
  ("DOC SYNC DEFERRED: PANEL_MAP rows for b and c, PROVENANCE for the new table, caption still
  uses the old term").
- PANEL_MAP and PROVENANCE rows are still written in the same edit. What waits is only the
  sweep of reusable lessons into the guideline files; the four documents update in the same edit.
- On "update docs" or "sync docs": review every unsynced row, fold reusable lessons into the
  guidelines (concept tags and style rules grow monotonically: refine or add, do not delete),
  check the four documents against the panels, then flip `Synced` to `yes`.
- Run `scripts/docs_status.py` before and after the sweep.

## 8. Outputs

- **Every edit ships PNG and PDF in place.** The live-text SVG is regenerated on every edit once
  a submission set exists, because a stale SVG is what the journal receives; before that it may
  wait until the layout holds. A submission SVG set "silently goes stale the moment a panel is
  re-rendered": in the source, a set left for later went stale after a single panel change and
  nobody noticed, and a co-author who resizes text in a vector editor works from that SVG. The
  newest rule (the author's standing "PNG + PDF + SVG" rule, late in the project) replaced an
  earlier drafting-stage instruction to leave SVGs until everything had settled.
- **Regenerate the SVG from the composed PDF in the same edit**, together with the drift section
  of `FIGURE_SVG_MANIFEST.md` and the caption when annotations change.
- **Match each journal SVG back to the submitted manuscript.** Rasterize each SVG and each figure
  image in the manuscript to grayscale at one size, compute the normalized correlation, pair
  each SVG with its best match, then look at every pair. Record the pairing, the score and any
  drift in `FIGURE_SVG_MANIFEST.md`; a low score means the SVG and the manuscript no longer show
  the same render.
- **Keep SVG text editable.** Glyph-path text is useless to a co-author who resizes text in an
  illustration program. PyMuPDF with `text_as_path=False` keeps text; a converter that outlines
  Type 3 fonts does not. Embed fonts as Type 42 in the plotting style (data-figures).
- **Back up outputs before re-composing.** On a near-full disk a composer truncated two PDFs
  mid-write; the backups restored them.
- **Never stop a build mid-write**, and run builds that write the same file one after another.
- **Keep a table of the plotted values next to each figure** for co-authors.
- **Name deliverables by the manuscript's current figure numbers**, numbered by first citation
  in the latest manuscript.

## 9. The render-parity harness

Use it before any refactor of shared figure code: moving panels onto shared helpers, changing a
style module, renaming labels across figures. In the source, one figure family moved onto a
shared package with zero regressions, and the harness caught a commit that had deleted a module
two panels still imported, which had left a composed figure silently stale.

```bash
cp <skill>/assets/units.example.json units.json     # list every panel, supplement and composer
python <skill>/scripts/parity/render_all.py --repo . --units units.json --baseline
# ... refactor ...
python <skill>/scripts/parity/render_all.py --repo . --units units.json
python <skill>/scripts/parity/compare.py --snap _verify_snap --intended INTENDED_CHANGES.tsv
```

- Each output gets a sha256, a 96 x 96 grayscale grid (PDFs rasterized at 110 dpi) and its PDF
  page size. Classes: identical; identical modulo encoding (mean absolute difference below
  0.004); changed as intended (listed in `INTENDED_CHANGES.tsv` with a one-line reason;
  template in `assets/repo/`); regressed (anything else, a changed page size, a missing output
  or a failed unit), which exits 1.
- Each unit runs in its own subprocess, so global plotting state cannot bleed between panels.
- Always run the full registry before comparing; a filtered run once skipped a composer.
  `render_all.py` warns about scripts that match `script_globs` and no unit runs.
- Track `baseline_manifest.tsv` (force-add it past any blanket `*.tsv` ignore); gitignore the
  snapshot folder.
- Look at the triptychs in `_verify_snap/diffs/` for every changed output.
- A label rename across figures is proved the same way, plus a token diff: compare the text
  tokens of old and new PDFs (`pdftotext`) and the vector marks (`page.get_drawings()`), and
  report where pixels changed ("all inside the four label boxes"). Then `number_parity.py`
  confirms no number moved.
- **A relabel across many figures starts by finding every place the label is produced**: grep
  the code, run `pdftotext` on the rendered PDFs, look at the images in the submitted document,
  and find upstream generators that a wrapper rewrites in memory. Patch the wrapper and leave
  upstream code unedited. Keep each figure's own casing (sentence case in one, title case in
  another). Back up every output first and render with `TMPDIR` on local scratch. Report a table
  (figure, old label, new label, file), how the numbers were checked, and what was deliberately
  not renamed, then ask one question (confirm the wording, update the manuscript file?).
- **When a published figure has no source** (a raster composite inside the document), repaint
  only the label with `scripts/repaint_label.py`: it takes a byte copy of the document's image,
  erases fixed label boxes given as arguments, draws the new text, writes PNG and PDF under a new
  name, and fails unless every changed pixel lies inside the boxes. Record the repaint in
  PROVENANCE with the date.

## 10. Source data and deposits

- **Source data per figure**: one folder per figure label, one CSV per panel, named
  `Fig<N><x>_<descriptor>.csv`, rebuilt by `code/source_data/build_<fig>.py` from the inputs the
  published panel read. The builder reruns into a temporary folder and must come out
  byte-identical; it reads every file back (shape, last line, UTF-8, header, no index column,
  no internal IDs, no NaN strings), and redraws the panel from the CSV for comparison.
- **A data deposit holds what the paper needs and no more.** The author's limit was 10 to 15
  reference tables of the kind colleagues already deposit; bulk outputs go to separate folders;
  "no readme, no text, just simple data". Show the file list before asking for approval of a
  large deposit; an approval given without opening the list was withdrawn an hour later.
- **Each deposited file must be readable alone.** An output that held only row numbers into
  another table was shipped with that table.
- **Check every identifier written from memory** (accession, collection ID) against local files
  before shipping it.
- **Source data follow what the published figure shows.** When a co-author restyled a figure
  after your render, the CSV uses the published wording and carries the extra information the
  restyled panels display (item names, for instance). List every difference from the repository
  render in the report.
- **Prove whether vector originals exist before saying none do.** When a co-author asks for
  them, content-match every `.pdf`, `.ai` and `.svg` in the user's folders, and every raster in
  the download and document folders, against the figure. Ship verified rasters wrapped in SVG and
  name the panels that need the co-author's own illustration files. Map figures by their in-text
  citation, never by caption heading: two captions in one manuscript were both headed "Figure 4".
