import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("ablation_seeds.csv")
g = df.groupby("variant")["score"].agg(["mean", "std"]).sort_values("mean", ascending=False)

fig, ax = plt.subplots(figsize=(6, 4))
colors = ["#1f77b4" if v == "full model" else "#ff7f0e" for v in g.index]
widths = [0.9 if v == "full model" else 0.6 for v in g.index]
bars = ax.bar(g.index, g["mean"], yerr=g["std"], color=colors, width=widths, edgecolor="black", capsize=4)
bars[0].set_hatch("//")
ax.text(0, g["mean"].iloc[0] + 0.01, "*", ha="center", fontsize=16)
ax.set_ylim(0.70, 0.83)
ax.set_title("Ablation study: contribution of each component to final model performance (mean ± std)")
ax.text(2.2, 0.825, "n=5 seeds, lr=3e-4, run_v7_final", color="grey", fontsize=7)
ax.legend(bars[:2], ["ours", "ablations"], loc="upper right")
ax.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("fig3_ablation.pdf", bbox_inches="tight")
plt.savefig("fig3_ablation.png", dpi=150, bbox_inches="tight")
