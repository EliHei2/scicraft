# Verifying the specification, claim by claim

The specification is the author's inputs saved verbatim plus a table that checks every factual claim in them. The
table is written before any code. In the project this skill comes from, a plan written by an online chat was wrong
on six points that would each have shaped the design; all six were caught by this table in the first hour.

## 1. Save the inputs

- **Paste every input unedited into `SPEC.md`, typos kept, as labeled parts.** The author's build prompt asked for
  it ("Persist. Save this prompt as SPEC.md"), and later agents need the exact words, not a paraphrase. A
  paraphrase loses the constraints the author slipped into a subordinate clause.
- **Label which part is the goal.** One project had three inputs: a chat-generated build prompt, a research brief
  and a follow-up message. The header said "Part B is the goal" and "treat Part A as a draft plan: re-verify every
  fact in it". Where two parts conflict, the goal part wins on science; the conflict and its resolution go to the
  "Key decisions" list of `NOTES.md`.
- **The author's own words outrank a chat-generated part on constraints.** The chat plan said "CPU only; never
  require CUDA or MPS"; the author's follow-up allowed the local GPU and forbade training on the CPU. The
  follow-up won.
- **New instructions are appended as dated amendments, quoted.** Never rewrite an earlier part to match a later
  one; the history of what was asked is evidence.

## 2. Extract the claims

A claim is any sentence a design decision could rest on. Extract every one of these kinds:

| Kind | Example from a chat plan | What checking found |
|---|---|---|
| what a published method computes | "the baseline's features are moments, quantiles, mutual information" | 70 dimensions: 10 scalars plus cumulative histograms; no quantiles, no mutual information |
| which data a paper used | "the paper used the standard benchmark suite" | two other corpora; the suite was used only for one secondary analysis |
| that something does not exist | "no pretrained weights exist" | five released checkpoints |
| how a library encodes its output | "categoricals are unflagged integer codes" | integer codes that are then z-scored with the numeric columns |
| a default value | "the v1 prior is the package default" | the default changed in a minor release, in a pull request the changelog does not mention |
| a size or overlap | "about 50 plus about 150 datasets" | 49 of the 51 datasets of one suite are inside the other: about 144 unique |
| a mechanism | "grouped sampling gives near-duplicate items" | items in a group share hyperparameters, not weights or data: overstated |
| a version, an identifier, a URL | "arXiv id X; code at repository Y" | checked, with the commit recorded |

## 3. Give each claim a verdict and its evidence

Verdicts: `true`, `partly wrong`, `wrong`, `overstated`, `changed in <version>`, `unverified`. The evidence column
starts with a tag ([RUN] ran it, [DOC] read it, [U] not yet) and then names the source exactly: URL with version,
file and line at a commit, or the command that was run and what it printed. `scripts/check_kickoff.py` refuses a
verdict without tagged evidence, and a verdict other than `unverified` that rests on [U].

Order of authority when sources disagree:

1. **The released code at a pinned commit**, because it produced the published numbers or weights.
2. Released weights and released result files (their shapes, sizes and values are facts).
3. The paper.
4. Documentation and changelogs (a changelog can omit a breaking change; one did).
5. A knowledge base, an agent's summary or a project note. One project's knowledge base described a regularizer
   with the wrong mathematics; the authors' repository had the actual test and its parameters. Correct the note
   in place once the code is read.

## 4. When paper and released code disagree

**Follow the code and tabulate the difference.** For a learned set encoder the paper gave 45,424 parameters and a
64-dimensional output; the released weights hold 75,072 parameters and give 32 dimensions, with different
sub-networks, subsampling, negative pairs and loss weighting. The project built the code's version, because that
is what the released weights and the published meta-features came from.

The table, one per replicated method, in `research/LITERATURE.md`:

| Item | Paper | Code (released weights) | Project follows |
|---|---|---|---|
| network | [as in the paper's table] | [as in the code, file:line] | code |
| parameters / output size | 45,424 / 64 | 75,072 / 32 | code |
| subsampling | [paper] | [code] | code |
| loss weights | unweighted (equation 9) | negatives weighted 2 | code |
| optimizer and steps | not stated | Adam 1e-3, gradient clip 0.5, at most 10k steps, early stop | code |

Pin every source: arXiv version, repository commit SHA, package version. A row without a pin cannot be re-checked.

## 5. License, gating and availability

Before choosing a model, dataset or code base, record for each candidate: code license, weight size, how the
weights are gated (open, a form, a token), the weight license, whether it installs on the project's Python, its
speed on the target hardware, and what it outputs. Cases from one project:

- **Code with no license** (the repository API returned `license: null`): port the ideas from the documented
  definitions and copy no code. The module header says so.
- **Non-commercial weights**: downloaded at run time, never redistributed with the project.
- **Weights behind a license acceptance plus a token**: unusable on a headless runtime unless the author accepts
  first; record it as a blocker with `[AUTHOR ACTION]`.
- **A weight host that no longer resolves** (the domain returned NXDOMAIN; an issue in the repository confirmed
  it): the candidate is out, with the issue number as evidence.

## 6. The strongest available version

The author expects the strongest model and the newest relevant paper, not the convenient public one. The author asked
"why didn't you use ... one? ultrathink" when a stronger checkpoint existed, and "how about the features from this
one? why didn't you inlucde these?" when a recent paper was missed. Search for releases newer than the
specification, including versions shared by collaborators, and make the model path a parameter so a local
checkpoint can replace the public one.

## 7. Briefing a survey agent

When the author asks for research helpers, one survey agent with a fixed scope worked:

- scope: the candidate list from the specification plus anything from the last 18 months;
- per candidate: code, license, weights, install, speed on the target hardware;
- test-run the top three on a toy input (one project used `make_classification(512, 20, n_informative=6,
  n_classes=3, random_state=0)` and a 1024 x 100 speed table);
- a download budget (1.5 GB; 0.78 GB used) and a scratch environment, deleted afterwards, with nothing installed
  into the project environment;
- a ranked recommendation of **at most one** addition, with the fallback "if even this is too much, choose none";
- a provenance and cleanup section: what was downloaded, deleted and left in place.

Then **spot-check the agent's key claims yourself** and list which ones were re-checked. Before fanning
out several agents with a shared preamble, check every assertion in the preamble against the raw outputs: one
preamble asserted a wrong reading three lines below a table that contradicted it, and six agents confirmed it.

## 8. Benchmark corpora

- **De-duplicate across suites before counting or pooling.** Match names after lower-casing and stripping
  non-alphanumerics. Confirm each match by identical row and column counts; in one rerun names caught only 40 of
  49, and the 9 renamed datasets each had a unique identical row count. Check what is left by eye. Keep the
  mapping in a file. 49 of 51 datasets of one suite were inside a larger one, so "about 190 datasets" was about
  144; tag that overlap [DOC], because it was read from the published lists, not computed by a run.
- **Record each dataset's split regime** (independent, temporal, grouped) and drop the grouping and time key
  columns a loader leaves in the frame.
- **Do not install a benchmark's heavy package to read its results.** One dry run pulled a distributed-computing
  stack and downgraded pandas from 3.0.6 to 2.3.3, while the per-dataset results were plain parquet files over
  HTTP. One results server refused Python's default User-Agent with HTTP 403; a generic client string fixed it.
