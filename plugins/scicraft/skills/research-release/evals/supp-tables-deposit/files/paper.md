# A compact tabular encoder for clinical feature tables (draft)

## Methods
We pretrained the encoder on five public tabular datasets (Supplementary Table 1). Hyperparameters are listed in
Supplementary Table 2: learning rate 0.0003, batch size 256, 40 epochs, weight decay 0.01. The 32 input features
used for the clinical tasks are listed in Supplementary Table 3. Evaluation tasks and their sources are given in
Supplementary Table 4. Software versions are in Supplementary Table 5.

## Results
The encoder reached a mean AUROC of 0.81 across the eight evaluation tasks (Figure 2). Per-sample predictions and
embeddings are available as reproducibility data.
