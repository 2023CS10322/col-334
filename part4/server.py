import socket
import threading
import json
from collections import deque, defaultdict

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

HOST = config['server_ip']
PORT = config['port']

# Read words from file
with open('words.txt', 'r') as f:
    words = f.read().strip().split(',')

# Thread-safe client queues for round-robin scheduling
client_queues = defaultdict(deque)
active_clients = set()
queue_lock = threading.Lock()
condition = threading.Condition(queue_lock)

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    client_id = addr[0]  # Use client IP as identifier
    
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            return
        
        # Add request to the client's queue
        with condition:
            client_queues[client_id].append((conn, data))
            active_clients.add(client_id)
            condition.notify()
            
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        # Note: Connection will be closed by the worker thread
        pass

def process_requests():
    # For round-robin, we'll keep track of which clients we've processed
    current_client_idx = 0
    client_list = []
    
    while True:
        with condition:
            # Wait until there's at least one request to process
            while not active_clients:
                condition.wait()
            
            # Update the client list if it changed
            if set(client_list) != active_clients:
                client_list = list(active_clients)
                
            # No clients left to process
            if not client_list:
                continue
                
            # Round-robin: Move to next client with requests
            attempts = 0
            while attempts < len(client_list):
                current_client_idx = (current_client_idx) % len(client_list)
                client_id = client_list[current_client_idx]
                
                if client_queues[client_id]:
                    # Process one request from this client
                    conn, data = client_queues[client_id].popleft()
                    
                    # If this client has no more requests, remove from active list
                    if not client_queues[client_id]:
                        active_clients.remove(client_id)
                        
                    # Move to the next client for next time
                    current_client_idx = (current_client_idx + 1) % len(client_list)
                    break
                else:
                    # This client has no requests, try next client
                    current_client_idx = (current_client_idx + 1) % len(client_list)
                    attempts += 1
            
            # If we've checked all clients and found no requests, wait
            if attempts == len(client_list):
                continue
        
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