# The loop in detail

Reconstructed from roughly 40 figure cycles over six months on one benchmark paper. A main
figure took 1 to 3 working days and about 100 to 300 messages from the author. One figure went
through five layouts (five bands at 211 mm tall, three bands at 191 mm, seven rows at 135 mm, a
large example plus a 3 x 2 grid at 236 mm, and a final 183 x 142 mm page). One row of another
figure took about ten rounds of notes. Plan for this; do not plan for one pass.

## Contents

1. Lock the message
2. Build variants beside the original
3. Lock the metric
4. Choose panels
5. Compose
6. Render, look, fix
7. Working with the author
8. Close-out

## 1. Lock the message

- **Write one sentence before any panel**, at the top of NARRATIVE.md and the figure log, with
  the date. The sentence that set the pattern had this shape: the method uniquely wins the
  balance of [metric A] and [metric B], is always strong on [secondary axes], in a fair
  head-to-head across [n] datasets and [m] platforms. The old line-spaghetti, beeswarm and heatmap panels it replaced
  were deleted as dead code.
- **Include the mechanism when there is one.** One claim was a double dissociation: method A
  corrupts neighborhood definition 1, method B corrupts definition 2, and the method under
  test stays near the reference on both. The panels were derived from it.
- **Name each panel's role in an arc.** "problem (a, b, c), then why (d), then how (e), then it
  works (f)", or establish, mechanism, quantification, consequence. A panel that cannot be tied
  to the sentence moves to the supplement or is dropped.
- **Keep a hero panel** that carries the sentence on its own (a trade-off plot, in the source).
- **If the author calls the figure "awful" or "degenerate", go back to the sentence, not to
  the panels.** "Degenerate" meant the evidence had been cut and two schematics were carrying
  the figure.
- **When the claim moves, re-derive the panel list.** Do not patch panels toward a new claim.
- **Before claiming something new, run a literature check.** When the phenomenon was already
  known, the figure was reframed as quantify, rank and decompose, with credit to the prior work.
- **Ground the claim in what the data can measure.** Research agents get the real feature list
  as a file; every claim and every citation they produce is verified (they produce wrong ones).
- **The author's question when the message is missing**: "what's the message of this figure in
  one sentence?" Ask it of yourself first.

## 2. Build variants beside the original

- **Additive, never destructive.** A new version is `figure_N_exp` with its own composer, its
  own panel scripts and its own geometry file, sharing only the style module and palette. The
  original stays untouched and runnable. Alternatives get `exp2`, `exp3` (minimal, one and a
  half columns, a co-author's markup). The author chooses; the winner becomes the figure; the
  rest move to `archived/`.
- **Exploration that may not work lives outside the repository** and graduates only if it
  looks right ("graduate only if the examples look good").
- **Reproduce the reference first.** "find the latest proper figure and just copy-paste exactly
  as is, then I will tell you what minimal changes to polish." Rerun the script that made the
  reference image; never re-implement it. Re-implementations changed heatmap aesthetics and
  broke the link between two panels' data, several times.
- **Minimal change to existing code.** "for each panel we pretty much already have a panel
  somewhere, so use minimal code changes." Commit often so that "bring back the previous
  version" takes one command.
- **Version every layout.** One supplement went volcano, heatmap, volcano, heatmap over five
  days; each "go back" was cheap only because the versions existed.

## 3. Lock the metric

- **Define metrics against the benchmark's own defaults**, verified in its code (file and line).
  "Default" means what the published rule applies: one export's "default" applied no threshold
  at all, so a panel built on it was measuring a bug. When a default is ambiguous, ask.
- **Expect churn and lock with a date.** One metric changed about five times and "made the
  author anxious". The lock line read: "LOCKED [date]. Do not re-tune the gate or numerator
  without the author."
- **Present trade-offs as options and let the author choose the gate**, with the cost of each
  option written down. Choose before seeing the ranking (evidence.md, section 13).
- **Implement the author's definition as stated.** When a quantity is defined in words (a
  geometric test with a minimum count), code that definition and lock it with a date. A
  convenient stand-in, a graph-topological version of a geometric test, inverted its sign at one
  neighbor count and cost three redefinitions. Panel constants import the same definition.
- **One implementation, imported everywhere.** "make sure your implementation is the same as
  the package's validate metric."
- **Keep a settings diff whenever numbers move.** The author asked for exactly this: "give me
  an overview of the current settings, what's different and why."

## 4. Choose panels

Lead with the form that shows the claim most directly. For a machine-learning paper:

| Claim | Panel that carries it | Evidence standard that bites |
|---|---|---|
| ranks first across tasks | rank per task, methods sorted by mean rank, one dot per task plus a mean marker | every method scored on every task, or the task dropped for all |
| wins a trade-off | the method's own sweep as a curve, competitors as points, the good corner marked | the native operating point marked; a two-point true version beside it |
| each component matters | drop-one ablation, median across seeds with interquartile range, dashed line at the full model | the full-model row equals the main table; seed noise shown |
| scales | runtime or memory against data size, one clock, failures as red x, lines broken at failures | equal marks per method; subset runs are non-runs |
| beats a baseline per item | head-to-head scatter of A against B on the same items, with x = y | same items, same eval protocol |
| differences per task | paired difference forest (ours minus each baseline) with bootstrap intervals, a star only where the interval excludes 0 | units are tasks or seeds; ties shown as ties |
| each competitor fails a different way | double dissociation: x = error under failure axis 1, y = error under failure axis 2, a reference crosshair at the reference value on both axes, each competitor far out on one axis, the method under test near the crosshair on both | both axes computed on the same items against the same reference |
| it looks right | qualitative examples picked by a stated rule | examples.md |

General rules:

- **A main figure needs at least one real-data example and one quantified panel.** A pipeline
  diagram goes to the supplement unless it is Figure 1. Never hand-draw a concept schematic in
  a plotting library; by default add none (canvas-schematics or tikz-figures when one is
  needed).
- **Introduce a category in the panel where the story reveals it.** An early panel shows the
  problem state only: "before you introduce [the new category] just drop them". ML form: the motivating
  failure panel does not show the fixed model's numbers.
- **Every quantitative panel must separate the arms.** A panel where every method scores about
  the same is not interesting: its number goes to the caption.
- **Add a "so what" panel**: the downstream decision the error flips (a stratification call, a
  deployment threshold, a leaderboard order).
- **Lead with the visible hero, then quantify** across the whole dataset.
- **Encode values, in one chart family per figure.** Dense dot plots ("it's not obvious what
  they say") and invented encodings were removed. When asked for "nicer", polish the existing
  plot type.

## 5. Compose

- Mock up from the geometry file (`scripts/mockup_layout.py`), then author every panel at its
  box size, then compose at native size with letters only (repository.md, section 3).
- **A regular mosaic.** Panels in a row share a height; a tall panel may span whole rows, but
  heights never form a patchwork. Panels of the same kind get identical plot areas.
- **A big figure is split before it is shrunk.** One figure grew to 343 mm tall; a print split
  was flagged, then the figure was compacted to one page of 183 x about 140 mm.

## 6. Render, look, fix

- After each render, open the PNG (review.md, section 1). Do not report from exit codes.
- **Notes arrive in bursts**, 5 to 30 messages one to three minutes apart, each naming a panel
  letter and a change, often while the previous render is running. Write each into the figure
  log in the author's words before touching anything, apply them in order, re-render, then
  trace every note against the render.
- **Adjustments come as factors**: 1.2x, 0.8x, 0.75x, 0.9x, "a tad" (about 1.1x). Keep sizes as
  named constants and apply the factor to exactly the elements named.
- **Data challenges come mid-loop** ("are you sure", "this cannot be true", "why does it have
  fewer cells?"). Stop and verify by an independent path before continuing; a surprise is a
  suspected bug.
- **Quiet surgery on an embedded image** (removing an outline from a raster tile inside a
  finished PDF). Re-run a copy of the tile script from its cached inputs and first prove the
  unmodified re-render equals the embedded image (0 differing pixels). Then remove the drawing
  step and confirm every differing pixel lies within the stroke width of what was removed.
  Replace the image in a copy of the PDF, deliver before, after and difference PNGs, and add no
  revision marking.
- **Show the render every turn** and make the smallest change asked. "don't generate anything,
  just move things and rename things" means exactly that.

## 7. Working with the author

- **Fewer check-ins, batched edits.** The author wanted speed.
- **The newest work on disk is the base**, whichever agent produced it ("go down that path,
  don't follow your own work").
- **Ignore a note clearly sent to the wrong chat**, and record that you ignored it.
- **Never kill processes you did not start** (the author ran notebooks in parallel), never stop
  a build mid-write, and do not run heavy renders concurrently with other heavy jobs.
- **Long runs are resumable and say where their files are.** "where can I see the intermediate
  results?" came up repeatedly.
- **Match the effort to the request.** Extra figures nobody asked for drew "you're just getting
  out of hand".
- **A figure agent that works across rounds** is continued with the same context, never
  restarted. It writes only to a staging folder, never into the paper; keeps the previous code
  version beside the new one; selects variants by environment flags; and returns PDFs, 200 dpi
  PNGs and a report with page sizes in mm, fonts and sizes, a text-extraction check for banned
  words, and a JSON of every printed number. It flags decisions for the lead (a figure taller
  than planned, a tint that makes near-zero differences look strong). The lead reads the PNGs
  and answers with numbered small fixes. In the source such an agent caught that the "p" it was
  told to print was an adjusted q in one figure and an unadjusted p in another.
- **Cluster-side work gets a self-contained hand-off file** with numbered rounds, exact paths,
  and the exact copy commands for only the needed files (cluster-jobs).

## 8. Close-out

1. Adversarial QA, the main-versus-supplement audit and the fact-check (review.md).
2. The four documents and the figure log updated, or the sync marked as owed.
3. PNG and PDF in place; the live-text SVG on every edit once a submission set exists; plotted
   values table.
4. A final check the author asked to keep as a file ("add this level of check in an md file as
   gaurdrails for final check for each figure"): `assets/repo/FINAL_CHECK.md`, copied into the
   figure folder. Rerun every script, confirm the outputs reproduce exactly, remove dead code,
   check every text detail against the code, record the date and commit.
5. Report: what changed per panel, what was checked and how, what was not checked, what the
   author must decide.
