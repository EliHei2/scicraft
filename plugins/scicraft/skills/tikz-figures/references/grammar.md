# The grammar: blocks, token rows, depth stacks, connectors

The vocabulary every architecture, method and overview figure is built from, with the
canonical compositions. All styles and macros are in `assets/preamble.tex`; every snippet
goes between the preamble and `\end{document}` and compiles in both themes.

**Contents**
1. The element table
2. Blocks and sub-layers
3. Token rows, visible and held-out
4. Depth stacks: three idioms
5. Arrows and connectors: the ink hierarchy
6. Transformer block
7. Teacher and student (JEPA two-rail layout)
8. Mechanism inset: show the operation itself
9. Scale spine (the Figure-1 overview)
10. kNN ego ball and partition tree
11. Tabular-model glyphs

---

## 1. The element table

| Element | Style or macro | Use for | Rule |
|---|---|---|---|
| module | `block`, `nnblock` | encoder, decoder, FFN, any trained part | gray fill, rounded 2.5 to 3 pt, min height 8 to 9 mm |
| the focal module | `block accent`, `nnblock accent` | the one trainable part the figure is about | one per figure |
| sub-layer | `nnlayer` | LayerNorm, attention, FFN rows inside a block | thin slate outline, white fill |
| in/out | `nnio`, `var`, `op` | inputs, outputs, operators such as plus | small circles |
| token cell | `token`, `tokenvis`, `masktoken` via `\tokenrow` | sequences, patches, set elements | 3.4 mm squares; visible = accent, held-out = gold dashed |
| labeled object | `chip` | one object tracked across panels | same box everywhere it appears |
| repetition | `\nnstack`, `\StackBox`, `\opstack` | x N layers, h heads, a module shared by k inputs | 2 to 3 offset copies, count named by a brace |
| operator box | `opbox`, `opbox accent`, `opbox map` | operator pipelines (serif look) | 1.3 pt black outline, fill encodes role |
| data flow | `flow`, `nnarrow` | the main path | ink, 0.8 to 0.9 pt |
| support flow | `flowfaint`, `agg`, `field` | aggregation, side inputs, fields | slate or annot, thinner |
| weight copy | `emaarrow` | EMA update, stop-gradient | slate, densely dashed |
| spine | `spine` | the one transport or headline arrow | 1.6 pt black |
| zoom connector | `frustum` | zoom box to the next frame, cross-panel links | `ink!45`, 0.4 pt, dashed |
| container | `group` + `grouptitle` | a module made of several blocks | dashed slate, title in the corner |
| spatial frame | `frame` | a panel of real geometry | `ink!85`, 0.6 pt, rounded 2 pt |

## 2. Blocks and sub-layers

```latex
\begin{tikzpicture}[base, node distance=10mm]
  \node[nnblock] (enc) {Encoder};
  \node[nnblock accent, right=of enc] (pred) {Predictor};
  \node[block, right=of pred] (head) {Head};
  \draw[nnarrow] (enc) -- (pred);
  \draw[nnarrow] (pred) -- (head);
  \begin{scope}[on background layer]
    \node[group, fit=(enc)(pred)] (G) {};
  \end{scope}
  \node[grouptitle, anchor=south west] at (G.north west) {backbone};
\end{tikzpicture}
```

## 3. Token rows, visible and held-out

`\tokenrow{(x,y)}{style}{n}{gap}` starts at `(x,y)` and steps right by `gap`. Keep the
gap a little larger than the 3.4 mm cell so cells read as separate.

```latex
\begin{tikzpicture}[base]
  \tokenrow{(0,0)}{tokenvis}{5}{4.2mm}
  \tokenrow{(21mm,0)}{masktoken}{3}{4.2mm}
  \tokenrow{(0,-7mm)}{token}{8}{4.2mm}
  \node[tag, anchor=east] at (-3mm,0) {context};
  \node[tag, anchor=east] at (-3mm,-7mm) {target};
\end{tikzpicture}
```

## 4. Depth stacks: three idioms

Depth is an offset faded copy, never a blur or a shadow. Keep 2 to 3 copies; a brace
outside the stack carries the real count.

```latex
\begin{tikzpicture}[base]
  % (a) empty shadow copies behind a labeled front block (x N layers)
  \nnstack{(0,0)}{nnblock}{22mm}{9mm}{2}{1.4mm}{1.1mm}
  \node[nnblock, minimum width=22mm, minimum height=9mm] at (0,0) {Block};
  \draw[brace] (13mm,5mm) -- (13mm,-5mm) node[midway, right=5pt, tag] {$\times N$};
  % (b) labeled faded copies in front of one another (h heads)
  \StackBox{(38mm,0)}{block}{2}{Attention}
  % (c) a module shared by k inputs: back copies send grey, the front sends black
  \opstack{(70mm,0)}{$\mathcal{E}_\phi$}
  \node[opbox accent] (c) at (92mm,0) {$\mathcal{C}$};
  \draw[agg] ([yshift=1.6ex]opfront.east) -- ([yshift=1.6ex]c.west);
  \draw[agg] ([yshift=0.8ex]opfront.east) -- ([yshift=0.8ex]c.west);
  \draw[spine] (opfront.east) -- (c.west);
\end{tikzpicture}
```

## 5. Arrows and connectors: the ink hierarchy

Black does structure, gray does support, color is never an arrow. From light to heavy:
`field` 0.5 pt gray, `traj` 0.5 pt gray, `frustum` 0.4 pt dashed, `agg` and `flowfaint`
0.7 pt, `flow` and `nnarrow` 0.8 to 0.9 pt ink, `spine` 1.6 pt black. Rules:

- **One dominant reading direction.** Left to right, or bottom to top. Arrows that
  double back need a reason a reader can see.
- **Arrows end at anchors** (`(a.east)`, `(b.north)`) so they stop at the box edge and
  never cross a label.
- **Square corners for routed data flow** (`-|` and `|-` through one shared gutter
  coordinate); never mix diagonals and right angles in one route.
- **A skip connection passes behind** the box it bypasses: draw it in an
  `on background layer` scope.
- **Label an edge with a positioned node** (`node[above]`, `node[midway, right=4pt]`);
  a bare `-- node {x}` sits on the line (the safety script flags it).

## 6. Transformer block

Sub-layers stacked inside one block, residuals as plus operators with a faint bypass,
token rows in and out, the repeat as a stack plus a brace.

```latex
\begin{tikzpicture}[base]
  \tokenrow{(-6.3mm,-14mm)}{token}{4}{4.2mm}
  \nnstack{(0,9mm)}{nnblock}{26mm}{34mm}{2}{1.4mm}{1.1mm}
  \node[nnblock, minimum width=26mm, minimum height=34mm] (B) at (0,9mm) {};
  \node[nnlayer, minimum width=20mm] (n1) at (0,-1mm) {LayerNorm};
  \node[nnlayer, minimum width=20mm] (at) at (0,5mm) {Attention};
  \node[op, scale=0.7] (r1) at (0,10mm) {$+$};
  \node[nnlayer, minimum width=20mm] (n2) at (0,15mm) {LayerNorm};
  \node[nnlayer, minimum width=20mm] (ff) at (0,21mm) {FeedForward};
  \draw[flow] (0,-11mm) -- (n1); \draw[flow] (n1) -- (at); \draw[flow] (at) -- (r1);
  \draw[flow] (r1) -- (n2); \draw[flow] (n2) -- (ff);
  \draw[flowfaint, rounded corners=2pt] (0,-4.5mm) -- (-12mm,-4.5mm) |- (r1.west);
  \draw[flow] (ff.north) -- (0,32mm);
  \tokenrow{(-6.3mm,34mm)}{tokenvis}{4}{4.2mm}
  \draw[brace] (16mm,26mm) -- (16mm,-8mm) node[midway, right=5pt, tag] {$\times N$};
\end{tikzpicture}
```

## 7. Teacher and student (JEPA two-rail layout)

Two horizontal rails meeting at a latent loss on the right. Top rail: the context
encoder (the focal, trainable block) over visible tokens, then the predictor fed the
context and gold mask queries. Bottom rail: the EMA target encoder over the full input,
with stop-gradient. A gray dashed EMA arrow runs from student to teacher. Held-out
targets and mask tokens are the one gold; everything else is blue or gray. Name the
anti-collapse term explicitly when the method has one.

```latex
\begin{tikzpicture}[base]
  % top rail: context encoder over visible tokens -> predictor with mask queries
  \tokenrow{(0,12mm)}{tokenvis}{4}{4.2mm}
  \node[nnblock accent, minimum width=18mm] (fc) at (34mm,12mm) {$f_\theta$};
  \draw[nnarrow] (15mm,12mm) -- (fc);
  \tokenrow{(50mm,19mm)}{masktoken}{2}{4.2mm}
  \node[nnblock, minimum width=18mm] (g) at (70mm,12mm) {$g_\phi$};
  \draw[nnarrow] (fc) -- (g);
  \draw[nnarrow] (54.2mm,16.8mm) |- ([yshift=2mm]g.west);
  \node (yh) at (90mm,12mm) {$\hat{y}$};
  \draw[nnarrow] (g) -- (yh);
  % bottom rail: EMA target encoder over the full input, stop-gradient
  \tokenrow{(0,-6mm)}{token}{6}{4.2mm}
  \node[nnblock, minimum width=18mm] (ft) at (34mm,-6mm) {$f_\xi$};
  \draw[nnarrow] (23.5mm,-6mm) -- (ft);
  \node (y) at (90mm,-6mm) {$\mathrm{sg}(y)$};
  \draw[nnarrow] (ft) -- (y);
  % EMA weight copy, student -> teacher
  \draw[emaarrow] (fc.south) -- (ft.north) node[midway, right=2pt, tag] {EMA};
  % rails meet at the latent loss
  \node[op, minimum size=7mm] (L) at (104mm,3mm) {$\mathcal{L}$};
  \draw[flow] (yh) -| (L); \draw[flow] (y) -| (L);
\end{tikzpicture}
```

## 8. Mechanism inset: show the operation itself

A mechanism figure must make the mechanism obvious, never suggestive. For attention,
draw Q, K, V as labeled operands, the score as an operator, the output as its own node.
Add one small inset for the one component a reader cannot guess (for example a
relative-position bias indexed by the offset between two positions). A vague arrow labeled "attention" was rejected.

```latex
\begin{tikzpicture}[base, node distance=7mm]
  \node[var] (q) {$Q$};
  \node[var, below=of q] (k) {$K$};
  \node[var, below=of k] (v) {$V$};
  \node[op, minimum size=7mm, right=14mm of k] (s) {$\cdot$};
  \node[nnblock accent, right=10mm of s] (sm) {$\mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d}}+B\right)$};
  \node[op, minimum size=7mm, right=10mm of sm] (m) {$\times$};
  \node[var, right=10mm of m] (o) {out};
  \draw[flow] (q) -- (s); \draw[flow] (k) -- (s); \draw[flow] (s) -- (sm); \draw[flow] (sm) -- (m);
  \draw[flow] (v) -| (m); \draw[flow] (m) -- (o);
  % inset: the relative-position bias B, one cell per offset -3 .. 3
  \begin{scope}[shift={($(sm.north)+(-10mm,3mm)$)}]
    \foreach \x in {0,...,6}
      \pgfmathtruncatemacro{\t}{8-2*abs(\x-3)}
      \fill[ramp\t] (\x*3mm,0) rectangle ++(2.6mm,2.6mm);
    \node[tag, anchor=east] at (-1mm,1.3mm) {$B$};
  \end{scope}
\end{tikzpicture}
```

## 9. Scale spine (the Figure-1 overview)

A left-to-right row of `frame`d panels joined by `frustum` connectors, each panel a scaled
scope of real geometry: the whole domain as density, then resolved points, then one
point's neighborhood. One small title above the whole figure at most; near-zero other
text. `scripts/density_zoom.py` generates the full four-level version from a point field;
the skeleton:

```latex
\begin{tikzpicture}[base]
  \foreach \i/\x in {1/0, 2/4.35, 3/8.7} {
    \begin{scope}[shift={(\x,0)}, x=1.5cm, y=1.5cm]
      \fill[accent!8] (-1,-1) rectangle (1,1);
      \draw[frame] (-1,-1) rectangle (1,1);
      % \input{frag_L\i.tex}   <- generated geometry goes here
    \end{scope}}
  \draw[ink, line width=0.5pt] (0.3,-0.4) rectangle (0.9,0.2);   % zoom box on panel 1
  \draw[frustum] (0.9,0.2) -- (2.85,1.5);
  \draw[frustum] (0.9,-0.4) -- (2.85,-1.5);
  \node[ptitle, anchor=south] at ([yshift=2mm]current bounding box.north) {one field, three scales};
\end{tikzpicture}
```

## 10. kNN ego ball and partition tree

**Ego ball.** Center dot, thin ink spokes (`egospoke`, 0.45 pt) to about 6 neighbors, a
light gray ring (`egoring`, `black!22`), the label `$z_u$` beside the center with no
leader line (a pointer reads as a seventh edge). Neighbors keep their own category color.

```latex
\begin{tikzpicture}[base]
  \draw[egoring] (0,0) circle (0.95);
  \foreach \p in {(0.9,-0.08),(0.23,0.85),(-0.64,0.64),(-0.85,-0.31),(-0.27,-0.85),(0.6,-0.6)} {
    \draw[egospoke] (0,0) -- \p;
    \fill[accent] \p circle (1.1pt);}
  \fill[navy] (0,0) circle (1.5pt);
  \node[anchor=south west, inner sep=1pt] at (0.2,0.12) {$z_u$};   % no leader line
\end{tikzpicture}
```

**Partition tree.** Internal nodes `tnint` (circles), leaves `tnleaf` (rounded squares),
edges `tedge`, the traced address `tpath` with `tnpath` nodes, nodes filled by depth from
the ramp. Draw the spatial partition and its tree side by side to show that the partition
is a tree. Generate both from the real partition code (`scripts/tikz_emit.py`); a
hand-drawn tree and a hand-drawn partition that did not match the code were both
rejected.

## 11. Tabular-model glyphs

Suggested, not yet tested in real work: the grammar above covers tabular foundation
models with the same parts. A table is a grid of `token` cells; columns that are features
share one fill, the target column takes `contrast`, the query targets to predict take
`masktoken`, a missing feature value is a white cell with a dotted outline;
training rows and query rows are separated by a `frustum` rule; row attention and column
attention are drawn as `attn` edges along one axis each.

```latex
\begin{tikzpicture}[base]
  \foreach \r in {0,...,4} \foreach \cc in {0,...,3}
    \node[token] at (\cc*4.2mm,-\r*4.2mm) {};
  \foreach \r in {0,...,2} \node[token, fill=contrast, draw=contrast!80!black] at (4*4.2mm,-\r*4.2mm) {};
  \foreach \r in {3,4} \node[masktoken] at (4*4.2mm,-\r*4.2mm) {};
  \node[token, fill=paper, draw=mist, densely dotted] at (2*4.2mm,-1*4.2mm) {};
  \draw[frustum] (-3mm,-10.5mm) -- (20mm,-10.5mm);
  \node[tag, anchor=east] at (-3mm,-4.2mm) {train};
  \node[tag, anchor=east] at (-3mm,-14.7mm) {query};
\end{tikzpicture}
```
