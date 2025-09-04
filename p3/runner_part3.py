import subprocess
import sys
import time
import json
import threading
import os

RESULTS_DIR = "results_part3"
CSV_FILE = os.path.join(RESULTS_DIR, "results.csv")

def run_proc(cmd, cid, greedy=False):
    """Run one client process and capture output"""
    args = [sys.executable, "client.py"]
    if greedy:
        args.append("--greedy")
    args.extend(["--id", str(cid)])
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = p.communicate()
    return out

def parse_elapsed(output: str) -> float:
    """Extract elapsed time from client output"""
    for line in output.splitlines():
        if line.startswith("ELAPSED_MS:"):
            return float(line.split(":", 1)[1])
    return float("nan")

def jfi(values):
    """Compute Jain’s Fairness Index"""
    s = sum(values)
    s2 = sum(v * v for v in values)
    n = len(values)
    return (s * s) / (n * s2) if s2 > 0 else 0.0

if __name__ == "__main__":
    # Load config
    with open("config.json", "r") as f:
        cfg = json.load(f)
    num_clients = int(cfg.get("num_clients", 10))
    c = int(cfg.get("c", 10))

    # Start server
    srv = subprocess.Popen([sys.executable, "server.py"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(0.5)

    # Run clients
    outs = [None] * num_clients

    def run_normal(i):
        outs[i] = run_proc("client.py", cid=i, greedy=False)

    def run_greedy(i):
        outs[i] = run_proc("client.py", cid=i, greedy=True)

    threads = []
    for i in range(num_clients - 1):
        t = threading.Thread(target=run_normal, args=(i,))
        t.start()
        threads.append(t)
    t = threading.Thread(target=run_greedy, args=(num_clients - 1,))
    t.start()
    threads.append(t)

    for t in threads:
        t.join()

    # Kill server
    try:
        srv.terminate()
    except Exception:
        pass

    # Parse times
    times = [parse_elapsed(o or "") for o in outs]
    j = jfi(times)

    # Ensure results dir exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Write CSV row
    new_file = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a") as f:
        if new_file:
            header = ["c"] + [f"client{i}" for i in range(num_clients)] + ["jfi"]
            f.write(",".join(header) + "\n")
        row = [str(c)] + [f"{t:.2f}" for t in times] + [f"{j:.4f}"]
        f.write(",".join(row) + "\n")

    # Print progress to terminal
    for i, t in enumerate(times):
        tag = "Greedy" if i == num_clients - 1 else f"Normal-{i}"
        print(f"[{tag}] finished in {t:.2f} ms")
    print(f"JFI(c={c}): {j:.4f}")
