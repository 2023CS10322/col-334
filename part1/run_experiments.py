# STARTER CODE ONLY. EDIT AS DESIRED
#!/usr/bin/env python3
import re
import time
import csv
import json
from pathlib import Path
from topo_wordcount import make_net

# Config
K_VALUES = []
val = 1
while val <= 100:
    K_VALUES.append(val)
    if val < 5:
        val += 1     # step of 1 for small k
    elif val < 15:
        val += 2     # step of 2
    elif val < 50:
        val += 10     # step of 5
    else:
        val += 20    # step of 10

RUNS_PER_K = 5
SERVER_CMD = "./server --config config.json"
CLIENT_CMD_TMPL = "./client --config config.json --quiet"

RESULTS_CSV = Path("results.csv")


def modify_config(key, value, filename="config.json"):
    """Update a key in config.json with the given value."""
    # Load existing config
    with open(filename, "r") as f:
        config = json.load(f)

    # Update the key
    config[key] = value

    # Write back to file
    with open(filename, "w") as f:
        json.dump(config, f, indent=2)

def main():
    # Prepare CSV
    if not RESULTS_CSV.exists():
        with RESULTS_CSV.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["k", "run", "elapsed_ms"])

    net = make_net()
    net.start()

    h1 = net.get('h1')  # client
    h2 = net.get('h2')  # server

    # Ensure words.txt exists (shared FS)
    if not Path("words.txt").exists():
        Path("words.txt").write_text("cat,bat,cat,dog,dog,emu,emu,emu,ant\n")

    # Start server
    srv = h2.popen(SERVER_CMD, shell=True, stdout=None, stderr=None)
    time.sleep(0.5)  # give it a moment to bind

    try:
        for k in K_VALUES:
            for r in range(1, RUNS_PER_K + 1):
                modify_config("k", k) # should implement this function
                cmd = CLIENT_CMD_TMPL
                out = h1.cmd(cmd)
                # parse ELAPSED_MS
                m = re.search(r"ELAPSED_MS:(\d+)", out)
                if not m:
                    print(f"[warn] No ELAPSED_MS found for k={k} run={r}. Raw:\n{out}")
                    continue
                ms = int(m.group(1))
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([k, r, ms])
                print(f"k={k} run={r} elapsed_ms={ms}")
    finally:
        srv.terminate()
        time.sleep(0.2)
        net.stop()

if __name__ == "__main__":
    main()
