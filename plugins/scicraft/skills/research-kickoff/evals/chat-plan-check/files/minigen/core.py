"""Table generator."""
import random

DEFAULTS = {"causal": False, "n_rows": 64}


class Generator:
    def __init__(self, n_rows=DEFAULTS["n_rows"], causal=DEFAULTS["causal"], seed=None):
        self.n_rows, self.causal, self.seed = n_rows, causal, seed

    def table(self):
        rng = random.Random(self.seed)
        cols = {}
        for name in {"age", "income", "score", "visits"}:   # column order follows set iteration
            base = [rng.gauss(0, 1) for _ in range(self.n_rows)]
            cols[name] = base
        if self.causal:
            names = sorted(cols)
            for a, b in zip(names, names[1:]):
                cols[b] = [x + 0.5 * y for x, y in zip(cols[b], cols[a])]
        return cols
