Title: Note on an unfair and inconsistent review by Reviewer Xq7P

Dear Area Chair,

We would like to draw your attention to our discussion with Reviewer Xq7P, whose follow-up and rating we find difficult to reconcile. We fully respect the reviewer's right to ask questions, and we have answered every point of the original review with new results in the revised paper.

The reviewer's own words after the rebuttal are positive. The reviewer writes:

> "The response clarifies some of my questions, and the paper is clearly written."

and, in the original review:

> "The paper is clearly written and the results are strong."

Yet the rating stays at 4. The follow-up names no gap in the evidence and asks for no concrete analysis that the paper lacks. Instead, it now rests on two new requests: that the method be substantially better than GraphFM on every task, and that it be validated on wet-lab measurements of new compounds.

We never claimed to be best on every task. Our claim is that one encoder pretrained on many molecule collections transfers across property prediction tasks, and the benchmark supports it.

| Original concern | Revision | The reviewer after the rebuttal |
|---|---|---|
| Averages only, unclear on how many tasks the encoder is better | First on 9 of the 14 tasks and second on 3 (lines 413 to 416) | "clarifies some of my questions" |
| Ablations on a small model | All six ablations rerun on the full model at 200k steps against an identically trained control (lines 447 to 450) | not raised again |
| Scaffolds seen in pretraining | Scaffold split: best mean rank (2.4), and on solubility our encoder ranks 4th of the 12 methods (lines 431 to 433) | not raised again |

**Our encoder ranks first on 9 of the 14 tasks among 12 compared methods, and its mean rank is 2.1 against 4.6 for the next method (lines 413 to 416). Removing the 3D distance bias lowers the mean score over the 14 tasks by .041, the largest of the six ablations (lines 447 to 450). Against GraphFM alone the difference is significant with a p-value of .031.**

Three statements of the follow-up tell only part of these results (reviewer in red, full result in green).

| Reviewer | Paper |
|---|---|
| $\color{red}{\textsf{"not substantially better than GraphFM"}}$ | $\color{darkgreen}{\textsf{first on 9 of 14 tasks, mean rank 2.1 against 4.6}}$ (lines 413 to 416) |
| $\color{red}{\textsf{"pretrained on more molecules"}}$ | $\color{darkgreen}{\textsf{best mean rank on a 2.1 million subset}}$ (lines 470 to 471) |
| $\color{red}{\textsf{"one seed"}}$ | $\color{darkgreen}{\textsf{median over three seeds}}$ (line 463) |

To put the first point in context once more: the comparison with GraphFM was raised by Reviewer Lm2T as well, who asked whether it is fair given that GraphFM was pretrained on fewer molecules. We answered this directly by pretraining our encoder on a random subset of 2.1 million molecules, the same number as GraphFM, and our encoder still has the best mean rank (2.6) on that subset. We believe that this settles the question of pretraining data size, and Reviewer Lm2T did not raise it again. In the same spirit we reported the median over three seeds for every number in Tables 1 and 2, as Reviewer Rk9D asked, with each seed in Appendix E.

On the first new request: beating every other method on every task by a large margin is not a criterion of the venue. The reviewer guideline asks reviewers to judge whether a submission "convincingly demonstrates new, relevant, impactful knowledge" and notes that this "does not necessarily require state-of-the-art results". The encoder ranks first on most tasks all the same.

On the second new request: wet-lab validation of new compounds is a separate study that belongs in a chemistry journal. The venue is a venue for representation learning. We would gladly provide evidence on any concrete point within the scope of the paper.

The other two reviewers recommend acceptance. Reviewer Lm2T writes of "strong empirical results and a useful public benchmark", and Reviewer Rk9D of "convincing ablations of the attention design".

We understand that reviewers may keep their ratings, and we do not ask the Area Chair to override anyone. We only ask that the rating be read together with the reviewer's own written assessment, which in our reading supports the paper, and with the criteria of the venue, which do not require the paper to be first on every single task by a large margin. We have tried throughout the discussion to answer each point quickly and in full, and we remain available until the end of the discussion period.

We kindly ask whether you could engage with the reviewer and request reconsideration, or otherwise weigh the rating against the reviewer's written assessment and the venue's criteria. We would also be grateful if the reviewer could be asked to state which concrete evidence would change the rating, since the follow-up names none.

We thank you for your time and for handling the discussion of our paper.

Best regards,

The authors
