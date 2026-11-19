"""tabeval: predict and summarize.

    python3 -m tabeval.cli predict --input data/table.csv --output out/predictions.csv
    python3 -m tabeval.cli summary --predictions out/predictions.csv --labels data/table.csv
"""
import argparse
import csv
import os

from tabeval.model import predict_row

WEIGHTS = [[0.8, -0.2, 0.1], [-0.3, 0.9, 0.0], [0.1, 0.1, 0.7]]


def cmd_predict(args):
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.input) as f, open(args.output, "w", newline="") as g:
        writer = csv.writer(g)
        writer.writerow(["row_id", "pred", "score"])
        for r in csv.DictReader(f):
            feats = [float(r[k]) for k in ("f1", "f2", "f3")]
            pred, score = predict_row(feats, WEIGHTS)
            writer.writerow([r["row_id"], pred, f"{score:.4f}"])


def cmd_summary(args):
    labels = {r["row_id"]: int(r["label"]) for r in csv.DictReader(open(args.labels))}
    preds = list(csv.DictReader(open(args.predictions)))
    correct = sum(int(p["pred"]) == labels[p["row_id"]] for p in preds)
    print(f"rows {len(preds)} accuracy {correct / max(len(preds), 1):.4f}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tabeval")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("predict", help="score every row of a table")
    p.add_argument("--input", "-i", required=True, help="CSV with row_id, f1, f2, f3")
    p.add_argument("--output", "-o", default="out/predictions.csv", help="where predictions are written")
    p.set_defaults(func=cmd_predict)
    s = sub.add_parser("summary", help="accuracy of a predictions file")
    s.add_argument("--predictions", required=True)
    s.add_argument("--labels", required=True)
    s.set_defaults(func=cmd_summary)
    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
