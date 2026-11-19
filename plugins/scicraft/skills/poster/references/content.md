# Content: what goes on the poster and where it comes from

## 1. Inventory before layout

1. List the paper's figure PDFs: the submission bundle (`figures/`, `source_assets/`), any figure dossier the
   repository keeps, the appendix figures. Open each one; note its panels and its bold caption claim.
2. List the manuscript's table sources (`m_results.tex` and the like) and the appendix tables.
3. Write a figure map, one line per poster slot:

| Slot | Source | Change | Printed width | Smallest text at print |
|---|---|---|---|---|
| key idea | the paper's concept figure | cropped to one panel | 13.1 cm | measure with layout_check |
| method left | Fig. 1 | trim only | 38.6 cm | |
| method right | Fig. 2 | text outlined (hidden strings) | 38.6 cm | |
| result | the showcase figure | none | 55.5 cm | |
| gallery left, right | two appendix figures | rows a to c kept, everything below removed | 38.6 cm each | |
| results | the manuscript's results table | comparator citations added | 51.3 cm | |

Printed width = design width x 0.841 (45.85 cm design is 38.6 cm printed). The last column comes from
`layout_check.py`: the labels inside a paper figure print at the paper's size times the enlargement, so a figure
made for a 13.97 cm text width and placed 38.6 cm wide is enlarged about 2.8 times.

4. Map each slot to one figure. A slot without a figure gets text or nothing; never a new diagram.

The poster this came from had four bands, and the slots that worked were:

- band 1: the abstract (55.5 cm) beside the key idea, which held the paper's concept figure and its defining
  equations in a box;
- band 2: the two method figures side by side, each with two or three caption sentences and, under the left
  one, the training objective with labeled braces;
- band 3: the main result figure with a text column, then two appendix gallery figures side by side
  (the author's favorite part: "never shrink or cut it");
- band 4: the data inventory (big numbers, then a per-group table) and the evaluation protocol beside the results
  table, its one-sentence takeaway and its key.

## 2. Crops and recolors

- Crop with `\includegraphics[width=..., trim=l b r t, clip]{file}`; trim values are bp of the source PDF. The
  pixels outside the crop and the text layer stay in the file: check the text layer (checks.md, gate 5).
- When a figure is cropped to some rows, keep the row labels and the shared column heads in the crop.
- When reused panels get new numbering, paint out the old panel letters in the source figure; do not cover them
  with a white box in LaTeX (the letters stay in the text layer).
- Recolor only to match the poster ground. On white, the paper's colors stay.
- Record every change in the provenance block: "text outlined", "rows below c removed (pixel-identical above)",
  "fonts embedded with embed_base14.py", "two hidden strings removed, render identical".

## 3. Own words

The rule: a poster sentence is a sentence of the paper with words cut out, in the paper's order. The check
(`own_words_poster.py`) passes a sentence when its words occur, in order, as at most four uninterrupted pieces of
one paragraph of the paper's source. That allows cutting a clause or two; it fails a paraphrase, a merge of two
sentences or an added connective.

Procedure:

1. Copy the abstract into the abstract node. Cut whole sentences first (those that restate the setting), then
   clauses. Keep: the question, what the method is, what it makes possible, the one result.
2. For each figure, take its caption: the bold claim becomes the bold lead, one or two of the following
   sentences stay.
3. For each section, take one or two sentences from the paper's text that carry its message, often the first
   sentence of a results paragraph.
4. Bold a key phrase inside a sentence; give the accent to four or five phrases of the abstract only.
5. Build and run:

```bash
python3 -I tools/own_words_poster.py build/poster_design.pdf ../paper/tex \
  --boxes build/poster_design.log --figure-boxes logo,sph,defs,f1,f2,fa,g1,g2,n6,t6,t9 --allow departures.txt
```

On the poster this came from, the check found 21 of 30 checked sentences in the paper as one to three pieces.
The 9 it did not find were exactly the departures the provenance block recorded: the byline and affiliations,
three sentences with acronyms spelled out, the plain-language table key and the release line. Put such lines in
`departures.txt` so the run is clean and the list is visible.

Examples of cuts that pass and edits that fail (invented text, one paper's style):

| The paper | On the poster | Passes |
|---|---|---|
| "We introduce a sparse mixture of adapters that routes each token to two experts, which reduces memory by a factor of four." | "We introduce a sparse mixture of adapters that routes each token to two experts." | yes, one piece |
| same | "Our sparse adapters cut memory fourfold." | no, rewritten |
| "Existing methods fix the granularity in advance. Yet no single granularity suits every task." | "Existing methods fix the granularity in advance, yet no single granularity suits every task." | yes (punctuation only) |
| same | "Because existing methods fix the granularity in advance, they fail on some tasks." | no, connective added |

## 4. Numbers and claims

- Every number on the poster is the paper's number, traced to its table or record. Big numbers are totals of the
  paper's per-item inventory, summed from the per-item rows, never copied from a summary sentence, which can count
  items twice.
- One rounding per number across the poster, the paper and any talk made from it.
- Write the unit word, not a power of ten ("Billion", or "B" with a note in the source that B is billion).
- Every sentence about data says which stage it covers: pretraining, fitting the probe, evaluation. "Trained on
  public data only" is false when the probes or the evaluation used other data.
- A caption that claims a visible agreement ("the structure is shared across samples") rests on a number the
  paper reports against a chance baseline, or it is made neutral.
- A planned feature is never written as existing; the release line says "coming soon" until it is public.
- Results of the paper's own tables appear complete. The template's table wrapper prints the manuscript's table
  as it is; do not delete rows or columns to save space, shrink the strip or cut text elsewhere.

## 5. What leaves, and why

- The model recipe: hyperparameters, exact loss weights, curriculum ("keep the secret sauce"). The poster shows
  the objective's terms by name with labeled braces, not their weights.
- Related work and most of the method text: the figures carry the method.
- Formula derivations: the poster keeps the defining equations of the key idea and the objective, typeset as in
  the paper.
- Anything the author has not made public (other projects' results, data under embargo).

## 6. Corpus beyond the paper

When the poster must say something the paper does not (a release line, a contact, a data credit), it is a
departure: write it plainly, put it in `departures.txt` and in the provenance block, and show the author the
list. Lines the author dictated in the conversation are kept as given and listed the same way.
