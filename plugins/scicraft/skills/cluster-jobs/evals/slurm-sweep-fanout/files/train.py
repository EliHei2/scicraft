"""Train one tabular model config. Writes <out>/<config_name>/metrics.json and model.pt."""
import argparse, json, pathlib, yaml, torch

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    cfg = yaml.safe_load(open(a.config))
    name = pathlib.Path(a.config).stem
    out = pathlib.Path(a.out) / name
    out.mkdir(parents=True, exist_ok=True)
    # ... model training (omitted) ...
    json.dump({"config": name, "val_auc": None}, open(out / "metrics.json", "w"))

if __name__ == "__main__":
    main()
