# Method

The backbone is a decoder-only transformer with 24 layers and a patch length of 32 time steps — short enough to keep local shape, long enough to keep the sequence under 512 tokens. Moreover, it leverages a scaling step that divides each series by its mean absolute value. Furthermore, missing values are masked rather than imputed, which honestly matters for sparse retail data. In other words, the backbone never sees an invented value.

Pretraining minimizes the quantile loss at 9 quantiles over 400,000 steps with a batch of 1,024 series. The field wants a single model for all horizons, so the backbone predicts horizons from 1 to 720 steps with one output head.
