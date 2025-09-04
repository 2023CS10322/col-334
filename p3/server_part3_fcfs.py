import json
import socket
import selectors
import threading
import queue
from typing import Dict, Tuple

REQ_QUEUE: "queue.Queue[Tuple[socket.socket, int, int]]" = queue.Queue()

class FCFSWordServer:
    def __init__(self, cfg_path: str = "config.json", words_path: str = "words.txt"):
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        self.host = cfg.get("server_ip", "0.0.0.0")
        self.port = int(cfg.get("port", 8887))
        self.selector = selectors.DefaultSelector()
        self.listen_sock: socket.socket | None = None
        # Load words file once
        with open(words_path, "r") as wf:
            raw = wf.read().strip()
        self.words = [w.strip() for w in raw.split(",") if w.strip()]
        # Per-connection read buffers
        self.buffers: Dict[int, bytearray] = {}
        # Worker thread
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)

    # --- protocol helpers ---
    def _handle_request(self, p: int, k: int) -> str:
        n = len(self.words)
        if p >= n:
            return "EOF\n"
        end = min(p + k, n)
        chunk = ",".join(self.words[p:end])
        # Append EOF if we reached file end in this response
        if end >= n:
            if chunk:
                return f"{chunk},EOF\n"
            else:
                return "EOF\n"
        return chunk + "\n"

    # --- network loops ---
    def _accept(self, sock: socket.socket):
        conn, addr = sock.accept()
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self._read_client)
        self.buffers[id(conn)] = bytearray()

    def _read_client(self, conn: socket.socket):
        try:
            data = conn.recv(4096)
        except ConnectionResetError:
            data = b""
        if not data:
            # client closed
            try:
                self.selector.unregister(conn)
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            self.buffers.pop(id(conn), None)
            return
        buf = self.buffers[id(conn)]
        buf.extend(data)
        # Extract full lines
        while True:
            nl = buf.find(b"\n")
            if nl == -1:
                break
            line = buf[:nl].decode(errors="ignore")
            del buf[:nl+1]
            line = line.strip()
            if not line:
                continue
            # Expect "p,k"
            try:
                p_str, k_str = line.split(",", 1)
                p = int(p_str.strip())
                k = int(k_str.strip())
            except Exception:
                # Malformed line; ignore
                continue
            # Enqueue request (FCFS across ALL clients)
            REQ_QUEUE.put((conn, p, k))

    def _worker_loop(self):
        while True:
            conn, p, k = REQ_QUEUE.get()
            try:
                resp = self._handle_request(p, k).encode()
                # sendall from single worker guarantees ordered writes per response
                conn.sendall(resp)
            except Exception:
                # socket might be gone; ignore
                pass

    def serve_forever(self):
        # Listen socket
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind((self.host, self.port))
        self.listen_sock.listen()
        self.listen_sock.setblocking(False)
        self.selector.register(self.listen_sock, selectors.EVENT_READ, self._accept)
        # Start worker
        self.worker.start()
        print(f"[FCFS] Listening on {self.host}:{self.port} with {len(self.words)} words loaded")
        try:
            while True:
                for key, _ in self.selector.select(timeout=1.0):
                    cb = key.data
                    if key.fileobj is self.listen_sock:
                        cb(self.listen_sock)
                    else:
                        cb(key.fileobj)
        finally:
            try:
                self.selector.close()
            except Exception:
                pass
            if self.listen_sock:
                self.listen_sock.close()

if __name__ == "__main__":
    FCFSWordServer().serve_forever()

