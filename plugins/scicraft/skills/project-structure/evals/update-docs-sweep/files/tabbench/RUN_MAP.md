# Run map

| Unit | Variant | Config | Output | Status | Manifest | Synced | Notes |
|---|---|---|---|---|---|---|---|
| suite_v2 | model_s | configs/model_s.yaml | results/runs/suite_v2/model_s | validated | yes | yes | |
| suite_v2 | model_m | configs/model_m.yaml | results/runs/suite_v2/model_m | done | yes | - | batch 512 runs out of memory on a 24 GB card; 256 fits |
| suite_v2 | model_b | configs/model_b.yaml | results/runs/suite_v2/model_b | failed | yes | - | job imported an old numpy from ~/.local; set PYTHONNOUSERSITE=1 in the job script |
| suite_v3 | model_s | configs/model_s.yaml | results/runs/suite_v3/model_s | done | yes | - | suite_v3 download needs the mirror URL in configs/paths.env, the default host times out |
