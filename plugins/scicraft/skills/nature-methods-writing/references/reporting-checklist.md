# Reporting and reproducibility checklist

Aligned with the Nature Portfolio Reporting Summary. Answer every item, including the negative ones: a blank reads
as an oversight. For how to choose and report a statistical test, use the `stats-reporting` skill; this list is
what the Methods must contain.

## Statistics and reproducibility (own subheading)

- [ ] Exact n for every comparison, and what n counts (datasets, seeds, cells, patients, prediction tasks).
- [ ] Whether measurements come from distinct samples or are repeated measures.
- [ ] The test named, one- or two-sided.
- [ ] Test statistic, confidence interval or spread, effect size and degrees of freedom where they apply.
- [ ] Exact P for significant and non-significant results alike, never only "P < 0.05" or "n.s.".
- [ ] The multiple-testing correction named (Benjamini-Hochberg, Holm). No unadjusted P as an endpoint.
- [ ] The statistical unit defined per analysis (transcript for coverage, cell for per-cell metrics, dataset for
      rank aggregation, seed for training variance).
- [ ] The error bar defined in words (the author's default is the median with the 25th to 75th percentile).
- [ ] A reporting threshold, if any (which P values are printed, which runs count as complete), stated once and
      applied to every result alike.

## Reproducibility

- [ ] Every software package named with its version (a software table in the Supplementary Tables is best).
- [ ] Random seeds reported, and the stochastic steps named.
- [ ] Results over several seeds where stochasticity matters, with the spread defined.
- [ ] Compute disclosed: hardware (GPU or CPU model, memory), runtime per run, total compute.
- [ ] Every setting stated as the value actually run, read from the run records (laws-and-firewall.md section 3).
- [ ] Settings used for other methods: each baseline with its version, its parameters and how they were tuned.
- [ ] A comparator's version checked against its commit: one stated release was an earlier release plus a few
      unreleased commits.
- [ ] Claimed resource limits checked against the logs: one stated uniform time limit was exceeded by a run in the
      logs.
- [ ] Hyperparameters in a table or a literal configuration block, with how they were selected.
- [ ] A reimplemented method or metric marked "adapted from [ref]", with why and with the list of differences.
- [ ] Each metric in a suite has one sentence on the failure it catches that no other metric catches, and names
      the geometry or subset it is computed on.
- [ ] The procedure regenerates the reported numbers from the text alone (workflow.md section 6).

## Study design (answer even when negative)

- [ ] Sample size: the rationale, or "No statistical method was used to predetermine sample size."
- [ ] Exclusions: what was excluded and why, or "No data were excluded beyond the quality filters described in
      Datasets and preprocessing."
- [ ] Randomization, or why it does not apply (deterministic code on fixed inputs).
- [ ] Blinding, or why it does not apply.
- [ ] Replication: what was repeated, and how many times.

## Availability (own subheadings, last in Methods)

- [ ] **Data availability**: every dataset with its accession, checked to be the exact dataset used and not a
      similar one (same tissue and technology is not enough; match the files). Plain URLs. Author-generated data
      deposited with an accession. References and atlases with accession or collection ID.
- [ ] **Code availability**: a DOI-minting archive (Zenodo, Code Ocean, Software Heritage), the version or commit
      that produced the numbers, an OSI license, the install path and the documentation link. A bare GitHub URL is
      not enough.
- [ ] Trained weights and processed data archived with their own DOIs where they exist.
- [ ] Every link opened once before submission. Object-store paths are case-sensitive; one capitalized prefix
      returned 404.

For checking accessions byte for byte against public bundles, use the `integrity-audit` skill.

## Phrases that fail review

| Phrase | Replace with |
|---|---|
| "Methods available upon request." | the methods, in the manuscript or supplement |
| "We used standard protocols." | the protocol cited, with every deviation |
| a P threshold used as a biological cutoff | each stated separately |
| a tool without a version | the version |
| "code is available on GitHub" | the archived version with its DOI and license |
