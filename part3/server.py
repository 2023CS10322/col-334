#!/usr/bin/env python3
import socket
import select
import collections

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

# Load words once
with open(FILENAME) as f:
    words = f.read().strip().split(",")

def handle_request(req: str) -> str:
    """Process a single 'p,k' request string and return response line (ending with \\n)."""
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
    # One listener, many nonblocking client sockets
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ls:
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind((SERVER_IP, SERVER_PORT))
        ls.listen()
        ls.setblocking(False)
        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

        inputs = [ls]                 # listener + all connected clients
        buffers = {}                  # sock -> partial-line text buffer
        rq = collections.deque()      # GLOBAL FCFS queue of (sock, request_line)

        while True:
            # Wait for IO on any socket (no threads)
            readable, _, _ = select.select(inputs, [], [], 0.005)

            for sock in readable:
                if sock is ls:
                    # New client
                    conn, _ = ls.accept()
                    conn.setblocking(False)
                    inputs.append(conn)
                    buffers[conn] = ""
                else:
                    # Data from a client
                    try:
                        data = sock.recv(4096)
                    except Exception:
                        data = b""
                    if not data:
                        # Client closed
                        if sock in inputs:
                            inputs.remove(sock)
                        buffers.pop(sock, None)
                        try:
                            sock.close()
                        except:
                            pass
                        continue

                    buffers[sock] += data.decode()
                    # Split into complete lines (requests)
                    while "\n" in buffers[sock]:
                        line, buffers[sock] = buffers[sock].split("\n", 1)
                        line = line.strip()
                        if line:
                            rq.append((sock, line))  # enqueue request globally

            # Serve exactly ONE request per loop iteration (strict FCFS by arrival)
            if rq:
                csock, line = rq.popleft()
                try:
                    resp = handle_request(line)
                    csock.sendall(resp.encode())
                except Exception:
                    # Drop dead sockets
                    if csock in inputs:
                        inputs.remove(csock)
                    buffers.pop(csock, None)
                    try:
                        csock.close()
                    except:
                        pass

if __name__ == "__main__":
    main()
