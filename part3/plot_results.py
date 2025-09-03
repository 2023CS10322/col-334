#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import math

RESULTS_CSV = Path("results_p3.csv")

# Load results: columns = ["c", "run", "jfi"]
df = pd.read_csv(RESULTS_CSV)

agg = df.groupby("c")["jfi"].agg(["mean", "std", "count"]).reset_index()
agg["sem"] = agg["std"] / agg["count"].pow(0.5)
agg["ci95"] = 1.96 * agg["sem"]

plt.figure()
plt.errorbar(agg["c"], agg["mean"], yerr=agg["ci95"], fmt="o-", capsize=4)
plt.xlabel("c (number of back-to-back requests by greedy client)")
plt.ylabel("Jain's Fairness Index (JFI)")
plt.title("Fairness vs Greedy Client Requests (FCFS)")
plt.grid(True)
plt.savefig("p3_plot.png", bbox_inches="tight", dpi=180)
print("Saved p3_plot.png")
