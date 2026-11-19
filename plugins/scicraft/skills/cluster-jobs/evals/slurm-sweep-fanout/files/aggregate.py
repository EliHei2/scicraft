"""Collect <runs>/*/metrics.json into one CSV on stdout."""
import json, pathlib, sys
rows = [json.load(open(p)) for p in sorted(pathlib.Path(sys.argv[1]).glob("*/metrics.json"))]
print("config,val_auc")
for r in rows:
    print(f"{r['config']},{r['val_auc']}")
