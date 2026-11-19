# Refutation of DESIGN_v2.md
Status: DRAFT
Date: 2026-03-05
Topic: critic reports

Read-only on src/. Every number quoted from probes/*.out.

## Item 1, column-position embedding before the mean pool. VERDICT: DIES as specified
pool_invariance.out: relative change of the pooled vector under a column permutation is 3.1e-08 with the
embedding added before the mean pool, and 2.4e-02 when the same embedding enters an attention pooler.
A mean of (z + p) is the mean of z plus a constant. The trap is scoped: "never add a position embedding in
front of a linear pool". In front of attention it works; that variant is deferred on cost, not refuted on
mechanism.

## Item 2, w_ctx x 64. VERDICT: SURVIVES-WEAKENED
The 0.4% gradient share is confirmed in grad_share.out. Its falsifier ("context loss falls 10%") is unsafe:
a rescaled term can fall in value without the trunk learning anything. Score it against the floors.

## Item 3, learned temperature. VERDICT: DIES
temperature_fit.out: 96.8% of the fitted gain comes from a single scalar rescale; the heteroscedastic part is
3.2%. Raising w_ctx captures the same gain with 0 LOC. A temperature of 0 is an absorbing state at init.

## Not checked
Nobody has read the context loss of a trained run. Every number above is at initialization.
