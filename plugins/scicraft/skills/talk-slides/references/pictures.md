# Pictures

A picture on a slide is evidence. The test for each one is the author's question: "what is the point of what you
are showing?" If a stranger to the data cannot see the title's claim in the picture, the picture is decoration,
however good it looks. Colored fields alone read as decoration to an audience that does not know what the colors
are.

## Contents
1. The patterns
2. Keys: color, scale, size of the data
3. Zooms and insets
4. Choosing what to show
5. Resolution
6. Reusing the author's figures
7. People and logos
8. Drawing your own panels
9. When there are no figures yet

## 1. The patterns

**The whole sample with its size.** The first picture of the data: the entire sample, full bleed, at the level the
audience knows (cells colored by the expert's types). A box on a ground-colored plate inside the picture gives the
size: units, measurements, features, and the scale bar (for a tissue section: cells, transcripts, genes and a 2 mm bar; for a benchmark: tasks, rows, columns, sources).
It shows the scale of the problem before a word is said. In the PDF, add zoom-in panels down to the finest unit.

**The zoom through scales.** One camera move from the whole sample to single measurements, with the name of the
current scale lit in a small ladder (tissue section, tissue region, niches, cells, transcripts) and a scale bar
that changes. In the PDF: the stages as a row of stills with the names above them.

**Expert's view against the method's view.** The same field of view twice, split by a vertical divider: the
annotation the audience trusts on one side, the method's output on the other. In the deck the divider moves; in the
PDF it stands in the middle. Label both sides. Choose a field of view where structures cross the divider, so the
eye follows a structure from one reading into the other. This pattern beats two panels side by side, because the
audience compares one place with itself.

**Any unit, same data.** The same small window drawn as the finest measurements, then as cells, then as bins of a
fixed size. It makes "the unit is chosen later" visible without a formula.

**One space for everything.** A picture of the embedding space (a sphere) that carries more than one kind of object:
single measurements as small points, cells as ringed points, a region as a marked point, with a key. Points with
the same color must fall together, otherwise the picture argues against the claim: choose display axes that
separate the annotated types and say in the notes that the picture shows three chosen directions of a larger space.
The author's note on such a picture: "make the points with similar color fall close to each other ... that's the
whole point". Fit the directions to separate the labels (a linear discriminant on the window), then check on
held-out points that the separation is not fitted noise, and draw the points larger and outlined.
`display_axes.py EMB.npy LABELS.npy OUT.npy` fits the discriminant with shrinkage, writes the points on the unit
sphere, and prints two held-out checks beside their chance level: the share of points nearest the center of their
own kind (against the share of the largest kind) and the share of each point's ten nearest neighbors with its label
(against shuffled labels). Use the axes only when both margins are clear; put both numbers and both baselines in
the notes and in `SOURCES.md` (`story.md` section 4).

**Search and its matches.** For a claim that the method finds similar things: (a) the whole sample with the
similarity as a glow, the selection ringed and the best matches boxed and numbered; (b) a zoom-in of the selection
in the expert's colors; (c) zoom-ins of two matches found elsewhere, at the same magnification. The audience sees a
vessel selected and two other vessels found. A similarity map alone only shows that something lights up. Pick the
matches by score, at a set distance from the selection and from each other, and say so in the notes. Name the
selections with words the audience uses.

**Other samples.** Three samples side by side in exactly the same grammar (same split, same labels), each with its
size in a box. Sameness of grammar is what says "it is the same method".

**The comparison.** Ranks per task with the method on top: lines that are switched on one method at a time (deck),
or a heat map of ranks with the mean rank and the rating as the last columns (PDF). The one number goes in the line
under the title. Group the other methods by what they are, so the audience reads kinds, not thirty names.

**How it works.** The paper's own figure or the website's own animation (see section 6). Every component and label
must be readable from the last row: thicken faint arrows and lift pale labels rather than redraw.

**What exists.** For the future slide: thumbnails of the data that exist and are not used yet, in one row, as
evidence of an asset, with the people who generated them beneath.

## 2. Keys

- **Color.** "If you use a color, explain what it is." Every slide that shows categorical colors carries the legend
  (a dot and a name, the ten most frequent categories, names as the annotation has them). Every continuous color
  has a word for what it encodes ("cosine similarity", "attention weight"). Use one palette for the same
  categories on every slide. A legend may be quiet (28 px, two columns under the text) but it is there.
- **Scale.** Every picture of the sample has a scale bar with its length. White type over tissue is unreadable, so
  the bar and its number sit on a plate in the ground color, inside the picture, top right. In a zoom the bar
  changes with the view.
- **Size of the data.** Where a sample first appears, its size stands in the picture. Use the sample's real totals.
- **A label that describes the rendering** ("1 in N points drawn", "every tenth row shown") is measured on the
  frame where it stands. Sampling is rarely uniform: one such label was true on average and false in the densest
  view.
- **What a marker means.** A ring is a selection, a numbered box is a match: keep one meaning per mark through the
  deck, and print the numbers in the zoom-ins too.

## 3. Zooms and insets

- Show the whole and the zoom-in together where the claim is about both ("show the whole thing, but do zoom-ins").
- A zoom-in never covers the place it zooms from, or another panel. Put insets in corners with the least content,
  or beside the main picture. The audit reports pictures that overlap unless they are named `overlay`, and it
  cannot tell whether an intended inset hides something: look.
- At the finest level, draw the units (cells) as thin light outlines over the measurements. Filled translucent
  shapes were called ugly and hide what is inside them.
- When the view is closer than the data's coarse rendering allows, switch to the finer rendering (cell polygons,
  single points). Blocks of a coarse grid at high magnification read as "pixelized".
- At least one zoom-in on an early slide reaches the level the audience works at (single cells), so they recognize
  their own data.

## 4. Choosing what to show

- Choose examples the audience can name. Prefer two different fields of view over two magnifications of one.
- If you chose an example by eye among many, write that in the notes. If a script chose it, write the rule.
- What worked: score every candidate (for example by how much of the picture's variation the labels explain), put
  the top six on contact sheets, pick by eye, and write "chosen by eye among N" in the notes, with N. For a query, pick the
  matches by score at a set distance from the query and from each other.
- Show continuity: the same structure in both readings, the same sample in whole and in zoom.
- One picture per point. Three small panels were replaced by two large ones, and then by one with zoom-ins.
- Never show the internal variant the author does not want named, in picture or label.

## 5. Resolution

- No picture is shown larger than its pixels. `deck.py` warns at build; `audit_deck.py` fails on it.
- The PDF twin is rendered at 3840 px per page: give stills two pixels per slide pixel (a still shown 956 px wide
  needs 1912 px). Render panels at their final size; do not rescale a small export.
- Large opaque stills are embedded as JPEG at quality 92 with full chroma (colored points stay crisp); logos,
  formulas and pictures with transparency stay PNG.
- Text inside a rendered panel is drawn at the size it will have on the slide: at least 28 slide px. For a panel
  shown at half its pixel size, that is 56 px in the panel.
- Website canvases and gallery tiles often cap their own resolution; check the pixel size you actually got.

## 6. Reusing the author's figures

Paper figures go on slides as they are: the author recognizes them and stands behind them. Redrawn charts and
diagrams were rejected as low quality.

- Render the figure's PDF to PNG at high resolution (`pdftoppm -png -r 600 fig.pdf out`, or PyMuPDF) and crop to
  the panel that carries the claim.
- On a dark deck never place it on a white plate. `dark_figure.py` inverts lightness and keeps hue, so each box
  keeps its color and white becomes the ground. Check afterwards that pale fills and thin labels are still visible.
- An animation the author already likes (from the website, from an earlier deck) is recorded and reused; change its
  labels or colors to match the deck, not its drawing. Ask which version of the method it shows: the submitted
  model and the evaluated one can differ, and the difference goes in the notes.
- Formulas for an in-field talk are rendered from the paper's TeX, never retyped (`audience.md` section 2).
- Numbers on slides are native text in the deck's type, not a screenshot of a table.

## 7. People and logos

- Real photographs, cut round (`Deck.portrait`). Look on the institute's people page, the lab page, a public
  profile; otherwise ask the author for the photo. Check that the photo is the right person (name beside it on the
  source page). Never an initials disc, never an empty ring, and never another face beside a real name: a wrong
  face is the worst of the three. While a photo is missing, `s.people` takes `None` for it and sets the name and
  role as text alone; say in the report that the photo is needed.
- People appear where their work is shown: those who generated the data on the slide about the data.
- Logos: only those the author asks for; the host's in the band. Place lab logos with the lab's name.
- **Licenses.** A picture or dataset from outside the project is used only when its record shows a license that
  allows it (CC BY 4.0 on a data record, a CC license and a named author on a media commons page). Record page,
  author and license in `SOURCES.md`, and portraits with the page and image address. When a site refuses scripted
  downloads, an honest, descriptive client name (what the download is for) worked where a generic one was refused;
  never disguise the client as a browser.

## 8. Drawing your own panels

When a picture has to be rendered from data:

- Dark ground in the deck's color; no axes, ticks or titles unless the audience needs them; labels in the deck's
  typeface (`Deck.type.font(size, weight)` gives the PIL font).
- Draw translucent fills on their own layer and composite: drawing on an RGBA layer with PIL overwrites alpha.
- A panel of points colored by thousands of categories is noise: draw all points as quiet density and the few
  that matter in color.
- Keep the render script beside the builder and name the still after the slide. Re-render rather than retouch.
- For charts (bars, heat maps, lines) follow the `data-figures` skill, then match ground and type.

## 9. When there are no figures yet

A talk is often needed before the paper has figures. The rule against redrawing the author's figures does not
forbid drawing: it forbids replacing theirs. With nothing to reuse:

- **Draw from the paper's numbers, plainly.** One mark per patient or sample, filled where the event happened (97
  and 315 circles say more to a ward than a sensitivity); a timeline with the events at their measured times; two
  rows that compare how often something is measured. These are the audience's own kinds of picture.
- **To scale, or said not to be.** Where the paper gives numbers, positions are computed from them. Where it gives
  only an order ("before", "a few times a day"), the picture has no axis values, and the notes and `SOURCES.md` say
  that it shows an order. Never invent a value to make a panel look measured.
- **The same window in every generation of the technology**: one fixed field shown as each earlier measurement
  method saw it, each panel with its count, all from real public data with checked licenses. When the densest panel
  reads as noise, draw everything in a quiet gray and only the few marked features in color.
- **A photograph of the real thing** (the device on a patient, the sample, the instrument) is the strongest picture
  such a talk can have. Ask for it by name in the report.
- **No picture is better than a decorative one.** A point without an honest picture is a statement slide.
- Stand-ins that remain in a delivered file are marked REPLACE and listed in the report under "not done".
- Markers need a key like colors do: `s.legend` takes `'ring'` as a third item for an outlined mark.
- Keep the render script (`build/render_panels.py`) so that the panels can be redrawn when the numbers change.
