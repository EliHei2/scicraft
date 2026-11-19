"""Tests that assert what the paper states, on the configuration the code actually loads.

Copy into tests/ and replace the constants with your paper's. Rules this file follows:
- every constant cites the paper location and the PAPER_MAP row it belongs to;
- derived rules are recomputed here from their inputs, never copied as a second literal;
- the test reads the shipped config through the loader the code uses (here: json), never a copy of the values;
- a test is kept only after it was seen failing: change one constant in config.json, run, watch it go red, revert.

Run: python3 -m pytest test_paper_constants.py -q    (or python3 test_paper_constants.py)
"""
import json
from pathlib import Path

CONFIG = Path(__file__).with_name("config.json")   # in a real repo: the shipped config through the real loader

# Paper Table 1 (PAPER_MAP section "Encoder", rows "Table 1 constants"). One dict, one place.
TABLE_1 = {
    "model.d_model": 768,
    "model.depth": 12,
    "model.heads": 12,
    "model.patch": 16,
    "optim.lr": 1e-3,
    "optim.warmup_steps": 10_000,
    "aug.mixup_alpha": 0.8,
}


def load():
    return json.loads(CONFIG.read_text())


def get(cfg, dotted):
    for part in dotted.split("."):
        cfg = cfg[part]
    return cfg


def test_config_matches_paper_table_1():
    cfg = load()
    wrong = {k: (get(cfg, k), v) for k, v in TABLE_1.items() if get(cfg, k) != v}
    assert not wrong, f"config differs from paper Table 1 (got, paper): {wrong}"


def test_head_width_rule_from_section_3():
    # Sec. 3.2: "each head has width d/h = 64". Recomputed from the config, so a width change that breaks the rule fails.
    m = load()["model"]
    assert m["d_model"] % m["heads"] == 0
    assert m["d_model"] // m["heads"] == 64


def test_embeddings_are_not_weight_decayed():
    # Sec. 4.1: "no weight decay on embeddings". A setting the paper states is a test, not a comment.
    assert load()["optim"]["decay_embeddings"] is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
