import torch


def make_loader(path, batch_size):
    data = torch.load(path)                     # (M, N, patch*patch*3), already normalized per patch
    return torch.utils.data.DataLoader(data, batch_size=batch_size, shuffle=True, drop_last=True)
