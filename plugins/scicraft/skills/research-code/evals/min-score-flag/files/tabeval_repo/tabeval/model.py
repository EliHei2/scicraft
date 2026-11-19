import math


def predict_row(features, weights):
    """Linear scores per class, softmax, return (class index, probability)."""
    logits = [sum(f * w for f, w in zip(features, ws)) for ws in weights]
    m = max(logits)
    exps = [math.exp(l - m) for l in logits]
    total = sum(exps)
    best = max(range(len(exps)), key=exps.__getitem__)
    return best, exps[best] / total
