# Provenance, data availability and references

Procedures behind SKILL.md sections 6 and 7.

## 1. Provenance by opening the artifact

A name, a folder or a caption says what someone believed. The file says what it is.

| Question | Open this | Seen |
|---|---|---|
| which reference dataset is this | the object's own fields: dataset ID, feature count, sample barcodes or row IDs | a caption credited two public atlases; the feature count matched a third source's probe set |
| which species | symbol case of the features (all uppercase is human) | a "mouse" dataset was human (every symbol uppercase) and had been typed against the wrong species |
| which section or sample | the unit count against the vendor's published count | a cell count gave away which section a file was |
| which collection | the curation service's API, by the object's dataset ID | collection IDs recovered through the API |
| which checkpoint | the stored config inside the checkpoint, the training-data hash, the step count | the run folder's name is not evidence |
| which evaluation split | the number of rows scored against the split's size, the split file's hash | a truncated split scores fine and means something else |
| did the run cover the input | the output's extent (spatial bins, row coverage) | a `full/` folder with "All done!" in its log was a crop |
| did a fallback run silently | a recorded count against the count the intended path gives | a reference count equal to the exact number of filtered records proved no fallback ran |

Also check schemas (column names and types), rows per dataset, and which quality filter each method's input
carried. Different inputs per method is a fairness question as well as a provenance one.

**Dataset descriptors that stand out.** A summary table of datasets (size, density, area, count, number of
classes) collects values from many places. Check every value far from its siblings against the provider's own
dataset page or the repository record before it goes into a table or figure, and write the URL beside the value.
A descriptor that cannot be verified is marked "not verified", never estimated. The author asked of one such
value "is [it] really true?? ... find the exact dataset and check all info there", and of two areas "make sure
[they are] not made up". For a model benchmark the same check would cover parameter counts, training-set sizes
and context lengths copied from model cards (suggested, not yet tested in real work).

## 2. Naming and citing an algorithm

When the text says the method "uses X like tool Y":

1. Grep every version of the package for the class and its author; read the implementation and note the line of
   every threshold. List every copy across repositories. Docstrings disagree with code (two copies called
   themselves "alpha-shape style" and "concave hull").
2. Extract the manuscript's paragraphs without executing anything. A docx is a zip; `scripts/docx_paras.py` reads
   `word/document.xml` and `word/comments.xml` with `zipfile` and ElementTree and writes one row per paragraph
   (index, style, image references, text) and per comment (id, anchor paragraph, text):
   ```bash
   cp manuscript.docx scratch/copy.docx
   python3 -I scripts/docx_paras.py scratch/copy.docx > paras.tsv
   grep -iE 'concave|hull|alpha.shape' paras.tsv
   ```
   Grep the comments as well as the body: reviewer comments name the claim as often as the text does. The
   `images` column maps each `word/media` file to its paragraph, so each legend is tied to its panel.
3. Read the comparator's source for each tagged version, and its changelog. Diff the versions. A changelog note
   ("pretty similar") applied to one version only.
4. Find the original reference and its original code. Match constants line by line (in one case the tolerance
   2·dmax, the angle 90°, the step 11.25° = 180/16). Where the port differs (1.5·dmax in one rule, a parameter
   estimated per unit), the right word is "adapted from". Get DOI metadata from Crossref or Semantic Scholar when
   the paper is paywalled.
5. Check what the competing name means in the libraries readers use (a library's `concave_hull` computes a
   χ-shape, a different algorithm). Keep the name only where the code really calls that function.
6. Trace which output feeds each reported statistic. Recompute the figure's numbers from the prep data. One "IoU"
   was a set Jaccard over records, not a polygon intersection over union.
7. Deliver: bottom line first; what the code does in numbered steps with file and line; the differences; the
   minimal replacement sentence for each location in the manuscript; the source links. Suggest; do not edit a
   co-authored docx unless asked.

When the author challenges your own earlier claim ("is it really similar to [the comparator]?"), re-examine it and
say plainly if you overstated: "No, only loosely, and I overstated it in my last answer." Then give the concrete
contrast and drop the comparison from the suggested text.

## 3. Reimplementations and packages

- Name each variant by origin: `<metric>_ours` (what produced the figures), `<metric>_<paper>` (our
  implementation of that paper's recipe), `<metric>_<paper>_pkg` (the authors' package, run as coded),
  `<metric>_nocap` (without a clip). Never "published", "signed" or "v2".
- Repeat the provenance in the summary, the definition, every caption, the row labels and the appendix.
- List the settings the paper leaves open and the values chosen. Do not call a reimplementation exact when the
  paper leaves settings open.
- Check the competitor's code: `curl https://api.github.com/repos/<owner>/<repo>` for created and pushed dates,
  license and commits; grep the raw source for default parameters; check whether the paper's code-availability
  statement cites that repository. In one case it did not, and the code's defaults disagreed with the paper.
- Run the package as shipped and report what it does. A package run as coded may not apply to the data at
  all; that is a fact to report, with its scope.

## 4. Data availability, byte-exact

"make sure these are really those datasets, not sth just similar tissue type and tech"

1. For each dataset named in the paper, find the candidate public bundle (vendor page, repository accession,
   object store).
2. List the remote archive and pull one small member over HTTP range requests:
   ```bash
   python3 scripts/remote_zip.py <bundle url> --list
   python3 scripts/remote_zip.py <bundle url> <small member> --compare <local copy of that member>
   ```
   Pick a member that identifies the run: an experiment descriptor, a metrics summary, a manifest, a config. The
   script prints size, md5 and sha256 of the remote member, reports IDENTICAL or DIFFERENT with the first differing
   byte, and exits 1 on any difference or missing member. It refuses to continue if the server ignores the Range
   header, so it never downloads the whole archive. It needs only the standard library.
3. Where no public match exists, determine the source from internal metadata (panel or vocabulary name, run ID,
   date, software version) and declare it newly generated or collaborator data.
4. Sanity-check labels against the data itself: symbol case for species, unit count for the section, feature count
   for the panel or vocabulary.
5. `curl -sIL <url>` every link. Object stores are case-sensitive: a prefix with a capital letter returned 404.
   Vendor sites behind bot checks return HTTP 429; their open CDN host usually supports ranges.
6. Write `DATA_AVAILABILITY.md`: per dataset the bundle ID, plain URL (not a hyperlink: "give links not
   hyperlinks!"), md5 of the compared member, and every error found. Feed the errors to the manuscript as author
   actions.

What it catches: mislabeled samples (condition, species), dead links, release folders whose files were never
uploaded, references cited under the wrong source, duplicated reference-list entries.

For machine-learning data the same check applies to a benchmark suite (task IDs and the hash of each split file),
a model release (the hash of each weight file against the model card), and a dataset on a hub (the revision
hash). Suggested, not yet tested in real work: the byte-exact procedure was used on vendor ZIP bundles only.

## 5. Reference audit

From a 278-entry book bibliography audited by five chunk agents and one style agent.

1. Extract the printed references from the `.bbl` (count `\bibitem`), parse the `.bib` with a brace-matching
   parser (a naive regex missed entries with odd bytes), and collect every citation context: the sentence around
   each `\cite`.
2. Fetch Crossref metadata per DOI (`https://api.crossref.org/works/<doi>` with `urllib`) and pre-compare each
   field with the bib entry after Unicode normalization (`difflib`). Four DOIs failed to resolve in one run.
3. Split into chunks of about 56 entries. Write the house bib rules in one file every agent reads.
4. Brief each chunk agent as an adversarial bibliographer and referee: "The author wants not ONE wrong reference.
   You audit and propose. You do NOT edit any [project] file. Your verdicts will be double-checked."
   - Per entry: `OK`, `FIX` (bib only), `REPLACE_IN_TEXT`, `QUERY`.
   - Per citation context: `FIT`, `WEAK`, `WRONG`, `SELF`.
   - Output `chunkN_findings.json` and `chunkN_summary.md`. Agents compile their corrected entries with bibtex and
     read the rendered `.bbl` for lost capitals.
5. A style agent checks the binding rules (attribution, quotes marked, joint or unpublished work named with authors
   and status, AI tools disclosed) and the bibliography style.
6. The coordinator re-verifies each chunk's corrected entries against Crossref, spot-checks samples, applies them
   and rebuilds.

What it caught: a wrong first-author given name; a documentation page cited for a claim it never makes; a research
briefing filed as an editorial; a trade-magazine news item carrying a primary claim; "required" overstating
"produces"; a healthy-tissue atlas cited for a lesion claim; a booktitle reduced to an acronym with 4 of 11
authors; a dataset page saying "same section" where the text said "adjacent section"; a vendor page that did not
state the cited threshold (repointed to one that does); "up to 40%" that the source gives as "on average 39% (4% to
84%)". In total 137 of 278 entries were corrected.

Rules that came with it:

- Cite at claim level: one source right after the clause it supports.
- A primary source for a primary claim; a summary or news item only for what it reports.
- Own unpublished work is never cited as evidence. A public preprint may be cited for attribution, with its status
  in words.
- Trim the `.bib` to cited entries: malformed unused entries break bibtex.

## 6. Quotes from paywalled papers

1. The publisher page returns a login; a mirror may be down.
2. NCBI E-utilities give the full text of open-access papers in PMC:
   ```
   https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=<DOI>[doi]
   https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>
   ```
3. Save the full text as plain text and search it before quoting:
   ```bash
   python3 scripts/kwic.py "on average" papers/*.txt              # each hit, about 80 characters either side
   python3 scripts/kwic.py --regex "up to \d+ ?%" papers/*.txt
   ```
   Each hit prints file, character offset and context; a space in the term also matches a line break. Quote from
   that output, never from memory: one word of a first-draft quote was wrong. Exit 1 means no hit, so the quote
   as remembered is not in the paper.
4. Europe PMC's REST API gives license and metadata by DOI.
