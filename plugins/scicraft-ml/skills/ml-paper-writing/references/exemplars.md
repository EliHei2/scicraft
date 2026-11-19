# Following a named exemplar

The author's working move when a paper, a figure or a table did not look right was to name one exemplar
and copy it, element by element. Taste stated as adjectives ("clean", "modern") produced weeks of
iteration; a named paper produced convergence.

## Choose the exemplars

- **Voice**: papers in the register of I-JEPA (Assran et al., 2023), GraphSAGE (Hamilton, Ying and
  Leskovec, 2017), Graphormer and the DINO line. "write like a human, look up top LeCun or Bengio or
  Leskovec papers."
- **Detail level and length**: the most-cited papers of the target venue in the last three years on a
  similar problem ("find the top 100 highly cited ICLR papers in last 3 years and adjust the detail level").
  Write down what they report: exact models and versions and where they were fetched, metric definitions,
  training protocol, inference time, GPU type, time and memory.
- **Typesetting**: one to three recent accepted papers at the same venue whose page the author likes. Get
  the arXiv source when possible and quote its preamble ("verified from source, not inferred from the
  rendered PDF"); otherwise measure the PDF.
- **Figures**: a specific figure of a specific paper ("plot like figure 4 of <arXiv id>"), or a panel the
  author made and approved. The `tikz-figures` and `canvas-schematics` skills build them.

Ask the user for their exemplar in the first message. If they have none, propose two from the venue's
recent proceedings and say why each fits.

## Copy, and record what was copied

1. For each element (accent color, callout style, table layout, heading style, caption form, figure
   palette), write down the exemplar's value.
2. Put the record at the top of the house add-on as a comment: element, value, source.
3. Justify every deviation in a comment. The venue style still wins over the exemplar.
4. When an output still looks wrong, compare it to the exemplar side by side before changing anything else.

## Match the density

An ML paper's density and page count follow recent top-venue papers: the main text carries the idea, the
losses and the core operator; heavy math, proofs and implementation details go to the appendix. Compare the
number of equations, figures and tables in the main text against the exemplar before cutting or adding.
