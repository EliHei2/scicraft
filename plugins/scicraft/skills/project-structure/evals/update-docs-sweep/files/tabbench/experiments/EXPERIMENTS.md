# Experiments log

## Entries

### 2026-11-12 model_b on suite_v2
- goal: first large-model run
- result: failed (ImportError deep in sklearn: numpy from ~/.local shadowed the env)
- next action: set PYTHONNOUSERSITE=1 and resubmit

### 2026-11-10 model_m on suite_v2
- goal: medium model
- result: done after one oom at batch 512; rerun at 256
