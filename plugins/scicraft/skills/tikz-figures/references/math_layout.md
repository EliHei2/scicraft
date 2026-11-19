# Math inside figures: equations, braces & annotations

Typeset equations as figure elements: boxed objectives, loss terms with under-braces,
arrows pointing at specific symbols, commutative-style diagrams. Math uses the theme's
family (`\figfont`: sans math in the minimal theme, Palatino in the serif theme, Computer
Modern with `\figfamily{cm}`), so equations look native to the figure. Keep at most one
boxed core equation per figure; the declutter standard bans paragraphs in the image. Snippets go between the
preamble and `\end{document}`.

**Contents**
1. Boxed / highlighted equation
2. Loss with annotated under-braces
3. Pointing an arrow at a term
4. Commutative-diagram-style arrows
5. Concept number line / axis-as-idea
6. Table as a figure
7. Math spacing tips

---

## 1. Boxed / highlighted equation

Wrap a key equation in a `block accent` to make it a focal object (e.g. the objective in
an overview figure). Use `\displaystyle` so sums/fractions render full size.

```latex
\begin{tikzpicture}[base]
  \node[block accent, inner sep=8pt] (eq)
    {$\displaystyle \mathcal{L} = \mathbb{E}_{x\sim p}\big[\|x-\hat{x}\|^2\big]
       + \beta\, D_{\mathrm{KL}}(q\|p)$};
\end{tikzpicture}
```

## 2. Loss with annotated under-braces

Name the pieces of an objective. `\underbrace{...}_{}` leaves the slot empty; place the
labels as `note` nodes below so they use the figure font and color.

```latex
\begin{tikzpicture}[base]
  \node (eq)
    {$\displaystyle \mathcal{L}(\theta)
      = \underbrace{\tfrac{1}{n}\sum_i \ell(f_\theta(x_i),y_i)}_{}
      + \underbrace{\lambda \|\theta\|^2}_{}$};
  \node[note, anchor=north] at ($(eq.south)+(-1.1,0.05)$) {data term};
  \node[note, anchor=north] at ($(eq.south)+(1.6,0.05)$) {regularizer};
\end{tikzpicture}
```

Tune the `(-1.1, …)` / `(1.6, …)` offsets to sit each label under its term; recompile and
nudge.

## 3. Pointing an arrow at a term

Call out one symbol with a curved gray arrow and a small label.

```latex
\begin{tikzpicture}[base]
  \node (eq) {$\displaystyle \rho_{t+1} = \nabla\psi_\theta \,\#\, \rho_t$};
  \node[note, above right=6mm and 0mm of eq.north] (l1) {transport map};
  \draw[->, slate, line width=0.5pt] (l1.south) to[out=-90,in=60] ($(eq.north)+(0.15,0)$);
\end{tikzpicture}
```

To target a precise symbol, wrap it in a named node inside the math:
`$\dots \tikz[baseline]{\node[inner sep=1pt](m){$\nabla\psi_\theta$};} \dots$` then draw to
`(m)`.

## 4. Commutative-diagram-style arrows

A 2×2 square of objects with labeled maps (equivariance / functoriality). Plain `flow`
arrows, `note` edge labels.

```latex
\begin{tikzpicture}[base, node distance=16mm]
  \node (X) {$X$};
  \node[right=of X] (Y) {$Y$};
  \node[below=of X] (X2) {$X'$};
  \node[below=of Y] (Y2) {$Y'$};
  \draw[flow] (X) -- node[note,above]{$f$} (Y);
  \draw[flow] (X) -- node[note,left]{$g$} (X2);
  \draw[flow] (Y) -- node[note,right]{$g'$} (Y2);
  \draw[flow] (X2) -- node[note,below]{$f'$} (Y2);
\end{tikzpicture}
```

## 5. Concept number line / axis-as-idea

A labeled axis used as a *concept* (cost, uncertainty, low→high) rather than a data plot.

```latex
\begin{tikzpicture}[base]
  \draw[->, ink, line width=0.8pt] (0,0) -- (5,0);
  \foreach \x/\lbl in {0.5/low, 2.5/medium, 4.5/high} {
    \draw[ink] (\x,0.08)--(\x,-0.08); \node[note, below] at (\x,-0.1) {\lbl};
  }
  \fill[accent] (3.6,0) circle (1.5pt) node[above=2pt, note, accent]{ours};
\end{tikzpicture}
```

Useful for cost/accuracy trade-off captions, "cheap → expensive" modality axes, etc.

## 6. Table as a figure

When a small comparison belongs *inside* the figure, a TikZ `matrix` keeps it in the same
font and lets you tint cells (e.g. bold the winner). For full data tables prefer real
LaTeX `tabular` in the body; this is for compact in-figure callouts.

```latex
\begin{tikzpicture}[base]
  \matrix (m) [matrix of nodes, nodes={anchor=center, minimum width=16mm, minimum height=6mm,
               font=\figM}, row sep=-\pgflinewidth, column sep=-\pgflinewidth,
               nodes in empty cells]
  {
    |[font=\figM\bfseries]| method & |[font=\figM\bfseries]| acc & |[font=\figM\bfseries]| cost \\
    ours  & |[fill=accent!15]| \textbf{0.85} & \$51 \\
    base  & 0.72 & \$336 \\
  };
  \draw[slate, line width=0.5pt] (m-1-1.south west) -- (m-1-3.south east);
\end{tikzpicture}
```

## 7. Math spacing tips

- The `base` and `spare axis` styles apply `\figfont`, so math matches the figure text.
  If a stray equation looks like the wrong family, give its `tikzpicture` the `[base]`
  option or its node `font=\figfont`.
- Thin spaces read better in sans math: `\,` between a number and unit or between factors
  (`\beta\, D_{\mathrm{KL}}`). Use `\mathrm{}` for multi-letter operators (KL, MSE) so they
  aren't italic-spaced.
- For large operators inline, `\displaystyle` or `\tfrac` (text-fraction) keeps height
  sane.
- `\|` for norms, `\langle\,\rangle` for inner products, `\#` for push-forward, `\sim` for
  "distributed as" all render cleanly in every theme.
- Keep equation nodes on their own layer above shaded regions: draw fills first, math last.
