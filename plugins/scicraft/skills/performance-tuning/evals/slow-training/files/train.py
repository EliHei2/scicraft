"""Toy point-cloud classifier. Each sample is a cloud of points; features are the mean offset to the k nearest
neighbors of every point, computed in the dataset. Logs loss every 10 steps to train_log.jsonl."""
import json
import time

import torch
from torch.utils.data import DataLoader, Dataset

SEED = 0
N_POINTS = 2048
K = 16


class Clouds(Dataset):
    def __init__(self, n):
        g = torch.Generator().manual_seed(SEED)
        self.pts = torch.randn(n, N_POINTS, 2, generator=g)
        self.y = (self.pts[:, :, 0].mean(1) > 0).long()

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        p = self.pts[i]
        d = torch.cdist(p, p)                                   # (N, N)
        idx = d.topk(K + 1, largest=False).indices[:, 1:]       # (N, K)
        feat = (p[idx] - p[:, None]).mean(1)                    # (N, 2)
        return torch.cat([p, feat], 1).mean(0), self.y[i]       # (4,)


def main():
    torch.manual_seed(SEED)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ds = Clouds(4096)
    dl = DataLoader(ds, batch_size=64, shuffle=True, num_workers=8,
                    generator=torch.Generator().manual_seed(SEED))
    model = torch.nn.Sequential(torch.nn.Linear(4, 128), torch.nn.ReLU(), torch.nn.Linear(128, 2)).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    step, t0 = 0, time.time()
    with open("train_log.jsonl", "w") as fh:
        for epoch in range(2):
            for x, y in dl:
                x, y = x.to(dev), y.to(dev)
                loss = torch.nn.functional.cross_entropy(model(x), y)
                opt.zero_grad()
                loss.backward()
                opt.step()
                step += 1
                if step % 10 == 0:
                    fh.write(json.dumps({"step": step, "loss": loss.item()}) + "\n")
    print(f"done {step} steps in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
