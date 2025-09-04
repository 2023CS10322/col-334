import socket
import threading
import json
from collections import deque

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

HOST = config['server_ip']
PORT = config['port']

# Read words from file
with open('words.txt', 'r') as f:
    words = f.read().strip().split(',')

# Thread-safe queue for requests
request_queue = deque()
queue_lock = threading.Lock()
condition = threading.Condition(queue_lock)

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            return
        
        # Add request to queue
        with condition:
            request_queue.append((conn, data))
            condition.notify()
            
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        # Note: Connection will be closed by the worker thread
        pass

def process_requests():
    while True:
        with condition:
            while not request_queue:
                condition.wait()
            conn, data = request_queue.popleft()
        
        try:
            # Parse request
            parts = data.split(',')
            if len(parts) != 2:
                conn.send("Invalid request format. Use: p,k\\n".encode())
                conn.close()
                continue
                
            p = int(parts[0])
            k = int(parts[1])
            
            # Check if offset is valid
            if p >= len(words):
                conn.send("EOF\n".encode())
                conn.close()
                continue
                
            # Get words starting at offset p
            end_idx = min(p + k, len(words))
            response_words = words[p:end_idx]
            
            # Add EOF if reached end of file
            if end_idx == len(words):
                response_words.append("EOF")
                
            # Send response
            response = ','.join(response_words) + '\n'
            conn.send(response.encode())
            
        except ValueError:
            conn.send("Invalid parameters. Use integers: p,k\\n".encode())
        except Exception as e:
            print(f"Error processing request: {e}")
        finally:
            conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        # Start worker thread
        worker = threading.Thread(target=process_requests, daemon=True)
        worker.start()
        
        # Accept connections
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()