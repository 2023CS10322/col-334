#!/usr/bin/env python3
import socket

# --- Simple config parser (no json import) ---
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
config = load_config()
SERVER_IP = config.get("server_ip", "10.0.0.100")
SERVER_PORT = int(config.get("port", 8887))
FILENAME = config.get("filename", "words.txt")

# Load words
with open(FILENAME) as f:
    words = f.read().strip().split(",")

def handle_request(req: str) -> str:
    try:
        p, k = map(int, req.split(","))
    except:
        return "EOF\n"

    if p >= len(words):
        return "EOF\n"

    slice_words = words[p:p+k]
    if p + k >= len(words):
        slice_words.append("EOF")
    return ",".join(slice_words) + "\n"

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((SERVER_IP, SERVER_PORT))
        s.listen()
        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode().strip()
                if not data:
                    continue
                response = handle_request(data)
                conn.sendall(response.encode())

if __name__ == "__main__":
    main()
