# Animated & multi-frame figures

Moving versions of the static recipes: a dot descending a loss surface, a sample
swept along a trajectory, a diffusion forward/reverse sweep, a rotating point cloud,
message passing spreading round by round, an architecture assembling block by block.
All snippets assume the shared `assets/preamble.tex` (palette + `base`, `block`,
`block accent`, `flow`, `var`, `note` styles).

**Default path: a frame deck rendered to PNG.** One cropped page per `tikzpicture`,
rasterized with `pdftoppm`. It needs no extra package, and it is the only form whose
frames can be looked at one by one. A self-contained animated PDF needs `animate.sty`
(often missing: check `kpsewhich animate.sty`); beamer overlays are for slides. Turning
frames into a GIF or MP4 needs ffmpeg, ImageMagick or gifsicle, which the user may have to
install (section 11). Every frame-deck recipe below was compiled in both themes.

**One required preamble change for a frame deck.** The shared `assets/preamble.tex` sets
`\documentclass[border=6pt]{standalone}`, which is single-page and *errors on `\newpage`*
(`! Improper \prevdepth`). For a multi-frame deck, add the `multi` option to that one
line so each `tikzpicture` becomes its own cropped page, with no `\newpage`:
```latex
\documentclass[border=6pt,multi=tikzpicture]{standalone}   % the ONE preamble edit
```
This is harmless for single figures (still one page) and is the only change needed. Every
recipe below loops `\foreach ... { \begin{tikzpicture}...\end{tikzpicture} }` and `standalone`
emits one page per picture. Do **not** put `\newpage` inside a `standalone` document.

**Contents**
1. Delivery modes (frame deck → PNG; `animate`; beamer)
2. The frame-macro idiom (`\StageBase`, the frame-size lock, motion forms)
3. Gradient descent on a loss surface
4. A sample swept along a trajectory
5. Diffusion forward / reverse
6. Rotating 3D point cloud
7. Message-passing propagation
8. Incremental architecture build-up (frame deck + beamer overlay)
9. Two extras: scaling-law point, teacher-student EMA
10. Anti-overflow circular fill (progress ring)
11. GIF / MP4 assembly (user installs one tool) + the four design gates

---

## 1. Delivery modes (in priority order)

1. **Frame deck to PNG (the default; plain pdflatex).** With
   `multi=tikzpicture` set (see the caveat above), each `tikzpicture` is its own cropped
   page; rasterize every page and look at the first, a middle and the last PNG. No extra package, no `\newpage`.
   ```bash
   pdflatex -interaction=nonstopmode -halt-on-error deck.tex   # one page per tikzpicture
   pdftoppm -png -r 150 deck.pdf frame      # -> frame-1.png, frame-2.png, ...
   python3 scripts/render_figure.py deck.tex --dpi 150   # same, plus the frame-size check
   ```
2. **`animate` self-contained PDF (OPTIONAL, gated).** Only if `kpsewhich animate.sty`
   succeeds. Then, in the preamble add
   `\usepackage{animate}` and wrap the per-frame body:
   ```latex
   % requires animate.sty -- check: kpsewhich animate.sty
   \begin{animateinline}[poster=first,controls,loop]{6}  % 6 fps
     \multiframe{8}{i=0+1}{ \DiffFrame{\i} }              % \DiffFrame from §5
   \end{animateinline}
   ```
   This plays inside a PDF viewer that runs JavaScript (Acrobat/pdf.js); it is the only
   route to a self-contained animated PDF.
3. **Beamer overlays (for talks).** Use `\only<k->{...}`
   inside one `tikzpicture` for an incremental build on a slide (§8). Beamer brings its
   own class and fonts, so it cannot `\input` the `standalone` preamble, copy the
   `\definecolor` + `\tikzset` lines you need into the beamer preamble.

The frame deck is also the *only* mode you can self-inspect: render the PNGs and look.

## 2. The frame-macro idiom

Every multi-frame figure is one redrawn stage plus one moving accent. Two rules make it
read as deliberate motion rather than jitter:

- **Frame-size lock (required).** Put `\path[use as bounding box] (...) rectangle (...)`
  as the first line of *every* frame, sized to the largest extent any frame reaches.
  Without it `standalone`/cropping re-fits each page and the figure visibly jumps frame
  to frame. (Also a `workflow_qa.md` gotcha.)
- **Redraw a fixed base, move one element.** Factor the static backdrop into a macro
  (`\StageBase`) drawn identically every frame; only an `accent`/`contrast` accent moves.

```latex
% the redrawn backdrop (loss basin); call it first inside every frame
\newcommand{\StageBase}{%
  \path[use as bounding box] (-3.2,-2.6) rectangle (3.2,2.6); % FRAME-SIZE LOCK
  \fill[cloud] (-3.2,-2.6) rectangle (3.2,2.6);               % identical every frame
  \foreach \s/\o in {1.55/15,1.2/30,0.85/48,0.5/68,0.22/88}
    \draw[accent!\o!white, line width=0.7pt] (0,-0.1) ellipse ({\s*1.6} and {\s*1.15});
  \fill[accent] (0,-0.1) circle (0.7pt);                     % the minimum
  \node[note] at (0,-2.2) {$\mathcal{L}(\theta)$};}
```

**Motion forms.** Discrete build (a step appears, a node lights up): drive it with
`\ifnum`/`\ifcase` on an integer frame index. Continuous sweep (a point glides along a
path, a noise level ramps): drive it with `\pgfmathsetmacro` interpolation on a real
parameter. **Never smooth a categorical change**, a node that switches state should
snap, not crossfade.

> Two `\foreach` footguns hit hard here. (1) `\fi` is a TeX primitive, never name a
> loop variable `\foreach \fi in {...}` (use `\ff`, `\r`, `\k`). (2) A bare
> `\ifnum...\fi` directly in a `\foreach` body trips pgffor's brace counting; put the
> per-frame body (with its conditionals) in a `\newcommand{\Frame}[1]{...}` and loop
> `\foreach \ff in {0,...,N}{\Frame{\ff}}`, the macro gives a clean group, and with
> `multi=tikzpicture` each `\Frame` emits its own page (no `\newpage`).

## 3. Gradient descent on a loss surface

A dot stepping down the hand-drawn basin from §2. Earlier steps stay as a faint `contrast`
trail; the live iterate carries a white halo so it reads over the rings; the
`(converged)` tag appears **only** on the final frame (a semantic-edge-frame: a label is
shown only in frames where it is true).

```latex
\def\px{{-2.55,-1.75,-1.05,-0.5,-0.12}}   % fixed descent path (x)
\def\py{{1.55,0.95,0.5,0.12,-0.02}}       %                     (y)
\foreach \f in {0,1,2,3,4}{%
  \begin{tikzpicture}[base]
    \StageBase                                                 % from §2
    \foreach \k in {0,...,\f}{%                                % steps so far
      \ifnum\k>0
        \pgfmathsetmacro{\pkx}{\px[\k-1]}\pgfmathsetmacro{\pky}{\py[\k-1]}
        \pgfmathsetmacro{\cx}{\px[\k]}\pgfmathsetmacro{\cy}{\py[\k]}
        \draw[contrast!70, line width=0.9pt, ->] (\pkx,\pky) -- (\cx,\cy);
      \fi}
    \pgfmathsetmacro{\hx}{\px[\f]}\pgfmathsetmacro{\hy}{\py[\f]}
    \fill[white] (\hx,\hy) circle (3.2pt);                     % halo
    \fill[contrast] (\hx,\hy) circle (2pt);                       % live iterate
    \node[note, anchor=south west] at (-3.1,2.15)
      {step \f\ifnum\f=4\ \textbf{(converged)}\fi};
  \end{tikzpicture}}                                           % one page per frame (multi=)
```

Here `\px[\k]` indexes a flat `\def` array, that works because `\px` is *one* brace
group. Do **not** do `\foreach \p in {{a,b},{c,d}}` then `\p[0]`: `\foreach` strips the
inner braces and the index fails (use explicit `\foreach \x/\y in {a/b, c/d}` instead,
as in §6).

## 4. A sample swept along a trajectory

A point gliding along a fixed flow path (the OT/trajectory motif). Continuous sweep:
`\tt` runs 0→1, evaluated on a cubic Bézier in closed form, leaving a fading trail. The
white halo keeps the marker legible over the curve (same trick is a static fix for a dot
over a dense point cloud, cross-link `multiscale_density_zoom.md`).

```latex
\newcommand{\TrajBase}{%
  \path[use as bounding box] (-0.4,-1.4) rectangle (6.4,1.8);   % FRAME LOCK
  \fill[cloud] (-0.4,-1.4) rectangle (6.4,1.8);
  \draw[slate, line width=0.8pt] (0,0) .. controls (2,1.6) and (4,-1.6) .. (6,0.2);
  \fill[accentL] (0,0) circle (1.6pt);  \node[note,left=1mm] at (0,0) {$x_0$};
  \fill[contrast] (6,0.2) circle (1.6pt); \node[note,right=1mm] at (6,0.2) {$x_1$};}
\newcommand{\Bez}[1]{% point on the fixed cubic at parameter #1 -> sets \bx,\by
  \pgfmathsetmacro{\bx}{(1-#1)^3*0 + 3*(1-#1)^2*#1*2 + 3*(1-#1)*#1*#1*4 + #1^3*6}%
  \pgfmathsetmacro{\by}{(1-#1)^3*0 + 3*(1-#1)^2*#1*1.6 + 3*(1-#1)*#1*#1*(-1.6) + #1^3*0.2}}
\foreach \ff in {0,1,2,3,4,5}{%
  \pgfmathsetmacro{\tt}{\ff/5}
  \begin{tikzpicture}[base]
    \TrajBase
    \foreach \s in {0,0.2,...,\tt}{\Bez{\s}\fill[accent, opacity=0.28] (\bx,\by) circle (1.4pt);}
    \Bez{\tt}
    \fill[white]   (\bx,\by) circle (3.4pt);                   % halo
    \fill[accent] (\bx,\by) circle (2.1pt);                   % live sample
    \node[note,anchor=south west] at (-0.3,1.4)
      {$x_t$,\ $t=\pgfmathprintnumber[fixed,precision=1]{\tt}$};  % round; raw \tt prints 0.59999
  \end{tikzpicture}}                                           % one page per frame (multi=)
```

## 5. Diffusion forward / reverse

A point cloud blurring to noise, then sharpening back, shown as two labeled sweeps:
frames 0 to 3 forward (clean→noise, `\sig` ramps up), 4 to 7 reverse (noise→clean, `\sig`
ramps down). `\pgfmathsetseed{7}` before the scatter loop fixes the base pattern so it is
the *same* cloud being perturbed each frame (not a fresh random splatter).

```latex
\newcommand{\DiffFrame}[1]{% #1 = 0..7  (0-3 forward, 4-7 reverse)
  \begin{tikzpicture}[base]
    \path[use as bounding box] (-2.3,-2.3) rectangle (2.3,2.3);  % FRAME LOCK
    \fill[cloud] (-2.3,-2.3) rectangle (2.3,2.3);
    \ifnum#1<4 \pgfmathsetmacro{\sig}{#1/3}\def\lbl{forward: clean $\to$ noise}%
    \else      \pgfmathsetmacro{\sig}{(7-#1)/3}\def\lbl{reverse: noise $\to$ clean}\fi
    \pgfmathsetseed{7}                                          % same cloud each frame
    \foreach \i in {1,...,40}{%
      \pgfmathsetmacro{\cx}{ifthenelse(\i<21,-0.7,0.7)}        % two target clusters
      \pgfmathsetmacro{\bx}{\cx + 0.16*rnd*cos(360*rnd) + \sig*1.7*rand}
      \pgfmathsetmacro{\by}{0.16*rnd*sin(360*rnd) + \sig*1.7*rand}
      \fill[accent, opacity={0.8-0.3*\sig}] (\bx,\by) circle (1.3pt);}
    \node[note,anchor=south] at (0,-2.15) {\lbl\ ($\sigma{=}\sig$)};
  \end{tikzpicture}}
\foreach \ff in {0,...,7}{\DiffFrame{\ff}}                       % one page per frame (multi=)
```

## 6. Rotating 3D point cloud

A fixed set of 3D points re-projected at a per-frame azimuth (`3d`/equivariance-frame
companion). Tilt is held at 18°; only the azimuth `\az` advances. Nearer points (larger
projected depth) draw bigger and more opaque, giving a cheap z-cue.

```latex
\foreach \az in {0,40,80,120,160,200}{%
  \begin{tikzpicture}[base]
    \path[use as bounding box] (-2.4,-2.4) rectangle (2.4,2.4);  % FRAME LOCK
    \fill[cloud] (-2.4,-2.4) rectangle (2.4,2.4);
    \pgfmathsetmacro{\ca}{cos(\az)}\pgfmathsetmacro{\sa}{sin(\az)}
    \pgfmathsetmacro{\ct}{cos(18)}\pgfmathsetmacro{\st}{sin(18)}
    % list each point as X/Y/Z -- do NOT nest {a,b,c} and index, \foreach strips braces
    \foreach \X/\Y/\Z in {%
      -0.6/0.4/0.5, 0.7/-0.2/0.3, 0.1/0.8/-0.4, -0.5/-0.6/-0.2,
      0.4/0.5/0.6, -0.8/0.1/-0.5, 0.2/-0.7/0.5, 0.6/0.6/-0.3,
      -0.3/-0.4/0.7, 0.5/-0.5/-0.6, -0.7/0.5/0.1, 0.0/0.0/0.0}{%
      \pgfmathsetmacro{\sx}{1.7*(\X*\ca - \Y*\sa)}              % project to screen-x
      \pgfmathsetmacro{\sy}{1.7*((\X*\sa + \Y*\ca)*\st + \Z*\ct)}%           screen-y
      \pgfmathsetmacro{\dep}{(\X*\sa + \Y*\ca)*\ct - \Z*\st}    % +1 front .. -1 back
      \pgfmathsetmacro{\rad}{1.4 + 0.7*\dep}\pgfmathsetmacro{\op}{0.45 + 0.45*(\dep+1)/2}
      \fill[accent, opacity=\op] (\sx,\sy) circle (\rad pt);}
    \node[note, anchor=south] at (0,-2.25) {azimuth $\az^\circ$};
  \end{tikzpicture}}                                           % one page per frame (multi=)
```

## 7. Message-passing propagation

Activation spreading from a seed node hop by hop (reuse the `graphs_geometry.md` §2
grammar). Each node carries its graph distance `\HOP` from the seed; in round `\r` a node
is `accent` iff its hop ≤ `\r`. The graph here has diameter 2, so round 2 fills it.

```latex
\def\NX{{0,-1.3,1.3,-2.4,0.0,2.4,-1.3,1.3}}   % node x
\def\NY{{0,1.0,1.0,2.0,2.1,2.0,-1.3,-1.3}}    % node y
\def\HOP{{0,1,1,2,2,2,1,1}}                    % graph distance from seed (node 0)
\foreach \r in {0,1,2}{%
  \begin{tikzpicture}[base]
    \path[use as bounding box] (-3.1,-2.0) rectangle (3.1,2.9);  % FRAME LOCK
    \fill[cloud] (-3.1,-2.0) rectangle (3.1,2.9);
    \foreach \a/\b in {0/1,0/2,0/6,0/7,1/3,1/4,2/4,2/5,6/7}{%    % edges first (behind)
      \pgfmathsetmacro{\ax}{\NX[\a]}\pgfmathsetmacro{\ay}{\NY[\a]}
      \pgfmathsetmacro{\bx}{\NX[\b]}\pgfmathsetmacro{\by}{\NY[\b]}
      \draw[slate, line width=0.6pt] (\ax,\ay) -- (\bx,\by);}
    \foreach \i in {0,...,7}{%                                   % nodes: lit iff hop<=r
      \pgfmathsetmacro{\nx}{\NX[\i]}\pgfmathsetmacro{\ny}{\NY[\i]}\pgfmathsetmacro{\h}{\HOP[\i]}
      \ifdim\h pt>\r pt \node[var, minimum size=6mm, fill=cloud] at (\nx,\ny) {};
      \else \node[var, minimum size=6mm, fill=accent!30, draw=accent!75!black] at (\nx,\ny) {};\fi}
    \node[note, anchor=north] at (0,2.85) {round \r: hop-\r\ neighbourhood reached};
  \end{tikzpicture}}                                           % one page per frame (multi=)
```

`\ifdim\h pt>\r pt` compares the integer macros as lengths, a portable way to compare
two `\pgfmath`/loop integers without `\ifnum` expansion headaches inside the loop.

## 8. Incremental architecture build-up

Reveal one block + its incoming arrow per frame. **Pin every block at a fixed
coordinate** (not `right=of <prev>`) so the layout does not reflow as blocks appear; lock
the bounding box to the full final extent.

```latex
\newcommand{\BuildFrame}[1]{% #1 = number of revealed stages 0..4
  \begin{tikzpicture}[base, node distance=12mm]
    \path[use as bounding box] (-1.4,-1.6) rectangle (10.6,1.6);  % FULL extent, FRAME LOCK
    \coordinate (x) at (0,0);
    \coordinate (p1) at (2.4,0); \coordinate (p2) at (4.8,0);
    \coordinate (p3) at (7.2,0); \coordinate (p4) at (9.6,0);
    \node[var] at (x) {$x$};
    \ifnum#1>0 \node[block]        (enc) at (p1) {Encoder}; \draw[flow] (x)  -- (enc);\fi
    \ifnum#1>1 \node[block accent] (z)   at (p2) {$z$};      \draw[flow] (p1) -- (z);  \fi
    \ifnum#1>2 \node[block]        (dec) at (p3) {Decoder}; \draw[flow] (p2) -- (dec);\fi
    \ifnum#1>3 \node[var]          (xh)  at (p4) {$\hat{x}$};\draw[flow] (p3) -- (xh); \fi
    \node[note,anchor=south west] at (-1.3,1.25) {stage #1\,/\,4};
  \end{tikzpicture}}
\foreach \r in {0,...,4}{\BuildFrame{\r}}                        % one page per frame (multi=)
```

**Beamer overlay equivalent** (for a live talk). One slide,
overlay specs reveal cumulatively. Copy the colors/styles you use into the beamer
preamble, beamer cannot load the `standalone` preamble. Each revealed node anchors to an
already-revealed one, so `positioning` stays valid.

```latex
\documentclass{beamer}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,backgrounds,fit}
\definecolor{accent}{HTML}{2B59C3}\definecolor{ink}{HTML}{1A1A1A}
\definecolor{cloud}{HTML}{E7E9EE}\definecolor{paper}{HTML}{FFFFFF}
\tikzset{
  base/.style={line width=0.7pt, line cap=round, line join=round, >={Stealth[length=2.2mm,width=1.8mm]}},
  block/.style={draw=ink, line width=0.7pt, rounded corners=2.5pt, fill=cloud, inner sep=6pt, minimum height=9mm, text=ink, align=center},
  block accent/.style={block, fill=accent!12, draw=accent!75!black},
  var/.style={draw=ink, circle, line width=0.7pt, fill=paper, minimum size=7mm},
  flow/.style={->, line width=0.9pt, draw=ink}}
\begin{document}
\begin{frame}
\begin{tikzpicture}[base, node distance=12mm]
  \node[var] (x) {$x$};
  \only<2->{\node[block, right=of x]        (enc) {Encoder};  \draw[flow] (x)   -- (enc);}
  \only<3->{\node[block accent, right=of enc](z)  {$z$};       \draw[flow] (enc) -- (z);}
  \only<4->{\node[block, right=of z]        (dec) {Decoder};  \draw[flow] (z)   -- (dec);}
  \only<5->{\node[var, right=of dec]        (xh)  {$\hat{x}$};\draw[flow] (dec) -- (xh);}
\end{tikzpicture}
\end{frame}
\end{document}
```

## 9. Two extras

**Scaling-law point sliding along the fitted line.** The fitted power law (a straight
line in log-log) is fixed; only the highlighted `(N, loss)` marker slides. White marker
under the `contrast` marker = the halo trick in `only marks` form.

```latex
\newcommand{\ScaleFrame}[1]{% #1 = 0..4 -> position along log N
  \begin{tikzpicture}
    \begin{axis}[spare axis, width=7cm, height=5cm,
       xlabel={$\log_{10} N$}, ylabel={$\log_{10}\mathcal{L}$},
       xmin=2,xmax=8, ymin=-1.2, ymax=0.8, clip=false]
      \addplot[accent, line width=1.1pt, domain=2:8] {1.4 - 0.3*x};   % L ~ N^{-0.3}
      \pgfmathsetmacro{\nx}{2.6 + 1.2*#1}\pgfmathsetmacro{\ny}{1.4 - 0.3*\nx}
      \addplot[only marks, mark=*, mark size=1.4pt,
               mark options={fill=white,draw=white}] coordinates {(\nx,\ny)};   % halo
      \addplot[only marks, mark=*, mark size=1.1pt, contrast] coordinates {(\nx,\ny)};
    \end{axis}
  \end{tikzpicture}}
\foreach \r in {0,...,4}{\ScaleFrame{\r}}                        % one page per frame (multi=)
```

**Teacher-student EMA update.** The teacher is fixed; the student moves a fraction toward
it each frame (geometric approach, factor 0.55), with a short `slate` pull-arrow showing
the partial step. This is the SSL EMA motif, student glides toward the EMA teacher.

```latex
\newcommand{\EmaFrame}[1]{% #1 = step 0..4
  \begin{tikzpicture}[base]
    \path[use as bounding box] (-0.6,-1.3) rectangle (6.6,1.5);   % FRAME LOCK
    \fill[cloud] (-0.6,-1.3) rectangle (6.6,1.5);
    \coordinate (T) at (5.4,0);
    \pgfmathsetmacro{\sx}{0.6 + 4.8*(1 - pow(0.55,#1))}           % student x: closes the gap
    \draw[flowfaint, dashed] (0.6,0) -- (5.4,0);
    \fill[contrast] (T) circle (2.4pt); \node[note,above=1mm] at (T) {teacher $\theta_t$ (EMA)};
    \draw[->, slate, line width=0.8pt] (\sx,0) -- ($(\sx,0)!0.45!(T)$);
    \fill[white] (\sx,0) circle (3.6pt); \fill[accent] (\sx,0) circle (2.4pt);
    \node[note,below=1mm] at (\sx,0) {student $\theta_s$};
    \node[note,anchor=south west] at (-0.5,1.15)
      {step #1:\ $\theta_t\!\leftarrow\! m\,\theta_t+(1{-}m)\,\theta_s$};
  \end{tikzpicture}}
\foreach \r in {0,...,4}{\EmaFrame{\r}}                          % one page per frame (multi=)
```

## 10. Anti-overflow circular fill

A progress ring (training %, sampling step). **Never draw a single near-360° `arc[]`** , 
floating-point rounding can wrap it to a thin gap or a full overshoot. Draw the partial
sweep as one bounded arc from 90° clockwise, and special-case 100% as a closed `circle`.

```latex
\newcommand{\RingFrame}[1]{% #1 = step 0..4 (0,25,50,75,100 %)
  \begin{tikzpicture}[base]
    \path[use as bounding box] (-1.6,-1.6) rectangle (1.6,1.9);   % FRAME LOCK
    \pgfmathsetmacro{\fracdone}{#1/4}                             % NOT \frac (math primitive)
    \pgfmathsetmacro{\ang}{90 - 360*\fracdone}                    % end angle, clockwise from top
    \pgfmathsetmacro{\pct}{100*\fracdone}
    \draw[cloud, line width=4pt] (0,0) circle (1.05);            % track
    \ifnum#1<4 \draw[accent, line width=4pt] (90:1.05) arc (90:\ang:1.05);% bounded sweep
    \else      \draw[accent, line width=4pt] (0,0) circle (1.05);\fi      % full ring, no 360 arc
    \node[font=\figfont\bfseries] at (0,0)            % \sansmath keeps digits sans
      {\pgfmathprintnumber[fixed,precision=0]{\pct}\%};         %   (else CM serif numerals leak)
    \node[note,anchor=south] at (0,-1.55) {training progress};
  \end{tikzpicture}}
\foreach \r in {0,...,4}{\RingFrame{\r}}                         % one page per frame (multi=)
```

For finer fills draw completed quarter-arcs explicitly and only the *current* partial
quarter as a short live arc, the same principle, more reliable past 75%.

## 11. GIF / MP4 assembly + design gates

**Assembly may be the user's step.** If none of ffmpeg, ImageMagick (`magick`) or
gifsicle is installed, produce the frames and hand over the exact command:

```bash
pdflatex deck.tex && pdftoppm -png -r 150 deck.pdf frame      # we produce frame-*.png
# then ONE of (user installs the tool):
ffmpeg -framerate 6 -pattern_type glob -i 'frame-*.png' -vf palettegen pal.png
ffmpeg -framerate 6 -pattern_type glob -i 'frame-*.png' -i pal.png -lavfi paletteuse out.gif
# or:  magick -delay 16 -loop 0 frame-*.png out.gif
# or:  gifsicle --delay 16 --loop frame-*.gif > out.gif      # frames must be GIFs first
```

A contact sheet is the three key PNGs (start, middle, end), shown to the user.

**Four design gates** (apply before animating at all, most figures are better as a
static small-multiple):

- **Animation Design Gate.** State what changes between frames and why motion beats a
  static row of panels. If a reader gets it from three side-by-side stills, ship the
  stills. Give each change enough dwell to be seen.
- **Motion Form Gate.** Discrete (a block appears, a node lights) vs continuous (a point
  glides, noise ramps). Pick one per element. **Never smooth a categorical change.**
- **Pacing Gate.** Map semantic states to frames, not the reverse: a highlight holds
  ≈0.5 to 1 s, a newly built structure ≈1 to 1.5 s, a dense or final state ≈1.5 to 3 s. One
  semantic state is not always one frame, hold the payoff longer.
- **Semantic-edge-frame check.** A label that asserts something (`converged`, `breach`,
  `σ=0`) appears **only** in the frames where it is true (see the `(converged)` tag in
  §3).

> Process discipline is shared with `workflow_qa.md` (presentation modes, the
> render-and-inspect loop, `check_tikz_safety.py`, the exact-vs-schematic gate, the
> bounded repair loop, the versioned-PNG rule), it applies frame by frame here. Render
> the deck, look at the start/middle/end PNGs, fix the smallest defect, re-render.
