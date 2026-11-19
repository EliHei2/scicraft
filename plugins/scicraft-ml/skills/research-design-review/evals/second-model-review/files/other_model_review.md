# Review of the pretraining objective

C1. The reconstruction term uses cosine distance, which is norm-invariant and hides collapse. Switch to smooth-L1.
C2. The isotropy regularizer dominates training and starves the predictor. Its weight should be cut.
C3. The model collapses: effective rank of the embeddings will go to 1 under this loss.
C4. The masking ratio of 0.75 is far from the published optimum; sweep it.
C5. Overall the objective is degenerate and should be redesigned from scratch.
