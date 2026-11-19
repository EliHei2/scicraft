# The page, part by part

Each part below says what it holds, what it must not hold, and which classes of the starter carry it. The starter's
`index.html` has every part in this order with placeholders in square brackets. The behavior-check template counts
the placeholders that are left, so none ships by accident.

## Contents
1. The bar
2. First screen (and the comparison view)
3. Opening
4. A second interaction
5. How it works
6. The data block
7. Results
8. Rows that open
9. Supporting evidence
10. Gallery (and honest gallery images)
11. Release
12. Close and footer
13. What is not on the page
14. A personal or lab homepage

## 1. The bar (`.top`)

A thin fixed bar: the mark (and, once the title has scrolled away, the name), links to the sections, one button on
the right, and a hairline that shows how far down the page is. The link of the section on screen is lit.

- Links are the section names, in page order. On phones the links hide and the button stays.
- The button is the one action a visitor may want ("Cite", later "Paper" or "Code"). It may lead to a line that says
  "coming soon"; it must not pretend something exists.
- At the top of the page the bar's left side is empty: the mark is large beside the name (below).

## 2. First screen (`.hero`, `.mast`, `.stage`)

The name, the rest of the title, the authors, and the one interaction, all in the first screen on a laptop.

- **The mark** (`#mark` in the bar, `.mast-mark` as its slot): one image. `page.js` draws it in the slot at the top
  and interpolates it to its place in the bar while the page scrolls the first hundred pixels or so. Give the slot
  the mark's aspect ratio. Ship the mark at four times its bar size so it is sharp when large.
- **The name** is the short name of the method or dataset, set very large (54 to 104 px). The rest of the title is
  the subtitle.
- **Nothing over the name.** Two different taglines were tried and both were thrown out ("it's cringe and vague";
  "this should not be at the top of the page").
- **Authors** with superscripts, and their institutes as small marks or short names. Roles and full affiliations can
  sit in a card under the pointer. Mark joint supervision once. **Each name and its superscript are one group**
  (`<span class="au">` with `white-space: nowrap`): a superscript that wrapped to the next line alone was called out
  ("affiliations for no reasons go to second line only for one name"). `audit.js` reports a broken group.
- **Institute marks.** Search the machine first (`find ~/Desktop ~/Downloads -iname "*logo*"`). For a missing
  institute, fetch the official SVG from its own site or Wikimedia Commons into an empty scratch folder, rasterize
  it with the headless browser, turn it into a white mark on a clear ground, compose all marks in one row on the page
  ground and look at the row before using it. Ship each at four times its display size.

### The interaction

It fills the rest of the first screen. It needs: a real `<input type="range">` or equivalent so the keyboard works,
labels in opposite corners so they never meet on a narrow screen, a quiet invitation that goes away on first touch,
and a way back to the starting view. If it flies by itself, any deliberate touch stops it, and a page scroll that
merely passes under a resting pointer does not.

### The comparison view: like with like

The lead case for a model paper is a divider between a reference (human labels, the input, a baseline) and the
model's output on the same sample: segmentation masks against predictions, annotated rows against embeddings
colored by cluster. Rules that came out of building one:

- **The reference keeps its own native unit.** Expert annotations of objects stay objects; per-item labels stay per
  item. The reference is never rendered coarser than it is to match the model.
- **The model's side carries the scale chooser** (automatic, each coarser grid, the native unit, raw points). Both
  sides switch their level of detail on one shared zoom schedule.
- **When a coarser view of the reference is drawn** (for example at the lowest zoom), it uses the model's grid
  pitch, footprint and fade, and the pointer names the dominant label of the cell under it.
- **Both sides have the same width and show the same window.** The first request was parity (both sides must
  show the same unit); a day later the author fixed the left
  side to the reference's native unit and put the chooser on the right. The later rule is the one above.
- **Overlays contrast with the ground.** At the finest zoom, fills go and thin white outlines appear on both sides
  ("black on black is not visible"). Categorical color is fine as long as the legend says what each color is
  ("point is that you know what it is").
- A coarse model output set beside a fine reference without saying so is a misleading comparison. If a coarser view
  is the only one possible, the note under the view says so.

Under the view, one or two quiet sentences (`.viewer-note`) say what is shown and carry the paper's caveat, if it
has one (for example that the annotations are an external reference).

**A sample chooser in the first screen offers only samples that have full-resolution data.** A sample without it
belongs in the gallery ("if we don't have in high resolution then in the gallery is fine").

## 3. Opening (`#idea`, `.why`, `.mainclaim`)

At most three short statements of the problem, in gray, and the paper's main claim, one sentence, in white. About 40 words.

- The statements are the author's own (from a talk or a post) or the paper's sharpest sentences. One line each.
  No elaboration under them: if a statement needs a sentence of support, it is not sharp enough.
- The main claim is one sentence of the paper. With the statements above it, a "therefore" in it has its antecedent.
- No abstract, not even folded. No paragraphs.

## 4. A second interaction

Only if the paper has a second thing worth touching (for example querying any region or any row in the browser).
Its section has a head, the interaction, and one note of two sentences at most that says what happens and what it
is computed on. State sizes exactly ("a disc of 50 µm radius", not "a 50 µm disc" for something 100 µm across).

## 5. How it works (`#method`)

Before the results ("first put how it works then evaluation results ... it's sexier"). The head's mono line names
what the figures cover in a few words.

- Go straight from the head to the first figure. No introductory paragraph, no row of cards about the fields the
  work draws on.
- Each figure has a short title, a canvas, and step captions that are the paper's sentences, one or two per step.
  Remove a step that only restates another.
- Figures run on real data from the showcase sample where they can, and are schematic only where the paper's is.
- **A drawing claims no more than the paper.** An encoder figure once drew four levels where the paper's table says
  three. For every figure, list what it asserts and find the sentence or table of the paper that backs it.
- Labels with mathematics are typeset by TeX and drawn as glyph outlines (`patterns.md` section 13).
- Schematic boxes or spheres sit on a light plate with dark ink; real data stays on the dark ground ("make the box
  ... and the sphere white").

## 6. The data block (`.block`, `.stats.five`)

The last layer of "How it works": what the model was trained on or built from.

- One plain statement as its heading (for example "Trained on four public benchmarks.").
- Three to five numbers from the paper, each with a one- or two-word label. They count up once in view.
- One sentence the author wants said about this version (for example that it is the first checkpoint and more will
  come). The author's words, not a slogan of yours.
- No results here. On phones the first number takes a row of its own and the rest pair up.

## 7. Results (`#results`)

- The head, one sentence from the paper on what was evaluated, then **two numbers** (`.stats.two`): the headline
  result in the largest type on the page after the name, each with a label that says exactly what it counts
  ("on 4 of 5 tasks", "rating, against 1025 for the next method").
- **A headline number names the model variant it belongs to.** When the paper reports two readouts or two sizes, a
  "1st" that belongs to one of them says so; a reviewer once read such a row as a best of two.
- **One figure for the main claim**, open. Its heading can be read aloud only (`.sr`) when the two numbers already
  say it. Under it: one or two sentences from the paper, including the paper's sentence on significance, and a small
  "How to read the chart" that holds the paper's caption.
- A second open figure only if it shows something different in kind (for example ranks per task as a heat map).
- Then rows (below): the full table, how the benchmark is run.
- Task and metric names carry `data-term`; the builder supplies one line per task from the paper and its score.

## 8. Rows that open (`.folds`, `details.fold`)

```html
<div class="folds">
  <details class="fold" id="table"><summary><h3 class="claim">The full table</h3><i aria-hidden="true"></i></summary>
    <figure class="result"> ... </figure>
  </details>
</div>
```

- The line is the claim as the paper states it, or a plain name for reference material. It ends in a plus that
  turns into a minus.
- Give every row an `id`: links can then point into it, and the page opens it for them.
- Small charts get `.result.side`: the chart on the left, its sentences on the right.
- Never nest rows. Never open one by default.

## 9. Supporting evidence (`#evidence`)

A head, one sentence from the paper, and rows: ablations, other backbones, amount of data, whatever the paper has.
Controls and robustness studies stay in the paper and come onto the page only if the author asks, and then as rows.
A result that weakens a claim on the page is never dropped while the claim stays: the claim changes.

## 10. Gallery (`#gallery`, `.wall`, `dialog.inspector`)

- A wall of equal square tiles with no labels. A tile shows the model's output and, under the pointer, the
  reference. Fix the number of columns so the last row never holds one tile.
- A click opens a dialog over the page: the divider on the left, and on the right the sample's name, one line that
  describes it with numbers that are really its own, the layer choices if there are any, small extra views, a legend
  that names **every** color in the picture (also the gray of "other"), and "previous" and "next". Escape and a
  click outside close it; the page behind does not scroll.
- Sets that are different in kind or lower in quality (whole samples beside crops, data from another source) go
  last, in their own row, with a short mono caption that names the source.
- Notes in the dialog say how a picture was made when that differs from the rest (for example that it is encoded from
  a sample of the data), in one sentence.

### Honest gallery images

- **Every image comes from the model the paper reports, run on data it was not trained on.** A render from an older
  model trained on the very sample it shows stayed off the page: it "can't go in honestly". Among honest renders of
  the reported model, take the most vivid ("take the best figures we had so far, old or new").
- **Write each tile's provenance into the builder log** before it ships: checkpoint, training set, and whether the
  sample was in training. A tile without that line does not ship.
- **When an ask cannot be met honestly, name the input that would make it possible** ("one export of per-sample
  embeddings from the paper's checkpoint") instead of shipping a substitute.
- **An item ships only with its matching reference layer.** An item without one waits on disk on a hold list that
  the deploy step reads (`gate.py --skip data/gallery/<prefix>`); it is not deleted. Show the subset that has both
  layers ("show just the complete ones for now").
- **Labels from someone else's automatic annotation are attributed as such** in the legend or the note ("the
  vendor's automated labels"), above all when they look wrong for the sample (a label from the wrong organ was
  the case). Offer to hide such entries; do not rename them.

## 11. Release (`#release`)

- The head's mono line is the status ("coming soon", later the version).
- A list of what exists or is coming, one line each: Code, Weights, a hosted demo, Cite. Each says what it is, where
  it will live and its status.
- The planned interface as five lines of code, if the author has settled on it.
- Rows: the model card (input, output, size, speed, training data, license) and the paper's limitations paragraph,
  verbatim.
- For a model or dataset release (weights, model card, leaderboard) read `ml-release.md`.

## 12. Close and footer

The paper's last sentence set large, one link back to the top (it can restart the showcase), then the footer with
marks only: the project's and the institutes' or funders' (30 px high, opacity .85). No list of affiliations, no
footnotes.

## 13. What is not on the page

- An abstract, a "TL;DR", a "key contributions" list, a news box, testimonials, emoji.
- Anything the paper does not say. A page sentence that is not in the paper needs the author's own words behind it,
  and it is declared in the round's report (SKILL.md section 10).
- Results the paper keeps out of its main text, weak statistics, intervals, test statistics. They stay in the paper.
- Raw sample names, internal paths, the names of unpublished collaborators or cohorts.
- A second copy of anything.

## 14. A personal or lab homepage

The same minimal grammar carries a researcher's or a lab's own site: one rich page that scrolls, typography as the
signature, nothing machine-made. What differs, from the author's homepage:

- The voice is first person, specific and dry; concrete numbers and names stand where adjectives would.
- **Type: Source Serif 4 for text (fallback Georgia) and Inter for labels and interface text only**, italic for the
  titles of venues and books, old-style figures for dates. This is the default, from the author's notes on their own
  site; a display serif for the name is a personal brand choice to make with the owner, never a default. The owner's
  titles of papers stay as written.
- One background motif that echoes the research (an animated graph or manifold), and only one.
- Never slogans, labels in capitals, fake terminal prompts or `[DATASET_SHARD]`-style flourishes, or the "not X but
  Y" cadence.

What the author asked for over about ten rounds on their own homepage, and what they threw out:

- **Stance first, then the work.** The first screen says what the owner works on and why, in general terms, and only
  the most important results; detail comes lower. A first draft that opened on tools and papers was redone as
  "more about [the field] and my philosophy and background ... more general".
- **Tell the work in the order of its scale**, from the smallest unit up (in the original, from molecules to
  tissues; in machine learning, from a layer to a model to a system), so each project builds on the last.
- **Scale claims in digits** ("3 million images", never "three million images"), with the unit.
- **Skills grouped by area**, a few words each (machine learning, data engineering, software, spoken languages). A
  list of tool flags and acronyms ("FSDP torch.compile bf16") was thrown out as jargon, and so was an internal
  method name in a heading; write the plain name of the idea.
- **No competitor results.** A line saying the work outperformed two named methods was dropped; the page says what
  the work does.
- **The e-mail address obfuscated** (`name [at] host`), not a `mailto:` link.
- **Every link opens a real page of the owner's.** Click each one before the page ships; a link to a placeholder or
  to someone else's profile is a bug.
- **One image per paper, taken from its Figure 1**, at one size, and every logo at one height.
- Personal warmth stays small: one signature element at most (in the original, a draggable elastic graph with its
  name and a short quote).
