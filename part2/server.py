#!/usr/bin/env python3
import socket

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

# Load config
config = load_config("config.json")

SERVER_IP = config["server_ip"]
SERVER_PORT = int(config["server_port"])
FILENAME = config["filename"]

# Load words file once
with open(FILENAME) as f:
    words = f.read().strip().split(",")

def handle_client(conn):
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            return
        try:
            p, k = map(int, data.split(","))
        except:
            conn.sendall(b"EOF\n")
            return

        if p >= len(words):
            conn.sendall(b"EOF\n")
            return

        slice_words = words[p:p+k]
        if p + k >= len(words):
            slice_words.append("EOF")

        response = ",".join(slice_words) + "\n"
        conn.sendall(response.encode())
    finally:
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((SERVER_IP, SERVER_PORT))
        s.listen()

        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

        while True:
            conn, addr = s.accept()
            handle_client(conn)   # sequential, no threading

if __name__ == "__main__":
    main()
