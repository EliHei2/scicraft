# Reply to Reviewer 2

We thank the reviewer for the careful reading.

**Q1 (contamination).** No evaluation dataset is in the pretraining corpus. We checked this by hashing column names
and the first 1,000 rows of every table, and no hash matched. We also verified that no evaluation table was ever
used to choose hyperparameters.

**Q2 (seeds).** The ablation uses three seeds, not one (Section 5). Removing the row-attention block lowers mean
balanced accuracy from 0.812 to 0.786, and removing the column embedding lowers it to 0.801.
