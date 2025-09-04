import time
import json
import socket
import argparse

def read_line(sock: socket.socket) -> str:
    """Read one line terminated by \\n from socket"""
    buf = bytearray()
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        buf.extend(ch)
        if ch == b"\n":
            break
    return buf.decode()

def normal_client(host, port, k, start_p, cid):
    """Normal client: 1 request -> wait -> next"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    p = start_p
    start = time.time()
    try:
        while True:
            s.sendall(f"{p},{k}\n".encode())
            resp = read_line(s)
            if not resp or "EOF" in resp:
                break
            p += k
    finally:
        s.close()
    elapsed_ms = (time.time() - start) * 1000.0
    print(f"[Normal-{cid}] ELAPSED_MS:{elapsed_ms:.2f}", flush=True)
    return elapsed_ms

def greedy_client(host, port, k, start_p, c, cid):
    """Greedy client: send c requests back-to-back -> wait for c replies -> repeat"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    offset = start_p
    start = time.time()
    try:
        while True:
            # Send c requests without waiting
            for i in range(c):
                s.sendall(f"{offset + i*k},{k}\n".encode())

            # Collect c responses
            saw_eof = False
            for _ in range(c):
                resp = read_line(s)
                if not resp or "EOF" in resp:
                    saw_eof = True
            if saw_eof:
                break
            offset += c * k
    finally:
        s.close()
    elapsed_ms = (time.time() - start) * 1000.0
    print(f"[Greedy-{cid}] ELAPSED_MS:{elapsed_ms:.2f}", flush=True)
    return elapsed_ms

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--greedy", action="store_true", help="Run as greedy client")
    parser.add_argument("--id", type=int, default=0, help="Client ID (for logging)")
    args = parser.parse_args()

    # Load config.json
    with open("config.json", "r") as f:
        cfg = json.load(f)
    host = cfg.get("server_ip", "127.0.0.1")
    port = int(cfg.get("port", 8887))
    k = int(cfg.get("k", 5))
    start_p = int(cfg.get("p", 0))
    c = int(cfg.get("c", 3))

    if args.greedy:
        greedy_client(host, port, k, start_p, c, args.id)
    else:
        normal_client(host, port, k, start_p, args.id)
