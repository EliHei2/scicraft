# Scoping a line of work

How to start a model or a research line so that the first weeks produce something that can be judged, and so
that later redesigns are measured against something real.

## 1. Frame on the data type

- State the problem as a conjunction of properties of the data, not as a dataset. For a tabular foundation model:
  heterogeneous column types, missing values, many small tables from different sources, the table (not the row)
  as the unit of transfer. For a time-series model: irregular sampling, gaps, many short
  series from different sensors.
- Name the home application as one representative instance. Show it beside two or three other domains in the
  framing, and benchmark only where you have results; other domains are "discussed only".
- Use generic vocabulary in figures and design documents (element, feature id, region, group). Domain words stay
  inside the domain section.
- The novelty is the conjunction of properties. List prior work for each conjunct; when every conjunct is
  occupied, claim only the conjunction. Verify every "first" before it reaches an abstract.
- Why: research briefs that framed the work around one domain's validity pulled the agents' design toward that
  domain's benchmark, and the author had to reset the work to representation-first.

## 2. The minimal first step

Write a short `DESIGN_SPEC.md` (template in `assets/DESIGN_SPEC_TEMPLATE.md`) for a deliberately small sibling of
the full idea:

- Drop every advanced component: one scale, no routing, no extra losses.
- Pick one headline experiment that can be seen. One convergence test: split the input features into K
  disjoint subsets, train one model per subset on the same samples, align all embeddings to run 0 by Procrustes,
  and color every run through one shared PCA to RGB basis fitted on run 0. If the runs learn the same structure,
  the same colors appear in the same places. This is visual first; keep held-out quantitative evaluation off the
  default pipeline until the picture works.
- Tabular instance (a one-day sprint): within 30 minutes, cheap descriptive statistics of every table, then a PCA
  and a UMAP over tables colored by benchmark source. Then add representation families one at a time
  (meta-features, row-embedding means, pretrained-model embeddings), one plot per family plus one concatenated
  plot, then stability checks (resplits and resamples of each table shown in the same PCA).
- Judge representations visually as well as by a metric. A metric that disagrees with an obvious picture is
  audited before it is believed.

## 3. Representation first

For self-supervised and foundation models:

- Stage-one success is the training objective falling without collapse, a health tripwire (effective rank,
  per-dimension standard deviation, covariance spectrum) and a frozen linear or kNN probe on held-out data.
- Downstream tasks are frozen probes that come later. They do not choose the architecture.
- How to read those diagnostics belongs to `training-diagnostics`; how to score probes belongs to `ml-evaluation`.

## 4. Staged optimization

| Stage | Contents | Gate to leave it |
|---|---|---|
| 1 | bf16 autocast, fused AdamW, gradient clipping, warmup plus cosine or WSD, weight-decay split (none on biases, norms, embeddings and learned tokens), proper init, LayerNorm or RMSNorm, dropout, dataloader workers with pinned memory, EMA where the architecture needs it | the loss goes down and the representation does not collapse |
| 2 | `torch.compile` where it is clean, FlashAttention or FlexAttention, fused or Triton kernels, quantization, FSDP or another multi-GPU strategy | a measured speedup with an identical loss trajectory at a fixed seed |

- Write no test suite until stage 1 trains. "don't focus on tests just yet, let's first make sure the model works
  at all."
- A stage-2 change must prove it does not change the objective: same seed, same loss trajectory. A speedup that
  alters the loss but still trains is the worst outcome, because it quietly produces publishable numbers. One
  speed cut (fewer random projections in a regularizer) made two of four runs collapse.
- Develop where you edit, execute where the GPU is. On a laptop without GPU or data run only static checks
  (`python -m py_compile`, a linter); label every verification step with the machine it runs on.

## 5. Anchor on methods known to work

- For each design axis (tokenization, positional encoding, attention pattern, objective, anti-collapse term,
  readout, scaling rule), find what the two or three strongest working models do. Read primary sources and the
  authors' code, weighting recent work.
- Record adopt, adapt or reject with a reason in the project notes.
- Check every reimplemented method against its authors' code. A project knowledge base once described a
  regularizer with the wrong math; the reference repository had the actual test and parameters.
- Deviation from precedent needs a written reason. Stacking several components no working system combines is a
  warning sign.
- When an external chat or another model drafted the plan, verify each "fact" by running the installed code. A
  drafted plan was wrong about a baseline's features, about the corpus, about whether pretrained weights existed,
  and about the overlap between two benchmarks.

## 6. Keep the reference

- Tag the last commit that worked and carry it as a named arm in every sweep (for example with a `git worktree`
  checkout of that commit).
- When a result regresses, diff the code against that commit before proposing changes. A missing positional
  encoding and a regressed variant were both found this way.
- Push before any risky change.
- Do not version-number a conceptually new model as the next release of the old one; give it a new name and keep
  code names stable.

## 7. Enumerate, agree, freeze

1. Write every stage from raw data to final output as a numbered table: stage, options, choice, evidence (your
   result or a paper).
2. Get agreement on the table.
3. Freeze it in the design spec with status LOCKED and a date. A later change gets a dated "added later" note.
4. Superseded designs get status SUPERSEDED-BY with a pointer, and move to an archive folder so they cannot
   mislead. Before building, search for later records: two design tournaments once ran on the same day and the
   older one was implemented first.
5. Keep a "cut as fake-able" list: features removed for faking progress stay removed until there is evidence.

## 8. Surface semantic choices

Choices that change what is measured (a scale, a window size, a data filter, a knob that discards data) go to the
person who owns the work with the options and the retained fraction. Do not change them unilaterally. Any drop of
data is shown before it is applied ("first show me locally what you removed").

## 9. Guard the claimed unit of learning

When the claim rests on the unit a model learns from, write invariants that stop the design from drifting to an
easier unit, give each one a check, and run the checks in every design review. Typical invariants say what may
enter as input, where the weights start, and which operations could leak the easier unit into the result.

These are guardrails of the project in the sense of the sibling skill
(`project-structure/references/governing-documents.md`): each gets an id, what it prevents and its check.

## 10. Optimizer settings that were each a measured failure

- No weight decay on embeddings or learned tokens. Rare inputs carry the most specific signal.
- An EMA teacher horizon, 1 / (1 - m), of at least 10 times the episode length, and a final momentum below 1
  while the loss is still on a plateau.
- A separate gradient clip per parameter set, with the fraction of steps that hit each clip in the log. Log it,
  and do not read it as a verdict on the learning rate: the rule "a clip-hit fraction of 1.0 means the learning
  rate is 10 times too high" was shown wrong under AdamW.
- One training step runs in this order: target pass, backward per view, clip per parameter set, one optimizer
  step, one EMA update. A non-finite gradient skips the optimizer step and the EMA update together, so teacher
  and student never drift apart. Twenty skips in a row end the run with a fatal message.

## 11. Pretraining on a stream of heterogeneous samples

Suggested, not yet tested in real work as a whole; each line comes from a request of the author.

- Fix one token vocabulary for every sample (feature ids, column names) from a versioned authority file, and
  record its hash in each checkpoint, so a token id means the same thing in every epoch
  (`configs-and-sweeps.md`, section 9).
- When a batch holds one sample, shuffle the order of samples every epoch.
- Sample with token frequency in mind, since rare tokens appear in few samples, and log exposure per token.
- Keep a health log per sample (loss, a collapse canary, the count of non-finite values). Down-weight or exclude
  a sample that keeps failing, with a record.
- Fit loosely across samples and plan light adaptation or fine-tuning at test time for inputs outside the
  training distribution. Forcing the pretraining to fit every sample was rejected.
