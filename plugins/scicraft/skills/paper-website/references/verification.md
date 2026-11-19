# Checks, the reviewer, and known traps

## Contents
1. Setting up
2. The loop for every change
3. What the behavior checks cover
4. Interaction and touch
5. The adversarial reviewer, and a panel when asked
6. Comparing a picture with the paper's
7. Known traps

## 1. Setting up

```bash
cd <project>-site/pipeline && npm i puppeteer-core          # uses the Chrome that is installed; no download
cp <skill>/scripts/{_browser.js,audit.js,shot.js,touch.js,sweep.js,gate_check.js} . && cp <skill>/scripts/behave.template.js behave.js
python3 <skill>/scripts/serve.py 8765 ../public             # in the background, from the site folder
```

All node scripts read the same environment (`_browser.js`): `URL`, `READY` (a JS expression that is truthy when the
page can be checked; a page with a WebGL viewer needs its own, e.g. `READY='window.viewer && window.viewer.ready'`),
`SETTLE` (a statement that stops autoplay), `PW_FILE` (the password file of a gated build), `PUPPETEER`, `CHROME`.

Run one browser at a time against the local server. Open a fresh browser for each script run and close it at the
end: a capture script once left headless browsers open through a shadowed variable, and the local server stalled
after several pages. When cleaning up, kill only the browsers your scripts started, never the author's Chrome.
Another session may run its own server on a common port; pick an unusual one and check what `URL` answers.

## 2. The loop for every change

1. `node pipeline/behave.js 1440` and `node pipeline/behave.js 390`.
2. `node pipeline/audit.js` and `OPEN=1 node pipeline/audit.js` (rows open). Default widths 320, 390, 768, 1024, 1440;
   add 360, 375, 414 and 900 before a deploy that matters.
3. `node pipeline/shot.js 1440 900 /tmp/x top '#results' 'open:#table > summary'`, then the same at `390 844`, and
   **read the images**. Chrome repeats the top of a page in full-page shots beyond about 16,000 px, so shoot the
   viewport at targets instead.
4. For a page with interactive figures: `node pipeline/touch.js 390` and `node pipeline/sweep.js` (section 4).
5. The builders: every one that checks the page must pass.
6. After the deploy, step 1 again with `URL=<live address> PW_FILE=pipeline/.beta_password`, and for a gated build
   `node pipeline/gate_check.js 1440` and `390` (deploy.md section 3).

Optional, for a heavy viewer: measure the frame rate at each zoom stop and through any automatic flight, at the
desktop and the phone pixel ratio. The site this skill came from measured 60 fps at every stop before it deployed.
Suggested, not yet tested in real work: at each stop, count frames for three seconds in a puppeteer script built on
`_browser.js`,

```js
const fps = await page.evaluate(() => new Promise((r) => { let n = 0; const t0 = performance.now();
  (function f() { n++; performance.now() - t0 < 3000 ? requestAnimationFrame(f) : r(n / 3); })(); }));
```

once with `deviceScaleFactor` 1 and once with 3 (`page.setViewport`), and report every stop under 50 fps. The snippet
was run once on `assets/fx/example.html` while its figure played (60.7 fps at both ratios); it has not met a heavy
viewer.

A check that fails is fixed or explained before the report; a check you did not run is named as not run.

## 3. What the behavior checks cover

The template's generic checks, which hold for any page built from the starter:

- the mark is in its slot beside the name at the top and at its small size in the bar after a scroll; the first
  words of the masthead are the name (no eyebrow or tagline before it);
- the first screen's divider moves by the arrow keys;
- every row starts closed and opens on a click; with all open, every chart is drawn, everything that rises has
  risen, nothing reaches past the right edge;
- none of the banned words or marks is in the page text, in `aria-label`s or in `alt`s; every in-page link has a
  target; how many bracketed placeholders are left;
- a term's definition appears under a real pointer, inside the screen, and leaves with it;
- a link that changes while the page is open opens its row;
- the gallery starts closed; a click opens the dialog inside the screen with the page locked; its two labels never
  meet and its title is never under the picture; previous and next wrap; Escape closes;
- the bar shows progress at the end; the footer is outside `<main>`; the console is clean.

Add project checks as the site grows. The ones that proved their worth:

- every number of a block equals the paper's (`137 | 2.4 B | ...` against the records), and the sections are in the
  agreed order;
- each chart shows what its claim says (count of bars, of filled and empty tiles, the values of the top row);
- a plain press, drag and release works in every widget (a pointer gesture that starts on an `<img>` is taken by the
  browser's image drag unless the image is `draggable="false"` with `pointer-events: none`). A beta tester found
  that dragging needed a double click; it was reproduced with real mouse events (`page.mouse.down`, `move`, `up`)
  before it was fixed;
- "back to the top" restarts the showcase even when the pointer rests where a control will land;
- the data file holds no key that no chart reads.

## 4. Interaction and touch

Screenshots cannot show a gesture that is swallowed or a figure that throws at one moment of its timeline. A
read-only reviewer found that `touch-action: pan-y` on a canvas blocked the sideways swipe of its scroll wrapper and
fired `pointercancel` mid-lasso, so "draw a region" collapsed to a tap on phones; no screenshot had shown it.

- **`touch.js [width]`** (default 390) sends real touches through the browser's input pipeline: a vertical swipe that
  starts on each figure (`FIGS`) still scrolls the page; a sideways drag on each divider moves it without scrolling;
  a steep and a flat drag across each element that owns a drag (`DRAG`, default `[data-drag]`) complete without
  `pointercancel`; a tap on `TAP` (default the first gallery tile) leaves the state `TAP_OK` says.
- **`sweep.js [width ...]`** (default 1440 and 390) drives each interactive figure through its timeline at 60
  moments when `SEEK` says how (`SEEK='el.__fig && el.__fig.seek(t)'`), moves a real pointer over a 12 by 6 grid of
  it, and fails on any console error, page error or failed request.
- Add to the project's `behave.js` whatever the figures promise: autoplay starts when a figure comes into view, step
  chips jump to their step, play and pause work.
- Re-run all of them after every fix.

Both scripts were rebuilt from the description of the original checks, whose code was lost. They were run on the
starter page and on a test canvas: `touch.js` failed a canvas with `touch-action: pan-y` (steep drag canceled) and
a divider with `touch-action: none` (page did not scroll), and passed the starter; `sweep.js` reported a figure that
threw past the middle of its timeline.

## 5. The adversarial reviewer, and a panel when asked

Before a deploy that matters, and whenever the author asks for a hunt: **one** subagent, read-only, on the local
build. One is enough; a fleet costs more than it finds. Give it this brief, adapted:

```
You are doing an adversarial bug hunt and refinement review of a research project web page. Be hard on it. The lead
author wants anything found that is broken, redundant, inconsistent, sloppy or that looks machine-made.

What you are reviewing: <local URL>, sources in <path>/public (index.html, site.css, page.js, charts.js, data/).
<Three sentences on the page's structure: what is open, what is a closed row, how the gallery opens.>
The paper of record: <path to the TeX>.

Hard constraints: read-only on the site folder; do not deploy, push or change git state; never read or print the
password or secret files; nothing about the project goes to any outside service; write your scripts and screenshots
only into <scratch folder>; do not spawn further agents.

Tools: headless Chrome through puppeteer-core at <path>; ready when <READY expression>; examples to copy from:
<paths of shot.js, audit.js, behave.js, touch.js>. One page per width.

Hunt at widths 1440, 1280, 1024, 768, 390 and 360:
1. Layout: overflow, overlaps, clipped text, one-word last lines, lone items in grids, uneven spacing, anything
   touching the bar, tooltips or dialogs cut by an edge.
2. Behaviour: every row opens, draws and closes; links into rows; the dialog (open, step, close three ways, scroll
   lock, focus); the divider by mouse, keys and touch; tooltips; the showcase; no console errors or failed requests.
3. Copy, every visible sentence and every aria-label and alt: filler, triads, slogans, repeats, contradictions,
   separators the author banned, terms that must be uniform, numbers that must agree everywhere <list them>,
   statistics wording <the author's rules>, leftovers that mention removed parts <list them>.
4. Dead weight: CSS, JS and comments for parts no longer on the page; files under public/ that nothing references.
5. Accessibility basics: heading order, labels, alt texts, keyboard reach, focus outlines, reduced motion.
6. The data shown about each sample.
7. Claims of the drawings: for every figure, list what it asserts and find the sentence or table of the paper that
   supports it. Report any drawing that shows more than the paper says.

Return at most 25 findings, bugs and taste apart. For each: what, where (selector and file:line), widths, evidence
(a screenshot path or measured numbers), and the exact change you propose. Reproduce every finding first; do not
report guesses. End with what you checked and found clean.
```

Then: verify each bug yourself before fixing (some will be two true statements that merely look contradictory),
fix what is real, add a check for each fix, and decide the taste points against the author's explicit wishes. A
reviewer will suggest removing things the author asked for; decline those and say so in the report. For item 7,
check the cited TeX line yourself before changing a figure.

**When the author asks for several lenses** ("do another set of refiners and engagers ... and scientists"), one
reviewer stays the default otherwise. Then run four read-only reviewers in parallel, each told not to edit any file,
each given the same inputs (full-page screenshot slices at 1440 and 390, `index.html`, the paper's TeX), each with
one lens:

1. a design director signing off a product page: ranked findings, each with the exact CSS change;
2. an interaction and narrative designer: the first ten seconds, the scroll, how the page ends;
3. a cognitive scientist: attention, memory and trust, "without any hype or manipulation";
4. a skeptical domain lead and a conference reviewer from machine learning: each a 60-second verdict and what they
   would still ask.

Check every paper passage they cite, take what fits the author's rules, and list the declined suggestions with a
reason in the round's report. A suggestion to move results above the method, or to add a tagline, is declined by
the rules in SKILL.md section 11.

## 6. Comparing a picture with the paper's

When the question is whether the page shows the paper's picture (colors, resolution, version):

```python
a = np.asarray(Image.open(site_tile).convert('RGB')).astype(float)
b = np.asarray(Image.open(paper_tile).convert('RGB').resize(site_size, Image.BOX)).astype(float)
content = (abs(a - ground).sum(2) > 30) & (abs(b - ground).sum(2) > 30)
for c in range(3): print(np.corrcoef(a[..., c][content], b[..., c][content])[0, 1], a[..., c][content].mean(), b[..., c][content].mean())
```

High correlation and equal channel means say it is the same field and color rule; then look for what makes it
*feel* different (bin size of the first frame, saturation, an overlay). Report both the numbers and the cause.

## 7. Known traps

- **Shell heredocs that hold JS** (template literals, `$(`, `$$`) or long inline Python can be refused by the
  shell's safety check. Write scripts and patch scripts with the file tool and run them. A file tool may refuse to
  overwrite a placeholder file it has not read: read it first.
- **A synthetic `pointerover` in a headless test is undone at once** by the real pointer position left by an earlier
  click (for example the sign-in button of the gate). Hover with `page.mouse.move`.
- **`touch-action` decides who owns a gesture.** On an element inside a sideways-scrolling wrapper, `pan-y` blocks
  the wrapper's swipe and cancels a drag that starts vertical. Test both gestures with `touch.js`.
- **A tooltip that hides on scroll** needs the page at rest: wait a second after `scrollIntoView` before checking.
- **A test that starts its walk half-way down** misses what rises in the first screens; walk from the top.
- **An element with a CSS animation is its own stacking context**: a header that must paint over the viewer needs
  `position: relative; z-index`.
- **`text-wrap: pretty` does not prevent short last lines**; `balance` does, up to about six lines.
- **Rounding a stored value and then printing fewer digits** can differ from the paper by one in the last place.
- **A push script written for zsh fails under bash after its first commit is already pushed.** Run scripts by their
  path so the shebang decides, and test scripts the author will run with the system's own `/bin/bash` and tools
  (macOS ships rsync 2.6.9 and BSD grep, sed and awk).
- **Spherical or other iterative layouts of many points take minutes**: build them once into `public/data`. **Check
  a decorative embedding layout before it ships**: compute how many of each point's k nearest neighbors survive the
  layout and how many of its layout neighbors share its label, and look at both sides of a sphere. One spherical
  layout kept 0.5% of neighborhoods; parameter trials on 25,000 points and a rebuild on 60,000 brought it to 39%
  same-label neighbors. The report then says what the picture is ("a display of 60,000 of the points, not the
  model's output").
- **The disk fills.** Check free space yourself (`df -h .`) before a big build, and before asking the author to free
  any; keep fetched raw data outside `public/`.
- **The paper moves while you work.** Before pasting or rebuilding, look for a newer revision folder and at file
  times; say in the report which revision the page follows.
