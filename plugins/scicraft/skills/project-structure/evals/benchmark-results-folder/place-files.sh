#!/usr/bin/env bash
# Builds a small benchmark project, embbench/, whose results are scattered and whose settings are duplicated.
set -eu
R=embbench
mkdir -p "$R/src/embbench" "$R/scripts" "$R/notebooks" "$R/out_20261101_0930/figs" "$R/out_20261109_1712/figs"
echo '"""Embedding benchmark on tabular datasets."""' > "$R/src/embbench/__init__.py"
cat > "$R/src/embbench/models.py" <<'PY'
"""Fake embedding models: a stand-in for the real ones."""
import hashlib


def embed(model, table_id, dim=8):
    if model == "model_c" and table_id.endswith(("#1", "_1")):
        raise RuntimeError("model_c ran out of memory on this table")
    h = hashlib.sha256(f"{model}|{table_id}".encode()).digest()
    return [b / 255 for b in h[:dim]]
PY
cat > "$R/scripts/run_bench.py" <<'PY'
"""Embed every table with every model and plot the result."""
import json, os, sys, time
sys.path.insert(0, "src")
from embbench.models import embed

MODELS = ["model_a", "model_b", "model_c"]
TABLES = ["credit-g", "adult", "phoneme", "spambase"]
NOISE = [0.1, 0.3]
SEEDS = [0, 1]

out = f"out_{time.strftime('%Y%m%d_%H%M')}"
os.makedirs(f"{out}/figs", exist_ok=True)
res = {}
for m in MODELS:
    for t in TABLES:
        for lvl in NOISE:
            for s in SEEDS:
                key = f"{t}_{lvl}_{s}"
                res[f"{m}:{key}"] = embed(m, key)   # crashes the whole run on model_c
json.dump(res, open(f"{out}/embeddings.json", "w"))
open("figs_latest.png", "w").write("figure")         # overwritten every time
PY
cat > "$R/notebooks/explore.py" <<'PY'
# %% settings (copied from run_bench.py, slightly different)
MODELS = ["model_a", "model_b"]
TABLES = ["credit-g", "adult", "phoneme"]
NOISE = [0.1, 0.2]
# %% load
import json, glob
latest = sorted(glob.glob("out_*"))[-1]
res = json.load(open(f"{latest}/embeddings.json"))
print(len(res))
PY
echo '{}' > "$R/out_20261101_0930/embeddings.json"; echo png > "$R/out_20261101_0930/figs/umap.png"
echo '{}' > "$R/out_20261109_1712/embeddings.json"
echo png > "$R/figs_latest.png"
printf '__pycache__/\n' > "$R/.gitignore"
printf '# embbench\n\nCompare embedding models on tabular datasets.\n' > "$R/README.md"
