---
type: llm
focus: trace
weight: 1
---

The v1 prior uses mix_scm with is_causal sampled from True and False (passed in scm_sampled_hp and removed from scm_fixed_hp), or the answer checks the installed default, finds is_causal fixed to False, and says this differs from the pretraining recipe.
