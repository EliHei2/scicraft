---
name: paper-website
description: Builds, refines, checks and deploys the project website of a research paper (project page, model or dataset release page, interactive results page, password-gated preview for co-authors). Use it whenever the user wants a page for a paper or preprint, asks to bring a site up to a new revision, to make it nicer, simpler or "sexier", to add a gallery, a viewer, a comparison slider, a method animation or a leaderboard, to hunt bugs on it, or to publish, gate or take down a preview, even when they only say "the site" or "the page". Holds what goes on the page and what waits behind a click, copy rules against machine-made text, native charts from the paper's records with build-time checks, honest gallery and comparison views, a tested dark starter page, and scripts for a local server, layout audit, screenshots, behavior, touch and gate checks, a leak scan and an encrypted gate. Use data-figures for figures in the paper itself and research-release for the code and weights.
---

# paper-website

How to build the website of a research paper so that its author says "I like it a lot". Distilled from building one
site over many rounds with a demanding lead author, for a machine-learning paper with an interactive showcase,
benchmark results, a gallery and a gated preview. Almost every rule here is something the author asked for or
something the author threw out, so each comes with its reason. Where the author of the site at hand says otherwise,
they win: write their rule into `DEPLOY.md` with the date and follow it.

> **PRIME DIRECTIVE: less is more.** The page shows three or four big things and lets the visitor touch the paper's
> main claim. Everything else waits behind a click. Words are rationed: say very little, and when you say something
> it has to be the best thing to say there. When the author asks for "nicer", "cooler" or "sexier", remove and
> embolden. Do not add.

The failure to fear is a page that "smells of AI": taglines, rows of statistic tiles, card grids, the same content
twice, boilerplate blocks, clever charts, long paragraphs. Section 11 lists what was thrown out and what replaced it.
Read it before you design anything.

Three failures cost the most rounds in the original project. Guard against them from the first minute:

1. **Adding when asked to improve.** Cards for each ablation were called "so complicated and smells AI"; the plain
   heat map that replaced them was never rejected (sections 3 and 10).
2. **A number or sentence that is not the paper's.** The page drifts from the paper unless a builder checks every
   number and every quoted sentence against the records and the TeX at build time (section 4).
3. **A picture or a comparison the paper cannot back.** A gallery render from a model trained on the sample it
   shows, a coarse model output set beside a fine reference, a drawing with one level more than the paper's table
   (section 3).

## 0. Before building

Collect these by reading the project, and ask only for what cannot be found, in one message:

- **The paper of record**: the TeX (preferred) or PDF of the current revision, and who edits it. Another session or a
  co-author may be changing it while you work, so check for a newer revision before you paste anything. When another
  session owns a document you find faults in, do not edit it: hand that session a table of what is printed and the
  remedy for each, one row per fault.
- **The records behind every number**: the JSON or CSV the paper's figures and tables are made from, and the figure
  code. The page draws from these, never from numbers typed by hand.
- **The pictures**: the data and the color rules of the paper's own figures of its showcase example, and which
  checkpoint made each render.
- **People**: authors in order, roles, affiliations, logos, the project's mark.
- **What may be shown**: is the work unpublished or under double-blind review, are there patient or in-house data,
  which licenses do public data carry, what is released (code, weights, demo, citation) and what is only coming.

Decide three things, and tell the author your choice in one line each:

1. **The one interaction that shows the claim.** For a model, usually a divider between a reference (labels, the
   input, a baseline) and the model's output on the same sample, with zoom or a scale chooser; for a benchmark
   paper, the ranks per task that the visitor can point at. It goes at the top and it is the reason the page exists.
2. **Public or gated.** Unpublished work gets a password gate and no indexing (section 7).
3. **Where it lives**: a folder beside the paper repository, never inside its history (`<project>-site/`).

For a new kind of project with no starter that fits, survey first: fingerprint about 100 paper pages of top
machine-learning work for fonts, media and section rhythm (keep the results in memory only), screenshot about 24 into
a contact sheet, and read the source of the closest one. The starter below already encodes the outcome of that
survey, so skip it when the starter fits.

Start from the starter: copy `assets/starter/public/` to `<project>-site/public/` and
`assets/starter/pipeline/` to `<project>-site/pipeline/`, copy the scripts you need from `scripts/` into `pipeline/`,
and keep these beside them:

```
<project>-site/
├── public/        what is deployed: index.html, site.css, page.js, charts.js, data/, brand/, fonts/
├── pipeline/      never deployed: builders that write public/data, the checks, the gate, the secrets
├── retired/       never deployed: every block that left the page, so it can come back
└── DEPLOY.md      one page: what each builder does, how to deploy, how to take it down, the author's rules
```

## 1. The page

One long page, one column, sections under hairlines. This order is the one that survived:

| Part | Holds | State |
|---|---|---|
| First screen | the mark large beside the name, the rest of the title, authors with marks of their institutes, the one interaction | open |
| Opening | at most three short statements of the problem in the author's words, then the paper's main claim in one sentence | open, about 40 words |
| A second interaction, if the paper has one | e.g. query any region or any row, computed in the browser | open |
| How it works | interactive method figures with the paper's sentences as step captions, ending on what the model was trained on (one statement, a few numbers, one sentence) | open |
| Results | two numbers, **one** figure for the main claim, one more only if it shows a different thing; then rows | figure open, rest closed |
| Supporting evidence | ablations, other backbones, amount of data: a lead sentence and rows | closed |
| Gallery | a wall of tiles; a click opens the comparison in a dialog | wall open |
| Release | what exists and what is coming, each said once; the planned interface; model card and limitations as rows | list open |
| Close | the paper's last sentence, a way back up, the marks | open |

Rules that shaped it:

- **How it works comes before the results** ("first put how it works then evaluation results ... it's sexier"). An
  engagement reviewer once moved results up; the author moved them back the same evening.
- **Nothing stands over the name.** No tagline, no eyebrow, and never a result claim at the top of the page.
- **No abstract on the page.** It is too much text. The opening is a few statements and one sentence.
- **Results are not in the opening or the data block.** The data block says what the model was built from and, if the
  author wants it said, that this is a first version with more to come.
- **A closed row is a claim.** Its line is the finding as the paper states it; the figure, table or list opens under
  it. Reference material (full table, protocol, model card, limitations) is always a row.
- **Never the same content twice.** Not a table and a heat map of it both open, not tiles that restate a heading,
  not affiliations at the top and again as a list in the footer.
- **The footer holds marks only.**
- **A citation is offered when the paper can be cited.** Until then "Cite" is one more line that says "coming soon".

Details, markup and what each part must not contain: `references/anatomy.md`. A personal or lab homepage follows
the same grammar with a first-person voice (`references/anatomy.md` section 14).

## 2. Words

- **Paste, do not write.** Running text is whole sentences from the paper, so the page speaks with the author's voice
  and cannot drift from the paper. When a sentence is lifted out of its paragraph, remove connectives that point at
  what is no longer there ("Finally", "Thus", "Yet", "therefore", "such fields").
- **The author's own lines beat the paper's when they offer them**, but they will offer more than the page can hold.
  Take the one or two strongest and let the structure carry the rest. Do not explain them.
- **Display text is concrete.** A label says what the thing is or what the number counts, with the unit after the
  number: "11 of 12 datasets", not "first, any 4 or more".
- **A headline number names the variant it belongs to.** If the paper has two readouts or two sizes, "1st" says
  which one; a reviewer once read such a number as a best of two.
- **Banned, because they read as machine-made**: chains of fields ("A × B × C" and the same with middle dots), any
  dot, bullet or pipe set between phrases (write a comma or a sentence), slogan triads, the same statement in two
  places, filler captions, evaluative words where a measured relation exists (`best`, `leads`, `wins`, `strongest`,
  `best published`, `falls behind` become "ranks first by [measure]", "is rated above") in text you write; a
  sentence the author wrote with one of them and a named measure stays as written. The shared rank vocabulary is
  owned by the sibling skill `stats-reporting/references/vocabulary.md`.
- **A replacement obeys every standing ban, not only the one just stated.** A replacement for a "×" line used middle
  dots and was rejected the same evening.
- **One statistics language: the paper's.** Do not mix kinds of evidence, and never swap in a different statistic to
  make a claim look better. If the author has display rules (for this author: no p value above .01 in front, no
  confidence intervals, one correction method), they become build checks, they apply to every result alike, the
  rivals' and the unfavorable ones included, and the full statistics stay in the paper, which the page points to.
  The package default is adjusted p and the IQR on display, with a 95% CI printed where the size of an estimate is
  the claim; a no-CI display rule never removes an interval from the paper's tables (see the sibling skill
  `stats-reporting/references/spread-and-intervals.md`).
- **Typography carries meaning.** A number stays on the line of its unit (`45&nbsp;µm`). No last line of one word:
  short blocks use `text-wrap: balance`, longer ones get their last words bound with `&nbsp;`. An author's name and
  its superscript break only as one group.
- **Names agree everywhere.** A row label in a chart, the caption under it and the table use the same name. After a
  renaming, the old name leaves no trace in text, charts, table, code or tests: sweep with grep, then add a guard.

## 3. Figures

- **Draw them natively from the records** (plain SVG, no library, `charts.js` in the starter), each under its claim.
  A chart plays once when it comes into view and has a hover layer. Do not paste the paper's figures as images.
- **Simple forms**: heat maps, plain bars from a baseline, dots, rank lines. One encoding per fact. When the author
  asks for something "stronger", make the same form cleaner; do not invent cards, pictograms or a second view.
  A heat map of the largest effect per row and column, with the value printed in the tile, has never been rejected.
- **The wins carry the weight** ("bigger boldness of big wins"): first place in the heaviest type, rank tints rising
  from third to first, the best rank the lightest tile on a dark ground. This is allowed because every value stays
  printed, and the same weight goes to whoever is first in a column (`references/patterns.md` section 4).
- **No error bars or intervals unless the paper's figure has them and the author wants them.** Significance is said
  in the paper's words under the figure. A figure whose claim is the size of an estimate keeps its interval.
- **Definitions live under the pointer.** Task and metric names carry a one-line definition from the paper
  (`data-term` in the starter), not a paragraph beside the chart.
- **Pictures of the model's output are the paper's**: same data, same color rule, same resolution on the first
  frame. When someone says a picture "looks old", do not argue from memory. Compare it with the paper's figure
  numerically (per-channel correlation and means of the two images) and look at both, then say what you found.
- **A comparison view compares like with like.** The reference keeps its own native unit; the model's side carries
  the scale chooser; a coarser view of the reference uses the model's grid and footprint; both sides have the same
  width and window; overlays contrast with the ground (white outlines at the finest zoom on a dark page). Detail in
  `references/anatomy.md` section 2.
- **Every gallery image is honest**: made by the model the paper reports, on data it was not trained on, with its
  provenance in the builder log; among such renders take the most vivid. An item ships only with its reference
  layer; one without waits on a hold list. Someone else's automatic labels are attributed as such. Detail in
  `references/anatomy.md` section 10.
- **Method figures**: a canvas that plays once in view, rests on a finished frame before and after, skips ahead on a
  click, takes each step's caption from the paper, and claims no more than the paper (one drawing showed four levels
  where the paper's table has three). Build them on `assets/fx/core.js`, which does all of this and exposes the
  `seek` hook the sweep check needs (`references/patterns.md` section 14). Mathematics in labels is TeX drawn as
  glyph outlines (`scripts/tex_labels.py`, `assets/tex.js`).
- **A figure that must stay an image** is recolored for the ground by rule with `scripts/darken_figure.py`, never put
  on a white plate; data images inside it are extracted as originals (`--extract-images`), never recolored.
- **Gallery**: a wall of equal tiles without labels (the reference shows under the pointer), a column count that
  never leaves one tile alone in the last row, extra or lower-resolution sets last, and a dialog with the divider,
  a legend that names every color in the picture, previous and next.
- **A decorative embedding picture is checked before it ships** (neighborhood preservation and label purity of
  neighbors; `references/verification.md` section 7), and the report says what it is.
- New palettes: validate them (the `dataviz` skill has a validator, where it is installed). Text never wears a
  series color.

## 4. Numbers that cannot drift

Every number on the page is produced by a builder in `pipeline/` and checked at build time. The pattern is in
`assets/starter/pipeline/build_results.template.py`:

1. Read the records through the paper's own figure code where possible, so the page and the paper share one path.
2. Write `public/data/results.json` with **only what the page draws**. A value nobody draws (a test statistic, a p
   value, an interval) does not ship, even unseen.
3. Check the page: every number written in `index.html` and every sentence quoted from the paper must be found in
   the records and in the paper's TeX, or the build fails.
4. Turn the author's rules into guards in the same check: banned words and marks, forbidden statistics, retired
   names, blocks that must not come back.

When the paper moves to a new revision, point the builders at it, run them, and fix what the checks report. If the
paper and its records disagree, the page follows the paper and you tell the author what you found, in one line.

## 5. Look

The starter's `site.css` is the design system; the `design-system` skill holds the same tokens across media. Its
choices, and why (sizes in `references/patterns.md` section 1):

- **Dark ground `#141416`, the color the output renders already sit on**, so their colors read as in the paper. One
  column of 1080 px. Sections are layers: a hairline, a large name, one mono line with a single fact at the right.
- **Type**: Helvetica Neue with Inter as fallback, IBM Plex Mono for labels and scale bars, both fallbacks
  self-hosted (no request leaves the page) with their license texts. One accent for the paper's method (`#8ec9ff`),
  one for the strongest comparator (`#e69f00`).
- **No cards, shadows, gradients or rounded panels.** Hairlines, type and space do the work.
- **The mark** stands large beside the name on the first screen and shrinks into the bar as the page scrolls. It is
  one image, moved by `page.js`, so there is never a second mark.
- **Phones are a first-class layout**: grids collapse, the dialog fills the screen, hover has a tap equivalent, and
  every gesture a widget owns is tested with real touches.

Patterns with code (rows that open, the chart wrapper, the dialog, the tooltip, the builder, large data, figures that
stay images, TeX labels): `references/patterns.md`.

## 6. How it is built

- Plain HTML, CSS and ES modules. No framework, no bundler, no build step for the page itself. It must open from a
  static host and from `scripts/serve.py`.
- A chart inside a closed row is built when the row opens; a link that points into a closed row opens it first
  (on load, on a click, and when the address changes later).
- Large data are fetched by HTTP ranges in chunks the viewer needs, each file under the host's limit. Measure the
  whole site against the host's deploy time limit before the first push; every reduction for size gets a
  before-and-after picture at the finest zoom. Point layers are packed by `scripts/pack_points.py` and object
  outlines traced by `scripts/build_masks.py` (`references/patterns.md` section 11).
- Whatever leaves the page moves to `retired/` with a one-line note. Dead CSS and JS go with it.
- `DEPLOY.md` is kept current: builders, order, deploy, take-down, the hold list, and the author's rules with dates.

## 7. Private until it is public

Treat an unpublished paper's site as confidential. `references/deploy.md` has the steps; the rules are:

- **Gate it** with `scripts/gate.py` (the page is encrypted inside a sign-in page, assets sit under a secret folder,
  `robots.txt` disallows everything) and say plainly that this keeps casual visitors out and is not strong access
  control. Never print the password or the secret folder name in logs, reports or commits; mask them in every output
  you show. Give the password to the author in the conversation when they ask.
- **Scan before every push** with `scripts/leak_scan.py`: local and cluster paths, e-mail addresses, tokens, sample
  or patient identifiers, image metadata, the password itself. A hit inside a compressed binary may be chance bytes;
  check before acting.
- **Anonymize in the builder**: raw sample names never leave the script that reads them.
- **Nothing about the project goes to an outside service.** Fonts and scripts are self-hosted.
- **Deploying is the author's decision**, taken once for the preview and again for going public. Keep the take-down
  command in `DEPLOY.md`. Follow the project's rules for commit messages.

## 8. A model or dataset release

Suggested, not yet tested in real work: the site this skill came from shipped its release block with every item
still "coming soon". `references/ml-release.md` has the list of what exists, the model card on the page (one source
with the card on the hub), a leaderboard chart built from the same tested charts and builder checks, weights,
license and version lines, and a hosted demo. What has evidence: each line says what it is, where it lives and its
status; a line becomes a link only when the thing exists; a license is named only once the author confirms it;
versions are `0.x` until launch and `1.0.0` at launch. The release itself is the `research-release` skill.

## 9. Verify, then say it is done

Layouts are judged by looking, behavior by checking. For every change:

1. `node pipeline/behave.js 1440` and `390`: PASS or FAIL lines (start from `scripts/behave.template.js`; every bug
   that is fixed and every rule the author sets becomes a check).
2. `node pipeline/audit.js` and again with `OPEN=1`: overflow, last lines of one word, labels that broke, numbers
   split from their units, grids with a lone last item, author groups that broke, from 320 to 1440 px.
3. `node pipeline/shot.js ...` and **look at the shots**. The audit finds measurable faults, not ugly ones.
4. For interactive figures: `node pipeline/touch.js 390` (a vertical swipe on a figure scrolls the page, a sideways
   drag on a divider moves it, a drag on a canvas completes without `pointercancel`, a tap selects) and
   `node pipeline/sweep.js` (each figure through its timeline and under a sweeping pointer, failing on any console
   error). Screenshots once hid a lasso that collapsed to a tap on phones.
5. Before a deploy that matters, one adversarial reviewer (a single read-only subagent) hunts for what is broken,
   redundant, inconsistent, machine-made, or drawn beyond what the paper says. Verify what it reports, apply with
   judgement, and decline what contradicts the author's explicit wishes. When the author asks for several lenses,
   run a panel of four (design, interaction, cognition, domain and ML reviewer). Briefs and gotchas:
   `references/verification.md`.
6. Build, scan, push, wait for the host, then run `gate_check.js` and step 1 against the live address.

Report what the checks printed. If something was not checked, say so.

## 10. Working with the author

- **A rule given for one place holds everywhere.** "No dots between things" is about the tooltips too. Sweep the
  whole site, then add a guard so it cannot return.
- **"Nicer" means simpler.** When a figure is called weak, the fix is usually a plainer form of the same data.
- **Do not add what was not asked for.** If something seems missing, say so in one line and let the author decide.
- **When the author doubts something, check it and show the evidence**, including when they turn out to be right for
  a different reason than they gave.
- **Record decisions with the author's words and the date** in `DEPLOY.md` and in memory. Later rounds override
  earlier ones.
- **A fix for someone using the page right now ships alone**, before the larger round goes on.
- **After an outage or a long silence, the first message gives the state of each job in one line** ("Upload: failed,
  nothing reached GitHub, retrying in 8 batches. Animations: three of four rendered. Nothing is public."), then
  work. Check machine state yourself (free disk, what is deployed) before asking the author.
- **Any command the author must run is one line.**
- **End every round with a short report**, readable on a phone, in this order:
  1. whether it is live, and where;
  2. what changed, one line per change, in the author's terms;
  3. what you did on your own judgement, which always includes **every place the page departs from the paper**: a
     sentence that is not the paper's ("one caption sentence is mine"), a demo parameter that differs from the
     paper's ("these bin sizes divide this window evenly; they are not the paper's supports"), a number re-ranked by
     a page choice, a picture that is schematic rather than computed, a display that is not the model's output ("a
     display of 60,000 of the points, not the model's output"), and the reviewer suggestions you declined;
  4. what needs the author's word;
  5. which checks ran, and which did not.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words, or the reason | Replaced by |
|---|---|---|
| a tagline over the title, in any wording | "it's cringe and vague"; "this should not be at the top of the page" | nothing |
| dots, bullets or pipes between phrases | "please never use AI slop like `·` in between things" | a comma, or a sentence |
| the abstract and opening paragraphs | "LESS is MORE, just very selectively say sth" | three short statements and the main claim |
| results before the method | "first put how it works then evaluation results" | showcase, how it works, then results |
| a row of statistic tiles under a figure | restates the heading, invites weak numbers | one sentence under the figure |
| cards with bars for each ablation | "so complicated and smells AI" | one heat map, value in the tile |
| a table and a heat map of it, both open | the same thing twice | heat map open, table in a row |
| first place in the same weight as the rest | "bigger boldness of big wins" | heavy type and rising tints, values printed |
| robustness and control figures | not what the page sells; they stay in the paper | a row, if asked for |
| a figure with pictograms and bands | a weak picture of a null result | dropped from the page, kept in the paper |
| error bars and intervals beside p values | "CI is ugly and not uniform with p-value" | the paper's sentence |
| an affiliation list in the footer | repeats the top, read as a bug | marks only |
| a name whose superscript wrapped alone | "affiliations for no reasons go to second line only for one name" | each name and its marks one group |
| a BibTeX block before the paper is citable | pretends it can be cited | "Cite, coming soon" |
| a reference rendered coarser than the model's output | both sides must show the same unit | reference in its native unit, chooser on the model's side |
| black outlines on a dark picture | "black on black is not visible" | thin white outlines |
| a figure pasted on a white plate | "the background transparent and not white, don't just copy paste" | recolored by rule, data tiles as originals |
| a gallery render from a model trained on that sample | "can't go in honestly" | renders of the reported model on held-out data |
| a low-resolution sample in the first screen | "if we don't have in high resolution then in the gallery is fine" | the gallery's last row |
| a coarse first frame of the showcase | "looks like an old one" | the paper figure's resolution |
| text blocks added unasked | dilutes the page | removed |

## Files in this skill

| File | Use |
|---|---|
| `assets/starter/public/` | the page to start from: structure, design system, behaviors, example data marked as such, fonts with their licenses |
| `assets/starter/pipeline/build_results.template.py` | the builder pattern: records in, checked JSON out, page checks and guards |
| `assets/tex.js` | page module that draws TeX labels from `tex_labels.py` output on a canvas or inline |
| `assets/fx/` | method-figure engine (`core.js`, `parts.js`, `fx.css`) and a toy scene (`example.html`) |
| `assets/unpack_points.js` | page module that fetches and unpacks `pack_points.py` and `build_masks.py` chunks |
| `scripts/serve.py` | local server with HTTP ranges: `python3 serve.py 8765 public` |
| `scripts/behave.template.js` | behavior checks to copy and grow |
| `scripts/audit.js` | layout audit at several widths, with `OPEN=1` for closed rows |
| `scripts/shot.js` | screenshots at selectors, offsets, or after a click |
| `scripts/touch.js` | real touch gestures on a phone viewport |
| `scripts/sweep.js` | each interactive figure through its timeline and under the pointer |
| `scripts/gate_check.js` | end-to-end check of a gated build, local or live |
| `scripts/_browser.js` | shared by the node scripts: Chrome, the gate, `READY`, `SETTLE` |
| `scripts/gate.py` | password-gated build of `public/` into `dist/` (needs `cryptography`) |
| `scripts/leak_scan.py` | what must not leave the machine |
| `scripts/push_dist.sh` | push `dist/` in small commits with retries |
| `scripts/darken_figure.py` | a paper figure recolored for a dark page; embedded images extracted untouched (numpy, PyMuPDF, Pillow) |
| `scripts/tex_labels.py` | TeX labels as glyph outlines for canvas figures (pdflatex, PyMuPDF) |
| `scripts/pack_points.py` | a large point layer packed into small range-fetched chunks (numpy); `--self-test` |
| `scripts/build_masks.py` | filled outlines of many objects from their own points (numpy, shapely 2.1); `--self-test` |
| `references/anatomy.md` | every part of the page, the comparison view, honest gallery images, what each part must not hold |
| `references/patterns.md` | design tokens and code patterns, large data and outlines, figures that stay images, TeX labels, method figures |
| `references/deploy.md` | gate, host, sizes, leak scan, take-down, going public, commands the author runs |
| `references/verification.md` | the checks, touch and sweep, the reviewer's brief and the panel, known traps |
| `references/ml-release.md` | the release block of a model or dataset page (mostly suggested, not yet tested) |

The node scripts need Node 18 or later and `puppeteer-core` installed in the site's `pipeline/` (`npm i
puppeteer-core`); they use the Chrome that is installed. Python scripts need Python 3.9 or later.
