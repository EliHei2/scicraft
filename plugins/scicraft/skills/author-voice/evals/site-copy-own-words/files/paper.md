# Sparse Mixture Distillation for Small Language Models

## Abstract

Small language models are deployed where memory is scarce, but distilling them from a large teacher loses most of the teacher's rare-domain knowledge. We introduce sparse mixture distillation, a training scheme that routes each token of the teacher's output distribution to one of eight small expert heads during distillation and merges the heads into a single dense student afterwards. On 14 downstream benchmarks a 350M-parameter student distilled this way reaches a mean accuracy of 61.2, against 58.9 for standard logit distillation at the same size. The gain is concentrated on the six rare-domain benchmarks, where it is 4.1 points on average, whereas on the eight general benchmarks the two students are within 0.6 points. Merging the heads adds no parameters and no inference cost. Code and weights are released.

## 1. Introduction

A distilled student inherits what its teacher says most often. Logit distillation matches the student's output distribution to the teacher's, token by token, and the loss is dominated by frequent tokens from general text. Rare-domain knowledge, such as chemical names or legal citations, appears in few tokens and contributes little to the gradient. The student therefore forgets it first.

Sparse mixture distillation separates these signals during training. Each token is routed to one of eight expert heads by a router trained on the teacher's hidden states, so tokens from rare domains are learned by heads that general text does not overwrite. After training, the heads are averaged with router-derived weights into one dense output layer. The student that is deployed has exactly the architecture and the cost of a standard student.

## 2. Results

The distilled student reaches a mean accuracy of 61.2 over the 14 benchmarks, against 58.9 for logit distillation and 55.4 for a student trained from scratch on the same data (Table 1). On the six rare-domain benchmarks the gain over logit distillation is 4.1 points on average, indicating that the expert heads retain knowledge that the shared head loses. On the eight general benchmarks the two distilled students are within 0.6 points.

Merging costs little. The merged student is 0.3 points below the unmerged mixture on average. Distillation takes 1.4 times the compute of logit distillation, which is paid once.

## 3. Limitations

We distill only from one teacher family. The router needs the teacher's hidden states, so closed models that expose only output probabilities cannot be used as teachers.
