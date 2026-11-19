"""Masked-autoencoder pretraining loop (small stand-in for the eval)."""
import argparse
import json

import torch
from torch import nn

from model import MAE
from data import make_loader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    model = MAE(dim=cfg["dim"], mask_ratio=cfg.get("mask_ratio", 0.75)).cuda()
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=0.05)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=cfg["steps"])
    loader = make_loader(cfg["data"], batch_size=cfg["batch_size"])
    log = open(f"{a.out}/train.jsonl", "a")
    step = 0
    for x in loader:
        x = x.cuda(non_blocking=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            pred, mask = model(x)
            loss = ((pred - x) ** 2).mean()          # reconstruction loss over all patches
        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % 50 == 0:
            log.write(json.dumps({"step": step, "loss": loss.item(), "lr": sched.get_last_lr()[0]}) + "\n")
        step += 1
        if step >= cfg["steps"]:
            break


if __name__ == "__main__":
    main()
