# Reproduce first, then extend

The published baseline is reproduced before anything new is built on it, and a reimplementation is proven against
the authors' own outputs before it is used. In the project this comes from, the exact replication of the
published baseline was the first view, "the published baseline every other view is read against".

## 1. Order

1. **The published baseline, exactly.** Run it, or reimplement it from the code (never only from the paper), on
   the data the authors used, and recover their published number or their released outputs.
2. **A trivial floor.** The cheapest method that could explain the result: raw-feature averaging plus PCA, a
   constant predictor, a random-initialization twin of the model. The author asked for these by name: "the
   baseline also should be run which is just averaging".
3. **The approximation**, where the project must deviate (a different sample size, a different preprocessing),
   labeled A, with the deviation recorded.
4. **The extension**, labeled E.

A published row is reproduced by your own pipeline before it is trusted next to your numbers. Comparator numbers
copied from a paper stay frozen as published and are marked as copied.

## 2. Proving a reimplementation

The protocol that accepted a port of a learned set encoder:

1. **Find the authors' released intermediate outputs.** Here: a CSV of the encoder's outputs for 63 datasets
   shipped in the authors' repository.
2. **Reproduce their exact protocol**, including the parts the paper does not state: here 160 subsamples from each
   dataset's training fold and 160 from its validation fold, each 256 rows x 16 features x 3 label columns, then
   averaged. The authors had min-max scaled each output dimension.
3. **Compare with two numbers**: the minimum over dimensions of the per-dimension Pearson r, and the Spearman
   correlation of the two pairwise-distance structures. The port reached 1.0000 on both. `scripts/parity.py`
   computes both, matches rows by id, and with `--minmax` scales both sides the same way first.
4. **Re-run from the documented snippet**, not from the scratch file. The agent copied the code block out of the
   notes and ran it in the project environment: r = 1.0000 on 12 datasets. A snippet that was never run from the
   notes is not documented code.
5. **Record it** as the evidence of the R row in `STATUS.md`.

```bash
python3 scripts/parity.py authors_outputs.csv my_outputs.csv --id dataset --minmax --report research/parity.md
```

A dimension mismatch (the paper's 64 against the code's 32) stops the check with exit code 2; that is a finding
for the paper-versus-code table, not a bug in the comparison.

**Set the tolerance from a noise floor.** Run the reference implementation against itself (two seeds, two devices
or two ensemble members) and set the tolerance from that difference; one brief used "ten times the code's own
difference from itself". A numpy copy of a library's preprocessing matched the library's torch functions to
4.8e-7, and the test tolerance was set at 1e-4.

**An exploration harness must reproduce the production number exactly** before it is used to decide anything.
When a number from one script and a number from another disagree, probe definitions until the digits match, and
say openly when they cannot be matched.

## 3. Naming: exact, approximate, extension

- **Every component is typed R, A or E** in `STATUS.md` with its location in code (`file.function`) and its
  evidence. The research brief asked for it: "Clearly distinguish: exact reproduction, approximate reproduction,
  new experimental extension."
- **A substitute never carries the original's name.** The brief said to implement a fallback "but DO NOT call the
  fallback" by the original method's name. The same rule rejected a public package that shared the original's
  name: "Not faithful; do not call it" by that name.
- **Deviations go in a table** (component, original, this project, why), and every one is visible where results
  are reported. One project used groups of 1 where the published recipe used groups of 4, stated the consequence
  (items independent instead of sharing hyperparameters in fours), and kept it in the deviations list.

## 4. Anchor on what is known to work

- **For each design axis, find what the two or three strongest working models do, with citations, weighted by
  recency, and adopt, adapt or reject each with a reason.** The author's words: "make sure we're really testing the
  newest top techniques ... from frontier labs/ and top ML gurus papers not random. sth that's working." Write the
  result to the project's knowledge notes.
- **A hard constraint the author set is obeyed and never reintroduced.** If evidence contradicts it, argue it in
  one paragraph and wait.
- **Check the claim against the authors' code, not against a summary of it** (`references/verify-spec.md`
  section 3).

## 5. The last good commit

- **Tag the last commit that demonstrably worked and carry it as a named baseline in every comparison.** "keep the
  og versions (cuz they wroked)"; "we had a version on 13th that was working super nice"; "get this model from this
  commit and compare to that too". `STATUS.md` names it on its "Reference" line.
- **When something regresses, diff against that commit first.** A redesign shipped without its positional
  encoding and was found only by such a diff weeks later; another variant regressed against the simpler one it
  replaced.
- **Push before any risky change**, so the reference survives.

## 6. Determinism before comparison

- Seed every generator per item, run the generator single-process, and parallelize across items yourself.
- Prove it across processes with `scripts/hashseed_check.py`, and prove the outputs are not trivially constant
  with `--expect-different`:

```bash
python3 scripts/hashseed_check.py -- python3 make_item.py --seed 11
python3 scripts/hashseed_check.py --expect-different -- python3 make_item.py --seed 11 :: python3 make_item.py --seed 12
```

- Fix the precision and device for anything compared across machines (`references/notes.md` section 3).
- When a result looks suspiciously identical, fast or low, treat it as a bug until a file proves otherwise: hash
  the outputs of variants that should differ. Three variants of one model once produced identical embeddings; the
  author caught it from the pictures ("r3/r4/r5 literally have the same umaps").

## 7. Contract tests (pointer)

The checks above become tests once the code exists: determinism, parity with the reference implementation, fixed
output length, the invariances the analysis relies on. Writing them belongs to `research-code`; the comparison of a
finished paper against its code belongs to `paper-code-parity`.
