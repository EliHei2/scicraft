Notes from the authors' GitHub (checked 2026-10-08):
- released checkpoints: 5 splits, license CC-BY-NC-4.0
- architecture in the code: Dense(2->32), 8 residual blocks of 4 Dense layers, output 32-d
- parameter count when loaded: 75,072
- eval script: bootstrap, then train_test_split(test_size=0.3)
