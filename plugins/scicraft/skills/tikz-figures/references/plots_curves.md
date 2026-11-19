# Quantitative plots: curves, bars, scatter, distributions

PGFPlots recipes on the `spare axis` style of `assets/preamble.tex` (left and bottom
spines, ticks outside, frameless legend, the theme's font for text and math). Each snippet
goes between the preamble and `\end{document}`.

**The numbers in these snippets are placeholders.** A real figure reads its values from
the records with `table` (section 1), never from numbers typed into the source; that is
the exact side of the exact-versus-schematic gate (`workflow_qa.md`, section 6). For a
results figure assembled with other matplotlib panels, use the `data-figures` skill.

**Contents**
1. Reading the records: curves and a mean plus or minus std band from a CSV
2. Line curves with a baseline
3. Shaded band from two named paths
4. Log-scale scaling law
5. Grouped bar chart
6. Stacked bar chart
7. Scatter, two classes
8. Histogram
9. Box summary
10. A faceted row with panel letters and one shared legend
11. Styling reminders
12. Serif-look conventions: despined black axis, ordinal wedge, twin bars, violin

---

## 1. Reading the records

A training log with one row per step and columns `step,mean,std` (computed from the runs,
for example 3 seeds) plots directly. The band is mean plus or minus std, computed by
PGFPlots from the same file, so it cannot drift from the line.

```latex
\begin{filecontents*}[overwrite]{curve.csv}
step,mean,std,base
0,0.95,0.10,0.97
1,0.63,0.09,0.80
2,0.48,0.07,0.71
3,0.39,0.05,0.66
4,0.34,0.04,0.63
5,0.31,0.04,0.61
\end{filecontents*}
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={epoch}, ylabel={validation loss}, ymin=0]
  \addplot[name path=hi, draw=none] table[col sep=comma, x=step, y expr=\thisrow{mean}+\thisrow{std}] {curve.csv};
  \addplot[name path=lo, draw=none] table[col sep=comma, x=step, y expr=\thisrow{mean}-\thisrow{std}] {curve.csv};
  \addplot[accent, fill opacity=0.15] fill between[of=hi and lo];
  \addplot[accent] table[col sep=comma, x=step, y=mean] {curve.csv};
  \addplot[slate, dashed] table[col sep=comma, x=step, y=base] {curve.csv};
  \node[note, accent, anchor=west] at (axis cs:5.1,0.31) {ours};
  \node[note, anchor=west] at (axis cs:5.1,0.61) {baseline};
\end{axis}
\end{tikzpicture}
```

`filecontents*` keeps the example self-contained; in a real figure the CSV is written by
the analysis code and only `table {...}` lines appear in the `.tex`. State in the caption
what the band is (std over 3 seeds, or a 95% interval) and how many runs it covers.

## 2. Line curves with a baseline

The method in the accent with small filled marks; the baseline dashed in the contrast; a
reference gray and dotted.

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={labels acquired}, ylabel={accuracy},
             xmin=1, ymin=0.5, ymax=0.9, legend pos=south east]
  \addplot[accent, mark=*, mark size=1.3pt] coordinates {(1,.60)(2,.68)(3,.74)(4,.79)(5,.83)(6,.85)};
  \addplot[contrast, dashed, mark=none, line width=0.9pt] coordinates {(1,.55)(2,.60)(3,.64)(4,.67)(5,.70)(6,.72)};
  \addplot[mist, dotted, mark=none] coordinates {(1,.50)(2,.55)(3,.58)(4,.61)(5,.63)(6,.65)};
  \legend{ours, baseline, random}
\end{axis}
\end{tikzpicture}
```

## 3. Shaded band from two named paths

Name an upper and a lower path and fill between them; draw the band before the line so the
line sits on top. Band opacity 0.12 to 0.18 keeps two overlapping bands readable.

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={epoch}, ylabel={loss}, ymin=0]
  \addplot[name path=hi, draw=none] coordinates {(0,1.05)(1,.72)(2,.55)(3,.44)(4,.38)(5,.35)};
  \addplot[name path=lo, draw=none] coordinates {(0,.85)(1,.54)(2,.41)(3,.34)(4,.30)(5,.27)};
  \addplot[accent, fill opacity=0.15] fill between[of=hi and lo];
  \addplot[accent, line width=1pt] coordinates {(0,.95)(1,.63)(2,.48)(3,.39)(4,.34)(5,.31)};
\end{axis}
\end{tikzpicture}
```

## 4. Log-scale scaling law

A power law is a straight line on log-log axes. A fitted line must come from the fit to
the plotted points, with its exponent stated; on a schematic, draw no fit.

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xmode=log, ymode=log,
             xlabel={parameters $N$}, ylabel={test loss},
             log basis x=10, log basis y=10,
             ytick={0.75,1,1.5,2}, yticklabels={0.75,1,1.5,2}]   % no fractional powers of ten on the axis
  \addplot[accent, mark=*, mark size=1.2pt]
    coordinates {(1e6,2.1)(3e6,1.7)(1e7,1.35)(3e7,1.1)(1e8,0.9)(3e8,0.74)};
  \addplot[contrast, dashed, no marks, line width=0.9pt]
    coordinates {(1e6,2.0)(3e8,0.7)};
  \node[note, anchor=west] at (axis cs:3e6,1.1) {$L \propto N^{-\alpha}$};
\end{axis}
\end{tikzpicture}
```

## 5. Grouped bar chart

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, ybar, bar width=6pt,
             symbolic x coords={tabular, vision, text},
             xtick=data, ymin=0, ylabel={accuracy},
             enlarge x limits=0.25,
             legend style={at={(0.5,1.05)}, anchor=south, legend columns=-1, draw=none, fill=none}]
  \addplot[fill=accent, draw=accent!70!black] coordinates {(tabular,.80)(vision,.83)(text,.78)};
  \addplot[fill=contrast, draw=contrast!70!black] coordinates {(tabular,.72)(vision,.75)(text,.70)};
  \addplot[fill=mist, draw=slate] coordinates {(tabular,.68)(vision,.70)(text,.66)};
  \legend{ours, baseline, random}
\end{axis}
\end{tikzpicture}
```

## 6. Stacked bar chart

Three parts at most; the parts take `c1` to `c3`.

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, ybar stacked, bar width=10pt,
             symbolic x coords={A,B,C,D}, xtick=data, ymin=0, ylabel={fraction}]
  \addplot[fill=c1, draw=none] coordinates {(A,.5)(B,.4)(C,.6)(D,.3)};
  \addplot[fill=c4, draw=none] coordinates {(A,.3)(B,.35)(C,.2)(D,.45)};
  \addplot[fill=c2, draw=none] coordinates {(A,.2)(B,.25)(C,.2)(D,.25)};
\end{axis}
\end{tikzpicture}
```

## 7. Scatter, two classes

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={error on task A}, ylabel={error on task B}, xmin=0, ymin=0]
  \addplot[only marks, mark=*, mark size=1pt, accent, opacity=0.8]
    coordinates {(2,1.5)(3,2.1)(5,3.0)(7,4)(4,2.8)(6,3.6)(8,5)(3.5,2.4)};
  \addplot[only marks, mark=o, mark size=1pt, contrast]
    coordinates {(12,10)(15,12)(9,8)(14,11)(11,9)(16,13)(10,7.5)};
  \legend{ours, baseline}
\end{axis}
\end{tikzpicture}
```

Marks follow density: smaller marks for dense data, no mark sitting on another; for
binned data use bigger marks or a real raster.

## 8. Histogram

Bars pale, an overlaid density line (if any) saturated.

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={error}, ylabel={count}, ymin=0,
             ybar interval, bar width=1pt]
  \addplot[fill=accent!20, draw=accent!40]
    coordinates {(0,2)(2,9)(4,16)(6,12)(8,7)(10,4)(12,2)(14,1)(16,0)};
\end{axis}
\end{tikzpicture}
```

## 9. Box summary

`boxplot` comes with the `statistics` library (loaded in the preamble).

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, ylabel={score}, xtick={1,2,3},
             xticklabels={ours, base, random}, boxplot/draw direction=y]
  \addplot+[boxplot, accent, fill=accent!15] table[row sep=\\,y index=0]
    {0.80\\0.82\\0.79\\0.85\\0.83\\0.81\\};
  \addplot+[boxplot, contrast, fill=contrast!15] table[row sep=\\,y index=0]
    {0.70\\0.73\\0.69\\0.75\\0.72\\0.68\\};
  \addplot+[boxplot, slate, fill=mist!30] table[row sep=\\,y index=0]
    {0.62\\0.66\\0.60\\0.68\\0.64\\0.61\\};
\end{axis}
\end{tikzpicture}
```

## 10. A faceted row with panel letters and one shared legend

More than three series, or the same metric on several tasks, becomes a row of panels
with one shared legend above it and bold lowercase letters at each panel's top left
(stock matplotlib facets ship without letters; journals want them). Matched panels share
one y range so they can be compared by eye.

```latex
\begin{tikzpicture}
\begin{groupplot}[group style={group size=3 by 1, horizontal sep=12mm},
    spare axis, width=4.6cm, height=3.6cm, ymin=0.5, ymax=0.9, xmin=1, xmax=5,
    xlabel={budget}, legend to name=sharedleg, legend columns=-1]
  \nextgroupplot[ylabel={accuracy}]
    \addplot[accent, mark=*, mark size=1.1pt] coordinates {(1,.62)(2,.70)(3,.76)(4,.80)(5,.82)};
    \addplot[contrast, dashed] coordinates {(1,.58)(2,.63)(3,.67)(4,.70)(5,.71)};
    \legend{ours, baseline}
  \nextgroupplot
    \addplot[accent, mark=*, mark size=1.1pt] coordinates {(1,.55)(2,.64)(3,.70)(4,.74)(5,.77)};
    \addplot[contrast, dashed] coordinates {(1,.54)(2,.60)(3,.64)(4,.66)(5,.68)};
  \nextgroupplot
    \addplot[accent, mark=*, mark size=1.1pt] coordinates {(1,.66)(2,.72)(3,.77)(4,.80)(5,.81)};
    \addplot[contrast, dashed] coordinates {(1,.65)(2,.70)(3,.73)(4,.75)(5,.76)};
\end{groupplot}
\node[panel, anchor=south east] at ($(group c1r1.north west)+(-0.1,0.1)$) {a};
\node[panel, anchor=south east] at ($(group c2r1.north west)+(-0.1,0.1)$) {b};
\node[panel, anchor=south east] at ($(group c3r1.north west)+(-0.1,0.1)$) {c};
\node[anchor=south] at ($(group c2r1.north)+(0,0.35)$) {\pgfplotslegendfromname{sharedleg}};
\end{tikzpicture}
```

## 11. Styling reminders

- `spare axis` already removes the box and puts ticks outside; never re-add
  `axis lines=box`.
- A faint horizontal grid only if it aids reading: `ymajorgrids, grid style={mist!50,
  line width=0.3pt}`.
- Marks of 1 to 1.3 pt; a filled mark for the focal series, `mark=o` or none for others.
  No zoo of triangles and squares.
- At most three series per axis; more becomes facets (section 10).
- Set `xmin` and `ymin` so curves do not float; fix both limits when panels are compared.
- Name axes concretely, with units: "validation loss", "parameters N", "time (s)". A
  vague label ("density") was rejected in favor of the measured quantity.
- Inline labels at the line ends beat a legend; a legend, when needed, is frameless.
- Pgfplots text at its printed size: build the axis at the width it prints (`width=` of
  the column) and do not set fonts smaller than the preamble's tiers. Figure text set too
  small is the commonest way a good plot looks cheap.
- Emphasis by color only where the values are plotted to scale: a baseline is drawn pale
  only where it is weak in the numbers.

## 12. Serif-look conventions

For panels that sit beside operator-pipeline figures in the serif theme. Rules:

- **Despined black axis.** Left and bottom spine only, `ink` at 0.9 pt, ticks outside, no
  gridlines. The style below is figure-local; paste it once per file.
- **Navy against the contrast.** `navy` is ours, single or train; `contrast` is the
  competitor, combination or test. A third series, if unavoidable, is `accentL`.
- **Citations as `link` text** in parentheses are the only colored text.

### 12a. Comparison scatter with an in-figure citation

```latex
\pgfplotsset{
  despined/.style={
    width=6cm, height=4.5cm, axis lines=left,
    axis line style={ink, line width=0.9pt},
    tick align=outside, tick style={ink, line width=0.7pt},
    every tick label/.append style={font=\figfont\figM},
    label style={font=\figfont\figM, text=ink},
    title style={font=\figfont\figL, text=ink},
    every axis plot/.append style={line width=1pt},
    legend style={draw=none, fill=none, font=\figfont\figM},
    legend cell align=left, clip=false,
  },
}
\begin{tikzpicture}
\begin{axis}[despined, xlabel={component 1}, ylabel={component 2}, xmin=0, ymin=0]
  \addplot[only marks, mark=*, mark size=1.1pt, navy, opacity=0.6]
    coordinates {(2,1.5)(3,2.1)(2.4,1.8)(3.6,2.6)(1.8,1.2)(2.9,2.0)(3.2,2.3)(2.6,1.9)};
  \addplot[only marks, mark=*, mark size=1.1pt, contrast, opacity=0.6]
    coordinates {(6,4.6)(6.8,5.2)(5.6,4.2)(7.1,5.5)(6.4,4.9)(5.9,4.4)(6.6,5.0)};
  \legend{ours, competitor}
  \node[cite, anchor=south east] at (axis cs:7.4,0.4) {(Author et al., Year)};
\end{axis}
\end{tikzpicture}
```

### 12b. Ordinal wedge axis

When the x variable is ordinal and monotone, drop the numeric ticks and draw a solid black
wedge widening left to right, meaning "more".

```latex
\pgfplotsset{
  despined/.style={
    width=6cm, height=4.5cm, axis lines=left,
    axis line style={ink, line width=0.9pt},
    tick align=outside, tick style={ink, line width=0.7pt},
    every tick label/.append style={font=\figfont\figM},
    label style={font=\figfont\figM, text=ink},
    every axis plot/.append style={line width=1pt},
    legend style={draw=none, fill=none, font=\figfont\figM},
    legend cell align=left, clip=false,
  },
}
\begin{tikzpicture}
\begin{axis}[despined, ylabel={$r^2$}, ymin=0, ymax=1, xmin=0.5, xmax=5.5,
             xtick=\empty, xlabel={}]
  \addplot[navy, mark=*, mark size=1.2pt]
    coordinates {(1,.82)(2,.74)(3,.63)(4,.55)(5,.48)};
  \addplot[contrast, dashed, mark=none, line width=0.9pt]
    coordinates {(1,.70)(2,.58)(3,.47)(4,.40)(5,.35)};
  \legend{single, combination}
\end{axis}
\begin{scope}[shift={(0,-0.55)}]
  \fill[ink] (0,0.02) -- (0,-0.02) -- (5.4,-0.16) -- (5.4,0.16) -- cycle;
  \node[font=\figfont\figM, text=ink, anchor=west] at (5.5,0) {number of perturbations};
\end{scope}
\end{tikzpicture}
```

### 12c. Twin mirrored bar panels

Two `xbar` panels share one column of categories: the left grows toward the labels
(`x dir=reverse`), the right away. The direction of "better" is in each axis label; a thin
dashed `annot` line marks a threshold.

```latex
\pgfplotsset{
  twinbar/.style={
    width=4.2cm, height=5cm, xbar, bar width=7pt,
    axis line style={ink, line width=0.9pt},
    tick align=outside, tick style={ink, line width=0.7pt},
    every tick label/.append style={font=\figfont\figS},
    label style={font=\figfont\figM, text=ink},
    ytick={1,2,3}, ymin=0.4, ymax=3.6,
    every axis plot/.append style={draw=ink, line width=0.6pt},
    enlarge y limits=0.18, clip=false,
  },
}
\begin{tikzpicture}
\begin{axis}[twinbar, name=L, axis lines=left, x dir=reverse,
             xlabel={$r^2\rightarrow$}, xmin=0, xmax=1,
             yticklabels={baseline, ours, identity}]
  \addplot[fill=navy] coordinates {(0.62,1)(0.81,2)(0.40,3)};
  \draw[annot, dashed, line width=0.6pt] (axis cs:0.5,0.4) -- (axis cs:0.5,3.6);
\end{axis}
\begin{axis}[twinbar, at={(L.east)}, anchor=west, xshift=10mm,
             axis y line=none, axis x line=bottom,
             xlabel={$\leftarrow$ MMD}, xmin=0, xmax=1, yticklabels={}]
  \addplot[fill=contrast] coordinates {(0.28,1)(0.15,2)(0.55,3)};
  \draw[annot, dashed, line width=0.6pt] (axis cs:0.5,0.4) -- (axis cs:0.5,3.6);
\end{axis}
\end{tikzpicture}
```

### 12d. Violin

PGFPlots has no violin. A symmetric smooth body in a flat fill, a thick black IQR bar, a
thin whisker, a white median dot with a thin ring. The body shape here is schematic; for
data, compute the density in Python and emit the outline (`generators.md`).

```latex
\begin{tikzpicture}[x=1cm,y=1cm]
\newcommand{\violin}[2]{%
  \begin{scope}[shift={(#1,0)}]
    \fill[#2]
      (0,0)
      .. controls (0.10,0.6) and (0.30,1.1) .. (0.34,1.6)
      .. controls (0.30,2.1) and (0.14,2.7) .. (0,3)
      .. controls (-0.14,2.7) and (-0.30,2.1) .. (-0.34,1.6)
      .. controls (-0.30,1.1) and (-0.10,0.6) .. (0,0) -- cycle;
    \fill[ink] (-0.045,1.0) rectangle (0.045,2.1);
    \draw[ink, line width=0.7pt] (0,0.5) -- (0,2.7);
    \filldraw[fill=white, draw=navy, line width=0.3pt] (0,1.6) circle (1.3pt);
  \end{scope}}
\violin{0}{navy}
\violin{1}{contrast}
\violin{2}{accentL}
\draw[ink, line width=0.9pt] (-0.5,0) -- (2.5,0);
\foreach \x/\t in {0/ours, 1/treated, 2/control}
  \node[font=\figfont\figM, text=ink, below=2pt] at (\x,0) {\t};
\node[font=\figfont\figM, text=ink, rotate=90, anchor=south] at (-0.85,1.6) {score};
\end{tikzpicture}
```
