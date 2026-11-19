# Introduction

Time-series forecasting is a cornerstone of modern decision-making — from energy grids to retail. The field wants models that transfer across domains without retraining. Moreover, current forecasting backbones are trained per dataset, which honestly limits their reach. Furthermore, per-dataset training requires thousands of labelled series per domain. In other words, every new domain needs its own model.

We present a pretrained forecasting backbone that leverages 2.1 million public series from 9 domains. It forecasts unseen domains zero-shot and reaches a mean absolute scaled error of 0.81 against 0.93 for the best per-dataset model.
