#!/usr/bin/env python3
import socket
import select
import collections
import threading
import time

# --- Simple config parser (no json import) ---
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

# Load config
config = load_config()
SERVER_IP   = config.get("server_ip", "10.0.0.100")
SERVER_PORT = int(config.get("port", 8887))
FILENAME    = config.get("filename", "words.txt")
PROC_MS     = int(config.get("proc_ms", 0))        # optional per-request processing time (ms)
REPEAT      = int(config.get("repeat_words", 1))   # optional multiplier for file length

# Load words once (optionally repeat to make the file longer)
with open(FILENAME) as f:
    base = f.read().strip().split(",")
words = base * max(1, REPEAT)

def handle_request(req: str) -> str:
    """Process a single 'p,k' request and return a newline-terminated response."""
    try:
        p, k = map(int, req.split(","))
    except Exception:
        return "EOF\n"

    if p >= len(words):
        return "EOF\n"

    slice_words = words[p:p+k]
    if p + k >= len(words):
        slice_words.append("EOF")

    if PROC_MS > 0:
        time.sleep(PROC_MS / 1000.0)  # uniform service time (optional)

    return ",".join(slice_words) + "\n"

# === Shared state (protected by locks) ===
rq = collections.deque()          # global FCFS queue of (sock, line)
rq_lock = threading.Lock()

inputs = []                       # list of connected client sockets (nonblocking)
inputs_lock = threading.Lock()

buffers = {}                      # sock -> partial text buffer
buffers_lock = threading.Lock()

def receiver_thread(listener: socket.socket):
    """Accept clients and read requests; enqueue each request globally (FCFS)."""
    listener.setblocking(False)

    while True:
        # Snapshot inputs for select safely
        with inputs_lock:
            current_inputs = inputs[:]

        try:
            readable, _, _ = select.select([listener] + current_inputs, [], [], 0.005)
        except Exception:
            continue

        for sock in readable:
            if sock is listener:
                try:
                    conn, _ = listener.accept()
                    conn.setblocking(False)
                    with inputs_lock:
                        inputs.append(conn)
                    with buffers_lock:
                        buffers[conn] = ""
                except Exception:
                    continue
            else:
                try:
                    data = sock.recv(4096)
                except Exception:
                    data = b""

                if not data:
                    # client closed
                    with inputs_lock:
                        if sock in inputs:
                            inputs.remove(sock)
                    with buffers_lock:
                        buffers.pop(sock, None)
                    try:
                        sock.close()
                    except:
                        pass
                    continue

                # append data to per-sock buffer and split into lines
                with buffers_lock:
                    buffers[sock] += data.decode()
                    buf = buffers[sock]

                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            with rq_lock:
                                rq.append((sock, line))
                    buffers[sock] = buf  # save back the remainder

def worker_thread():
    """Pop from rq and serve requests one-by-one (strict FCFS)."""
    while True:
        csock, line = None, None
        with rq_lock:
            if rq:
                csock, line = rq.popleft()

        if csock is None:
            # nothing to serve; small sleep to avoid busy-spin
            time.sleep(0.0005)
            continue

        try:
            resp = handle_request(line)
            csock.sendall(resp.encode())
        except Exception:
            # on error, drop the socket from our sets safely
            with inputs_lock:
                if csock in inputs:
                    inputs.remove(csock)
            with buffers_lock:
                buffers.pop(csock, None)
            try:
                csock.close()
            except:
                pass

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ls:
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind((SERVER_IP, SERVER_PORT))
        ls.listen()
        print(f"Server listening on {SERVER_IP}:{SERVER_PORT} (threaded FCFS)")

        t_recv = threading.Thread(target=receiver_thread, args=(ls,), daemon=True)
        t_work = threading.Thread(target=worker_thread, daemon=True)
        t_recv.start()
        t_work.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Server shutting down...")

if __name__ == "__main__":
    main()
