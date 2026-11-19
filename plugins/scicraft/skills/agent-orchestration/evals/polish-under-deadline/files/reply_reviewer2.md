# Response to Reviewer 2

We thank the reviewer for the careful reading and the concrete questions. We answer each point below and give the line numbers of the revised PDF.

**W1. The gains could come from the larger training budget, not the routing scheme.**
This is a fair concern. We ran a controlled comparison: the same data, the same number of training steps and the same teacher, with only the routing removed (a single head of matched parameter count). Our student is better on 5 of 7 tasks, and the two tasks where it is not are within one standard deviation over seeds (Table R1, lines 212 to 230). So the routing contributes beyond the budget.

**W2. Why exact match and not token-level F1?**
We use exact match because several tasks have short answers where partial credit is misleading, and it is the metric used by the two benchmarks we compare against. We now also report token-level F1 in Appendix C.3; the ranking of methods does not change on any task.

**W3. The ablation removes components one at a time, which hides interactions.**
We agree that one-at-a-time ablations cannot show interactions. We added the two pairwise ablations the reviewer suggested (Table R2). Removing both components costs more than the sum of removing each alone on 3 of 7 tasks, which we now state in Section 5.2.

**Q1. Is the evaluation data disjoint from the distillation data?**
Yes. No evaluation question appears in the distillation set. We checked this by exact and near-duplicate string matching, and list the evaluation sources in Appendix A.2.

**Q2. Code availability.**
The code and the trained weights will be released with the camera-ready version; an anonymized copy is in the supplementary material.

We hope these answers address the reviewers concerns, and we are happy to clarify anything further.
