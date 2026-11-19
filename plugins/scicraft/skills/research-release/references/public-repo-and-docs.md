# The public repository, its documentation and the hosted demo

## Contents

1. What goes in and what stays out
2. The done-tests
3. Documentation tested like code
4. Files every release carries
5. Model files
6. A hosted demo
7. Versions and names
8. Commits, attribution and the agent files
9. Announcing the release

## 1. What goes in and what stays out

| In | Out |
|---|---|
| README, LICENSE, CITATION.cff, pyproject.toml, CHANGELOG.md, THIRD_PARTY.md | the benchmark harness, ablation arms, comparators |
| `src/<pkg>/` | operations scripts, scheduler files, campaign documents |
| `configs/`: the release recipe and one tiny test config | internal Markdown (status files, briefs, agent files such as CLAUDE.md) |
| `docs/` with the notebooks | the internal checkpoint and in-house outputs |
| `tests/`: CPU only, under 2 minutes, small committed golden tensors | data, results, large binaries |
| CI: tests, docs build, package publishing (PyPI trusted publishing) | code under a non-commercial or copyleft license |

- The size check lists "Markdown files outside docs/". Each one needs a reason (README, CHANGELOG, THIRD_PARTY).
- Keep agent files out of shared history with `.git/info/exclude` (local only, never committed).
- Never commit a file over 100 MB (the code host's limit); look for anything over 50 MB before the first push.
  A 230 MB push failed with HTTP 408 and went through with
  `git -c http.version=HTTP/1.1 -c http.postBuffer=524288000 push origin main`. In zsh, `${PIPESTATUS[0]}` is empty,
  so capture `$?` of the push without a pipe.

## 2. The done-tests

1. **One minute.** A newcomer reads the top of the README, installs, pastes six lines, and has a result and a
   figure.
2. **Ten minutes.** A fresh agent with only the README and the docs completes the main tasks without opening the
   source.
3. **Two minutes on the hosted demo**, when there is one.
4. **Nothing needs an apology.** "No dead options, no leftover experiment, no unexplained constant, no file whose
   purpose is unclear from its first line." The author's version: "code has not hole or werid things!"

Run tests 1 and 2 with fresh agents that have not seen the build. Every stumble is fixed in the product, never
explained away.

## 3. Documentation tested like code

The author pointed at scvi-tools and ComplexHeatmap: "properly and narriatively documented, not overwhelming,
minimal examples, obvious what to do ... it's not about just fancy figures, it's about clarity too".

- Stack that was specified: Sphinx with sphinx-book-theme, myst-nb with stored outputs (no execution during the
  build), sphinx-design, sphinx-copybutton, autosummary.
- Pages: Home (one sentence, one figure, the install line, three cards), Quickstart, Tutorials, Concepts, Model,
  How to, Troubleshooting (every error message a user can meet, with its fix), API, Release notes, Cite.
- Gates:
  - `python -m sphinx -W -b html docs docs/_build` (warnings are errors) and `python -m sphinx -b linkcheck docs
    docs/_build/link` (no dead links);
  - every public name has a docstring with an example that runs (`python -m pytest --doctest-modules src/`);
  - every notebook runs from a fresh kernel (`jupyter nbconvert --to notebook --execute --inplace nb.ipynb`, or
    `pytest --nbmake docs/`);
  - the leak scan with `--style` passes on the docs and the built HTML;
  - the field test of distillation gate A6 has put its time and memory table into the docs.
- The notebook rules are in `notebooks-and-exactness.md`.

**Install lines and commands that were not run are marked.** Write `UNTESTED` next to any install line, platform or
command you could not run here (a GPU wheel index, a Windows path, a conda channel), and say so in the report.
The notebook release of a segmentation paper marked its untested install lines this way.

## 4. Files every release carries

- **CITATION.cff** at the repository root (template in `assets/CITATION.cff`). The code host shows a "Cite this
  repository" link from it.
- **CHANGELOG.md** in the Keep a Changelog form, with a thanks line naming contributors by handle when they agree.
- **THIRD_PARTY.md**: every borrowed file or idea with its source and license. No file may come from
  non-commercial or copyleft code.
- **NOT_IN_PAPER.md** (internal, never published): techniques the code would newly disclose. It feeds the license
  and IP questions (`license-ip.md`). Template in `assets/not_in_paper.md`.
- **FACTS.md** (internal): every number in README, docs and model card with its source file. A number nobody can
  trace is removed or marked `[VERIFY]`.
- **PAPER_MAP** in `docs/` when the paper is the specification: a table by paper section, `| paper | code |`, plus
  every place where the code makes a choice the paper leaves open. Keeping it current is the `paper-code-parity`
  skill.

## 5. Model files

- The deployed weights (`model.safetensors`), the config, the vocabulary and a model card.
- **A release that invites continued training ships what continued training needs.** In the instance the release
  checkpoint held only the encoder; continued pretraining also needs the target encoder, the predictor and the
  optimizer state. They went into a second file (`training.safetensors`), and the author was told that these weights
  become public too.
- `data/SOURCES.md` with the license of every example file shipped.
- The model card leaves its Results heading empty for the author to fill from FACTS.md.
- Keep two models apart when in-house data exist: a public checkpoint trained on public data, and an internal one
  that "and all in-house outputs never leave the cluster". The checkpoint name carries its data tier.

## 6. A hosted demo

Specify the demo as the visit, step by step, with its own acceptance checks.

- The visit that was specified: a cached example on opening, a preview within seconds, one button, three views that
  appear in turn, recoloring without recomputing.
- Checks: ten broken inputs each give a one-sentence fix; two sessions at once; phone and desktop layouts.
- **Plan for the end of funding.** Paid hardware is usually offered for a fixed period only. The demo must
  still run as a page on free hardware after that date; write the date and the fallback into the demo's README.
- The paid tier must fit the largest input users will bring (in the instance, the largest data type of the field).
- Name the demo by its proper term and give its monthly cost when telling the senior authors.

## 7. Versions and names

- **Check the name before anything else is created**: the package index, the docs host, the code host and the model
  hub (in the instance PyPI, Read the Docs, GitHub and Hugging Face). The release plan put this check first,
  before any repository existed. Choose a name free on all four. If none is, decide the import name and the
  distribution name separately and say so in the README (Suggested, not yet tested in real work).
- `0.x` or `1.0.0rc1` until launch, `1.0.0` at launch; the weights carry the same version.
- One name per thing across package, docs, model card and paper. Rung names for model sizes stay as they are in the
  paper.
- Default branch `main`.

## 8. Commits, attribution and the agent files

- **No assistant attribution in anything a lab or the public reads.** "people won't trust it if it has your sign
  all over it." Private repositories may carry such lines; the rule is per destination. The leak scan treats
  `Co-Authored-By`, `Generated with`, `claude.ai` and `CLAUDE.md` as errors for this reason.
- Commit subjects name the decision ("Drop the unused sampler and make the patch size a constant"), not the file.
- Never force-push a shared branch.

## 9. Announcing the release

A release message to senior authors is a plan in the author's voice: what is released and when, the demo and its
cost, the internal model and what in-house data means, the vision in two or three plain sentences, then at most
three questions. A version built from headings and lettered options was rejected as machine-made. The
`author-voice` skill holds the voice rules.
