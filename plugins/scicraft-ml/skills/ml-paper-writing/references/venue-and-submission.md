# Venue style, page limit and anonymity

Contents: the venue style is never touched; the house add-on; macros; submission, camera-ready and preprint;
fitting the page limit; anonymity hygiene; the referee self-review; the build.

## The venue style is never touched

Fetch the official style from the venue's author guide for the current year ("fetch the style properly!!").
The style file owns the page geometry, type sizes, fonts, section heads, title block, abstract, running head
and bibliography style. Never edit it, never load `geometry`, never change the font size, never use a
`\...geometryfalse` switch: the author's own pre-submission verdict file called such changes reject-level.

The exemplar ICLR paper the author measured uses the stock style: "every 'distinctive modern' thing on the
page comes from four tcolorbox environments the authors defined by hand". That is the whole room there is.

## The house add-on

Load the venue package first (with `times` when the venue loads it so), then `\input{ml_addon}`. The add-on
(`assets/ml_addon.tex`) adds only:

- one accent color for links, citations and callout rules (`26735B` muted green in the add-on;
  any one dark hue works), everything else ink;
- two callouts with a pale fill and a 1.8 pt left rule: the contributions block and the terminology box;
- table helpers: `\grp`, `\best`, `\second`, `\pmsd`, `\na`, rank fills, ablation colors, a ragged column;
- `\rwpara` run-in heads, `\tightenmaindisplays`/`\restoremaindisplays`, `\widefig`;
- cleveref, so "Table 1" comes from `\cref{tab:main}` and never drifts from its float.

It is written in core LaTeX with xcolor, without tcolorbox, because one build machine shipped a tcolorbox
too new for its kernel. Fonts, shims for a minimal TeX install, print variants and the full table generator
are in the `latex-typesetting` skill. If the venue forces Times text with Computer Modern math, keep it and
make the figures match the paper.

When figure or callout work stalls on looks, copy a named exemplar paper (`exemplars.md`), not a house
skill: one figure stalled for weeks until the author said to copy one exemplar and drop the house skill.

## Macros

Name a macro for every method and model name and every recurring operator; never type them raw. A retired
name then changes in one place.

```latex
\newcommand{\method}{\textsc{Name}}
\DeclareMathOperator*{\argmax}{arg\,max}
\newcommand{\sg}{\operatorname{sg}}            % stop-gradient
\providecommand{\Lpred}{\ensuremath{\mathcal L_{\rm pred}}}
```

Write `\method{}` before a following word, or the space is swallowed (one book shipped "10 µmof" five
times through a unit macro).

## Submission, camera-ready and preprint

| Version | Style | Authors | Links | Extras |
|---|---|---|---|---|
| submission | venue style, anonymous switch | "Anonymous authors" | accent color allowed | no acknowledgements |
| camera-ready | venue style, final switch | real | black if the venue asks (`\hypersetup{allcolors=black}`) | acknowledgements, code link |
| preprint (arXiv) | free | real | accent | the `latex-typesetting` preprint preamble, Palatino text and math |

The original version of this skill gave one free-form preamble (Palatino and Helvetica headings, indigo
accent) for every ML manuscript. The submitted papers kept the venue's typography untouched; the free-form
preamble survives only for preprints.

## Fitting the page limit

Measure, then plan. The limit is checked on the venue's own style, at the current year's page count (one
author note: "this year it should be 9 pages"; verify per venue and year).

1. Put `\label{mainend}` after the last sentence that counts toward the limit. Build twice.
2. `python3 scripts/page_budget.py build/main.aux --limit 9 --tex main.tex --pdf build/main.pdf` prints the
   page of the label, words per section and the overrun in words at 820 words per full ICLR-style page
   (about 14 words per line, 59 lines). Measure your venue's density on a full text page of an accepted paper.
3. Plan moves against that number, in this order:
   - move detail readers do not need to follow the argument to the appendix (implementation tricks, secondary
     tables, proofs), with a pointer;
   - cut words by the voice rules, never facts (`preserve_diff.py` on the cut text, then move the facts that
     left);
   - tighten display math in the main text only (`\tightenmaindisplays` after `\maketitle`,
     `\restoremaindisplays` before the appendix: 3pt above and below);
   - set small figures beside their paragraph: `wrapfigure{r}{0.43\linewidth}` to `0.46\linewidth`, with
     `\vspace{-1.0\baselineskip}` above and below, the figure next to its own text;
   - use `\rwpara{...}` run-ins in place of `\paragraph`;
   - let a wide figure overhang into the right margin (`\widefig`), never the left, which carries the line
     numbers, instead of shrinking its labels.
4. Keep a page-arithmetic table per edit (words before and after, lines gained) when many edits compete.
5. Never shrink fonts, margins or figure labels; never `\vspace` hacks inside the venue's title block.

## Anonymity hygiene

For a double-blind venue, before every upload:

- `\author{Anonymous authors\\Paper under double-blind review}`; the final-copy switch off; no `\thanks`.
- No acknowledgements, funding or grant numbers.
- Your own published work cited in the third person ("Smith et al. showed"), never "our previous work".
  Your own unpublished work is never cited as evidence; when it must be mentioned, in words ("under review").
- Code and data links point to an anonymous mirror, not to a personal or lab account. Suggested, not yet
  tested in real work: use the venue's recommended anonymous code-hosting route.
- No project website, talk or model name that a search engine ties to the authors in the submitted text.
- Figures: scan the text layer of every figure PDF; a name painted over in white is still read by pdftotext.
  One figure came within one `\includegraphics` of shipping a retired project name this way.
- PDF metadata (Author, Title, Creator) carries no name.

```bash
python3 scripts/anon_check.py paper/ --pdf build/main.pdf --figures paper/figures --names ~/private/names.txt
```

The names file lives outside the package and the repository: author names, affiliations, lab and project
names, the code name of the model, repository user names. Venues differ on preprints and on code links; read
the current call for papers.

## The referee self-review

Before submission, review the paper as the venue's referee would and write it down
(`assets/self_review_template.md`). The author wrote one for an architecture paper before its first
submission; its verdict that the draft had no numbers yet set the order of the next months of work.

1. **Summary of claims**, numbered, in the paper's own terms. A claim the reviewer cannot restate is unclear.
2. **Strengths** worth keeping through revisions (a falsification protocol stated in advance is one).
3. **Weaknesses as the reviewer will raise them**, each with a priority and one action:
   - P1: would sink the paper on its own (no results for the central claim, a conjecture where a theorem is
     needed, an uncontrolled variable in the main comparison);
   - P2: a reviewer will press on it (an alternative not compared, a design choice not defended, framing
     ahead of the evidence);
   - P3: notation, constants, reproducibility. Write the constant: "O(log n) parameters" becomes the count at
     the largest n reported.
   Where a weakness has several fixes, list them from cheapest to strongest and mark the recommended one.
4. **Novelty table against the three closest papers**: prior work, what it shares with the method, the
   distinction. Reviewers decide novelty from such a table at a glance; the paper itself should carry one.
5. **Venue fit**: the bar at each candidate venue and the minimum realistic path to it.
6. **Suggestions** grouped as must-have before submission, strong to have, nice to have, cut or appendix.
7. **Scores on the venue's own form** (novelty, technical depth, empirical evidence, writing), each with
   one sentence of reason.
8. **The single most valuable action now.**

Fix every P1 before any cosmetic pass. Framing that outruns the measurements costs more with reviewers than
limited experiments do, so trim the claim when the self-review finds that gap.

## The build

`pdflatex; bibtex; pdflatex; pdflatex`, then gate on the log, never on the exit code: an out-of-tree build
once shipped a PDF with every citation as "[?]" and exit 0. Gates: zero `^! ` errors, zero undefined
references or citations, zero overfull boxes, every font embedded (`pdffonts`), the main-text end page, and
the PDF size against the platform limit. The `latex-typesetting` skill has the gate script.
