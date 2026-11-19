# Bibliography hygiene

Read this when adding, cleaning or merging references, and before every submission.

## 1. Engine and style

- **natbib with BibTeX.** biber was missing on the minimal install met, and natbib plus BibTeX
  built everywhere.
- Author-year, round, for books and reports: `\usepackage[round,authoryear,sort&compress]{natbib}`,
  `\setlength{\bibsep}{2.4pt plus 1pt}`, `\renewcommand{\bibfont}{\small\raggedright}` (ragged
  right avoids a stretched first entry), style `plainnat` or a local copy of it.
- Numbered in order of appearance for Nature-family supplements: `[numbers,sort&compress]` with
  `unsrtnat`.
- ML venues: the venue's `.bst`, unchanged. In a dense venue paper set the bibliography small with
  `\bibsep 0pt` in the preamble, never by editing the `.bst`.
- One manual `thebibliography` is acceptable for a submission whose source must be
  self-contained; it went back to BibTeX with the venue `.bst` in the final revised build.
- DOIs as links: plainnat writes `\doi{<bare DOI>}`; define `\doi` before the `.bbl` is read,
  with `_` made harmless:

```latex
\makeatletter
\newcommand*{\doi}{\begingroup\catcode`\_=12 \house@doi}
\newcommand*{\house@doi}[1]{\endgroup\href{https://doi.org/#1}{\nolinkurl{https://doi.org/#1}}}
\makeatother
\Urlmuskip=0mu plus 1mu\relax     % long URLs may break
```

## 2. Checks, offline

`python3 scripts/bib_check.py --tex main.tex sections/*.tex appendix.tex --bib refs.bib`

| Finding | Level | What to do |
|---|---|---|
| cited key without entry | error | add the entry; never print "?" |
| `NEEDS_CITATION_shortdesc` placeholder | error | find the source or rewrite the claim; zero before shipping |
| duplicate key | error | merge after checking both entries |
| two keys of one work in one `\cite` | error | it prints "?" with an alias table; cite one key |
| one work under two keys (same DOI or title) | warning | print once; keep both keys working with `\bibkeyalias{alias}{printed}` in a manual bibliography, or by mapping the alias in the source; never rename a key the text uses |
| article or proceedings without DOI | warning | add the DOI |
| unbraced acronym or CamelCase in a title | warning | brace it: `{GNN}`, `{ImageNet}`; plainnat sentence-cases titles |
| preprint-only entry | info | check arXiv or bioRxiv for a published version |
| uncited entry | info | park it in a file that is not `\input` (`refs_uncited.bib`); do not delete it silently |

- Pass every `.tex` that cites: main text, sections, appendices. The original key-coverage check
  compared cites in main plus appendices against bibitems plus aliases.
- Gate: BibTeX reports 0 warnings over all cited keys (`latex_gate.py` reads the `.blg`).

## 3. Checks against the record (network; the user runs them)

`python3 scripts/bib_check.py --tex main.tex --bib refs.bib --crossref` fetches
`https://api.crossref.org/works/<DOI>` for each entry with a DOI and reports title, year and
first-author mismatches. Set `CROSSREF_MAILTO` to join Crossref's polite pool. It was run once
while building this skill and confirmed two entries; it needs internet and is not part of an
offline gate.

Beyond Crossref, by hand or with a verifier agent:

- PubMed or Europe PMC for biomedical papers (equal-contribution flags, issue numbers);
- the arXiv and bioRxiv APIs: has the preprint since been published? cite the published version;
- PMLR and NeurIPS proceedings pages; Semantic Scholar or OpenReview for ICLR venues and years.
  A `.bib` and the printed references once disagreed on year and venue (arXiv 2021 against ICLR 2022).

House conventions applied to every edited entry: full journal names; issue numbers and article
numbers as published; DOIs; full author lists up to about fifteen authors, correct leading authors
before "others" above that; braces around acronyms and proper names in titles.

## 4. Rules that are never bent

- **Never rename a key the text uses.** "Keep the ids that was used in the .tex main file." A
  270-entry repair recorded: "No key was changed. No entry was removed."
- **Resolve a citation by title and DOI, never by key.** Keys like `smith2020` collide; match on
  normalized title and DOI, then on first-author surname and year.
- **One writer edits the `.bib`.** Parallel agents propose; one agent or person applies, after a
  snapshot. After a cleaning script, diff the key sets before and after: one cleaner silently lost
  two entries, restored from the diff. Transcription debris (notes like "Transcribed from...",
  markdown links) prints in the bibliography; remove it.
- **Self-citation.** Unpublished own work is never cited as evidence; say it in words ("under
  revision at [journal]", "under review at [venue]") or cite the public preprint where it covers
  the point, with `note = {Under revision at [journal]}`. Published own work is cited for
  attribution; evidence citations go to independent sources or to an internal `\cref`.
- **Claims about cited work are checked against the cited work.** A pass over about 290 claims
  found 50 wrong: contradicted by the paper, absent from it, the wrong paper, or misstated.
- Priority claims ("we introduced X") are checked against the literature; an earlier definition
  is credited.
