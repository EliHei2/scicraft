# Architectures, pipelines and method schematics

Copy-paste recipes for model and method figures. They assume `assets/preamble.tex`
(styles `base`, `block`, `block accent`, `flow`, `flowfaint`, `group`, `op`, `var`,
`panel`, `note`, `tag`, `chip`, `opbox`, the `\StackBox` and `\opstack` macros). The
element vocabulary and the canonical transformer, teacher-student and scale-spine
compositions are in `grammar.md`; open it first.

**Contents**
1. Linear block pipeline (encoder, latent, decoder)
2. Dashed module container with corner title
3. Stacked layers with a brace
4. Attention head
5. U-Net (encoder-decoder with skips)
6. Multi-stage overview with data glyphs
7. Action loop (policy, environment, reward)
8. Foundation model as a box (several inputs, one embedding)
9. Branching multi-task head
10. Panel letters, legends and composite layout
11. Layout and alignment tactics
12. Heads as a stack beside the operands
13. Residual path drawn behind its block
14. Orthogonal router
15. Two lanes converging on a shared block
16. Abstract object paired with its literal structure
17. Discrete actions with one accent terminal token
18. Radial callout overview
19. Operator pipeline (serif look)

---

## 1. Linear block pipeline

The workhorse. Modules left to right, the accent on the focal component, inputs as
`var` circles.

```latex
\begin{tikzpicture}[base, node distance=12mm]
  \node[var] (x) {$x$};
  \node[block, right=of x] (enc) {Encoder};
  \node[block accent, right=of enc] (z) {$z$};
  \node[block, right=of z] (dec) {Decoder};
  \node[var, right=of dec] (xh) {$\hat{x}$};
  \draw[flow] (x) -- (enc);
  \draw[flow] (enc) -- (z);
  \draw[flow] (z) -- (dec);
  \draw[flow] (dec) -- (xh);
  \draw[flowfaint] (xh) to[out=-60,in=-120] node[note,below]{$\mathcal{L}(x,\hat{x})$} (x);
\end{tikzpicture}
```

## 2. Dashed module container

Group several nodes and title the box in its corner. Put the box on the background layer
so its stroke sits behind the contents.

```latex
\begin{tikzpicture}[base, node distance=11mm]
  \node[block] (a) {Embed};
  \node[block, right=of a] (b) {Mix};
  \node[block, right=of b] (c) {Readout};
  \draw[flow] (a)--(b); \draw[flow] (b)--(c);
  \begin{scope}[on background layer]
    \node[group, fit=(a)(b)(c)] (G) {};
  \end{scope}
  \node[grouptitle, above right=0pt and 1pt] at (G.north west) {Backbone};
\end{tikzpicture}
```

## 3. Stacked layers with a brace

For "x N layers" drawn out explicitly. A slight vertical offset reads as depth; the brace
on the right names the count. For a compact version use the stacked copies of section 12 or `\nnstack` in `grammar.md`.

```latex
\begin{tikzpicture}[base]
  \foreach \i in {0,1,2} {
    \node[block, minimum width=26mm] (L\i) at (0,{-\i*11mm}) {Transformer block};
  }
  \draw[flow] (L0.south) -- (L1.north);
  \draw[flow] (L1.south) -- (L2.north);
  \node[var, above=9mm of L0] (in) {$x$};
  \node[var, below=9mm of L2] (out) {$h$};
  \draw[flow] (in)--(L0); \draw[flow] (L2)--(out);
  \draw[brace] ([xshift=4mm]L0.north east) -- ([xshift=4mm]L2.south east)
    node[midway, right=6pt, note]{$\times N$};
\end{tikzpicture}
```

## 4. Attention head

Q, K, V as labeled operands into a scaled dot product, then the head output. Operands stay
neutral: their labels carry their identity, so the accent stays free for the focal step.
For the full mechanism figure with a bias inset see `grammar.md`, section 8.

```latex
\begin{tikzpicture}[base, node distance=8mm]
  \node[varfill] (Q) {$Q$};
  \node[var, below=of Q] (K) {$K$};
  \node[var, below=of K] (V) {$V$};
  \node[op, right=14mm of K] (att) {$\cdot$};
  \node[block accent, right=12mm of att, align=center] (sm)
    {softmax\\$\frac{QK^\top}{\sqrt{d}}$};
  \node[block, right=10mm of sm] (out) {head$_i$};
  \draw[flow] (Q) -- (att); \draw[flow] (K) -- (att);
  \draw[flow] (V) to[out=0,in=-150] (sm.south west);
  \draw[flow] (att) -- (sm); \draw[flow] (sm) -- (out);
\end{tikzpicture}
```

## 5. U-Net (encoder-decoder with skip connections)

Narrowing and widening blocks suggest down- and up-sampling; dashed gray skips bridge
matching levels.

```latex
\begin{tikzpicture}[base]
  \foreach \i/\w in {0/26,1/20,2/14} {
    \node[block, minimum width=\w mm] (e\i) at (0,{-\i*11mm}) {enc \i};
  }
  \foreach \i/\w in {0/26,1/20,2/14} {
    \node[block accent, minimum width=\w mm] (d\i) at (42mm,{-\i*11mm}) {dec \i};
  }
  \node[block, minimum width=12mm] (mid) at (21mm,-33mm) {bottleneck};
  \draw[flow] (e0)--(e1); \draw[flow] (e1)--(e2); \draw[flow] (e2)--(mid);
  \draw[flow] (mid)--(d2); \draw[flow] (d2)--(d1); \draw[flow] (d1)--(d0);
  \foreach \i in {0,1,2} \draw[flowfaint, dashed] (e\i.east) -- (d\i.west);
\end{tikzpicture}
```

## 6. Multi-stage overview figure

The Figure 1 of a method paper: input object, processing, output, with small data glyphs
and the learned core in the accent. Compose with glyphs from the other references. The
dots here are placeholders: in a real figure they come from the data or the generator
(`generators.md`).

```latex
\begin{tikzpicture}[base, node distance=13mm]
  \node[draw=mist, rounded corners, fill=cloud, minimum size=12mm] (data) {};
  \foreach \p in {(-2.5mm,2mm),(1mm,3mm),(2.5mm,-1mm),(-1mm,-2.5mm),(0,0)}
    \fill[accent] ([shift={\p}]data.center) circle (0.7pt);
  \node[note, below=1mm of data] {samples};
  \node[block accent, right=of data, minimum height=12mm] (model) {$f_\theta$};
  \node[draw=mist, rounded corners, fill=paper, minimum size=12mm, right=of model] (pred) {};
  \draw[accent, line width=1pt] ([xshift=-4mm,yshift=-3mm]pred.center)
        to[out=20,in=200] ([xshift=4mm,yshift=3mm]pred.center);
  \node[note, below=1mm of pred] {prediction};
  \draw[flow] (data)--(model); \draw[flow] (model)--(pred);
  \node[panel] at ([xshift=-7mm,yshift=6mm]data.north west) {a};
\end{tikzpicture}
```

## 7. Action loop

Policy and environment exchanging action and state, with the reward as the one contrast.

```latex
\begin{tikzpicture}[base, node distance=20mm]
  \node[block accent] (pi) {policy $\pi_\theta$};
  \node[block, right=34mm of pi] (env) {environment};
  \draw[flow] (pi.north) to[out=60,in=120] node[note,above]{action $a_t$} (env.north);
  \draw[flow] (env.south) to[out=-120,in=-60] node[note,below]{state $s_{t+1}$} (pi.south);
  \node[op, fill=contrastL, draw=contrast, right=8mm of pi, yshift=-13mm] (r) {$r$};
  \draw[flowfaint] (env.south west) to[out=-150,in=0] (r.east);
  \draw[flowfaint] (r.west) to[out=180,in=-30] (pi.south east);
\end{tikzpicture}
```

## 8. Foundation model as a box

Several heterogeneous inputs collapse into one embedding. The inputs are gray blocks; the
model is the accent. Name each input by what it is.

```latex
\begin{tikzpicture}[base, node distance=6mm]
  \node[block] (img) {images};
  \node[block, below=of img] (tab) {tables};
  \node[block, below=of tab] (txt) {text};
  \node[block accent, right=16mm of tab, minimum height=20mm] (fm) {Foundation\\model};
  \node[var, right=14mm of fm] (z) {$z$};
  \foreach \m in {img,tab,txt} \draw[flow] (\m.east) -- (fm.west);
  \draw[flow] (fm)--(z);
\end{tikzpicture}
```

## 9. Branching multi-task head

One trunk, several task heads, all neutral; the trunk is the accent.

```latex
\begin{tikzpicture}[base, node distance=10mm]
  \node[block accent] (h) {shared $h$};
  \node[block, above right=2mm and 16mm of h] (t1) {classify};
  \node[block, right=16mm of h] (t2) {regress};
  \node[block, below right=2mm and 16mm of h] (t3) {segment};
  \foreach \t in {t1,t2,t3} \draw[flow] (h.east) -- (\t.west);
\end{tikzpicture}
```

## 10. Panel letters, legends, composite layout

- **Panel letters**: bold lowercase, no period, at each panel's top left, aligned across
  panels: `\node[panel] at (current bounding box.north west) {a};`.
- **Legend**: label inline on the object where possible and drop the legend. When a
  legend is needed, a small frameless stack of swatch and label rows:

```latex
\begin{tikzpicture}[base]
  \foreach \i/\c/\lbl in {0/accent/ours, 1/contrast/baseline, 2/mist/observed} {
    \draw[\c, line width=2pt] (0,{-\i*5mm}) -- ++(6mm,0);
    \node[note, right=2mm, anchor=west] at (6mm,{-\i*5mm}) {\lbl};
  }
\end{tikzpicture}
```

- **Composite**: one `tikzpicture`, each panel in `\begin{scope}[shift={(7cm,0)}]` with
  its own letter. Keep equal baselines. Two to four clean panels beat eight cramped ones;
  if a figure is trying to be two figures, split it.

## 11. Layout and alignment tactics

- Use `positioning` (`right=12mm of x`) over hand-placed coordinates; spacing stays
  uniform and survives edits.
- Align a row by a shared `minimum width`, a column by a shared `minimum height`.
- Name the anchor an arrow leaves or enters: `(a.east)`, `(b.north west)`.
- Curved flows: `to[out=30,in=150]`, gentle and consistent.
- Midpoint: `\coordinate (m) at ($(a)!0.5!(b)$);`.
- Budget whitespace first, then place; "delete and align" fixed the overlapping
  hand-laid architecture figure this skill grew out of.

## 12. Heads as a stack beside the operands

"h heads" is a depth cue, never h drawn boxes: one labeled block with two empty copies
behind it (`\nnstack` plus a front `nnblock`), and the count written on a brace outside
the stack. Here the three operands enter from the left as token rows, the stacked head
block sits in the middle, and the merge is one block to the right.

```latex
\begin{tikzpicture}[base]
  \foreach \lab/\y/\sty in {Q/8mm/tokenvis, K/0mm/token, V/-8mm/token} {
    \tokenrow{(0,\y)}{\sty}{3}{4.2mm}
    \node[tag, anchor=east] at (-3mm,\y) {$\lab$};
    \draw[nnarrow] (11mm,\y) -- (22mm,0);
  }
  \nnstack{(36mm,0)}{nnblock accent}{24mm}{14mm}{2}{1.3mm}{1.1mm}
  \node[nnblock accent, minimum width=24mm, minimum height=14mm] (h) at (36mm,0) {attention\\head $i$};
  \draw[brace] (36mm,9.5mm) -- (50mm,9.5mm) node[midway, above=4pt, tag] {$h$ heads};
  \node[nnblock] (m) at (66mm,0) {concat\\$+$ linear};
  \draw[nnarrow] (h.east) -- (m.west);
  \draw[nnarrow] (m.east) -- ++(9mm,0) node[right] {$z$};
\end{tikzpicture}
```

## 13. Residual path drawn behind its block

A residual adds the input of a sub-layer to its output. Draw the sum as a plus operator
and send the bypass around the side inside `on background layer`, so it never crosses a
box face. Keep the bypass gutter wider than the widest box.

```latex
\begin{tikzpicture}[base]
  \node[nnlayer, minimum width=22mm] (f) at (0,0) {sub-layer $F$};
  \node[op] (s) at (0,10mm) {$+$};
  \coordinate (in) at (0,-10mm);
  \draw[nnarrow] (in) -- (f);
  \draw[nnarrow] (f) -- (s);
  \draw[nnarrow] (s) -- ++(0,8mm) node[above] {$x + F(x)$};
  \begin{scope}[on background layer]
    \draw[nnarrow, draw=slate] (0,-6mm) -- (-16mm,-6mm) |- (s.west);
  \end{scope}
  \node[anchor=north] at (in) {$x$};
\end{tikzpicture}
```

## 14. Orthogonal router

Branching and merging data flow uses square corners. Route a fan-in through one shared
gutter coordinate so the lines stack into the target's west face. `tikz-ext` offers
automatic orthogonal routing but is missing from a minimal TeX install; the manual
`-|` and `|-` operators work everywhere.

```latex
\begin{tikzpicture}[base, node distance=14mm]
  \node[block] (a) {split};
  \node[block accent, above right=8mm and 22mm of a] (b) {branch A};
  \node[block, below right=8mm and 22mm of a] (c) {branch B};
  \node[block, right=70mm of a] (m) {merge};
  \draw[flow] (a.east) -| ([xshift=-9mm]b.west) |- (b.west);
  \draw[flow] (a.east) -| ([xshift=-9mm]c.west) |- (c.west);
  \coordinate (g) at ([xshift=-9mm]m.west);
  \draw[flow] (b.east) -| (g) |- (m.west);
  \draw[flow] (c.east) -| (g) |- (m.west);
\end{tikzpicture}
```

## 15. Two lanes converging on a shared block

Two input streams, each with its own encoder, converging on one block placed at the
lanes' midpoint, so the layout survives a change of lane spacing.

```latex
\begin{tikzpicture}[base, node distance=10mm]
  \node[var] (x1) {$x_1$};
  \node[block, right=of x1] (e1) {Encoder};
  \node[var, below=14mm of x1] (x2) {$x_2$};
  \node[block, right=of x2] (e2) {Encoder};
  \draw[flow] (x1)--(e1); \draw[flow] (x2)--(e2);
  \coordinate (mid) at ($(e1.east)!0.5!(e2.east)$);
  \node[block accent, right=18mm of mid, anchor=west] (fuse) {Fuse $\to z$};
  \draw[flow] (e1.east) -| ([xshift=8mm]e1.east) |- (fuse.west);
  \draw[flow] (e2.east) -| ([xshift=8mm]e2.east) |- (fuse.west);
\end{tikzpicture}
```

## 16. Abstract object paired with its literal structure

An abstract glyph (a graph) directly above the literal structure it abstracts, joined by
one thin arrow: "this cartoon stands for that data". The seed keeps the scatter fixed.

```latex
\begin{tikzpicture}[base]
  \foreach \n/\x/\y in {1/0/24mm, 2/10mm/28mm, 3/18mm/22mm, 4/9mm/18mm}
    \node[var, minimum size=4mm, fill=accentL!45] (n\n) at (\x,\y) {};
  \draw[structedge] (n1)--(n2); \draw[structedge] (n2)--(n3);
  \draw[structedge] (n1)--(n4); \draw[structedge] (n4)--(n3);
  \node[draw=mist, fill=cloud, rounded corners, minimum size=16mm] (st) at (9mm,2mm) {};
  \pgfmathsetseed{7}
  \foreach \i in {1,...,18}
    \fill[slate] ([shift={(rnd*12mm-6mm, rnd*12mm-6mm)}]st.center) circle (0.5pt);
  \draw[flowfaint] (n4.south) -- (st.north);
\end{tikzpicture}
```

## 17. Discrete actions with one accent terminal token

Neutral chips for the ordinary actions; the one special action (a terminal stop, an
absorbing state) in the contrast. A brace groups the ordinary ones.

```latex
\begin{tikzpicture}[base, node distance=3mm]
  \foreach \k/\lbl in {0/$a_1$, 1/$a_2$, 2/$a_3$, 3/$a_4$}
    \node[chip=cloud] (c\k) at ({\k*12mm},0) {\lbl};
  \node[chip=contrastL, draw=contrast, right=8mm of c3] (stop) {stop};
  \draw[brace, decoration={brace, mirror, amplitude=4pt}]
    (c0.south west) -- (c3.south east)
    node[midway, below=5pt, tag]{discrete actions};
\end{tikzpicture}
```

## 18. Radial callout overview

One central object, its parts named in the surrounding whitespace, placed by angle and
anchored on the side facing the core so the leaders stay short. A `\foreach` over
`angle/anchor/title/symbol` makes a fourth callout a one-line edit.

```latex
\begin{tikzpicture}[base]
  \node[block accent, minimum size=16mm] (core) {$f_\theta$};
  \foreach \ang/\anch/\ti/\sy in {%
      150/east/Encoder/$z=f(x)$,
      30/west/Predictor/$\hat z$,
      270/north/Objective/$\mathcal{L}$} {
    \coordinate (p) at ($(core.center)+(\ang:22mm)$);
    \draw[flowfaint] (core) -- (p);
    \node[anchor=\anch, align=left] at (p) {{\bfseries \ti}\\[1pt]\sy};
  }
\end{tikzpicture}
```

## 19. Operator pipeline (serif look)

A left-to-right pipeline of flat, thick black-outlined rounded boxes (`opbox`) joined by
black arrows, the equation pinned to the top and the geometry below restating it. Fill
encodes role: generic transforms gray, exactly one `opbox accent` box, a tall
`opbox map`. A module shared by k inputs is an `\opstack`: its back copies send gray
`agg` arrows, its front sends a black `spine` arrow. Gray role captions sit under the
boxes. The look is the serif theme's (modeled on a published monograph, see THIRD_PARTY.md); set `\figtheme{serif}` for the full effect, though it compiles in both.

```latex
\begin{tikzpicture}[base]
  \node[eq] (eq) at (3.0,2.7)
    {$\hat{y}=\mathcal{T}_\theta\!\big(\mathcal{C}_\Phi(\mathcal{E}_\phi(\mu),\,c_{1:k})\big)$};
  \node (mu) at (-2.3,0.9)  {$\mu$};
  \node (c1) at (-2.3,0.25) {$c_1$};
  \node      at (-2.3,-0.3) {$\vdots$};
  \node (ck) at (-2.3,-0.9) {$c_k$};
  \draw[densely dotted, ink, line width=0.8pt] (-1.95,1.2) -- (-1.95,-1.2);
  \node[rotate=90, font=\figfont\figL, text=ink] at (-2.8,0) {inputs};
  \opstack{(0.2,0)}{$\mathcal{E}_\phi$}
  \node[note, below=10pt of opfront] {embedding};
  \node[opbox accent] (c) at (3.2,0) {$\mathcal{C}_\Phi$};
  \node[note, below=2pt of c] {combinator};
  \node[opbox map] (t) at (6.0,0) {$\mathcal{T}_\theta$};
  \node[note, below=2pt of t] {map};
  \node (y) at (7.6,0) {$\hat{y}$};
  \foreach \n in {mu,c1,ck} \draw[spine, line width=0.9pt] (\n.east) -- ([xshift=-3pt]opfront.west);
  \draw[agg] ([yshift=1.6ex]opfront.east) -- ([yshift=1.6ex]c.west);
  \draw[agg] ([yshift=0.8ex]opfront.east) -- ([yshift=0.8ex]c.west);
  \draw[spine] (opfront.east) -- (c.west);
  \draw[spine] (c.east) -- (t.west);
  \draw[spine] (t.east) -- (y);
  \draw[spine] (mu.north) to[out=70,in=150] (t.north west);
\end{tikzpicture}
```

Size each operator symbol to nearly fill its box. For the dot clusters, fields and
transport arrows that often accompany this pipeline see `distributions_fields.md`,
section 13.
