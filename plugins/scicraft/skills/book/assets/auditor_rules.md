# Rules for auditors of [book short name], round [N]

Read this file in full before anything else. You are an adversarial, fresh-context auditor of a book built from the author's papers
that is submitted [date]. Precision matters more than volume.

## Where things are

- Repository root: [path]. **You are read-only on the repository.** Do not edit, move or build anything in it.
- Your lane: [lane name]. Files and line ranges: [file:lines, ...]. Propose nothing outside them.
- Audit folder for your output: [audit/roundN/]. Write `[LANE].json` there, nothing else.
- Sources of truth, in order of authority: [author's brief] > [decisions file] > the papers ([paths], latest
  version wins on numbers, the supplementary methods win on procedure) > the code ([repo paths]) when paper and
  code disagree (follow the code and flag it) > the author's wording.
- Build (do not run it on the repository; a scratch copy only if your lane needs one): [command].

## The author's rules (verbatim where quoted; they override any advice of yours)

1. The book is made from the author's papers, words and figures. Nothing is invented: no term, framework,
   limitation, comparison or evaluation that is not in the papers or the brief.
2. The author's own text gets error fixes only: facts, typos, house bans. No rewording for style.
3. Figures may only be cropped, masked, arranged, resized, moved or split, never re-made. Never rotated.
4. Credits come only from the papers' contribution sections or the author's word, never from acknowledgements.
   An unconfirmed credit is a query.
5. Unpublished own work is never cited; its status is stated in words ("under revision at [Journal]").
6. The Introduction carries no results of the author's own studies.
7. Every factual claim has a citation right after the clause it supports; no bundles; primary sources.
8. Captions: bold claim title, panel key in the book's letters, one plain source line ("Adapted from Fig. N of
   \citet{key}." or "Taken from Fig. N of \citet{key}."), no mention of slides, posters, drafts or licenses.
9. House bans: [em dashes, inline semicolons, mid-sentence colons beyond 1 to 2 per chapter, "not X but Y",
   filler openers, the project's banned terms: ...].
10. [Rules the author added this round, verbatim.]

## Known open items (the author decides these; do not propose)

- [item]

## What to return

A JSON file `{"edits": [...]}`; each item:
`{"id": "[LANE]-N", "file": "...", "old": "...", "new": "..." or null, "why": "rule or source", "type":
"surgical|semantic|query", "severity": "blocker|major|minor", "source": "file:line or page"}`

- `old` is copied from the CURRENT file, occurs exactly once in it, is at least 30 characters, contains no newline,
  and overlaps no other item. The items apply cleanly one after another.
- `surgical`: an error fix that changes no meaning. `semantic`: changes what the text claims. `query`: a question
  for the author, with `"new": null`.
- Preserve in every `new`: numbers, citation keys in order, `\cref`, `\label`, begin/end pairs, math, table bodies.
- Before returning, apply all your edits to a copy and confirm they apply and the braces balance.

Your final message (under 300 words): counts by type and severity, the five most serious findings, what you only
pattern-searched and did not read, and any rule you think conflicts with another. Deadline: [time].
