"""Train the tabular model on the income benchmark and print test accuracy per seed."""
import argparse


def train(lr=1e-3, epochs=30, seed=0, weight_decay=0.01):
    """Train one model. Returns test accuracy in percent."""
    raise NotImplementedError("training code omitted from this excerpt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    a = ap.parse_args()
    for s in a.seeds:
        acc = train(lr=a.lr, epochs=a.epochs, seed=s)
        print(f"seed={s} lr={a.lr} epochs={a.epochs} test_acc={acc:.2f}")


if __name__ == "__main__":
    main()
