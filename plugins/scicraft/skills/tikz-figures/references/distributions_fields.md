# Distributions, densities, fields, OT & trajectories

The signature imagery of this corpus: Gaussian blobs, density contours, loss landscapes,
optimal-transport couplings, and flow trajectories between point clouds. Uses `base` for
schematic versions and `spare axis` / pgfplots for quantitative ones. Snippets go between
the preamble and `\end{document}`.

**Contents**
1. 1D Gaussian / mixture curve
2. 2D Gaussian blob (radial shading) and a mixture of blobs
3. Density contours (concentric, schematic)
4. Loss-landscape contours (pgfplots `contour gnuplot` alternative: hand-drawn)
4b. Flat versus sharp minima with the stationary mass drawn
5. 3D loss surface (pgfplots `surf`)
6. Point cloud (scattered particles)
7. Optimal-transport coupling between two point clouds
7b. OT coupling: magnitude-by-saturation + Wasserstein-cost double arrow
8. Trajectory / flow between snapshots (population dynamics)
8b. Trajectory overlay (predicted solid, observed gray dotted)
8c. Single-hue ordinal lightness ramp (time is not a categorical series)
9. Vector field / gradient field
9b. Learned-potential filled contour + colorbar; streamline field
10. SDE / sample paths
11. Equation callout attached to a schematic (borderless soft fill)
12. Styling notes
13. Serif-look transport recipes
   13.1 Two-tone dot distribution (source $\mu_0$ navy / target $\mu_1$ `accentMd`)
   13.2 Gray vector-field grid $v(t,\cdot)$ with alpha-falloff
   13.3 Thick black curved transport arrow + riding $\mu_t$ label
   13.4 Gray wiggly Brownian / Schrödinger cloud + one highlighted navy path
   13.5 Blues energy/density landscape (flat bands + down-gradient arrow)
   13.6 Equation pinned to the TOP, geometry as its visual restatement
   13.7 Canonical worked template: the dynamic-OT panel, end to end

---

## 1. 1D Gaussian / mixture

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={$x$}, ylabel={$p(x)$}, ymin=0,
             domain=-4:6, samples=120, axis y line=none]
  \addplot[accent, line width=1pt] {exp(-(x)^2/2)/sqrt(2*pi)};
  \addplot[contrast, line width=1pt, dashed] {exp(-(x-2.5)^2/(2*0.6))/sqrt(2*pi*0.6)};
\end{axis}
\end{tikzpicture}
```

A two-component mixture: add the components or plot the sum
`{0.5*exp(...) + 0.5*exp(...)}` as a filled curve with `\closedcycle` and
`fill=accent!12`.

## 2. 2D Gaussian blob and a mixture

Radial shading gives the soft "density" look without a real contour solver. Use it for one blob per figure;
the components of a mixture are flat fills at low opacity.

```latex
\begin{tikzpicture}[base]
  % single blob
  \shade[inner color=accent!55, outer color=accent!3] (0,0) circle (12mm);
  % a mixture: flat overlapping blobs in muted hues
  \begin{scope}[xshift=40mm]
    \fill[accent!45,   fill opacity=0.45] (-3mm,2mm) circle (9mm);
    \fill[contrast!45, fill opacity=0.45] (6mm,-2mm) circle (7mm);
    \fill[accentL!80,  fill opacity=0.55] (2mm,7mm) circle (6mm);
  \end{scope}
\end{tikzpicture}
```

## 3. Density contours (schematic, concentric)

When you want "a distribution" as line contours rather than fill. Wobble the rings
slightly with `plot[smooth cycle]` for an organic look.

```latex
\begin{tikzpicture}[base]
  \foreach \r/\o in {14/20, 10/40, 6/65, 3/90} {
    \draw[accent!\o!white, line width=0.8pt]
      plot[smooth cycle, tension=0.8] coordinates
      {({-\r*0.1},{\r*0.09}) ({\r*0.11},{\r*0.07}) ({\r*0.09},{-\r*0.1}) ({-\r*0.08},{-\r*0.08})};
  }
  \fill[accent] (0,0) circle (0.6pt); % mode
\end{tikzpicture}
```

## 4. Loss-landscape contours

For a controlled, repeatable landscape, hand-draw nested closed curves around two basins
(a wide/flat one and a narrow/sharp one, directly evoking flat-vs-sharp minima).

```latex
\begin{tikzpicture}[base]
  % flat (wide) basin on the left — widely spaced rings
  \foreach \s/\o in {1.4/15, 1.0/30, 0.6/50, 0.3/70} {
    \draw[accent!\o!white, line width=0.7pt]
      (-2.2,0) ellipse ({\s*1.1} and {\s*0.9});
  }
  \node[note] at (-2.2,-1.5) {flat minimum};
  % sharp (narrow) basin on the right — tightly spaced rings
  \foreach \s/\o in {1.4/15, 1.0/30, 0.6/50, 0.3/70} {
    \draw[contrast!\o!white, line width=0.7pt]
      (2.2,0) ellipse ({\s*0.5} and {\s*1.3});
  }
  \node[note] at (2.2,-1.7) {sharp minimum};
\end{tikzpicture}
```

## 4b. Flat versus sharp minima with the stationary mass drawn

Two basins of equal depth but different sharpness, with the stationary density of the
optimizer drawn as a scatter that is heavy in the flat basin and sparse in the sharp one.
When the claim is about where the mass goes, draw the mass; a label alone does not show
it. Ring spacing encodes curvature (wide rings mean flat), so both basins keep the same
ring count and only the radial scale changes. If sharpness is measured in a
reparametrization-invariant metric (for example against the Fisher information), name
that metric on the axis or in the caption, because Euclidean Hessian sharpness is not
invariant under function-preserving reparametrizations.

```latex
\begin{tikzpicture}[base]
  % flat basin: wide, gently spaced rings -> SGD parks here
  \foreach \s/\op in {1.5/12, 1.15/24, 0.8/40, 0.45/60, 0.18/82}
    \draw[accent!\op!white, line width=0.7pt] (-2.4,0) ellipse ({\s*1.15} and {\s*0.95});
  \fill[accent] (-2.4,0) circle (1pt);
  \node[note] at (-2.4,-1.85) {flat (low $S$)};
  % sharp basin: SAME depth, tightly spaced rings -> exponentially less mass
  \foreach \s/\op in {1.5/12, 1.15/24, 0.8/40, 0.45/60, 0.18/82}
    \draw[contrast!\op!white, line width=0.7pt] (2.2,0) ellipse ({\s*0.42} and {\s*1.25});
  \fill[contrast] (2.2,0) circle (1pt);
  \node[note] at (2.2,-1.85) {sharp (high $S$)};
  % SGD stationary mass: heavy in the flat basin, sparse in the sharp one
  \pgfmathsetseed{7}
  \foreach \i in {1,...,80} {
    \pgfmathsetmacro{\x}{-2.4+0.85*rand}\pgfmathsetmacro{\y}{0.65*rand}
    \fill[accent,opacity=0.30] (\x,\y) circle (0.7pt);}
  \foreach \i in {1,...,12} {
    \pgfmathsetmacro{\x}{2.2+0.22*rand}\pgfmathsetmacro{\y}{0.55*rand}
    \fill[contrast,opacity=0.30] (\x,\y) circle (0.7pt);}
  \node[note] at (0,2.15) {$\pi(\theta)\propto e^{-S(\theta)}$};
\end{tikzpicture}
```

Caveats go in the caption, never in the figure: which sharpness measure, which
estimator, under which noise model the mass result holds. The drawing is schematic; for a
measured landscape from logged eigenvalues, feed a real grid to the `surf` route of
section 5 or the `contour filled` route of section 9b.

## 5. 3D loss surface (pgfplots)

A genuine surface plot. Keep the colormap muted; rotate for a readable 3/4 view.

```latex
\begin{tikzpicture}
\begin{axis}[width=8cm, height=6cm, view={40}{30},
             axis lines=none, colormap={ink}{color=(accent!10) color=(accent!70)},
             domain=-2:2, y domain=-2:2, samples=30]
  \addplot3[surf, shader=interp, fill opacity=0.9]
    {0.6*(x^2 + y^2) - 0.8*exp(-((x-0.6)^2+(y-0.6)^2)*3)};
\end{axis}
\end{tikzpicture}
```

## 6. Point cloud

Scattered particles for a "sampled population". Use `\foreach` over jittered coords, or a
random seed.

```latex
\begin{tikzpicture}[base]
  \foreach \i in {1,...,60} {
    \pgfmathsetmacro{\x}{2*rand}
    \pgfmathsetmacro{\y}{1.2*rand}
    \fill[accent, opacity=0.7] (\x,\y) circle (0.9pt);
  }
\end{tikzpicture}
```

Two populations: loop a second color with an offset center to show source vs target.

## 7. Optimal-transport coupling

> For the serif look of this imagery (two-tone dots, a grey vector field, one thick black
> transport arrow, the equation pinned to the top) see section 13.

Two point clouds with faint gray lines mapping source to target (the optimal-transport
motif). Keep coupling lines very light so the points stay dominant.

```latex
\begin{tikzpicture}[base]
  % source (left, blue) and target (right, contrast) — fixed coords for reproducibility
  \foreach \i/\x/\y in {0/0/0, 1/0.2/0.8, 2/-0.3/0.5, 3/0.1/-0.6, 4/-0.2/-0.2} {
    \coordinate (s\i) at (\x,\y); \fill[accent] (s\i) circle (1.1pt);
  }
  \foreach \i/\x/\y in {0/4/0.1, 1/4.3/0.9, 2/3.7/0.4, 3/4.1/-0.5, 4/3.9/-0.1} {
    \coordinate (t\i) at (\x,\y); \fill[contrast] (t\i) circle (1.1pt);
  }
  % coupling (a soft many-to-one mapping)
  \foreach \i in {0,...,4} \draw[mist, line width=0.4pt, opacity=0.8] (s\i) -- (t\i);
  \draw[mist, line width=0.4pt, opacity=0.6] (s0) -- (t2);
  \draw[mist, line width=0.4pt, opacity=0.6] (s3) -- (t4);
  \node[note] at (0,-1.3) {source $\mu$}; \node[note] at (4,-1.3) {target $\nu$};
\end{tikzpicture}
```

## 7b. OT coupling: magnitude-by-saturation + Wasserstein-cost double arrow

A coupling carries mass, so encode it. Transport links
get a single hue at two saturations, `contrast` (focal / high-mass) thick, `contrastL`
(secondary / low-mass) thin, and the Wasserstein cost being *measured* is a gray
double-headed `<->` spanning the two supports. Keep the supports `navy` (ours) and
`truth` (observed), so color still carries one meaning per role.

```latex
\begin{tikzpicture}[base]
  \foreach \i/\x/\y in {0/0/0.4, 1/0.2/1.1, 2/-0.3/-0.4, 3/0.1/-1.0} {
    \coordinate (s\i) at (\x,\y); \fill[navy] (s\i) circle (1.6pt);}
  \foreach \i/\x/\y in {0/4/0.5, 1/4.3/1.2, 2/3.7/-0.3, 3/4.1/-0.9} {
    \coordinate (t\i) at (\x,\y); \fill[truth] (t\i) circle (1.6pt);}
  \draw[contrast,    line width=1.3pt] (s0) -- (t0);   % high mass: saturated + thick
  \draw[contrast,    line width=1.3pt] (s1) -- (t1);
  \draw[contrastL, line width=0.6pt] (s2) -- (t2);   % low mass: tint + thin
  \draw[contrastL, line width=0.6pt] (s3) -- (t3);
  \draw[contrastL, line width=0.6pt] (s0) -- (t2);   % a spread-out low-mass link
  % transport cost being MEASURED: grey two-headed arrow across the supports
  \draw[<->, mist, line width=0.8pt] (0.1,-1.7) -- node[note,below=1pt]{$W_2(\mu,\nu)$} (4.0,-1.7);
  \node[note,text=navy] at (0,2.0) {$\mu$};
  \node[note,text=slate]     at (4,2.0) {$\nu$};
\end{tikzpicture}
```

Saturation+width is two channels for one quantity (mass), redundant on purpose, so the
figure survives grayscale printing. Reserve `contrast` for the few links you want read first;
if every link is `contrast` the encoding is gone.

## 8. Trajectory / flow between snapshots

Population evolving across time snapshots: clouds at t0..tT with curved
flow arrows; predicted (blue) overlaid on observed (gray).

```latex
\begin{tikzpicture}[base]
  \foreach \t/\x in {0/0, 1/2.2, 2/4.4, 3/6.6} {
    % observed cloud (grey)
    \foreach \j in {1,...,12} {
      \pgfmathsetmacro{\dx}{0.28*rand}\pgfmathsetmacro{\dy}{0.5*rand}
      \fill[mist, opacity=0.7] ({\x+\dx},{\dy}) circle (0.8pt);
    }
    \node[note] at (\x,-1.1) {$t_{\t}$};
  }
  % flow direction
  \draw[->, accent, line width=1pt] (0.4,0.9) to[out=20,in=160] (6.2,0.9);
  \node[note, accent] at (3.3,1.5) {learned flow $\rho_t$};
\end{tikzpicture}
```

## 8b. Trajectory overlay (predicted solid, observed gray dotted)

The headline population-dynamics motif: a *predicted* trajectory laid over the *observed*
one, the contrast carried by line STYLE (a colorblind-safe second channel), not by adding a
second hue. Predicted is a solid `navy` line through filled navy nodes; observed is
gray `truth` dotted through hollow gray nodes (use `dash pattern=on 0pt off 4pt` with
`line cap=round` for round dots, not square dashes). A `dash dot` segment is the standard
elision break when a segment is extrapolated / unobserved. A small *frameless* legend sits
in the whitespace.

```latex
\begin{tikzpicture}[base]
  % observed: grey round-dotted through hollow grey nodes
  \draw[truth, line width=1pt, dash pattern=on 0pt off 4pt, line cap=round]
    (0,0.2) to[out=25,in=170] (2.1,0.7) to[out=-10,in=200] (4.2,0.35)
    to[out=20,in=160] (6.3,0.95);
  \foreach \x/\y in {0/0.2, 2.1/0.7, 4.2/0.35, 6.3/0.95}
    \node[circle,draw=truth,fill=white,line width=0.8pt,inner sep=1.6pt] at (\x,\y) {};
  % predicted: solid navy through filled nodes, with a dash-dot elision break
  \draw[navy, line width=1.1pt]
    (0,-0.2) to[out=22,in=175] (2.1,0.35) to[out=-8,in=205] (4.2,0.0);
  \draw[navy, line width=1.1pt, dash dot] (4.2,0.0) -- (4.9,0.18); % extrapolated
  \draw[navy, line width=1.1pt] (4.9,0.18) to[out=18,in=165] (6.3,0.6);
  \foreach \x/\y in {0/-0.2, 2.1/0.35, 4.2/0.0, 6.3/0.6} \fill[navy] (\x,\y) circle (1.8pt);
  % frameless mini legend
  \begin{scope}[shift={(0.1,2.0)}]
    \draw[navy,line width=1.1pt] (0,0) -- (0.7,0);
    \node[note,right=1mm,anchor=west] at (0.7,0) {predicted $\hat\rho_t$};
    \draw[truth,line width=1pt,dash pattern=on 0pt off 4pt,line cap=round] (3.0,0) -- (3.7,0);
    \node[note,right=1mm,anchor=west] at (3.7,0) {observed};
  \end{scope}
  \foreach \x/\t in {0/0,2.1/1,4.2/2,6.3/3} \node[note] at (\x,-1.0) {$t_{\t}$};
\end{tikzpicture}
```

For a headline trajectory figure `navy` is the protagonist ink (darker and less saturated
than `accent`); keep `accent` for model-component schematics.

## 8c. Single-hue ordinal lightness ramp (time is not a categorical series)

When a panel sequence is indexed by *time / step / ordinal*, encode it as ONE hue at rising
lightness, never as the categorical `c1 to c4` series, an ordinal axis is a ramp, and a
categorical palette on it falsely implies the snapshots are unrelated kinds. Drive the ramp
with `navy!\op` and a fixed seed per panel so the jitter is stable across compiles.

```latex
\begin{tikzpicture}[base]
  \foreach \k/\op/\x in {0/28/0, 1/52/1.6, 2/76/3.2, 3/100/4.8} {
    \foreach \j in {1,...,14} {
      \pgfmathsetseed{\k*97+\j}
      \pgfmathsetmacro{\dx}{0.30*rand}\pgfmathsetmacro{\dy}{0.55*rand}
      \fill[navy!\op, opacity=0.85] ({\x+\dx},{\dy}) circle (1pt);}
    \node[note] at (\x,-1.15) {$t_{\k}$};
  }
  \draw[->, slate, line width=0.7pt] (-0.6,1.5) -- (5.4,1.5) node[tag, right] {time};
\end{tikzpicture}
```

## 9. Vector field / gradient field

Arrows on a grid, length/!color by magnitude, a gradient ∇J or a transport map.

```latex
\begin{tikzpicture}[base]
  \foreach \x in {-1.5,-1,...,1.5} \foreach \y in {-1.5,-1,...,1.5} {
    \pgfmathsetmacro{\u}{-0.30*\x}\pgfmathsetmacro{\v}{-0.30*\y}
    \draw[->, slate, line width=0.5pt, >={Stealth[length=1.4mm,width=1.1mm]}]
      (\x,\y) -- ++(\u,\v);  % small head, longer shaft: heads must not swamp the field
  }
  \fill[contrast] (0,0) circle (1pt); % attractor
\end{tikzpicture}
```

## 9b. Learned-potential filled contour + colorbar; streamline field

For a learned potential `$\Phi_\theta$` (an energy, a value function, a free-energy
surface) the accurate route is a genuine pgfplots `contour filled` with a
SINGLE-HUE colormap (`paper` → `navy`) and a thin colorbar. One hue, not a rainbow:
the surface is a scalar field, so a monotone lightness ramp is the honest encoding.

```latex
\begin{tikzpicture}
\begin{axis}[width=8cm, height=6cm, view={0}{90},
             axis lines=none, enlargelimits=false,
             colormap={pot}{color=(paper) color=(navy)},
             colorbar, colorbar style={width=3mm, tick style={ink},
               ticklabel style={font=\figfont\figS}, ylabel={$\Phi_\theta$}},
             domain=-2:2, y domain=-2:2]
  \addplot3[contour filled={number=8}, samples=40, shader=interp, z buffer=sort]
    {0.5*(x^2+y^2) - exp(-((x-0.7)^2+(y+0.3)^2)*2) - 0.7*exp(-((x+0.9)^2+(y-0.6)^2)*2.5)};
\end{axis}
\end{tikzpicture}
```

The streamline companion: many thin `slate` integral curves of `$-\nabla\Phi_\theta$`,
denser than the coarse §9 arrow grid, draining into the basins. The exact streamline ODE is
overkill for a schematic, here each short stroke points at its nearest sink, which reads as
a flow field at figure scale (swap in a real `quiver`/`table` for a quantitative one).

```latex
\begin{tikzpicture}[base]
  \fill[navy] (-0.9,0.6) circle (1.2pt);   % the two sinks of Phi
  \fill[navy] (0.7,-0.3) circle (1.2pt);
  \foreach \gx in {-1.8,-1.4,...,1.8} \foreach \gy in {-1.6,-1.2,...,1.6} {
    \pgfmathsetmacro{\ax}{-0.9}\pgfmathsetmacro{\ay}{0.6}
    \pgfmathsetmacro{\bx}{0.7}\pgfmathsetmacro{\by}{-0.3}
    \pgfmathsetmacro{\da}{(\gx-\ax)^2+(\gy-\ay)^2}
    \pgfmathsetmacro{\db}{(\gx-\bx)^2+(\gy-\by)^2}
    \pgfmathsetmacro{\tx}{\da<\db ? \ax : \bx}   % aim at the closer sink
    \pgfmathsetmacro{\ty}{\da<\db ? \ay : \by}
    \pgfmathsetmacro{\nx}{\tx-\gx}\pgfmathsetmacro{\ny}{\ty-\gy}
    \pgfmathsetmacro{\nn}{sqrt(\nx*\nx+\ny*\ny)+0.0001}
    \draw[slate, line width=0.4pt, opacity=0.8]
      (\gx,\gy) -- ++({0.22*\nx/\nn},{0.22*\ny/\nn});
  }
  \node[note] at (0,-2.1) {streamlines of $-\nabla\Phi_\theta$ (two sinks)};
\end{tikzpicture}
```

## 10. SDE / sample paths

Several noisy 1D trajectories converging, diffusion / Langevin samples.

```latex
\begin{tikzpicture}
\begin{axis}[spare axis, xlabel={$t$}, ylabel={$x_t$}, samples=80, domain=0:5]
  \addplot[contrast, opacity=0.55, line width=0.6pt] {2*exp(-x)+0.25*sin(deg(6*x+1))*exp(-0.3*x)};
  \addplot[accentL,  opacity=0.55, line width=0.6pt] {2*exp(-x)+0.25*sin(deg(6*x+2))*exp(-0.3*x)};
  \addplot[contrast, opacity=0.55, line width=0.6pt] {2*exp(-x)+0.25*sin(deg(6*x+3))*exp(-0.3*x)};
  \addplot[accent, line width=1.2pt] {2*exp(-x)}; % mean path
\end{axis}
\end{tikzpicture}
```

> Gotcha: don't name a `\foreach` variable `\o`, it clashes with LaTeX's `\o` (ø) and
> breaks inside `\addplot`. Safe single letters: `\i \j \k \x \y`. When looping colors,
> prefer listing `\addplot`s explicitly as above, or use a 2-part `\foreach \k/\col in {...}`.

## 11. Equation callout attached to a schematic (borderless soft fill)

To hang a loss/objective off a schematic without a hard box stealing attention, use the
`callout` style (rounded, soft `cloud` fill, *no* border) tied to the component by a
faint `softarrow`. The eye reads the diagram first and the math as annotation, which is the
intent. (See `math_layout.md` for the equation typesetting itself.)

```latex
\begin{tikzpicture}[base]
  \node[block accent] (enc) at (0,0) {$T_\theta$};
  \node[var] (x) at (-2.2,0) {$x$};  \node[var] (y) at (2.2,0) {$\hat y$};
  \draw[flow] (x) -- (enc); \draw[flow] (enc) -- (y);
  \node[callout] (L) at (0,-1.9)
    {$\displaystyle \min_\theta\ \mathbb{E}\,\|T_\theta(x)-y\|^2 + \lambda\,\mathrm{OT}(\mu,\nu)$};
  \draw[softarrow] (L.north) -- (enc.south);
\end{tikzpicture}
```

A warm-tinted `contrastL` fill is the convention for a *loss* callout when you want it to
read distinctly from a cool definitional one; keep at most one of each per panel.

## 12. Styling notes

- **One shaded blob per figure.** `\shade[inner color=.., outer color=..]` for the one density blob;
  flat fills with `fill opacity` 0.1 to 0.5 for bands and overlapping densities.
- **Reproducibility.** `rand` changes every compile. For a figure you'll keep, either fix
  coordinates explicitly (as in §7) or set a seed: `\pgfmathsetseed{42}` before the loop.
- **Color = identity.** Blue is consistently "ours/predicted", gray "observed/data", contrast
  "target/true". Carry the same mapping across every panel. For a headline trajectory
  figure the protagonist ink is `navy` and "observed" is `truth` (section 8b).
- **Ordinal is a ramp, not a series.** A time/step/snapshot index is ONE hue at rising
  lightness (`navy!28 → !100`, §8c), never the categorical `c1 to c4` palette, the
  latter implies the snapshots are unrelated kinds.
- **Style is a second channel.** Predicted-vs-observed and high-vs-low mass both read in
  grayscale when carried by dash style / line width (§8b) or saturation+width (§7b), so the
  one-accent rule survives. A `dash dot` segment is the standard elision/extrapolation break.
- **Don't over-contour.** 3 to 5 rings reads as a density; 12 reads as a topo map. Fewer,
  spaced rings look calmer. Curvature lives in ring *spacing*, so a flat-vs-sharp pair (§4b)
  keeps the same ring count and only rescales the radii.
- For genuine data contours/heatmaps from a grid, pgfplots `contour prepared` or
  `matrix plot`/`surf` with a `table` is the accurate route; the hand-drawn versions here
  are for schematics.

---

## 13. Serif-look transport recipes

The serif theme's version of this file's imagery (the theme's model is credited in
THIRD_PARTY.md). Set
`\figtheme{serif}` for the full look; the snippets compile in both themes. The grammar in
one line: two-tone dot clusters and a gray vector field, joined by one thick black curved
transport arrow, with the equation pinned to the top. Black does structure, gray does
support, blue carries identity, on a lot of white.

**Ink discipline across every panel:** `navy` is the source ($\mu_0$, $t_0$), `accentMd`
the target ($\mu_1$, $t_1$); lightness alone encodes the direction of time. In empirical
scatters gray truth is drawn under, navy prediction over. Black is structure (the spine,
the time axis), gray (`annot`, through `field`, `agg`, `traj`) is support, and color is
never an arrow. `contrast` appears only as a target in real two-condition data.

Line weights: `field` 0.5 pt gray, `traj` 0.5 pt gray, axis and aggregation 0.7 to
1.1 pt, box outlines 1.3 pt black, `spine` 1.6 pt black. All heads are Stealth.

### 13.1 Two-tone dot distribution (source $\mu_0$ navy / target $\mu_1$ `accentMd`)

Solid filled disks, uniform radius within a population, organically clustered (never a
lattice). Schematics use ~6 to 10 honest dots; the empirical variant (right) uses many dots at
low opacity so overlaps darken, with **gray truth UNDER, navy prediction OVER**, quality is
read as "does navy cover grey".

```latex
\begin{tikzpicture}
  % source cluster: dark navy = mu_0 / t_0 (fixed coords, organic not lattice)
  \foreach \p in {(0,0),(0.22,0.30),(-0.20,0.25),(0.10,-0.22),(-0.16,-0.12),(0.06,0.16),(-0.05,0.05)}
    \fill[navy] \p circle (2.2pt);                      % solid navy disks, uniform radius
  \node[font=\figL, text=navy] at (0,-0.7) {$\mu_0$};  % serif math label, on the cluster
  % target cluster: lighter blue = mu_1 / t_1 (lightness alone encodes time)
  \begin{scope}[xshift=42mm]
    \foreach \p in {(0,0.30),(0.20,0.42),(-0.10,0.20),(0.16,-0.30),(-0.20,-0.24),(0.04,-0.05)}
      \fill[accentMd] \p circle (2.2pt);                  % mid-blue target disks (accentMd, NOT pale)
    \node[font=\figL, text=accent] at (0,-0.7) {$\mu_1$};
  \end{scope}
  % empirical-scatter variant (right): many dots at low opacity so overlaps darken;
  % grey truth UNDER, navy prediction OVER.
  \begin{scope}[xshift=80mm]
    \pgfmathsetseed{11}
    \foreach \i in {1,...,70}{
      \pgfmathsetmacro{\x}{0.7*rand}\pgfmathsetmacro{\y}{0.5*rand}
      \fill[truth, opacity=0.55] (\x,\y) circle (1.4pt);}  % truth grey under
    \foreach \i in {1,...,70}{
      \pgfmathsetmacro{\x}{0.6*rand+0.05}\pgfmathsetmacro{\y}{0.45*rand}
      \fill[navy, opacity=0.55] (\x,\y) circle (1.4pt);}   % prediction navy over
    \node[note] at (0,-0.95) {empirical: opacity overlap};
  \end{scope}
\end{tikzpicture}
```

For a real two-condition overlay (treated against control) the target dots take
`contrast`; otherwise the pair is `navy` and `accentMd`. Target dots are a saturated
mid-blue in the serif theme (`#6078B8`), never the pale `accentL`, which is a fill and
halo tone and reads washed out as dots.

### 13.2 Gray vector-field grid $v(t,\cdot)$ with alpha-falloff

A regular rectangular grid of identical thin **light-gray** `field` arrows, all the same
length, rotated to trace a smooth flow. Dim the field where it passes under a distribution by
laying a white opacity disk over it so the field recedes behind the dots.

```latex
\begin{tikzpicture}
  % regular grid of identical thin grey arrows, rotated to trace a smooth flow
  \foreach \x in {0,0.6,...,4.2}{
    \foreach \y in {0,0.6,...,3.0}{
      \pgfmathsetmacro{\ang}{40*sin(\x*60)+20*cos(\y*60)}   % smooth flow angle (deg)
      \draw[field] (\x,\y) -- ++(\ang:0.32);}}            % field = grey 0.5pt Stealth
  % a distribution sitting on the field; fade the field behind it with a white opacity disk
  \fill[white, opacity=0.30] (2.1,1.5) circle (9mm);        % alpha-falloff so field recedes
  \foreach \p in {(2.1,1.5),(2.30,1.72),(1.92,1.66),(2.20,1.30),(1.96,1.34)}
    \fill[navy] \p circle (2pt);
  \node[note] at (2.4,3.55) {time-varying vector field $v(t,\cdot)$};  % grey serif gloss
\end{tikzpicture}
```

### 13.3 Thick black curved transport arrow + riding $\mu_t$ label

The figure's spine: a thick **solid-black** Bézier with a Stealth head (`spine`,
~2 to 3× heavier than the field/cloud lines), the $\mu_t$ label riding the curve, a gray serif
side-gloss, and a small local $\nabla\varphi$ gradient annotation at the source.

```latex
\begin{tikzpicture}
  % source mu_0 (navy) and target mu_1 (accentMd) clusters
  \foreach \p in {(0,0),(0.18,0.26),(-0.18,0.20),(0.10,-0.20),(-0.12,-0.10)}
    \fill[navy] \p circle (2.2pt);
  \node[font=\figL, text=navy] at (0,-0.65) {$\mu_0$};
  \coordinate (src) at (0.2,0.1);
  \begin{scope}[xshift=46mm]
    \foreach \p in {(0,0.20),(0.18,0.34),(-0.10,0.14),(0.14,-0.26),(-0.16,-0.20)}
      \fill[accentMd] \p circle (2.2pt);
    \node[font=\figL, text=accent] at (0,-0.65) {$\mu_1$};
    \coordinate (tgt) at (-0.2,0.1);
  \end{scope}
  % the figure's spine: thick solid-black curved transport arrow, label rides the curve
  \draw[spine]                                          % spine = thick black 1.6pt Stealth
    (src) .. controls +(1.4,0.9) and +(-1.4,0.7) .. (tgt)
    node[midway, sloped, above, font=\figL, text=ink] {$\mu_t$};
  \node[note] at (2.3,-0.05) {= curve in the space of measures};
  % a small local gradient annotation at the source
  \draw[ink, line width=1pt, ->, >={Stealth[length=2mm]}]
    ($(src)+(-0.35,0.25)$) -- ++(0.42,0.42) node[right, font=\figL]{$\nabla\varphi$};
\end{tikzpicture}
```

### 13.4 Gray wiggly Brownian / Schrödinger cloud + one highlighted navy path

Dozens of thin (~0.5pt) light-gray jagged polylines (`traj`) fanning between source and
target, collectively a lens-shaped cloud (overlap darkens the core). Promote **exactly one**
path to a darker-navy "example trajectory" (`trajhi`), drawn last on top, with a thick
black time axis underneath (the `\timeaxis` idiom).

```latex
\begin{tikzpicture}
  \pgfmathsetseed{5}
  % the grey cloud: dozens of thin jagged polylines fanning source->target,
  % collectively a lens; overlap darkens the core.
  \foreach \i in {1,...,32}{
    \pgfmathsetmacro{\j}{0.9*rnd-0.45}                       % start height jitter
    \draw[traj]                                            % traj = grey 0.5pt opacity .55
      (0,\j) to[out=20,in=160]
      ({1.4},{\j+0.25*rnd-0.12}) to[out=-20,in=200]
      ({2.8},{\j*0.4+0.15*rnd});}
  % promote EXACTLY ONE path to a highlighted navy example, drawn last on top
  \draw[trajhi]                                            % trajhi = navy 0.8pt solid
    (0,0.05) to[out=20,in=160] (1.4,0.18) to[out=-20,in=200] (2.8,0.02);
  \node[font=\figL, text=navy] at (2.05,0.6) {example trajectory};
  % time axis underneath (the \timeaxis idiom): thick black ->, serif "time"
  \draw[ink, line width=1.2pt, ->, >={Stealth[length=2.4mm]}]
    (0,-0.95) -- (2.8,-0.95) node[midway, below, font=\figL]{time};
\end{tikzpicture}
```

`rnd` (not `rand`) returns 0 to 1 here, so the jitter stays on one side; `\pgfmathsetseed{5}`
fixes the cloud across compiles. Bump the cloud count to ~48 to 64 and drop `traj`'s opacity
toward 0.4 for a denser Schrödinger-bridge lens.

### 13.5 Blues energy/density landscape (flat bands + down-gradient arrow)

Discrete **flat** filled `Blues` bands (~12 levels, **light = low energy, dark = high**) with
the band edges drawn as dotted navy iso-contours, a thin solid-black 4-sided spine with sharp
corners, Palatino serif numeric ticks only (no title/axis-label/grid), and a discrete
colorbar. The "arrow" variant adds one bold straight black Stealth arrow pointing
**down-gradient** (toward the light basin). This is the vector PGFPlots route, no gnuplot /
shell-escape needed (the built-in `contour filled` filler draws the band edges, so
`contour gnuplot` is deliberately avoided).

```latex
\begin{tikzpicture}
\begin{axis}[
    width=8cm, height=6.6cm, view={0}{90}, enlargelimits=false,
    axis on top, scale only axis,
    % sharp thin black 4-sided spine, serif numeric ticks only, no title/label/grid
    axis line style={black, line width=0.9pt},
    every tick/.style={black, line width=0.6pt}, tick align=outside,
    tick label style={font=\figfont\figS}, xtick={-2,0,2}, ytick={-2,0,2},
    title={},
    % matplotlib "Blues" ramp: low=light, high=dark (reads on-brand, blue family)
    colormap={Blues}{
      rgb255=(247,251,255) rgb255=(222,235,247) rgb255=(198,219,239)
      rgb255=(158,202,225) rgb255=(107,174,214) rgb255=(66,146,198)
      rgb255=(33,113,181)  rgb255=(8,81,156)    rgb255=(8,48,107)},
    colorbar, colorbar style={width=3mm, tick style={black},
      ticklabel style={font=\figfont\figS}},
    domain=-2.4:2.4, y domain=-2.4:2.4]
  % flat filled Blues bands (~12 levels); the band EDGES are drawn as dotted navy
  % iso-contours (no gnuplot needed: the built-in contour filler draws the edges).
  \addplot3[contour filled={number=12, draw color=navy},
            contour/every contour label/.style={},
            samples=42, shader=flat, z buffer=sort,
            contour/draw color=navy]
    {0.55*(x^2+y^2) - 1.4*exp(-((x-0.7)^2+(y+0.4)^2)*2.2)};
  % single down-gradient black Stealth arrow (the "arrow" variant)
  \draw[black, line width=1.3pt, ->, >={Stealth[length=2.6mm]}]
    (axis cs:-1.4,1.3) -- (axis cs:0.5,-0.2);
\end{axis}
\end{tikzpicture}
```

The `Blues` stops are the matplotlib `Blues` ramp (also kept as a comment in the preamble);
light = low so a basin reads as a pale well at the center. This is the energy/density route;
for the "points resolve into structure" zoom and the UMAP-overlay results idiom see
`multiscale_density_zoom.md` and `bio_objects.md` (both in the serif look).

### 13.6 Equation pinned to the TOP, geometry as its visual restatement

Each schematic panel pairs a display serif-math equation at the **top** (a bare `eq` node,
or a borderless soft-fill `eqfill` for an objective, never a hard box) with the geometry
as its visual restatement directly below.

```latex
\begin{tikzpicture}
  % panel: a serif-math equation pinned to the TOP, the geometry its visual restatement below
  \node[panel] (la) at (-0.2,2.7) {a};
  \node[ptitle, anchor=west] at (0.3,2.7) {Dynamic Optimal Transport};
  % the equation callout at the top (bare serif math, no box)
  \node[eq] at (3.2,2.0) {$dX_t = v(t,X_t)\,dt + \sigma\, d\mathbb{W}_t$};
  % --- geometry below as the visual restatement ---
  \foreach \p in {(0,0),(0.18,0.24),(-0.16,0.18),(0.08,-0.18)}
    \fill[navy] \p circle (2pt);
  \node[font=\figL, text=navy] at (0,-0.55) {$\mu_0$};
  \begin{scope}[xshift=58mm]
    \foreach \p in {(0,0.18),(0.16,0.30),(-0.10,0.12),(0.12,-0.22)}
      \fill[accentMd] \p circle (2pt);
    \node[font=\figL, text=accent] at (0,-0.55) {$\mu_1$};
  \end{scope}
  \draw[spine] (0.2,0.1) .. controls +(1.8,1.0) and +(-1.8,0.8) .. (5.6,0.1)
    node[midway, sloped, above, font=\figL, text=ink]{$\mu_t$};
  % a borderless soft-fill variant for an objective (never a hard box)
  \node[eqfill] at (3.0,-1.4)
    {$\displaystyle \min_{\theta}\ \mathbb{E}\,\| \mathcal{T}_\theta(x) - y \|^2$};
\end{tikzpicture}
```

### 13.7 Canonical worked template: the dynamic-OT panel, end to end

The whole grammar in one panel, bold panel letter, roman title, italic qualifier,
equation pinned to the top, the gray field on the background layer, two-tone $\mu_0/\mu_1$
clusters with alpha-falloff disks, the thick black transport spine with a riding $\mu_t$, the
black time axis, and the in-figure citation as the **only** blue text (`cite`). This is the
reference layout to copy and re-fill.

```latex
\begin{tikzpicture}
  % ---- header: bold panel letter, roman title, italic qualifier ----
  \node[panel] (la) at (-0.3,3.5) {a};
  \node[ptitle, anchor=west] at (0.25,3.5) {Dynamic Optimal Transport};
  \node[font=\itshape, text=ink, anchor=west] at (0.25,3.05)
    {with external force $f$ and noise $g$};
  % ---- equation pinned to the top ----
  \node[eq] at (3.3,2.4) {$dX_t = v(t,X_t)\,dt + g(t)\,d\mathbb{W}_t + f(t,X_t)\,dt$};
  % ---- grey vector field behind everything ----
  \begin{scope}[on background layer]
    \foreach \x in {0,0.55,...,6.2}{
      \foreach \y in {-0.3,0.25,...,1.6}{
        \pgfmathsetmacro{\ang}{18*sin(\x*45)+10}
        \draw[field] (\x,\y) -- ++(\ang:0.28);}}
  \end{scope}
  % ---- source mu_0 (navy) ----
  \fill[white, opacity=0.35] (0.2,0.6) circle (8mm);
  \foreach \p in {(0,0.6),(0.20,0.84),(-0.18,0.74),(0.10,0.38),(-0.12,0.50)}
    \fill[navy] \p circle (2.2pt);
  \node[font=\figL, text=navy] at (0,-0.1) {$\mu_0$};
  % ---- target mu_1 (accentMd) ----
  \fill[white, opacity=0.35] (6.0,0.6) circle (8mm);
  \foreach \p in {(6.0,0.6),(6.20,0.82),(5.86,0.70),(6.10,0.34),(5.88,0.48)}
    \fill[accentMd] \p circle (2.2pt);
  \node[font=\figL, text=accent] at (6.0,-0.1) {$\mu_1$};
  % ---- thick black transport spine, mu_t riding it ----
  \draw[spine] (0.3,0.65) .. controls +(2.0,0.9) and +(-2.0,0.9) .. (5.7,0.65)
    node[pos=0.32, sloped, above, font=\figL, text=ink]{$\mu_t$};
  \node[note, anchor=east] at (2.55,1.62) {time-varying};   % gloss split, clear of the arrow
  \node[note, anchor=west] at (3.55,1.62) {field $v(t,\cdot)$};
  % ---- time axis + in-figure citation (the only blue text, parked in whitespace) ----
  \draw[ink, line width=1.1pt, ->, >={Stealth[length=2.4mm]}]
    (0,-0.75) -- (6.2,-0.75) node[midway, below, font=\figL]{time};
  \node[cite, anchor=east] at (6.2,-1.25) {(Author et al., Year)};
\end{tikzpicture}
```

The `on background layer` scope needs `\usetikzlibrary{backgrounds}` (already loaded in the
preamble). Park the citation and side-glosses in the panel's whitespace, not over the arrow;
the layout works when more than 40% of the canvas stays white.
