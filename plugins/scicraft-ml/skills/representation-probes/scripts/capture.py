#!/usr/bin/env python3
"""Read activations from a frozen PyTorch model without corrupting them, and check the reading.

Import `capture` and `compare` into your own extraction code, or run `--selftest` to watch the two hook bugs
happen on a toy model:

  1. A hook that stores its output without .detach().clone() records a tensor that later code mutates in
     place, so the stored value is not what the module produced.
  2. A hook that returns a value replaces the module's output, so the model's own forward pass changes.

The rule both bugs teach: a forward hook copies its output and returns None.

`compare` reports the largest absolute and relative difference between two extractions (two devices, two
precision settings, two input orders) so a precision or device change is measured before vectors are pooled
into one store.

Dependencies: torch (any recent version), numpy. Python 3.9 or later.
Exit code 1 when a selftest check fails.
"""
from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager

import numpy as np


@contextmanager
def capture(modules: dict):
    """Context manager. `modules` maps a name to a torch module. Inside the block, every forward call of each
    module appends a detached, cloned, float32, CPU copy of its output to got[name]. Hooks return None.
    Hooks that fire several times per call (one batch per ensemble member or normalization) give a list."""
    got = {name: [] for name in modules}
    handles = []

    def make(name):
        def hook(module, inputs, output):  # must return None: a returned value replaces the module output
            out = output[0] if isinstance(output, (tuple, list)) else output
            got[name].append(out.detach().clone().float().cpu())
        return hook

    try:
        for name, m in modules.items():
            handles.append(m.register_forward_hook(make(name)))
        yield got
    finally:
        for h in handles:
            h.remove()


def compare(a, b) -> dict:
    """Largest absolute difference and relative difference ||a-b|| / ||a|| between two extractions."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"shapes differ: {a.shape} vs {b.shape}")
    return {"max_abs": float(np.abs(a - b).max()),
            "rel": float(np.linalg.norm(a - b) / max(np.linalg.norm(a), 1e-300))}


def selftest() -> int:
    try:
        import torch
        from torch import nn
    except ImportError:
        print("torch is not installed; the selftest needs it")
        return 1
    torch.manual_seed(0)
    fails = []

    def check(name, cond, val):
        print(f"{'ok  ' if cond else 'FAIL'} {name}: {val}")
        if not cond:
            fails.append(name)

    class Toy(nn.Module):
        """Like an in-context model that adds label embeddings into the tensor a submodule returned."""

        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(8, 8)
            self.head = nn.Linear(8, 2)

        def forward(self, x, label_emb):
            h = self.enc(x)
            h += label_emb            # in-place write into the hooked module's output
            return self.head(h)

    model = Toy().eval()
    x, lab = torch.randn(32, 8), torch.randn(32, 8)
    with torch.no_grad():
        truth = model.enc(x).clone()

        # bug 1: no clone, so the stored tensor is mutated after the hook ran
        raw = []
        h = model.enc.register_forward_hook(lambda m, i, o: raw.append(o.detach()))
        model(x, lab)
        h.remove()
        d_raw = compare(truth, raw[0])["max_abs"]
        check("un-cloned hook records the mutated tensor", d_raw > 1e-3, f"max abs diff {d_raw:.3g}")

        with capture({"enc": model.enc}) as got:
            model(x, lab)
        d_ok = compare(truth, got["enc"][0])["max_abs"]
        check("cloned hook records what the module produced", d_ok == 0.0, f"max abs diff {d_ok:.3g}")

        # bug 2: a hook that returns a value replaces the module output
        ref_out = model(x, lab)
        store = {}
        h = model.enc.register_forward_hook(lambda m, i, o: store.setdefault("enc", o.detach().clone() * 0))
        bad_out = model(x, lab)
        h.remove()
        d_ret = compare(ref_out, bad_out)["max_abs"]
        check("a hook that returns a value changes the model output", d_ret > 1e-3, f"max abs diff {d_ret:.3g}")
        with capture({"enc": model.enc}):
            good_out = model(x, lab)
        check("capture() leaves the model output unchanged", compare(ref_out, good_out)["max_abs"] == 0.0, "0")

        # precision: half precision is not the float32 vector
        if hasattr(torch, "bfloat16"):
            lo = model.enc(x.to(torch.bfloat16).float()).float()
            d_prec = compare(truth, lo)["rel"]
            check("reduced-precision input changes the vector measurably", d_prec > 1e-4, f"rel diff {d_prec:.3g}")
    print("all checks passed" if not fails else f"{len(fails)} failed")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="demonstrate both hook bugs on a toy model")
    a = ap.parse_args(argv)
    if a.selftest:
        sys.exit(selftest())
    ap.print_help()


if __name__ == "__main__":
    main()
