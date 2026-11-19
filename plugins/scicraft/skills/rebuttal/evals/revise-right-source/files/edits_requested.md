Changes we promised in the replies (from our rebuttal notes):

1. Ablations: they now use the full model trained for 200k steps against an identically trained control. Replace
   the sentence about the small model. Add a new table "Ablations of the full model" with two rows:
   no 3D distance bias: -.041 ; no collection token: -.018 (change in mean score over the 14 tasks).
2. Add one sentence after the mean rank sentence: "When every test molecule whose scaffold occurs in the
   pretraining corpus is removed, our encoder keeps the best mean rank (2.4)."
3. Typo: nothing else to change.
