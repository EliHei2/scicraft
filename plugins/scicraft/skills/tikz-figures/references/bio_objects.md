# Biological objects: proteins, molecules, cells, tissue

The biology tier of this skill: domain glyphs drawn in the same flat schematic style,
legible and stylized, never photorealistic. A glyph should read as "protein", "cell" or
"molecule" at a glance and sit beside the architecture and plot panels. For tissue
cartoons with characterful cells, segmentation vignettes and image underlays drawn on an
HTML canvas, use the `canvas-schematics` skill, or `tissue-figures` from the biology plugin.

Snippets go between the preamble and `\end{document}`. They need the figure-local fills
and the embedding-strip macro below; paste this block once, right after
`\begin{document}` (or before it, after the preamble's `\tikzset` blocks):

```latex
% biology fills (pale; pair with black strokes) and the per-node embedding strip
\definecolor{celldisk}{HTML}{D2DEEA}   % pale-blue population disk
\definecolor{celltint}{HTML}{A8C0D8}   % deeper cell-interior tint
\definecolor{ctrlgrey}{HTML}{E4E4E4}   % pale control disk
\definecolor{popgrey}{HTML}{B8B8B8}    % mid-grey population disk
\definecolor{cellfill}{HTML}{D5E2EE}   % cell interior, serif look
% \embedglyph{(coord)}{label}: segmented vertical bar standing for h_i
\newcommand{\embedglyph}[2]{%
  \begin{scope}[shift={#1}]
    \foreach \k/\v in {0/30,1/70,2/20,3/55}
      \fill[accent!\v!white] (0,\k*1.6mm) rectangle ++(1.6mm,1.4mm);
    \draw[ink, line width=0.3pt] (0,0) rectangle (1.6mm,4*1.6mm);
    \node[note, right=0.5mm] at (1.6mm,3.2mm) {#2};
  \end{scope}}
```

**Contents**
1. Protein cartoon ribbon (helix + sheet + loop + residues)
2. Skeletal molecule (ring + double bonds + substituents)
3. Cell (membrane, nucleus, organelles)
4. Protein-protein docking (two blobs + interface keypoints)
5. Multiplex marker grid (spatial proteomics channels)
6. H&E vs spatial-proteomics tiles
7. DNA double helix / sequence motif
8. UMAP / embedding scatter with clusters
9. Lab & diagnostic icons (slide, vial)
10. Population disk of cells
11. Real-vs-predicted outline (solid vs dashed, colorblind-safe)
12. Freeform organic boundary holding a multi-scale graph
13. Typed-edge legend keyed by line style
14. Protein-graph message passing (three relations)
15. Docking overlay with internal mesh + loss callout
16. Abstract-space axis tripod (floating population blobs)
17. Reusable boxed token (track one object across panels)
18. Styling notes
19. Embedding overlay: gray truth under, navy prediction over
20. Cell cartoon: observed against predicted $\mathcal{T}(x)$

---

## 1. Protein cartoon ribbon

Secondary-structure shorthand: a coil for an α-helix, a thick arrow for a β-sheet, a thin
line for the connecting loop, beads for residues.

```latex
\begin{tikzpicture}[base]
  % alpha helix (coil)
  \draw[accent, line width=2pt, decorate,
        decoration={coil, aspect=0.5, segment length=3mm, amplitude=2mm}] (0,0) -- (2,0);
  % beta sheet (thick arrow)
  \draw[contrast, line width=1pt, -{Stealth[length=3mm,width=4mm]}, fill=contrast!30] (2.3,0) -- (3.8,0);
  % connecting loop
  \draw[slate, line width=1pt] (3.8,0) to[out=0,in=180] (4.6,0.5);
  % residue beads
  \foreach \x in {4.6,4.9,5.2} \fill[accentL] (\x,0.5) circle (1.5pt);
\end{tikzpicture}
```

For a multi-scale protein graph, draw residue beads and connect with a
mix of "primary" (solid) and "tertiary" (dashed) edges; see §13 below and §2 of
`graphs_geometry.md`.

## 2. Skeletal molecule

A clean aromatic ring with double bonds (parallel inner strokes) and labeled substituents.
The inner-stroke trick: shrink each ring edge slightly, then pull it toward the ring center
with `calc`.

```latex
\begin{tikzpicture}[base, atom/.style={font=\figM, inner sep=1pt}]
  \foreach \i in {0,...,5} \coordinate (a\i) at (\i*60+30:9mm);
  \coordinate (ctr) at (0,0);
  \draw[ink, line width=0.9pt] (a0)--(a1)--(a2)--(a3)--(a4)--(a5)--cycle;
  % double-bond inner strokes on alternating edges
  \foreach \i/\j in {0/1,2/3,4/5} {
    \draw[ink, line width=0.9pt]
      ($($(a\i)!0.15!(a\j)$)!0.16!(ctr)$) -- ($($(a\j)!0.15!(a\i)$)!0.16!(ctr)$);
  }
  % substituents, pointing clear of the ring
  \draw[ink, line width=0.9pt] (a0) -- ++(0.7,0.4)  node[atom, right]{Cl};
  \draw[ink, line width=0.9pt] (a5) -- ++(0.7,-0.4) node[atom, right]{OH};
  \draw[ink, line width=0.9pt] (a3) -- ++(-0.7,0)   node[atom, left]{N};
\end{tikzpicture}
```

Atoms are unlabeled carbons by convention; only heteroatoms (N, O, Cl, …) get text.

## 3. Cell (membrane, nucleus, organelles)

A soft wobbly membrane, a flat-filled nucleus with a hard edge, scattered organelle dots.

```latex
\begin{tikzpicture}[base]
  \draw[black, line width=1pt, fill=accentL!8]
    plot[smooth cycle, tension=0.8]
    coordinates {(-1.3,0)(-0.4,1.0)(0.9,1.1)(1.4,0.1)(0.8,-1.0)(-0.6,-1.0)};
  \draw[black, line width=0.6pt, fill=accent!30] (0.1,0.05) circle (5mm);
  \foreach \x/\y in {-0.7/0.4, 0.8/-0.5, -0.5/-0.5} \fill[contrast!70] (\x,\y) circle (1.3pt);
\end{tikzpicture}
```

**True-black stroke on hand-drawn bio glyphs.** Outline cells/blobs with `draw=black`, not
`ink`: pure black is the usual journal stroke for organic glyphs, and the pale
fills below (`celldisk`, `celltint`) only read with a hard edge. Keep `ink` for axes and
architecture boxes; the contrast between the two stroke colors is deliberate, not an
inconsistency.

A tissue patch = several such cells tiled with slight size/position jitter (§10), or simply
many nuclei (flat circles) scattered on a pale background.

## 4. Protein-protein docking

Two complementary blobs meeting at an interface, with matched keypoints bridged by dashed
lines.

```latex
\begin{tikzpicture}[base]
  \draw[slate, line width=1pt, fill=cloud]
    plot[smooth cycle, tension=0.8]
    coordinates {(-1.6,0)(-0.9,0.9)(0.1,0.7)(0.3,-0.2)(-0.5,-0.9)(-1.5,-0.7)};
  \draw[accent!70!black, line width=1pt, fill=accent!12]
    plot[smooth cycle, tension=0.8]
    coordinates {(0.6,0.2)(1.3,0.8)(2.2,0.4)(2.1,-0.5)(1.2,-0.7)(0.7,-0.2)};
  \foreach \y in {0.3,-0.1,-0.4} {
    \fill[contrast] (0.2,\y) circle (1.3pt); \fill[contrast] (0.65,\y) circle (1.3pt);
    \draw[contrast, line width=0.4pt, dashed] (0.2,\y)--(0.65,\y);
  }
\end{tikzpicture}
```

This is the compact version; for the full docking panel (interior mesh + red keypoints +
a bent leader to a loss callout) see §15.

## 5. Multiplex marker grid

A grid of small tiles in graded intensities of one hue, "markers" / channels in a spatial
proteomics panel.

```latex
\begin{tikzpicture}[base]
  \foreach \i in {0,1,2} \foreach \j in {0,1,2} {
    \pgfmathsetmacro{\v}{20+25*mod(\i+\j,3)+10*\i}
    \fill[accent!\v!white] (\i*7mm,\j*7mm) rectangle ++(6mm,6mm);
  }
  \node[note, below=1mm] at (1cm,0) {markers};
\end{tikzpicture}
```

## 6. H&E vs spatial-proteomics tiles

Contrasting the cheap routine stain (warm, diffuse) against the rich multi-channel assay
(structured grid).

```latex
\begin{tikzpicture}[base]
  % H&E: warm tile with scattered nuclei
  \fill[contrast!18] (0,0) rectangle (1.4,1.4);
  \pgfmathsetseed{3}
  \foreach \k in {1,...,30} {
    \pgfmathsetmacro{\px}{0.1+1.2*rnd}\pgfmathsetmacro{\py}{0.1+1.2*rnd}
    \fill[slate!50, opacity=0.5] (\px,\py) circle (1.2pt);
  }
  \node[note, below=1mm] at (0.7,0) {H\&E};
  % SP: structured multi-channel grid
  \begin{scope}[xshift=2cm]
    \foreach \i in {0,1,2} \foreach \j in {0,1,2} {
      \pgfmathsetmacro{\v}{25+22*mod(\i+2*\j,3)}
      \fill[accentL!\v!white] (\i*4.7mm,\j*4.7mm) rectangle ++(4.2mm,4.2mm);
    }
    \node[note, below=1mm] at (0.7,0) {spatial proteomics};
  \end{scope}
\end{tikzpicture}
```

## 7. DNA double helix / sequence

Two anti-phase sine strands with base-pair rungs. For a sequence motif, instead place
letters `A C G T` in colored boxes along a line.

```latex
\begin{tikzpicture}[base]
  \draw[accent, line width=1.2pt, domain=0:4, samples=80, smooth] plot (\x, {0.4*sin(deg(3*\x))});
  \draw[contrast,  line width=1.2pt, domain=0:4, samples=80, smooth] plot (\x, {0.4*sin(deg(3*\x)+180)});
  \foreach \x in {0.3,0.8,...,3.8}
    \draw[slate, line width=0.5pt] (\x,{0.4*sin(deg(3*\x))}) -- (\x,{0.4*sin(deg(3*\x)+180)});
\end{tikzpicture}
```

Sequence-as-boxes:

```latex
\begin{tikzpicture}[base, baseB/.style={minimum size=5mm, draw=none, font=\figM\bfseries, text=white}]
  \foreach \i/\b/\c in {0/A/accent, 1/C/contrast, 2/G/accentL, 3/T/contrast, 4/A/accent} {
    \node[baseB, fill=\c] at (\i*5.5mm,0) {\b};
  }
\end{tikzpicture}
```

## 8. UMAP / embedding scatter with clusters

Low-dimensional embedding colored by cluster, the staple of single-cell papers. Each
cluster is jittered points in one hue. (Set a seed for reproducibility.)

```latex
\begin{tikzpicture}[base]
  \pgfmathsetseed{11}
  \foreach \cx/\cy/\col in {0/0/accent, 2.2/0.6/contrast, 1.2/-1.6/accentL} {
    \foreach \k in {1,...,14} {
      \pgfmathsetmacro{\px}{\cx+0.45*rand}\pgfmathsetmacro{\py}{\cy+0.45*rand}
      \fill[\col, opacity=0.75] (\px,\py) circle (1pt);
    }
  }
\end{tikzpicture}
```

To add a soft hull, overlay a faint `plot[smooth cycle]` through the cluster's outer points
with `fill=<col>!10, draw=<col>!40`.

## 9. Lab & diagnostic icons

Minimal glyphs for a method/clinical pipeline (pair with the overview figure in
`architectures.md`).

```latex
\begin{tikzpicture}[base]
  % microscope slide
  \draw[ink, line width=0.8pt, fill=cloud, rounded corners=1pt] (0,0) rectangle (1.6,0.5);
  \fill[contrast!40] (1.15,0.25) circle (2.2pt);
  \node[note, below=1mm] at (0.8,0) {slide};
  % vial
  \begin{scope}[xshift=2.4cm]
    \draw[ink, line width=0.8pt] (0,0.7) -- (0,0.1) arc (180:360:3.5mm) -- (0.7,0.7);
    \fill[accent!30] (0,0.1) arc (180:360:3.5mm) -- (0.7,0.35) -- (0,0.35) -- cycle;
    \draw[ink, line width=0.8pt] (-0.08,0.7) rectangle (0.78,0.82);
    \node[note, below=1mm] at (0.35,0) {sample};
  \end{scope}
\end{tikzpicture}
```

## 10. Population disk of cells

The atomic unit of perturbation panels: a pale `celldisk` territory holding many jittered,
wobbly cell glyphs, a fraction in the deeper `celltint`, each with a nucleus hint. Pure
`black` strokes (§3). Place glyphs in polar coordinates with radius `1.5*sqrt(rnd)` so the
fill is uniform over the disk area, not bunched at the center.

```latex
\begin{tikzpicture}[base]
  \fill[celldisk] (0,0) circle (1.9cm);
  \draw[black, line width=0.8pt] (0,0) circle (1.9cm);
  \pgfmathsetseed{7}
  \foreach \k in {1,...,22}{
    \pgfmathsetmacro{\rr}{1.5*sqrt(rnd)}            % area-uniform radius (<=1.5cm: stays inside)
    \pgfmathsetmacro{\th}{360*rnd}
    \pgfmathsetmacro{\cx}{\rr*cos(\th)}\pgfmathsetmacro{\cy}{\rr*sin(\th)}
    \pgfmathsetmacro{\s}{0.28+0.10*rnd}             % per-cell size jitter
    \pgfmathsetmacro{\hot}{rnd}                      % ~30% of cells get the deeper tint
    \begin{scope}[shift={(\cx,\cy)}, scale=\s]
      \draw[black, line width=0.5pt,
            fill={\ifdim\hot pt>0.7pt celltint\else celldisk!55!white\fi}]
        plot[smooth cycle, tension=0.85]
        coordinates {(-1,0)(-0.35,0.85)(0.7,0.8)(1,-0.05)(0.5,-0.85)(-0.55,-0.8)};
      \fill[black!55] (0.05,0.05) circle (0.28);    % nucleus hint
    \end{scope}}
\end{tikzpicture}
```

The `\ifdim\hot pt>0.7pt` test reads the random draw as a length to pick the tint, a
fraction of cells become `celltint`, the rest a near-white wash, so the disk reads as a
heterogeneous population, not a uniform stipple. For a control-vs-treated pair, draw a
second disk on `ctrlgrey`/`popgrey` (the neutral population fills) beside it.

## 11. Real-vs-predicted outline

Encode real vs predicted by *line style*, not hue, so the contrast survives grayscale and
colorblind print. Same shape, jittered: solid black = observed, dashed black = predicted.

```latex
\begin{tikzpicture}[base]
  % observed cell: solid black outline, pale fill
  \draw[black, line width=1pt, fill=celldisk]
    plot[smooth cycle, tension=0.8]
    coordinates {(-1.3,0)(-0.4,1.0)(0.9,1.05)(1.35,0.05)(0.75,-1.0)(-0.6,-1.0)};
  % predicted cell: SAME shape jittered, dashed black outline, no fill
  \draw[black, line width=1pt, dashed]
    plot[smooth cycle, tension=0.8]
    coordinates {(-1.15,0.08)(-0.3,1.12)(1.05,1.0)(1.5,0.12)(0.82,-0.88)(-0.45,-0.92)};
  \node[note, align=left, right=2mm] at (1.5,0.4)
    {\rule[0.3ex]{4mm}{0.9pt}~observed\\
     \rule[0.3ex]{1.2mm}{0.9pt}\,\rule[0.3ex]{1.2mm}{0.9pt}~predicted};
\end{tikzpicture}
```

The mini frameless legend uses two `\rule`s (solid bar, two short bars) to mirror the line
styles. Keep both outlines the same color; the only signal is solid-vs-dashed.

## 12. Freeform organic boundary holding a multi-scale graph

A heavy (~2.2pt) `plot[smooth cycle]` territory, a protein domain or tissue region, with a
local graph living inside it. Roughen the cycle with `decorations.pathmorphing`'s
`random steps` for a hand-drawn organic edge. Lay interior nodes on a jittered grid so the
`esecondary` (kNN) edges stay short and never cross the disk; cross-link
`multiscale_density_zoom.md`.

```latex
\begin{tikzpicture}[base]
  % heavy freeform territory boundary (protein domain / tissue region)
  \draw[black, line width=2.2pt, fill=cloud,
        decoration={random steps, segment length=4mm, amplitude=0.4mm}, decorate]
    plot[smooth cycle, tension=0.7]
    coordinates {(-1.9,0.2)(-0.9,1.5)(0.8,1.6)(2.0,0.5)(1.7,-1.0)(0.2,-1.6)(-1.3,-1.1)};
  % a local graph inside: nodes on a jittered grid so kNN edges stay short
  \pgfmathsetseed{6}
  \foreach \i in {0,1,2,3} \foreach \j in {0,1,2}{
    \pgfmathsetmacro{\jx}{0.16*rand}\pgfmathsetmacro{\jy}{0.16*rand}
    \coordinate (n\i\j) at ({-1.2+0.8*\i+\jx},{-0.9+0.85*\j+\jy});}
  \foreach \i in {0,1,2} \foreach \j in {0,1,2}        % right neighbors
    \draw[esecondary] (n\i\j)--(n\the\numexpr\i+1\relax\j);
  \foreach \i in {0,1,2,3} \foreach \j in {0,1}        % up neighbors
    \draw[esecondary] (n\i\j)--(n\i\the\numexpr\j+1\relax);
  \foreach \i in {0,1,2,3} \foreach \j in {0,1,2} \fill[accent!70] (n\i\j) circle (1.6pt);
\end{tikzpicture}
```

Drop `random steps` for a smooth membrane; raise its `amplitude` for a more ragged
silhouette. The `\the\numexpr\i+1\relax` idiom indexes the neighbor in the `\foreach`.

## 13. Typed-edge legend keyed by line style

Three or four edge *meanings* (tree vs kNN vs cross-scale vs interior mesh) distinguished by
line style in one ink color. Uses the preamble's `eprimary` /
`esecondary` / `econnect` / `emesh`. Color is *not* the channel here; the line style is.

```latex
\begin{tikzpicture}[base, row/.style={anchor=west, font=\figM, text=ink}]
  \foreach \y/\sty/\lab in {%
      0/eprimary/{tree edge (parent--child)},
      1/esecondary/{$k$NN edge (leaf neighborhood)},
      2/econnect/{cross-scale connector},
      3/emesh/{interior mesh}}{
    \draw[\sty] (0,-\y*6mm) -- (1.1,-\y*6mm);
    \node[row] at (1.3,-\y*6mm) {\lab};
  }
\end{tikzpicture}
```

`emesh` is the one light-blue exception (it must recede behind nodes); the other three are
ink. If the figure is GNN-framed rather than bio-framed, the same trio is also documented in
§2 of `graphs_geometry.md`.

## 14. Protein-graph message passing (three relations)

Three edge relations on a protein graph, each its own *style+hue*: `structedge` (solid ink)
= graph backbone, `msg` (dashed contrast arrow) = aggregated message into a focal residue,
`attn` (dotted light-blue) = cross-graph attention to a partner (the docking case).
The `\embedglyph` macro draws the per-node embedding strip $h_i$.

```latex
\begin{tikzpicture}[base]
  % residue graph of one protein
  \foreach \k/\x/\y in {1/0/0, 2/1.1/0.5, 3/1.0/-0.7, 4/2.1/0.0, 5/2.0/-1.1}
    \node[circle, fill=accent!70, inner sep=2pt] (r\k) at (\x,\y) {};
  \foreach \a/\b in {1/2,1/3,2/4,3/4,4/5} \draw[structedge] (r\a)--(r\b);   % structure
  \foreach \a in {2,3,5} \draw[msg] (r\a) to[bend left=12] (r4);            % message into r4
  \node[note, below=1mm] at (r5.south) {protein};
  % partner protein
  \foreach \k/\x/\y in {1/3.4/0.3, 2/4.4/0.8, 3/4.5/-0.5}
    \node[circle, fill=contrast!80, inner sep=2pt] (s\k) at (\x,\y) {};
  \foreach \a/\b in {1/2,1/3,2/3} \draw[structedge] (s\a)--(s\b);
  \node[note, below=1mm] at (s3.south) {partner};
  % cross-graph attention
  \draw[attn] (r4)--(s1); \draw[attn] (r4)--(s3);
  % per-node embedding strip on the focal residue
  \embedglyph{(0.1,1.0)}{$h_i$}
\end{tikzpicture}
```

Three relations is the ceiling: one saturated accent (`msg` contrast), one structural ink
(`structedge`), one desaturated tint (`attn`). A fourth relation would need a fourth style,
which starts to read as noise, fold it into the legend (§13) instead.

## 15. Docking overlay with internal mesh + loss callout

The full docking panel: two complementary blob silhouettes, a thin light-gray triangular
mesh inside the receptor, red interface keypoints bridged across the gap, and a bent black
leader to a borderless `callout` carrying the interface loss. The mesh is a jittered grid
plus its diagonals (grid edges + one diagonal per cell ⇒ triangles); `emesh` keeps it faint.

```latex
\begin{tikzpicture}[base]
  % receptor blob with interior triangular mesh
  \draw[black, line width=1.4pt, fill=celldisk]
    plot[smooth cycle, tension=0.8]
    coordinates {(-2.0,0)(-1.3,1.1)(-0.1,0.9)(0.2,-0.1)(-0.6,-1.1)(-1.8,-0.9)};
  \pgfmathsetseed{5}
  \foreach \i in {0,1,2} \foreach \j in {0,1,2}{
    \pgfmathsetmacro{\jx}{0.10*rand}\pgfmathsetmacro{\jy}{0.10*rand}
    \coordinate (m\i\j) at ({-1.5+0.55*\i+\jx},{-0.55+0.6*\j+\jy});}
  \foreach \i in {0,1} \foreach \j in {0,1,2} \draw[emesh] (m\i\j)--(m\the\numexpr\i+1\relax\j);
  \foreach \i in {0,1,2} \foreach \j in {0,1} \draw[emesh] (m\i\j)--(m\i\the\numexpr\j+1\relax);
  \foreach \i in {0,1} \foreach \j in {0,1}                                  % diagonals -> triangles
    \draw[emesh] (m\i\j)--(m\the\numexpr\i+1\relax\the\numexpr\j+1\relax);
  % ligand blob, complementary
  \draw[accent!70!black, line width=1.4pt, fill=accent!12]
    plot[smooth cycle, tension=0.8]
    coordinates {(0.7,0.3)(1.4,1.0)(2.6,0.6)(2.6,-0.5)(1.5,-0.9)(0.6,-0.3)};
  % red interface keypoints on the facing edges, bridged across the gap
  \foreach \y in {0.3,-0.05,-0.4}{
    \fill[contrast] (0.16,\y) circle (1.6pt); \fill[contrast] (0.66,\y) circle (1.6pt);
    \draw[contrast, line width=0.5pt, dashed] (0.16,\y)--(0.66,\y);}
  % bent black leader to a borderless loss callout
  \draw[black, line width=0.6pt, -{Stealth[length=2mm]}]
    (0.4,-0.55) to[bend right=20] (1.7,-1.7);
  \node[callout] at (2.5,-1.7) {$\mathcal{L}_{\mathrm{int}}$};
\end{tikzpicture}
```

`contrast` (not `contrast`) is the right hue for the keypoints, it is the focal-coupling red and
reads as "this is the thing being matched." Cross-link `math_layout.md` for the callout.

## 16. Abstract-space axis tripod

For an abstract n-dim latent space: three thin `slate` rays from a shared origin, with named
population blobs floating in it. Size each blob node
to its label so the text never overflows the disk.

```latex
\begin{tikzpicture}[base]
  \draw[slate, line width=0.6pt, ->] (0,0) -- (-1.4,-0.9) node[note, below left=-1mm]{$z_1$};
  \draw[slate, line width=0.6pt, ->] (0,0) -- (2.2,-0.2)  node[note, right]{$z_2$};
  \draw[slate, line width=0.6pt, ->] (0,0) -- (0.2,2.0)   node[note, above]{$z_3$};
  \node[circle, fill=celldisk, minimum size=12mm, font=\figS, text=ink]   at (0.6,1.1) {ctrl};
  \node[circle, fill=celltint, minimum size=12mm, font=\figS, text=white] at (1.5,0.35){treated};
\end{tikzpicture}
```

The rays are not orthographic axes; they are a *suggestion* of dimensionality, kept thin and
gray so the blobs dominate. A small snippet, it may live in `graphs_geometry.md` instead if
the figure is graph-centric.

## 17. Reusable boxed token

Box one object once with `token` and reuse the identical box as a pipeline node *and* inline
in the objective, so the reader tracks a single entity across panels.
`token` takes the fill as its argument (`chip=celldisk`); the default is `accent!15`.

```latex
\begin{tikzpicture}[base]
  % same boxed token as a pipeline node ...
  \node[chip=celldisk] (cell) {cell $x$};
  \node[block, right=12mm of cell] (enc) {encoder};
  \node[chip=accent!15, right=12mm of enc] (z) {$z$};
  \draw[flow] (cell)--(enc); \draw[flow] (enc)--(z);
  % ... and the SAME token reused inline in the objective
  % (override minimum size + anchor on (t.base) so it sits on the math baseline)
  \node[note, below=10mm of enc, align=center]
    {minimize $\;\bigl\|\;$%
      \tikz[baseline=(t.base)]{\node[chip=accent!15, inner sep=1.5pt,
        minimum size=0pt, font=\figM] (t) {$z$};}%
      $\; -\; z^{\star}\;\bigr\|_2^2$};
\end{tikzpicture}
```

The inline copy needs `minimum size=0pt` and a `baseline=(t.base)` anchor; the default
`token` is sized for a node (5mm) and would otherwise drop below the math line. Cross-link
`math_layout.md`.

## 18. Styling notes

- **Stylize, don't render.** A protein is a coil + arrow, not a PDB cartoon. A cell is a
  wobbly blob + a flat circle. Legibility beats realism; these glyphs must survive being
  printed at 3 cm wide.
- **Black strokes on bio glyphs.** Hand-drawn cells/blobs take `draw=black` (§3), not `ink`;
  the pale `celldisk`/`celltint` fills need the hard edge. `ink` stays for axes/architecture.
- **Smooth blobs**: `plot[smooth cycle, tension=0.7 to 0.9]` through 5 to 7 coordinates. More
  points = lumpier; fewer = rounder. Roughen a territory boundary with `random steps` (§12).
- **Flat interiors**: a nucleus is a flat fill with a hard edge (`fill=accent!30`, a thin black stroke).
  Radial `\shade` is kept for one density blob per figure (`themes.md`).
- **Encode contrast by line style, not just hue** (§11): solid vs dashed for real vs
  predicted survives grayscale and colorblind print. Reserve hue for the focal accent.
- **Three relations is the ceiling** (§14): one saturated accent + one structural ink + one
  desaturated tint. More relations belong in a typed-edge legend (§13), keyed by line style.
- **Reproducibility**: `rand`/`rnd` reseed every compile, call `\pgfmathsetseed{N}` before
  scatter loops (§10, §12, §15), or hard-code coordinates for a figure you'll keep.
- **Keep the palette**: tissue/markers in tints of one hue; reserve a second hue for the
  contrasting modality. Don't rainbow the channels. Population fills are `celldisk`,
  `celltint`, `ctrlgrey`, `popgrey`; the focal interface red is `contrast`.
- **Decoration libraries** used here (`coil`, `random steps`) come from
  `decorations.pathmorphing`, already loaded in the preamble.
- **Serif look** (sections 19 and 20): glyphs outlined in `navy` on `cellfill`,
  observed against predicted as solid against dashed `navy`, marker dots `navy` plus one
  `contrast` for the contrasting state, embedding results as the frameless
  gray-under, navy-over overlay.

---

## 19. Embedding overlay: gray truth under, navy prediction over

A results idiom for perturbation and prediction panels. Each tile is unframed (no box, no
numeric ticks) with a lower-left L-glyph of two short arrows (`UMAP 1`, `UMAP 2`) standing
in for axes. Light-gray truth (`truth`) is drawn first, underneath; navy predictions last,
on top. Quality reads as "does navy cover grey", so the layer order carries the meaning.
The contrast is not used for scatter dots here. A small-multiple grid puts one model per
column (a `ptitle` and a small `note` below it) and one condition per rotated row, with a
shared two-dot legend at the right. The scatter here is seeded noise; a real panel plots
the embedding coordinates from the records.

```latex
\begin{tikzpicture}
  % --- one tile: grey truth UNDER, navy prediction OVER, NO axis box -------
  \newcommand{\umaptile}[3]{% #1=(origin) #2=title #3=sublabel
    \begin{scope}[shift={#1}]
      \pgfmathsetseed{4}
      % "Data" / measured cells -- light grey, drawn FIRST (underneath)
      \foreach \cx/\cy in {0.55/0.95, 1.25/0.55, 0.95/1.45}
        \foreach \k in {1,...,26}{
          \pgfmathsetmacro{\px}{\cx+0.30*rand}\pgfmathsetmacro{\py}{\cy+0.30*rand}
          \fill[truth, opacity=0.6] (\px,\py) circle (1pt);}
      % "Predictions" -- navy, drawn LAST (on top); read quality as navy covering grey
      \foreach \cx/\cy in {0.55/0.95, 1.25/0.55, 0.95/1.45}
        \foreach \k in {1,...,26}{
          \pgfmathsetmacro{\px}{\cx+0.28*rand}\pgfmathsetmacro{\py}{\cy+0.28*rand}
          \fill[navy, opacity=0.55] (\px,\py) circle (1pt);}
      % corner L-glyph instead of a frame (UMAP-1 horizontal, UMAP-2 vertical)
      \draw[ink,->,>={Stealth[length=1.6mm]}] (0,0) -- (0,0.7)
        node[above left=-1mm, rotate=90, font=\figS]{UMAP 2};
      \draw[ink,->,>={Stealth[length=1.6mm]}] (0,0) -- (0.7,0)
        node[right, font=\figS]{UMAP 1};
      % column header: centered bold-serif title + small grey sub-label
      \node[ptitle, font=\bfseries] at (1.0,2.3) {#2};
      \node[note, align=center] at (1.0,2.05) {#3};
    \end{scope}}
  \umaptile{(0,0)}{Model A}{identity init.}
  \umaptile{(3.2,0)}{Observed}{measured}
  % shared legend at right: two dots, Data (grey) then Predictions (navy)
  \begin{scope}[shift={(6.6,1.0)}]
    \fill[truth] (0,0.3) circle (1.6pt); \node[anchor=west, font=\figM] at (0.25,0.3) {Data};
    \fill[navy]  (0,0)   circle (1.6pt); \node[anchor=west, font=\figM] at (0.25,0)   {Predictions};
  \end{scope}
\end{tikzpicture}
```

For a full grid, wrap `\umaptile` in a column `\foreach` and add a rotated row label at
the left of each row. For embedding maps from real models (aligned colors across runs,
several resolutions) use the `embedding-maps` skill.

## 20. Cell cartoon: observed against predicted $\mathcal{T}(x)$

A concept-figure cell glyph: an irregular blob outlined in `navy` and filled `cellfill`.
Solid outline means observed; the same shape jittered with a dashed outline means the
predicted $\mathcal{T}(x)$, so the contrast survives grayscale. One to three marker dots
sit inside (`navy`, plus exactly one `contrast` for the contrasting state). A pale
`accentL` halo on the background layer groups the population. The learned map is a tiny
inline network glyph captioned $\mathcal{T}_\theta$; the example trajectory is one thick
black arc (the `spine` weight); a dotted rectangle marks a measurement snapshot.

```latex
\begin{tikzpicture}
  % --- soft pale halo grouping the OBSERVED population (drawn first, behind) -
  \begin{scope}[on background layer]
    \fill[accentL, opacity=0.45] (0.1,0.05) circle (1.25cm);
  \end{scope}
  % --- observed cell: SOLID navy outline, pale cellfill fill, marker dots ---
  \draw[navy, line width=1pt, fill=cellfill]
    plot[smooth cycle, tension=0.8]
    coordinates {(-0.95,0)(-0.3,0.78)(0.66,0.8)(1.0,0.05)(0.55,-0.78)(-0.45,-0.74)};
  \fill[navy] (-0.15,0.18) circle (1.5pt);     % 1-3 small solid marker dots inside
  \fill[contrast]  ( 0.35,-0.1) circle (1.5pt);     % one red marker = the contrasting state
  \node[note, below=1mm] at (0.1,-0.85) {observed};
  % --- the learned map T_theta as a tiny inline neural-net glyph -------------
  \begin{scope}[shift={(2.05,0.05)}]
    \foreach \y in {-0.28,0,0.28} \fill[navy] (0,\y) circle (1.1pt);     % input layer
    \foreach \y in {-0.18,0.18}   \fill[navy] (0.4,\y) circle (1.1pt);   % hidden layer
    \foreach \sy in {-0.28,0,0.28} \foreach \ty in {-0.18,0.18}
      \draw[annot, line width=0.4pt] (0,\sy)--(0.4,\ty);
    \node[font=\figL] at (0.2,-0.6) {$\mathcal{T}_\theta$};
  \end{scope}
  % --- thick black "path" Bezier arc: the example developmental trajectory ---
  \draw[ink, line width=1.6pt, ->, >={Stealth[length=2.6mm,width=2.2mm]}]
    (1.05,0.25) to[out=25,in=155] (3.35,0.25);
  % --- predicted cell T(x): SAME shape jittered, DASHED navy outline, no fill -
  \begin{scope}[shift={(4.3,0)}]
    \draw[navy, line width=1pt, dashed]
      plot[smooth cycle, tension=0.8]
      coordinates {(-0.92,0.06)(-0.26,0.84)(0.72,0.78)(1.05,0.1)(0.5,-0.72)(-0.5,-0.78)};
    \fill[navy] (-0.1,0.22) circle (1.5pt);
    \fill[contrast]  ( 0.4,-0.05) circle (1.5pt);
    % a dotted rectangle = a "measurement snapshot" of the predicted state
    \draw[densely dotted, ink, line width=0.7pt] (-1.15,-1.05) rectangle (1.3,1.05);
    \node[note, below=1mm] at (0.05,-1.15) {predicted $\mathcal{T}(x)$};
  \end{scope}
  % mini frameless legend: solid bar = observed, dashed bars = predicted
  \node[font=\figM, text=ink, align=left, anchor=west] at (5.9,0.2)
    {\textcolor{navy}{\rule[0.3ex]{4mm}{0.9pt}}~observed\\
     \textcolor{navy}{\rule[0.3ex]{1.2mm}{0.9pt}\,\rule[0.3ex]{1.2mm}{0.9pt}}~predicted};
\end{tikzpicture}
```

The halo goes `on background layer` so it never occludes the cell or its dots.
For a source/target population of these glyphs use the two-tone dot rule (dark
`navy` source, `accentMd` target); for the
transport between two populations, the thick black arc here is the same spine as
the curved transport arrow in `distributions_fields.md`.