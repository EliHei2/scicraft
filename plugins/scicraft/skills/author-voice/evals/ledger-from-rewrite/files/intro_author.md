# Introduction

Time-series forecasting supports decisions from energy grids to retail. Forecasting encoders are trained per dataset, so each new domain needs thousands of labelled series and its own model.

We present a pretrained forecasting encoder that uses 2.1 million public series from 9 domains. It forecasts unseen domains zero-shot and reaches a mean absolute scaled error of 0.81 against 0.93 for the best per-dataset model.
