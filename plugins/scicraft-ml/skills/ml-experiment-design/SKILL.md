---
name: ml-experiment-design
description: Designs machine-learning experiments before compute is spent, and writes the plan, configs and gates that keep them honest. Use it whenever someone scopes a new model or line of work, plans ablations, baselines or controls, builds a size ladder or a backbone swap, designs a robustness or perturbation study, sets up configs and sweeps, or wants a launch plan with kill and promote rules, also when they only say "what should we run", "design the ablations", "reviewers will ask why not X", "we have 5 days of GPU" or "these numbers look too good". It holds what agents get wrong: trivial baselines before the main model, one ablation arm per added component, trained controls matched on data seen (never untrained twins), one checkpoint per size, two zero levels in a robustness study, one config per structural variant, pre-registered gates, timing and memory logged at every step, and clean numbers treated as bugs. Prefer ml-evaluation for probes, metrics and statistics, training-diagnostics for a run that misbehaves.
---

# ml-experiment-design

How to decide what to train, in what order, against what, and under which rules, so that every run answers a
question a reviewer will ask and no result has to be explained away later. Distilled from a year of
foundation-model work (self-supervised pretraining, tabular foundation models, a benchmark against many
published methods, a size ladder, a revision with new ablations) in which the author pressed on every design choice
before the GPUs started. Lead examples are tabular and general machine learning; the same rules held for a
spatial-omics model.

> **PRIME DIRECTIVE: before a run starts, write down the question it answers, the arm it is compared against,
> and the number that would make you stop.** A run without all three is not an experiment yet.

Three failures cost the most time in the source work. Guard against them from the first plan:

1. **Comparisons that were not comparisons.** Ablation arms compared to an untrained twin, a control trained
   on a different number of samples, an ablation family whose base config was not the shipped one, five arm
   configs that differed only in comments and built the same network. Each produced a table that had to be
   thrown away (sections 3 and 6).
2. **Rules moved after the data arrived.** A success metric redefined several times, a row-selection rule changed
   repeatedly after scores were seen, a validation loss compared across an added loss term that produced three
   false kills. Freeze the rule first (section 7).
3. **Clean numbers believed.** Three arms equal to three decimals, identical standard deviations down a column,
   a validation curve too smooth, a run eighteen hours faster than physics allows. Every one was a bug: the same
   checkpoint loaded twice, a statistic computed over the wrong axis, a silent subset (section 9).

## 0. Before designing

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The claim.** The one sentence the paper or report will make, and what kind of evidence would change it.
- **The current reference.** The last commit that worked, its config, its numbers and where they are on disk.
- **The method as written.** Methods text, design notes, the config in force. When prose and config disagree,
  the config and the source win (`references/configs-and-sweeps.md`).
- **The budget.** GPU hours or days, the deadline, the hardware (card type and memory), and whether this machine
  can run anything at all. If the laptop has no GPU or no data, plan for another machine and hand over commands;
  run nothing heavy here.
- **Constraints the author has set.** Families of methods that stay, options already rejected, data that must be
  held out. Write them into a guardrails section and do not reintroduce a rejected option; if evidence contradicts
  a constraint, argue it in one paragraph and wait.
- **What was already tried.** A settled-levers index if one exists (lever, verdict, receipt). A new proposal must
  either cite a defect in the earlier control or be a confirmatory seed of a single-run effect.

Then show the plan before building it: one table, one row per run, with its question, its comparison arm, its
budget and its stop rule. Changing a row costs nothing now and a week later.

## 1. Scope the line of work

Detail and worked examples in `references/scoping.md`.

- **Frame the method on its data type, not on the home dataset.** State the problem as properties of the data
  (for a tabular model: heterogeneous columns, missing values, many small tables; for a time-series model:
  irregular sampling, gaps, many short series from different sensors). The home domain is one representative instance among peers. Framing
  decides what agents optimize: research briefs written around one domain's evaluation pulled the design toward
  that benchmark.
- **First step: a deliberately minimal sibling with one visual check.** Drop every advanced component, freeze a
  short design spec, and pick one headline experiment that can be seen. For example: split the input
  features into K disjoint subsets, train one model per subset on the same data, align all runs to run 0
  (Procrustes) and color them through one shared PCA to RGB basis; convergence reads as the same colors in the
  same places. In a one-day tabular sprint the bar was a visual result inside 30 minutes (descriptive statistics
  of each table, then a PCA and UMAP over tables colored by source), with representation families layered on one
  at a time.
- **Representation before downstream tasks.** For a self-supervised model the stage-one bar is the objective
  falling without collapse plus a frozen linear probe; downstream tasks come later and do not drive the
  architecture.
- **Stage the optimization.** Stage 1 is a working model that already has the common practice (bf16 autocast,
  gradient clipping, warmup plus cosine or WSD schedule, no weight decay on biases, norms and embeddings, proper
  init, pinned-memory loaders). Its gate is that the loss goes down. Stage 2 (compile, fused or custom kernels,
  quantization, multi-GPU strategy) waits until stage 1 trains without collapsing. A throwaway prototype may skip tests; the codebase that will be trained gets committed tests of its entry points from its first commit.
- **Anchor every design axis on methods known to work.** For each axis, find what the two or three strongest
  working models do, from primary sources, recent first. Adopt, adapt or reject with a reason, and record it.
  Deviation from precedent needs a stated reason; "we are the outlier" was the diagnosis of a design that failed.
- **Keep the last good commit as a named arm in every sweep.** When anything regresses, diff against it first.
  A redesign that does not beat where you started is not progress.
- **Enumerate the pipeline before choosing.** List every stage from raw data to final output with its options,
  the choice and the evidence (from your results or a paper). Agree it, then freeze it in a design spec with a
  status line (LOCKED or SUPERSEDED-BY) and a date. Implement only the latest locked design.

- **Guard the claimed unit of learning.** When the claim rests on the unit the model learns from, write
  invariants that protect it and check them in every design review (`references/scoping.md`, section 9). The
  same file lists optimizer settings that were each a measured failure and the rules for pretraining on a
  stream of heterogeneous samples.

## 2. The order of runs

**Trivial baselines first, then ablations, then the main model; the main model is the best bet and the
ablations run beside it.**

| Step | What it is | Tabular example | Why it comes first |
|---|---|---|---|
| 0 | a no-learning floor | column statistics or PCA of the raw features into the same probe | sets the bar any learned model must clear |
| 1 | a training-free version of each learned extra module | mean of neighbors' raw features instead of a learned aggregator | "the learned view must beat it to justify the machinery" |
| 2 | the reference: last good commit | the previous working model at its tagged commit | answers "does the redesign beat where we started?" |
| 3 | one step per added component | base model, then base + attention over columns, then + the new loss | each component's value is measured once, in order |
| 4 | the main model | the full design, the configuration you would bet on | the result |

- **Count parameters at every step of the ladder** and print them in the plan.
- **Evaluate every step of the ladder; render expensive visuals only for the main model and the baselines.**
- **Under a deadline, commit to one bet.** Give one recommended configuration with reasons, not a menu, and put
  the ablations beside it in parallel.

## 3. Ablations and controls

Detail in `references/ablations-and-controls.md`.

- **Every added component gets its own ablation arm, decided before coding.** List each component with its
  claim and the arm that removes or replaces it. A component you cannot afford to ablate is a component to cut.
- **Each arm changes one thing.** Changing a second axis (per-size layer counts, a new loss weight bundled with
  an architecture change) makes the arm uninterpretable. A scalar change with a plausibly large effect runs as
  its own arm, or it confounds every other arm.
- **The control is trained, matched on data seen, never an untrained twin.** Same recipe, same seed set, same
  step budget, compared at the same number of samples or tokens seen, not the same wall time. A random-init twin
  answers a different question (do the trained weights beat random features?) and belongs in the evaluation as a
  floor row named `<parent>-rand-init`, with its own seed; it never stands in for an ablation's control.
- **Ablate the shipped recipe.** Byte-diff each ablation family's base against the config you ship; re-run an
  old ablation under the current recipe and drop it if it no longer ablates. One wave ablated a degenerate
  default; a control inherited a different setting from the flagship.
- **Isolate one factor with a 2 x 2 when two factors are entangled.** {architecture A, B} x {setting 1, 2}
  separates them; a ladder in which every step shares the confounding setting cannot.
- **Every ablation wave carries one config-identical replicate arm as its noise unit.** A difference below 3
  replicate standard deviations is printed as a tie, with the SD. Claim a component only if full minus ablation
  exceeds max(per-task SE, |control seed 0 minus control seed 1|) and the sign holds between two checkpoints
  (two steps fixed in advance). Single-run arms are powered for large effects only.
- **Controls gate the family before any arm is read.** If a destroyed-input control (position only, shuffled
  features) scores at or above the baseline, the scoreboard is unusable.
- **Spend ablation budget on architecture, input masking and data order, not on loss-weight roulette.** A whole
  family of weight sweeps returned ties within 0.01; a two-line recipe fix beat both more steps and more capacity.
- **Anticipate the reviewer at design time.** For each choice, write the strongest reviewer question ("why not a
  plain transformer over all columns?", "why not gradient-boosted trees on the same features?") and answer it from
  theory, literature or a planned arm. If no answer exists, change the design.
- **A minimal decisive set.** Tier 0: gates before any long run. Tier 1: at most five experiments, each able to
  sink the paper, each with a written "falsified if" and the lever to pull if it fails. Tier 2: a necessity table
  with one replicate. Tier 3: scaling.

## 4. Size ladders and backbone swaps

Detail in `references/ladders-and-swaps.md`.

- **Pre-register sizes by order of magnitude of parameters** (for example three sizes an order of magnitude apart) and
  refuse toy settings. Local tests on small models mislead about large ones. Never subsample inputs below
  realistic size in the training path: a per-example cap that kept a fraction of each input was "the killer".
- **Scale along one axis, the way working families scale.** Keep the output embedding dimension fixed and add
  depth or width as the reference families do; keep everything else identical across sizes.
- **One checkpoint per size.** One size equals one reported checkpoint, chosen by a rule declared before scoring
  (a step fixed in advance, or the cooldown fork declared at launch). Never best-of-seeds, never best-of-sizes.
- **A short large run is not a scaling point.** Pre-write the fallback sentence: "The largest model reached only
  N steps at the cutoff and is reported as an in-progress capacity check in the appendix."
- **Test the concept apart from the architecture with a backbone swap.** Hold the objective, data, preprocessing
  and step count fixed; swap only the backbone (in its authors' implementation, parameter count within a few
  percent); compare at the same checkpoint step. Tabular form: the same prior and pretraining objective with two
  backbones.
- **Assert the sizes in a test.** Parameter counts within bands, every paper constant, derived rules recomputed.
  Change a default only through the plan of record plus that test.

## 5. Robustness studies

Detail in `references/robustness.md`.

- **A complete perturbation taxonomy, not a list of convenient noises.** Name the axes and cover each. For
  tables: missing values (MCAR), noise relative to column SD, nuisance columns (row-permuted copies: same marginals,
  no relation), redundant columns (noisy copies of the most informative), row dropout, label noise, outliers,
  scaling, monotone transforms, categorical corruption. Nuisance and redundant keep marginals intact so only the
  dependence structure differs. Instance-labeling form: boundary wrong vs object wrong, crossed with too little vs
  too much.
- **Signed severity in natural units**, one shared x-axis across perturbation types.
- **Two zero levels:** a verbatim copy of the clean input, and a copy re-derived through the same perturbation code
  at severity zero. Their gap measures the pipeline's own artifact. A bug that silently deleted a few percent of
  objects was visible in the zero level.
- **Never evaluate against the corrupted input.** The test set and every reference the evaluator reads come from
  the clean source. Enforce it in code: the preflight fails if the clean path resolves inside the perturbed tree.
- **Provenance per perturbed input:** parent, type, severity, seed, measured severity. Rebuild deterministically
  from the cached parent; do not store the perturbed copies.
- **Retrain at every level when the claim is about supervision**, and separate train-corrupt from predict-corrupt
  with a 2 x 2 when the question is whether the learned function or the input is to blame.
- **Trace the seed to every random source** and split perturbation seeds from training seeds. Run at least 3
  training seeds per level, including the zero levels. A claim of replicates was retracted when the seed reached
  only the corruption draw.
- **Test claimed invariances with a paired perturbation probe:** apply the transformation, measure the change in
  output, and add its null. Tabular form: permute rows and columns and check invariance or equivariance; keep the
  marginals and destroy the joint to test whether interactions are used.

## 6. Configs and sweeps

Detail in `references/configs-and-sweeps.md`; scripts `scripts/resolve_config.py` and
`scripts/ablation_audit.py`; templates in `assets/configs/`.

- **One small YAML per structural variant, `--set` overrides for numeric sweeps.** A variant file starts with
  `base: ../base.yaml` (deep-merged, the child wins) and changes a few lines. Numeric sweeps need no file.
- **Head each variant with the claim it tests** and keep a `| # | claim | arms | falsified if |` table in the
  ablation folder's README (`assets/configs/ablation/README.md`).
- **Write structural switches explicitly in every config.** Five arms once built an identical network because the
  switch was left to a dataclass default, and every run trained on a quarter of the vocabulary unnoticed.
- **Unknown keys are fatal.** A silently defaulted typo trains the wrong run. `validate()` derives dependent values
  and raises on impossible combinations.
- **New mechanisms are switches whose default is the current behavior**, and an equivalence test proves the
  default path is bit-identical.
- **Every config trains one real step in CI** on a tiny CPU config. A config that cannot train cannot be merged.
- **Echo the resolved config and its hash into the run log.** Key every comparison on that hash. Never queue a
  config that was not loaded through the loader.

```bash
python3 scripts/resolve_config.py configs/ablation/no_column_attention.yaml --schema configs/base.yaml \
    --set train.lr=3e-4 --out runs/arm1/resolved.yaml          # prints the config hash
python3 scripts/ablation_audit.py configs/ablation --base configs/base.yaml --max-keys 3
```

Before scaling a run, three more checks (`references/configs-and-sweeps.md`, sections 7 to 9): every result
record carries the hashes of the checkpoint, the scorer and the pooling code, and the table builder refuses a
mismatch; checkpoints are written through a temporary file and an atomic rename, and a resume is verified with
its overrides; the token or column vocabulary is pinned by a hash stored in every checkpoint.

## 7. Pre-registration and gates

Detail in `references/preregistration-and-gates.md`; templates `assets/PREREG_TEMPLATE.md` and
`assets/GATES_TEMPLATE.md`; script `scripts/prereg_check.py`.

- **Freeze the measurement chain and the selection rule before the first candidate exists.** Endpoint, task
  classes, row classes, tie band, win rule, checkpoint selection, seeds, scoring protocol. Tag the freeze commit;
  git timestamps are the receipt.
- **Selection is paired evidence on a fixed short list.** Benchmark at most 3 pre-named candidates once. Fix
  candidate rows by time or exposure, never by score. The selection set is never the reported set.
- **Gate every launch on the cheapest measurement that could invert the plan.** Run the zero-GPU checks first
  (minutes on a CPU), write an explicit STOP rule into the brief, and read a trained operating point before
  designing against it. Lock the design with one keep or kill number defined in advance.
- **Kill rules:** only after warmup, sustained over 3 consecutive evaluations, with a health criterion
  co-signing, never across a config change. Benchmark evidence alone may only steer.
- **Steer rules:** a written menu in order, one change per staged restart, never applied to a live run.
  Fallbacks are pre-staged as written configs, not decided under pressure.
- **Promote rules:** a candidate replaces the incumbent only with no significant paired loss on any task and at
  least one significant gain; on any ambiguity the incumbent stays. The champion is a step checkpoint.
- **A smoke test is sanity only.** Finite losses, memory within budget, every term carrying mass. Metrics are
  judged after warmup.
- **Steering rows never enter a paper table.** Name them apart (for example `ARM-` for steering, `BANK-` for
  paper-facing rows).
- **Deviations are dated and append-only**, including items that were not implemented. Watched creep paths:
  peeking mid-plateau, renaming after a relaunch, probe shopping, seed picking, arm promotion, drift of the
  selection set.
- **Under a deadline, score existing checkpoints before training new ones**, and stop runs that do not answer
  the questions on the table.

- **Seed every gate** and write the seed into its output. An unseeded gate mixed the effect with seed noise.
- **A gate is the numeric go or stop threshold of a short goal**, and every operational incident becomes a
  numbered guardrail with its check. Both documents are defined in the sibling skill
  (`project-structure/references/governing-documents.md`).
- **Keep a late anneal fork** as the device that guarantees a model, find the binding stage by measurement
  before buying compute, and stage one fallback override per failure regime.

## 8. Timing and memory at every step

Detail in `references/instrumentation.md`; script `scripts/step_meter.py`.

- **Log true GPU time per phase, peak VRAM and RSS at every logged step**, measured and never requested: CUDA
  events with one synchronize per step, `torch.cuda.max_memory_allocated`, resident memory. Report totals per
  phase (preprocessing, training, prediction) and per model.
- **One-shot jobs report wall time**, because a whole-dataset encode is dominated by host work between small
  forwards.
- **Size memory on at least 2000 steps of the densest data.** Short sizing runs read the peak about 20% low; peak
  VRAM is set by the rarest batch.
- **Cross-check every projection** (time, cost, memory) against a second, independently derived route. One unit
  slip made a plan 3 to 4 times too optimistic.
- **Never trade data for throughput without surfacing it.** Log the retained fraction per step and plot it; make
  the pipeline faster first.
- **Telemetry must never kill training.** The logger drops a record on error.

- **When new results arrive, run one fixed loop**: read only the synced metric files, regenerate the same plot
  set with the same script, say in two sentences where the run is heading and on what evidence, list the
  regenerated files (`references/instrumentation.md`, section 3).

## 9. Numbers that look too clean are bugs until cleared

Detail in `references/sanity-checks.md`; script `scripts/too_clean.py`.

| Symptom | First check |
|---|---|
| arms agree to 3 decimals | did they load different checkpoints? hash the weights and the outputs |
| identical SDs down a column | is the SD over folds, or over head seeds of one fold? |
| variants give identical pictures | compare the arrays by hash and the images pixel-wise; is the varied component on the path that is read out? |
| identical VRAM or time across models | is the meter measuring the model or a fixed overhead? |
| a run far faster than before | did a fast path silently skip data or fall back to a subset? |
| held-out curve suspiciously smooth or falling | is held-out really disjoint (groups, donors, sources)? |
| a claim over every method | was it computed over the methods that did not crash? print coverage per cell |
| a loss pinned at a constant | compute what a trivial predictor scores (`training-diagnostics`) |

- **Name the receipt of every number in one clause**: file, commit or job. "The tool printed it" is not a receipt.
- **Read no trend from fewer than 4 to 5 points or from the first ~10 steps.** The short read is most tempting when
  it confirms the fix you just made.
- **A default is not an observation.** Never `.get(k, 0)` a metric and interpret the result; print `absent`.
- **A null is a finding, scoped to the tested setting.** Do not synthesize a conclusion the numbers do not support.

## 10. Honest reporting of the design

- **Every arm that ran is reported**, favorable or not; a weak or mixed result goes to the appendix with its
  number. A reporting threshold is applied to every result alike and stated.
- **Selecting your own variant for the headline is a selection step.** Rank all variants on one fixed rule, apply
  it once, and report "selected from N variants by rule R".
- **Requested analyses are reported as they come out.** Re-running an analysis until a target rank appears is
  misreporting.
- **Record negative and inconclusive results by name**: inconclusive (could not answer; say what was missing),
  negative (answered no), dead (the measurement was degenerate), each with a next action. Reversals stay visible.

- **A campaign ends with a graded synthesis.** Every claim carries a grade for its evidence, from a
  pre-registered paired test down to an inference; then the costliest failures, the selection risks and "if we
  started over" (`references/campaign-synthesis.md`).

## 11. Check before handing over a plan or launching

1. `python3 scripts/ablation_audit.py <ablation dir> --base <shipped config>`: every arm resolves, differs from
   the base, differs from every other arm, and carries a claim header.
2. `python3 scripts/resolve_config.py <config> --schema <base>` for every config to be queued; record the hash.
3. `python3 scripts/prereg_check.py --repo . --prereg <PREREG.md> --results '<glob>'` before reading any score:
   no result committed before the freeze.
4. The one-step CI run of every config passed on CPU.
5. `python3 scripts/too_clean.py <results.csv>` on every new results table before anyone reads it as science.
6. Look at the plan table yourself: each run has a question, a comparison arm matched on data seen, a budget and
   a stop rule; each added component has its arm; the reference commit is an arm; the noise replicate exists.
7. Say what was not checked: runs not launched, configs not trained one step, numbers not traced to a file.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| ablation arms against random-init twins | "give me the trained ones!" | trained controls matched on data seen |
| a different layer count per size | "that would introduce another point of comparison, let's keep all the same" | one scaling axis |
| small local tests for a large model | "local test might be super misleading on such big models" | three sizes an order of magnitude apart |
| capping each input to fit memory | "the previous [cap] was the killer" | realistic input sizes; a faster pipeline |
| rejecting whole inputs to fit memory | "the most stupid" option | coverage measured; retained fraction surfaced |
| a menu of architectures under a deadline | "if you wanna bet your money on one single architecture ... how would you really go about it?" | one recommended configuration, ablations beside it |
| untested new methods | "use best practices for such models not ... untested methods" | designs anchored on working models |
| redesign with no reference | "we had a version on 13th that was working super nice" | last good commit as a named arm |
| components added without a test | "for every complication we need to properly run an ablation, so really think upfront" | one arm per component, planned before coding |
| tests before the model trains | "let's first make sure the model works at all" | stage 1 working model, then tests |
| identical numbers accepted | "why are all sd in a column the same almost? so suspicious" | clean numbers treated as bugs |
| a held-out curve believed | "is held out really valid heldout?" | group-disjoint splits checked first |
| a choice a reviewer would question, left open | "these are the questions reviewers might ask" | each choice answered by theory, literature or an arm |
| a silently subset dataset | "you lost them" | full data; subsampling only for rendering |

## Reference files

- `references/scoping.md`: domain-neutral framing, the minimal first step and its visual check, staged
  optimization, anchoring on working methods, the reference commit, the design spec, guarding the claimed unit,
  optimizer settings that failed, pretraining on heterogeneous samples.
- `references/ablations-and-controls.md`: the order of steps, one arm per component, matched trained controls, twins,
  2 x 2 isolation, noise units, decisive sets, reviewer questions.
- `references/ladders-and-swaps.md`: sizes, one checkpoint per size, the size test, backbone swaps.
- `references/robustness.md`: perturbation taxonomies, zero levels, the clean-reference rule, readouts, seeds,
  invariance probes.
- `references/configs-and-sweeps.md`: the config loader, variant files, overrides, validation, CI, equivalence,
  hashes in every record, checks before scaling, the vocabulary pinned by hash.
- `references/preregistration-and-gates.md`: the pre-registration file, the two-key firewall, the gates file,
  seeded gates, kill, steer and promote rules, incidents as guardrails, deadlines and the anneal fork.
- `references/campaign-synthesis.md`: the graded synthesis written at the end of a campaign.
- `references/instrumentation.md`: what to log per step and per job, sizing, projections, retained fraction.
- `references/sanity-checks.md`: the too-clean checklist, receipts, trend reading, coverage.
- `scripts/resolve_config.py`: resolve a `base:` chain and `--set` overrides, refuse unknown keys, print the hash.
- `scripts/ablation_audit.py`: audit an ablation folder against its base.
- `scripts/step_meter.py`: per-phase GPU time, peak VRAM and RSS per step; wall time and peaks per job.
- `scripts/too_clean.py`: flag identical arms, identical SD columns, coverage holes and identical arrays.
- `scripts/prereg_check.py`: confirm that no result file was committed before the pre-registration freeze.
- `assets/PREREG_TEMPLATE.md`, `assets/GATES_TEMPLATE.md`, `assets/DESIGN_SPEC_TEMPLATE.md`: fill-in templates.
- `assets/configs/base.yaml`, `assets/configs/ablation/no_column_attention.yaml`,
  `assets/configs/ablation/README.md`: a worked config set for a tabular transformer.
