import pandas as pd

feat = pd.read_csv("features.csv")
pred = pd.read_csv("preds.csv")

# predictions come back from the inference job, one row per user
df = pd.concat([feat.reset_index(drop=True), pred[["pred"]].reset_index(drop=True)], axis=1)
df = df.dropna()
acc = (df["label"] == df["pred"]).mean()
print(f"n={len(df)} accuracy={acc:.3f}")
