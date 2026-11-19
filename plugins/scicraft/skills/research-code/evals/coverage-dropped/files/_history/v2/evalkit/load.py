import csv

MIN_CONF = 0.5


class PredictionReader:
    """Reads a predictions CSV into a list of dicts."""

    def __init__(self, path, min_conf=MIN_CONF):
        self.path = path
        self.min_conf = min_conf

    def read(self):
        with open(self.path) as f:
            return [r for r in self._parse(csv.DictReader(f)) if r["conf"] >= self.min_conf]

    @staticmethod
    def _parse(reader):
        for r in reader:
            r["conf"] = float(r["conf"])
            yield r


def load_predictions(path, min_conf=MIN_CONF):
    """Read predictions and keep rows the model is confident about."""
    return PredictionReader(path, min_conf).read()
