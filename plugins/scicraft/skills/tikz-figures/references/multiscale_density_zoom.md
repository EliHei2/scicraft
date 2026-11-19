# Multiscale density zoom panels

The "one substrate, read at every scale" overview panel: a soft density field on a bounded
domain (a point cloud, a map, a tissue section, an embedding), then a coherent left-to-right
zoom cascade ending at a single element and its kNN neighborhood. It suits any overview that
zooms from a whole field to one point and its nearest neighbors.

The panel is generator-driven: Python computes the density and the point coordinates and
emits TikZ (`\fill ... plot[smooth cycle]` paths, `\fill` dots); a second step wraps them
in frames. Hand-typing coordinates does not scale and breaks coherence.

**The shipped generator.** `scripts/density_zoom.py` implements every rule in this file:
one point field (a CSV of `x,y,label` from your real data or code, or a seeded synthetic
field), KDE bands at relative levels 0.10, 0.36 and 0.66 with opacities 0.22, 0.42 and
0.72, nested crops, the ego chosen by radius quantile and angular gap, and `facts.json`.

```bash
python3 scripts/density_zoom.py --out zoom/ --preamble assets/preamble.tex   # synthetic, seed 7
python3 scripts/density_zoom.py --points field.csv --out zoom/ --preamble assets/preamble.tex
python3 scripts/render_figure.py zoom/fig.tex
```

It uses `contourpy` filled contours, so bands cut by a zoom window close along the window
edge; filling an open contour line with `smooth cycle` would draw a false chord.

**Contents**
1. The shape of the panel
2. One point field, nested crops
3. Density as three contour bands
4. The kNN ego ball
5. Palette: harmonize lightness and saturation
6. Serif look: one-hue density and the zoom cascade
7. A bounded domain read as a sphere
8. Frames, focus lines, whitespace
9. Assembly and delivery
10. Process

---

## 1. The shape of the panel

`[ domain with density ] --> [ zoom 1: still density ] --> [ zoom 2: points resolve ] --> [ zoom 3: one point + kNN ego-ball ]`

- **Level 1**, the whole domain as a density field (3-layer contour bands per category).
- **Level 2**, a magnified sub-window, *still density* (no individual points yet).
- **Level 3**, points resolve (real samples drawn from the density).
- **Level 4**, one element `u` and its immediate kNN neighbors, labeled `z_u`.

Dashed tapered focus lines connect each level's zoom-box to the next frame.

---

## 2. One point field, nested crops

The zoom must be **honest**: define a single point field in world coordinates *once*, then
each level is a **crop of the same field**, magnified. Never re-sample per level, that
produces a "fake" zoom where the clump in frame *k* has no relation to frame *k+1*.

```python
allp = np.vstack([P0,P1,P2])           # ONE field, all categories
def crop(box):                          # level k+1 = points inside level k's zoom box
    x0,y0,x1,y1=box
    m=(allp[:,0]>=x0)&(allp[:,0]<=x1)&(allp[:,1]>=y0)&(allp[:,1]<=y1)
    return allp[m]
def w2l(pts,box):                       # world -> local [-1,1]^2 for the frame
    x0,y0,x1,y1=box; cx=(x0+x1)/2; cy=(y0+y1)/2; s=max((x1-x0)/2,(y1-y0)/2)
    return np.array([((x-cx)/s,(y-cy)/s) for x,y in pts])
```

**Sub-lesson that bites:** do **not** subset/thin the points shown at level 3 if level 4's
kNN is computed over the full field, the ego's neighbors may be points you thinned away,
so a neighbor "appears from nowhere." Show the *same* set you compute kNN over. (If you
want level 3 sparser, sparsify the underlying field, not the display.)

---

## 3. Density as three contour bands

A real density reads as **peak + falloff**: saturated core fading to nothing. Two failure
modes to avoid, both of which reviewers (and demanding users) reject immediately:

- **Flat region fills** (argmax label map, solid color) → looks like a *political map*, not
  density. Contour-of-a-mask always yields hard, convex-ish territory edges.
- **Blurred mask** (gaussian-blur a solid blob) → looks like *smeared paint*: a flat color
  with a fuzzy edge, no internal concentration.

The thing that actually looks like density: **scatter clustered points, compute a real KDE,
render 3 nested filled contour levels** (faint outer → mid → dark core) per category.

```python
def kde(P, bw=0.05, G=720):
    H=np.zeros((G,G))
    ix=np.clip(((P[:,0]+1)/2*(G-1)).astype(int),0,G-1)
    iy=np.clip(((P[:,1]+1)/2*(G-1)).astype(int),0,G-1)
    for a,b in zip(ix,iy): H[b,a]+=1
    return gaussian_filter(H, sigma=bw*G/2)

# emit 3 layers; draw highest level LAST so the core sits on top
for lev,op in [(0.10,0.22),(0.36,0.42),(0.66,0.72)]:
    cs=plt.contour(xs,ys,Dk,levels=[lev])
    for seg in cs.allsegs[0]:
        if len(seg)<8: continue
        path=" ".join(f"({x:.3f},{y:.3f})" for x,y in seg[::2])     # SPACE-separated!
        f.write(f"  \\fill[{col}, opacity={op}] plot[smooth cycle,tension=0.6] coordinates {{{path}}};\n")
```

- **Irregular non-convex shape** comes from the *clustered point layout* (several
  anisotropic lumps per category, scattered), not from post-hoc warping of a blob.
- **Coverage vs honesty tension:** pure KDE fades to white where sparse. To "cover" the
  domain, spread the clusters out (push some toward the rim) rather than adding a flat
  background floor (which looks pasted). State the tradeoff to the user; let them choose.
- **Disconnected territories:** a category that recurs in several places (multiple
  separated lumps) reads as more biologically real than one connected blob.

### Coordinate gotcha (cost me a compile)
`plot[smooth cycle] coordinates { ... }` needs **space-separated** `(x,y)` points. Joining
with ` -- ` throws *"Cannot parse this coordinate."* Reserve `--` for `\draw` line paths.

---

## 4. The kNN ego ball

This is the most-scrutinized sub-figure. A correct, non-fake ego-ball requires:

1. **Compute kNN over exactly the displayed field** (see subsetting lesson above).
2. **Pick the ego deliberately.** The auto-choice "point nearest box center" often lands
   on a far-outlier neighborhood → an oversized empty ball with uneven spokes. Instead
   **scan candidate points and score their kNN** for: (a) a *roomy but moderate* radius
   (≈45th-percentile, not the tightest knot → not cramped, not sparse), and (b) **angular
   spread** so neighbors *surround* the center rather than clustering to one side.

```python
def angular_maxgap(p, knn, k):
    angs=sorted(math.atan2(allp[j][1]-p[1], allp[j][0]-p[0]) for j in knn)
    return max((angs[(i+1)%k]-angs[i])%(2*math.pi) for i in range(k))  # small = surrounded
# choose ego: moderate rmax AND small angular max-gap (e.g. < 2.4 rad)
```

3. **Size the window snugly**: `pad = rk * ~1.4` around the ball so it has margin but isn't
   lost in whitespace. Verify every neighbor's local coord is within `[-1,1]` (in-frame).
4. **Smaller dots** so near-coincident neighbors don't merge into one (a "missing node").
   Center ≈1.5pt, neighbors ≈1.1pt, context ≈0.8pt at this scale.
5. **Label `z_u` with no leader line**: a pointer reads as a 7th edge and usually doesn't
   even terminate on the node. Place the label directly beside the center node.
6. **Ring color**: a quiet **light gray** ring (`black!22`) frames the neighborhood without
   competing with the colored points or the black spokes. Spokes: thin **black/ink**, not
   gray. Color each neighbor dot by *its own* category (consistent with the territory it
   sits in), not all by the ego's category.

---

## 5. Palette: harmonize lightness and saturation

The single highest-impact aesthetic check: **measure** the fills' HLS and equalize them.
A muted categorical set has the colors at **comparable lightness and gentle,
comparable saturation**, no member shouting. A too-dark / too-saturated member (a common
trap with "mustard"/ochre) breaks the restraint instantly.

```python
import colorsys
def hls(hexv):
    r,g,b=(int(hexv[i:i+2],16)/255 for i in (0,2,4)); return colorsys.rgb_to_hls(r,g,b)
# target: all fills L ~0.63, S ~0.18-0.30; deep point variants L ~0.46
```

A serviceable muted, slightly-cool-leaning trio (fills / deep point variants):
`#8DA1B9·#54719C` dusty blue, `#BDA684·#967240` airy ochre, `#A691B6·#7A5B95` muted purple.
Structure (frames, axes, spokes) is near-black **ink** (`#1A1A1A`, 85% for frames); reserve
saturation for the data. Mustard "browner" vs "more gold" is a frequent user axis, expect
to tune its hue/lightness specifically.

The default category colors are the theme's (`accent`, `contrast`, `slate`). Use the
muted trio when several categories need their own hue on one domain. When the panel
encodes one scalar (a density magnitude, a potential, an energy) use the single-hue ramp
(`ramp1` to `ramp8`, low = light) of section 6.

---

## 6. Serif look: one-hue density and the zoom cascade

For a panel beside serif-theme figures, the whole panel collapses to two blues, gray and black: the density is
one ramp (low = light, high = dark), structure is sharp black, secondary ink is gray, and
the contrast is held back for the one contrasting category (it does not appear here).
These display coordinates are for the recipe; in production drive them from the
generator.

### 6a. Energy / density panel, flat `Blues` bands + dotted navy iso-contours

Discrete **flat** filled `Blues` bands (low energy = light, high = dark), a
**dotted dark-navy iso-contour** on every band edge (dot density reads as slope), a thin
**sharp** black 4-sided spine, **serif** (Palatino) numeric ticks only, no title, no axis
label, no gridline, a discrete colorbar, and the single bold-black down-gradient Stealth
arrow ("arrow variant"). The faithful vector route through PGFPlots `contour filled` needs an
external engine (`--shell-escape` + gnuplot/matlab); when that is unavailable, hand-draw the
bands as nested smooth blobs filled with the named `Blues` stops (below), it compiles
anywhere and reproduces the matplotlib look exactly. Largest/lightest band first, dark core
**last on top**.

```latex
% ramp0 .. ramp8 come from the preamble (matplotlib Blues, low = light)
\begin{tikzpicture}[x=1cm,y=1cm]
  % flat filled bands: lightest (largest) first, dark core last on top
  \foreach \col/\sc in {ramp1/1.00, ramp2/0.86, ramp3/0.72, ramp4/0.58,
                        ramp5/0.45, ramp6/0.33, ramp7/0.22, ramp8/0.12}{
    \begin{scope}[shift={(2.3,1.9)}, scale=\sc]
      \fill[\col] plot[smooth cycle,tension=0.7] coordinates
        {(1.4,0) (0.9,1.0) (-0.5,1.2) (-1.3,0.2) (-0.8,-1.0) (0.6,-1.1)};
      \draw[navy, densely dotted, line width=0.4pt]               % dotted navy iso-line
        plot[smooth cycle,tension=0.7] coordinates
        {(1.4,0) (0.9,1.0) (-0.5,1.2) (-1.3,0.2) (-0.8,-1.0) (0.6,-1.1)};
    \end{scope}}
  \draw[ink, line width=0.9pt] (0,0) rectangle (4.6,3.8);          % sharp thin black spine
  \foreach \x/\lab in {0.2/-2, 1.3/-1, 2.4/0, 3.5/1, 4.4/2}          % serif numeric ticks only
    \draw[ink, line width=0.6pt] (\x,0) -- (\x,-0.09) node[below,font=\figM]{\lab};
  \foreach \y/\lab in {0.2/-2, 1.1/-1, 2.0/0, 2.9/1, 3.6/2}
    \draw[ink, line width=0.6pt] (0,\y) -- (-0.09,\y) node[left,font=\figM]{\lab};
  \draw[ink, line width=1.3pt, ->, >={Stealth[length=2.4mm,width=2mm]}]
    (2.9,2.5) -- (2.3,1.9);                                          % ONE down-gradient arrow
  \begin{scope}[shift={(5.0,0)}]                                     % discrete serif colorbar
    \foreach \i/\col in {0/ramp1,1/ramp2,2/ramp3,3/ramp4,4/ramp5,5/ramp6,6/ramp7,7/ramp8}
      \fill[\col] (0,{\i*0.475}) rectangle (0.32,{(\i+1)*0.475});
    \draw[ink, line width=0.8pt] (0,0) rectangle (0.32,3.8);
    \node[font=\figM, anchor=west] at (0.4,0.1) {low};
    \node[font=\figM, anchor=west] at (0.4,3.7) {high};
  \end{scope}
\end{tikzpicture}
```

PGFPlots vector equivalent (needs gnuplot via `--shell-escape`): `\addplot3[contour
filled={number=12}]` with a `Blues` colormap, then a second dotted pass `\addplot3[contour
gnuplot={number=12}, dotted, draw=navy, line width=0.4pt]`. The 9 ramp stops above are the
matplotlib `Blues` anchors; feed them as a `colormap={cbblues}{rgb255=(247,251,255) ...}`.

### 6b. Zoom cascade: density, points resolve, kNN ego ball

The same nested-crop cascade, recast in the serif look: equal
square frames with **sharp black** (`ink` 0.9pt) spines, a navy `Blues` density tint at
level 1, the two-tone dot rule at "points resolve" (dense-core navy `navy`, periphery
lighter-blue `accentMd`), and the ego ball at the end with a quiet gray ring, thin
black spokes, a navy ego dot, and a `$z_u$` label set directly beside the node (no leader
line). Zoom windows are dotted `ink`; focus lines are tapered gray `ink` dashed at
`opacity=0.45`. The "ONE point field, nested crops" coherence law (top of this file) still
holds, these are display coordinates for the recipe; in production drive them from the
generator.

```latex
\begin{tikzpicture}[x=1cm,y=1cm]
  % frame 1: whole domain as a navy Blues density field
  \begin{scope}
    \clip (0,0) rectangle (3,3);
    \foreach \col/\sc in {ramp1/1.0, ramp3/0.62, ramp5/0.30}{
      \begin{scope}[shift={(1.5,1.6)}, scale=\sc]
        \fill[\col] plot[smooth cycle,tension=0.7] coordinates
          {(1.0,0) (0.55,0.9) (-0.7,0.8) (-0.95,-0.2) (-0.3,-0.95) (0.7,-0.7)};
      \end{scope}}
    \draw[ink, densely dotted, line width=0.5pt] (1.55,1.35) rectangle (2.25,2.05); % zoom window
  \end{scope}
  \draw[ink, line width=0.9pt] (0,0) rectangle (3,3);
  \node[note, anchor=south west] at (0.05,3.05) {density field};
  % frame 2: points resolve (two-tone navy/accentMd dots)
  \begin{scope}[shift={(4,0)}]
    \clip (0,0) rectangle (3,3);
    \fill[ramp1] plot[smooth cycle,tension=0.7] coordinates
      {(2.6,1.8) (1.8,2.6) (0.6,2.2) (0.6,1.0) (1.7,0.5) (2.6,0.9)};
    \foreach \p in {(1.0,1.2),(1.4,1.7),(0.9,1.9),(1.7,1.3),(1.3,2.1),(2.0,1.8),(1.6,2.4)}
      \fill[navy] \p circle (2.0pt);                  % dense core: navy mu_0
    \foreach \p in {(2.2,1.1),(2.4,2.0),(2.0,0.8),(2.5,1.5)}
      \fill[accentMd] \p circle (2.0pt);                  % periphery: lighter blue
    \draw[ink, densely dotted, line width=0.5pt] (1.05,1.35) rectangle (1.75,2.05);
  \end{scope}
  \draw[ink, line width=0.9pt] (4,0) rectangle (7,3);
  \node[note, anchor=south west] at (4.05,3.05) {points resolve};
  % frame 3: one element u + its kNN ego-ball (labeled z_u)
  \begin{scope}[shift={(8,0)}]
    \clip (0,0) rectangle (3,3);
    \def\eg{(1.5,1.5)}
    \draw[annot, line width=0.7pt] \eg circle (0.95);   % quiet grey ego ring
    \foreach \p in {(0.85,1.95),(2.15,1.75),(2.25,1.05),(1.35,0.6),(0.7,1.1),(1.95,2.1)}{
      \draw[ink, line width=0.6pt] \eg -- \p;            % thin black spokes
      \fill[accentMd] \p circle (1.6pt);}                  % neighbors (lighter blue)
    \fill[navy] \eg circle (2.1pt);                    % the ego u (navy), last on top
    \node[accent, font=\figL, anchor=west] at (1.65,1.5) {$z_u$}; % label, NO leader line
  \end{scope}
  \draw[ink, line width=0.9pt] (8,0) rectangle (11,3);
  \node[note, anchor=south west] at (8.05,3.05) {neighborhood};
  % tapered grey focus lines between frames (zoom-box corners -> next frame corners)
  \draw[ink, opacity=0.45, densely dashed, line width=0.4pt] (2.25,2.05) -- (4,3);
  \draw[ink, opacity=0.45, densely dashed, line width=0.4pt] (2.25,1.35) -- (4,0);
  \draw[ink, opacity=0.45, densely dashed, line width=0.4pt] (5.75,2.05) -- (8,3);
  \draw[ink, opacity=0.45, densely dashed, line width=0.4pt] (5.75,1.35) -- (8,0);
\end{tikzpicture}
```

### 6c. "Points resolve" as an embedding overlay

When the "points resolve" stage is a learned-embedding scatter rather than raw points,
draw it as an unframed overlay: light-gray truth under, navy prediction over (quality reads
as "does navy cover grey"), a lower-left L-glyph of two short arrows instead of an axis
box, and a two-dot legend.

```latex
\begin{tikzpicture}[x=1cm,y=1cm]
  % light-grey "Data"/measured cells UNDER
  \foreach \p in {(0.8,1.6),(1.1,1.9),(0.6,1.2),(1.4,1.7),(1.0,2.2),(1.6,2.0),
                  (2.0,1.5),(1.3,1.3),(0.9,1.0),(1.8,1.8),(2.2,2.1),(0.7,1.8)}
    \fill[truth, opacity=0.7] \p circle (2.6pt);
  % navy "Predictions" OVER (covering the grey = good fit)
  \foreach \p in {(0.85,1.55),(1.05,1.95),(0.62,1.25),(1.42,1.66),(1.02,2.15),
                  (1.58,1.98),(1.95,1.52),(1.33,1.28),(2.18,2.05),(0.73,1.75)}
    \fill[navy, opacity=0.6] \p circle (2.0pt);
  \draw[ink,->,>={Stealth[length=1.6mm]}] (0.2,0.6) -- (0.2,1.4)      % corner L-glyph
    node[midway,left,font=\figS,rotate=90,anchor=south]{UMAP 2};
  \draw[ink,->,>={Stealth[length=1.6mm]}] (0.2,0.6) -- (1.0,0.6)
    node[midway,below,font=\figS]{UMAP 1};
  \fill[truth] (3.0,2.0) circle (2.4pt); \node[font=\figM,anchor=west] at (3.15,2.0){Data};
  \fill[navy]  (3.0,1.6) circle (2.0pt); \node[font=\figM,anchor=west] at (3.15,1.6){Predictions};
\end{tikzpicture}
```

---

## 7. A bounded domain read as a sphere

To make a bounded 2D domain read as a *sphere* (not a flat disc) **subtly**:

- **Super-thin graticule**: a *few* latitude ellipses + meridian ellipses, `black` at low
  opacity (`~0.3`) and hairline width (`~0.12pt`). Too many lines, or solid black, reads as
  a globe/clip-art, users push back hard on that. Compute the ellipse radii in Python
  (`rx=R*cos(lat)`, `ry≈0.16R*cos(lat)`; meridians `rx=R*sin(lon)`) and emit as a file; an
  inline `\foreach` with `\pgfmathsetmacro` can fail with *"Unknown operator 'a'/'an'"* when
  results concatenate before `and` in `ellipse (rx and ry)`.
- A faint orthographic **foreshortening** of the territory paths (`r' = sin(r·π/2)`) bunches
  detail toward the limb.
- A thin rim (`ink!85`, ~0.5pt). Heavy radial *ball shading* tends to gray-out and muddy the
  colors, used cautiously if at all.

---

## 8. Frames, focus lines, whitespace

- Equal square frames, `ink!85` ~0.6pt, `rounded corners=2pt`. Generous inter-frame gap
  (frame centers ~2.9 apart for 2-unit frames) so the cascade breathes.
- Tapered **dashed focus lines** (`ink!45`, ~0.4pt) from the two right corners of each
  zoom-box to the two left corners of the next frame.
- A faint base fill (`<color>!8`) under each frame so contour-band seams never show white
  pinholes at triple junctions.

---

## 9. Assembly and delivery

Generate bodies as separate `\input` files during iteration (fast to regenerate), but
**deliver a self-contained `.tex`** by inlining every `\input` (regex-replace) so it
compiles anywhere with no external assets. **Verify the inlined file compiles in a clean
directory** before shipping. Keep `\documentclass{standalone}`.

> Authoring-loop gotcha: if you assemble by appending one generated body into the figure
> `.tex` once (`cat body >> fig.tex`), later regenerations of `body` won't take, the figure
> holds a frozen copy. Use `\input{body.tex}` so edits to the body actually apply, then
> inline only at the final delivery step.

Density-band figures emit many vector paths → the `.tex` can be ~0.5 MB of coordinates.
That's fine and prints crisply; mention it so the size isn't a surprise.

---

## 10. Process

This panel type is **highly iterative and taste-driven**. Always render to PNG and **share
the PNG every turn**, the user is judging a look, not a spec, and cannot evaluate a
description. Make the smallest change they asked for, re-render, show it. Resist
"improving" several things at once. Build the substrate first and get explicit sign-off on
the territory layout *before* softening it into density; get sign-off on the density
*before* adding the zoom; etc. Confirm shape/feel words ("irregular", "cloudy", "muted",
"brown not gold") with a quick options prompt rather than guessing.
