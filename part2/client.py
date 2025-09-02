#!/usr/bin/env python3
import socket
import sys
import time

# --- Simple config parser (same as server.py) ---
def load_config(filename="config.json"):
    config = {}
    with open(filename) as f:
        for line in f:
            line = line.strip().strip(",")
            if not line or line[0] in "{}":
                continue
            key, val = line.split(":", 1)
            key = key.strip().strip('"')
            val = val.strip().strip('"')
            config[key] = val
    return config

# Load config
config = load_config("config.json")

SERVER_IP = config["server_ip"]
SERVER_PORT = int(config["server_port"])
P = int(config["p"])
K = int(config["k"])

def main():
    start = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        req = f"{P},{K}\n"
        s.sendall(req.encode())
        data = s.recv(4096).decode().strip()
    end = time.time()

    elapsed_ms = int((end - start) * 1000)

    # Only print elapsed time (cleaner for experiments)
    print(f"ELAPSED_MS:{elapsed_ms}")

if __name__ == "__main__":
    main()
