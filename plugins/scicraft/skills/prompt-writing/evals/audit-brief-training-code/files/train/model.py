import torch
from torch import nn


class MAE(nn.Module):
    def __init__(self, dim=256, mask_ratio=0.75, patch=16):
        super().__init__()
        self.mask_ratio = mask_ratio
        self.embed = nn.Linear(patch * patch * 3, dim)
        self.encoder = nn.TransformerEncoder(nn.TransformerEncoderLayer(dim, 8, batch_first=True), 6)
        self.decoder = nn.Linear(dim, patch * patch * 3)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, dim))

    def forward(self, x):                      # x: (B, N, patch*patch*3)
        B, N, _ = x.shape
        keep = int(N * (1 - self.mask_ratio))
        idx = torch.rand(B, N, device=x.device).argsort(dim=1)
        mask = torch.ones(B, N, device=x.device)
        mask.scatter_(1, idx[:, :keep], 0)
        h = self.embed(x)
        h = torch.where(mask[..., None].bool(), self.mask_token.expand(B, N, -1), h)
        return self.decoder(self.encoder(h)), mask
