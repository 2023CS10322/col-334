#!/usr/bin/env python3
import socket
import time
import argparse
import os

# --- Simple config parser (no json lib) ---
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

def download_file(batch_size: int):
    offset = P
    all_words = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))

        while True:
            # Send batch_size requests
            for _ in range(batch_size):
                req = f"{offset},{K}\n"
                s.sendall(req.encode())
                offset += K

            # Read responses (keep reading until we hit EOF or file ends)
            data = s.recv(4096).decode().strip()
            if not data:
                break

            parts = data.split("\n")
            for resp in parts:
                if not resp:
                    continue
                if "EOF" in resp:
                    words_part = resp.replace("EOF", "").rstrip(",")
                    if words_part:
                        all_words.extend([w.strip() for w in words_part.split(",") if w.strip()])
                    return all_words  # Done, return immediately
                else:
                    all_words.extend([w.strip() for w in resp.split(",") if w.strip()])




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Number of back-to-back requests per round (rogue uses c > 1)")
    parser.add_argument("--client-id", type=str, default="client",
                        help="Client identifier for logging (unused but passed by runner)")
    args = parser.parse_args()

    start = time.time()
    _ = download_file(args.batch_size)
    end = time.time()

    elapsed_ms = int((end - start) * 1000)
    # Print ONLY elapsed time in required format
    print(f"ELAPSED_MS:{elapsed_ms}")

if __name__ == "__main__":
    main()
