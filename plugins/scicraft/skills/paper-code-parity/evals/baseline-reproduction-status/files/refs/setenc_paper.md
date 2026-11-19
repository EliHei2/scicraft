# SetEnc (excerpt)

Section 3. The encoder maps a dataset to a 64-dimensional vector. Table 2: the network has 45,424 parameters.

Section 4. Training uses triplets of datasets with Adam (learning rate 1e-3) and early stopping, at most 10,000
steps.

Section 5. Evaluation. We draw a bootstrap sample of the meta-dataset and split it 70/30 into train and test, and
report the accuracy of a discriminator trained on the embeddings.
