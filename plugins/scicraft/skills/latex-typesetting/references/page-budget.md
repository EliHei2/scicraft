# Page budgets, widows and orphan lines

Read this when a document is over a page limit, a page count target, or when lines and headings
strand.

## 1. Measure first

**A page limit is fitted by measurement, never by trial.**

- Put `\label{mainend}` after the last main-text sentence; the gate reports its page
  (`latex_gate.py --max-main-page 9`).
- Where on the page the text ends: `python3 scripts/locate_text.py main.pdf "last words of the conclusion."`
  prints page, x, yMin and yMax in pt from the top. In the original project the gate was "page 10
  with yMax < 730" on US letter, and the main text ended "on line 535 of page 10 (four lines spare)".
- How full each page is: `locate_text.py main.pdf --fill`. Keep text pages at least 80 % full.
  A page that ends at 40 % is a stranded float page or a near-empty chapter end.
- Density to convert words into pages: a single-column venue text page held about 14 words per 11 pt line,
  59 lines, about 820 words; a book page about 500 words. Use these only to plan cuts, then
  measure again.
- Keep a page-arithmetic table per edit: words before and after, lines or pt gained or lost.
  Compaction targets come from the `.toc`: pages per chapter now, word target per chapter.

### The proxy for a revision under a hard limit

When the full document cannot be rebuilt the way the venue will (different fonts, an unmodified
source that cannot take shims), predict where the main text ends with a proxy:

1. Rebuild the sections that will change from the submitted PDF's text, with the venue style,
   microtype, the same run-in heads, and placeholder boxes of the measured float heights.
   Calibrate until paragraph y positions match the submitted PDF (0.1 to 1.5 pt was achieved).
2. Compile a delta file that measures how much the earlier pages grow (lines plus pt).
3. Set the revised sections after that growth, injecting the offsets on the command line
   (`pdflatex "\newcommand{\EXTRALINES}{3}\newcommand{\EXTRAPT}{4.5pt}\input{proxy_rev}"`).
4. `pdftotext -bbox` both proxies and locate the last sentence (`locate_text.py`).

## 2. Moves, in order of losslessness

Take the moves from the top. Each later move costs more of the author's text.

| Order | Move | Detail and number |
|---|---|---|
| 1 | Remove layout waste | A `\FloatBarrier` that strands figures on 43 to 62 %-full float pages; a `\clearpage` before the appendix that leaves a half-empty page; a chapter whose last page carries one paragraph (trim a few lines there); a list of algorithms that can sit on the verso. One book went from 249 to 240 pages this way plus step 4. |
| 2 | Tighten main-text displays only | `\tightenmaindisplays`: above and below `3pt plus1pt minus2pt`, short skips `1pt plus1pt minus1pt`; `\restoremaindisplays` before the appendix. |
| 3 | Float geometry | Small figures as `wrapfigure{r}{0.43\linewidth}` to `{0.46\linewidth}` beside their paragraph, with `\vspace{-1.0\baselineskip}` above and below; the wrapped paragraph must be at least as tall as figure plus caption, or the indent leaks into the next heading. Side or wrapped captions stay at three lines. `\vspace{-4mm}` after a first figure. Fractions in `preambles.md`, section 10. |
| 4 | Run-in heads | `\rwpara{Bold run-in.}` in place of `\paragraph` saves the head's vertical space. |
| 5 | Your own additions | Caption text you wrote, pointer sentences you added, then float spacing, then figure scale. Free space from your additions before anything the author wrote. |
| 6 | Near-verbatim redundancy | The same fact said twice: keep it in the section that owns it and cross-reference elsewhere. Rank candidate cuts by space saved and test them on a copy. One redundancy pass removed 2,604 words from a book. |
| 7 | Method detail beyond what a reader needs to assess a result | Move it to the appendix or supplement with a pointer. |
| 8 | Over-long background and discussion | Shorten. |
| 9 | Vague sentences | Delete them; do not rephrase them. |

Never, at any step:

- change the venue's geometry, font size or its own spacing commands;
- shrink figure text below 4 pt at print size; spend margin with `\widefig` (overhang to the
  right, because the left margin carries the submission line numbers) before scaling a figure
  down;
- cut a main-text result with its number, controls and limits to fit. A result that must leave
  the main text moves to the appendix with its number and a pointer, never out of the record;
- rewrite the author's text to save space. Cut it, with their consent, or ask.

A figure redesign must keep its on-page height. After every move: rebuild, gate, render the
changed pages. A layout fix is accepted only after the page count and the pictures agree.

## 3. Widows, orphans and stranded lines

**No line, label or heading strands: no one-word last line, no heading at a page foot, no running
head that wraps.**

- In every preamble:

```latex
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000
\preto\section{\needspace{9\baselineskip}}       % etoolbox; needspace or the shim
\preto\subsection{\needspace{6\baselineskip}}
```

- One-word last lines of paragraphs, captions, titles and author blocks:
  `python3 scripts/locate_text.py main.pdf --runts` lists them. Fix with a tie between the last
  two words (`the~second~best.`), an `\mbox{}` around them, or a small rewording the author
  approves. A bold caption title broken with one word on its own line gets `\mbox{}` on its last
  word.
- Running heads: `\runninghead{Short}` (profile B) or `\section[Short]{Long title}`; a heading in
  the form "Role: subject" runs as its role alone.
- Contents: short entries with `\section[short]{long}`, so no entry wraps with a stranded word.
- Titles: no title broken "with a short middle line"; set line breaks by hand when needed.
- Width-driven wraps elsewhere (an affiliation line that breaks for one name): adjust the width
  or the spacing so it fits. The author's words: "affiliations for no reasons go to second line
  only for one name. adjust such things".
- Posters and other fully justified narrow text: `\hyphenpenalty=1000 \exhyphenpenalty=1000`
  (5000 left loose lines and one-word last lines); no hyphenated bold titles.
- After the layout settles, run `--runts` and look at the last line of every caption on the
  rendered pages.
