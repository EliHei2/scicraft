import matplotlib.pyplot as plt
sizes = [400, 900, 5000, 20000, 80000]
gain = [0.07, 0.05, 0.02, 0.004, -0.003]
plt.scatter(sizes, gain, label="RR-Pool vs XGBoost")
plt.axhline(0, ls="--", c="k")
plt.xscale("log"); plt.xlabel("training rows"); plt.ylabel("accuracy gain")
plt.legend(); plt.savefig("gain_vs_size.pdf")
