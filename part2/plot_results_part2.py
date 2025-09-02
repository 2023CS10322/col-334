#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results_p2.csv")

agg = df.groupby("num_clients")["elapsed_ms"].agg(["mean", "std", "count"]).reset_index()
agg["sem"] = agg["std"] / agg["count"].pow(0.5)
agg["ci95"] = 1.96 * agg["sem"]

plt.figure()
plt.errorbar(agg["num_clients"], agg["mean"], yerr=agg["ci95"], fmt='o-', capsize=4)
plt.xlabel("Number of concurrent clients")
plt.ylabel("Average completion time per client (ms)")
plt.title("Concurrent Clients vs Completion Time (avg ± 95% CI, n=5)")
plt.grid(True)
plt.savefig("p2_plot.png", bbox_inches="tight", dpi=180)
print("Saved p2_plot.png")
