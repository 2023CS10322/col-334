#!/usr/bin/env python3
import re
import time
import csv
from pathlib import Path
from subprocess import PIPE, TimeoutExpired
from world_topocount import make_net   # your topology file
from config_utils import modify_config # helper without json

# Config
NUM_CLIENTS_LIST = list(range(1, 33, 4))  # 1,5,9,..., 32
RUNS_PER_SETTING = 5
SERVER_CMD = "python3 server.py"
CLIENT_CMD = "python3 client.py"
RESULTS_CSV = Path("results_p2.csv")

COMM_TIMEOUT = 10  # seconds to wait for a client process to finish & produce output

def safe_get_output(proc):
    """
    Call communicate() on proc, handle TimeoutExpired, bytes -> str conversion,
    and return stdout (string) or empty string.
    """
    try:
        out, err = proc.communicate(timeout=COMM_TIMEOUT)
    except TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            out, err = proc.communicate(timeout=1)
        except Exception:
            out = None
    # Normalize
    if out is None:
        out = ""
    elif isinstance(out, bytes):
        try:
            out = out.decode('utf-8', errors='replace')
        except Exception:
            out = str(out)
    return out

def main():
    # Prepare CSV header
    if not RESULTS_CSV.exists():
        with RESULTS_CSV.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["num_clients", "run", "elapsed_ms"])

    net = None
    try:
        for nclients in NUM_CLIENTS_LIST:
            # update config.json
            modify_config("num_clients", nclients)

            # rebuild network with correct number of clients
            if net:
                net.stop()
            net = make_net()
            net.start()
            hS = net.get("hS")

            for r in range(1, RUNS_PER_SETTING + 1):
                # Start server in hS
                srv = hS.popen(SERVER_CMD, shell=True)
                time.sleep(0.5)  # wait for bind

                # Start all clients in parallel, capture stdout/stderr via PIPE
                procs = []
                for i in range(1, nclients + 1):
                    h = net.get(f"h{i}")
                    # Request a subprocess with pipes so communicate() returns output
                    proc = h.popen(CLIENT_CMD, shell=True, stdout=PIPE, stderr=PIPE, text=True)
                    procs.append((h, proc))

                # Collect results from all clients
                elapsed_list = []
                for h, proc in procs:
                    out = safe_get_output(proc)
                    # debug: print(client output)  # enable if you want to see outputs
                    m = re.search(r"ELAPSED_MS:(\d+)", out)
                    if m:
                        elapsed_list.append(int(m.group(1)))

                # Stop server for this run
                try:
                    srv.terminate()
                except Exception:
                    pass
                time.sleep(0.2)

                if not elapsed_list:
                    print(f"[warn] No results for num_clients={nclients} run={r}")
                    continue

                avg_ms = sum(elapsed_list) / len(elapsed_list)
                with RESULTS_CSV.open("a", newline="") as f:
                    csv.writer(f).writerow([nclients, r, avg_ms])
                print(f"num_clients={nclients} run={r} avg_elapsed_ms={avg_ms:.2f}")

    finally:
        if net:
            net.stop()

if __name__ == "__main__":
    main()
