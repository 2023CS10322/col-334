#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_CSV = Path("results_p3.csv")

# Load results: columns = ["c", "run", "jfi"]
df = pd.read_csv(RESULTS_CSV)

# Aggregate by c: mean, std, count
agg = df.groupby("c")["jfi"].agg(["mean", "std", "count"]).reset_index()

# Standard error of the mean
agg["sem"] = agg["std"] / agg["count"].pow(0.5)

# 95% confidence interval
agg["ci95"] = 1.96 * agg["sem"]

# Plot
plt.figure(figsize=(8,5))
plt.errorbar(
    agg["c"], agg["mean"],
    yerr=agg["ci95"],
    fmt="o-", capsize=4, linewidth=2
)
plt.xlabel("c (number of back-to-back requests by greedy client)")
plt.ylabel("Jain's Fairness Index (JFI)")
plt.plot(agg["c"], agg["mean"], "o-", linewidth=2)
plt.title("Fairness vs Greedy Client Requests (FCFS)")
plt.ylim(0, 1.05)  # JFI is always between 0 and 1
plt.grid(True, linestyle="--", alpha=0.7)
plt.savefig("p3_plot.png", bbox_inches="tight", dpi=180)
print("Saved p3_plot.png")
