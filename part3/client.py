#!/usr/bin/env python3
import socket
import time
import argparse

# --- Simple config parser (no json lib) ---
def load_config(filename="config.json"):
    cfg = {}
    with open(filename) as f:
        for line in f:
            line = line.strip().strip(",")
            if not line or line[0] in "{}":
                continue
            k, v = line.split(":", 1)
            cfg[k.strip().strip('"')] = v.strip().strip('"')
    return cfg

cfg = load_config()
SERVER_IP = cfg.get("server_ip", "10.0.0.100")
SERVER_PORT = int(cfg.get("port", 8887))
P = int(cfg.get("p", 0))
K = int(cfg.get("k", 5))

def download_file(batch_size: int):
    """
    Send 'batch_size' requests back-to-back, then block until we've received
    exactly 'batch_size' responses (unless EOF is seen earlier). Repeat until EOF.
    """
    offset = P
    all_words = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        buf = ""

        while True:
            # --- send a burst of `batch_size` requests ---
            for _ in range(batch_size):
                req = f"{offset},{K}\n"
                s.sendall(req.encode())
                offset += K

            # --- receive exactly `batch_size` responses (or stop early on EOF) ---
            got = 0
            while got < batch_size:
                chunk = s.recv(4096)
                if not chunk:
                    return all_words  # connection closed

                buf += chunk.decode()
                while "\n" in buf and got < batch_size:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    got += 1

                    if "EOF" in line:
                        # collect remaining words on the EOF line
                        words_part = line.replace("EOF", "").rstrip(",")
                        if words_part:
                            all_words.extend([w for w in words_part.split(",") if w])
                        return all_words
                    else:
                        all_words.extend([w for w in line.split(",") if w])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=1,
                    help="Back-to-back requests per burst (greedy uses c>1)")
    ap.add_argument("--client-id", type=str, default="client")
    args = ap.parse_args()

    t0 = time.time()
    _ = download_file(args.batch_size)
    t1 = time.time()

    # Print both elapsed and absolute finish time (for common-start timing)
    elapsed_ms = int((t1 - t0) * 1000)
    print(f"ELAPSED_MS:{elapsed_ms}")
    print(f"FINISH_EPOCH:{t1:.6f}")

if __name__ == "__main__":
    main()
