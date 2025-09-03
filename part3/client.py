#!/usr/bin/env python3
import socket
import time
import sys

# --- Simple config parser ---
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

config = load_config()
SERVER_IP = config.get("server_ip", "10.0.0.100")
SERVER_PORT = int(config.get("port", 8887))
P = int(config.get("p", 0))
K = int(config.get("k", 5))
C = int(config.get("c", 1))  # number of back-to-back requests for greedy client
NUM_CLIENTS = int(config.get("num_clients", 10))

def main():
    # h1 is greedy, others are normal
    # we detect greediness by hostname argument
    host_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    greedy = (host_id == 1)

    start = time.time()
    total_requests = C if greedy else 1

    for i in range(total_requests):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            req = f"{P},{K}\n"
            s.sendall(req.encode())
            _ = s.recv(4096).decode().strip()

    end = time.time()
    elapsed_ms = int((end - start) * 1000)
    print(f"ELAPSED_MS:{elapsed_ms}")

if __name__ == "__main__":
    main()
