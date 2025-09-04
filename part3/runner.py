#!/usr/bin/env python3

import os
import re
import time
import glob
import csv
import numpy as np
from pathlib import Path
from topology import create_network

RESULTS_CSV = Path("results_p3.csv")

class Runner:
    def __init__(self, config_file='config.json', runs_per_c=5):
        # --- Simple config parser (avoid json library) ---
        config = {}
        with open(config_file) as f:
            for line in f:
                line = line.strip().strip(",")
                if not line or line[0] in "{}":
                    continue
                key, val = line.split(":", 1)
                key = key.strip().strip('"')
                val = val.strip().strip('"')
                config[key] = val

        self.server_ip = config['server_ip']
        self.port = int(config['port'])
        self.num_clients = int(config['num_clients'])
        self.c_max = int(config['c'])       # max c to test
        self.p = int(config['p'])
        self.k = int(config['k'])
        self.runs_per_c = runs_per_c

        print(f"Config: {self.num_clients} clients, max c={self.c_max}, p={self.p}, k={self.k}")

    def cleanup_logs(self):
        logs = glob.glob("logs/*.log")
        for log in logs:
            os.remove(log)
        os.makedirs("logs", exist_ok=True)

    def parse_logs(self):
        """Return dict: {'rogue':[ms], 'normal':[ms,...]}"""
        results = {'rogue': [], 'normal': []}

        # Rogue log
        rogue_path = "logs/rogue.log"
        if os.path.exists(rogue_path):
            txt = open(rogue_path).read()
            m = re.search(r"ELAPSED_MS\s*:\s*(\d+)", txt)
            if m:
                results['rogue'].append(int(m.group(1)))

        # Normal clients
        for i in range(2, self.num_clients + 1):
            path = f"logs/normal_{i}.log"
            if os.path.exists(path):
                txt = open(path).read()
                m = re.search(r"ELAPSED_MS\s*:\s*(\d+)", txt)
                if m:
                    results['normal'].append(int(m.group(1)))

        return results

    # def calculate_jfi(self, completion_times):
    #     """JFI = (Σu)^2 / (n Σu^2), where u_i = 1/t_i"""
    #     all_times = completion_times['rogue'] + completion_times['normal']
    #     if len(all_times) != self.num_clients:
    #         print(f"[WARN] Expected {self.num_clients} times, got {len(all_times)}")
    #         return 0.0
    #     arr = np.array(all_times, dtype=float)
    #     arr[arr <= 0] = 1e-6
    #     utils = 1.0 / arr
    #     s = utils.sum()
    #     s2 = (utils ** 2).sum()
    #     n = len(utils)
    #     return (s * s) / (n * s2)
    def calculate_jfi(self, completion_times):
        all_times = completion_times['rogue'] + completion_times['normal']
        arr = np.array(all_times, dtype=float)
        # JFI on times (no inversion)
        s = arr.sum()
        s2 = (arr ** 2).sum()
        n = len(arr)
        return (s * s) / (n * s2)


    def run_experiment(self, c_value, run_id=1):
        print(f"Running c={c_value}, run={run_id}")
        self.cleanup_logs()
        net = create_network(num_clients=self.num_clients)

        try:
            server = net.get('server')
            clients = [net.get(f'client{i+1}') for i in range(self.num_clients)]

            # Start server
            server_proc = server.popen("python3 server.py")
            time.sleep(2)

            # Start rogue client
            rogue_proc = clients[0].popen(
                f"python3 client.py --batch-size {c_value} --client-id rogue > logs/rogue.log 2>&1",
                shell=True
            )

            # Start normal clients
            normal_procs = []
            for i in range(1, self.num_clients):
                proc = clients[i].popen(
                    f"python3 client.py --batch-size 1 --client-id normal_{i+1} > logs/normal_{i+1}.log 2>&1",
                    shell=True
                )
                normal_procs.append(proc)

            # Wait for clients
            rogue_proc.wait()
            for proc in normal_procs:
                proc.wait()

            # Stop server
            server_proc.terminate()
            server_proc.wait()
            time.sleep(1)

            # Parse logs & compute JFI
            results = self.parse_logs()
            jfi = self.calculate_jfi(results)

            # Write CSV
            with RESULTS_CSV.open("a", newline="") as f:
                csv.writer(f).writerow([c_value, run_id, jfi])

            print(f"c={c_value}, run={run_id}, JFI={jfi:.3f}")
            return jfi

        finally:
            net.stop()

    def run_varying_c(self):
        if not RESULTS_CSV.exists():
            with RESULTS_CSV.open("w", newline="") as f:
                csv.writer(f).writerow(["c", "run", "jfi"])

        for c in range(1, self.c_max + 1,4):
            for r in range(1, self.runs_per_c + 1):
                self.run_experiment(c, run_id=r)

        print("All experiments completed.")


def main():
    runner = Runner(runs_per_c=5)   # run each c 5 times
    runner.run_varying_c()

if __name__ == '__main__':
    main()
