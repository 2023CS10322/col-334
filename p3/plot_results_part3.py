import matplotlib.pyplot as plt
import csv

xs, jfis = [], []

with open("results_part3/results.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        xs.append(int(row["c"]))
        jfis.append(float(row["jfi"]))

plt.plot(xs, jfis, marker="o")
plt.xlabel("c (greedy batch size)")
plt.ylabel("JFI")
plt.title("Jain Fairness Index vs c (FCFS)")
plt.ylim(0, 1.05)
plt.grid(True, linestyle="--", alpha=0.5)
plt.savefig("p3_plot.png")
print("[PLOT] wrote p3_plot.png")
