# The release block of a model or dataset page

Most of this file is **Suggested, not yet tested in real work**. The site this skill came from shipped its release
block while every item was still "coming soon"; the weights, the hosted demo and the citation were not live when
the skill was written. What has evidence behind it is marked as such. Making the release itself (the cleaned code,
the weights files, the model card on the hub, the demo app) belongs to the `research-release` skill; this file is
about how the page shows it.

## Contents
1. What has evidence behind it
2. The list of what exists
3. The model card on the page
4. A leaderboard chart
5. Weights, license and versions
6. A hosted demo
7. Checks before the release goes live

## 1. What has evidence behind it

- The release section is a list of what exists or is coming, one line each (Code, Weights, a hosted demo, Cite),
  each saying what it is, where it will live and its status. Nothing pretends to exist before it does.
- "Coming soon" lines become links as each thing exists, and none claims more than exists (deploy.md section 6).
- The planned interface is shown as about five lines of code once the author has settled on it.
- The model card (input, output, size, speed, training data, license) and the paper's limitations paragraph,
  verbatim, are rows that open.
- A license is named on the page only once the author has confirmed it.
- Versions: `0.x` until launch, `1.0.0` at launch; the weights are named after the model and the version.
- A platform's own term is used and explained in one clause the first time (a hosted model page on Hugging Face is
  a "Space"; the author did not know the word).
- The data block says what the model was trained on in one plain statement ("Trained on four public benchmarks.") and,
  if the author wants it said, that this is a first checkpoint with more to come.

## 2. The list of what exists

Suggested, not yet tested in real work:

| Line | Before release | After release |
|---|---|---|
| Code | "GitHub, coming soon" | the repository link and the version tag |
| Weights | "Hugging Face, coming soon" | the model page link, the version and the size in MB |
| Hosted demo | "coming soon" | the link, and one clause on what the visitor can do there |
| Cite | "coming soon" | the BibTeX block with a copy button, once the paper can be cited |

Each link is checked from a browser that is not signed in: a link that needs a login reads as broken to a visitor.

## 3. The model card on the page

Suggested, not yet tested in real work:

- **One source for the card.** The page's model-card row and the card on the hub are written from the same file, so
  they cannot disagree. A difference between the two is a bug for the builder's checks.
- The rows: what goes in (with shapes and limits), what comes out, parameters, speed on named hardware, training
  data (sources and licenses), intended use, the paper's limitations verbatim, license, version.
- No numbers on the card that the paper does not report.

## 4. A leaderboard chart

Suggested, not yet tested in real work, built only from parts that are tested:

- A leaderboard is a benchmark table, so it follows SKILL.md sections 3 and 4: drawn natively from the records by the
  builder, one encoding per fact, the rank heat map or plain bars of the starter, the value printed in each tile,
  first place in heavy type for whichever method holds it.
- Every entry carries what the paper reports for it: the same split, the same metric, the same evaluation code. An
  entry evaluated differently from the rest is left out or marked in the row's label.
- The date of the snapshot and the version of each model stand in the chart's mono line.
- A row added after the paper (a new model, a new task) is shown only when the records hold it, and the page then
  says that the board goes beyond the paper.

## 5. Weights, license and versions

Suggested, not yet tested in real work:

- If the release invites further training, the page says what the weights contain (only the encoder, or everything
  continued training needs) in one line; the release itself decides it (`research-release`).
- The license line names the license of the code and of the weights separately when they differ.
- The version on the page, on the hub and in the code are the same string; the builder reads it from one place.

## 6. A hosted demo

Suggested, not yet tested in real work:

- The demo link says what the visit does in one clause ("embed a table of your own and see its nearest neighbours").
- A demo that may stop when its funding stops says nothing about lasting; when it moves to free hardware, the line
  changes with it.
- A widget that runs in the page itself (for example a small model compiled for the browser) is an interaction and
  follows the rules of the first screen (anatomy.md section 2) and the touch checks (verification.md section 4).

## 7. Checks before the release goes live

Suggested, not yet tested in real work:

1. Every link of the release list answers 200 from a browser that is not signed in.
2. The model card on the page and on the hub match (the builder's check).
3. The version string agrees everywhere.
4. The leak scan runs on the public build once more with fresh eyes on names, cohorts and licenses (deploy.md
   section 6).
5. The citation block is the paper's and the copy button copies exactly it.
