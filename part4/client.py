import socket
import time
import argparse
import json
import os

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

SERVER_IP = config['server_ip']
PORT = config['port']
K = config['k']

def download_file(batch_size, client_id):
    words = []
    offset = 0
    start_time = time.time()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    while True:
        connections = []
        responses = []
        
        # Create multiple connections for greedy client
        for i in range(batch_size):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((SERVER_IP, PORT))
                connections.append(s)
            except Exception as e:
                print(f"Connection error: {e}")
                for conn in connections:
                    conn.close()
                return None
        
        # Send requests
        for i, conn in enumerate(connections):
            request = f"{offset + i * K},{K}\n"
            try:
                conn.send(request.encode())
            except Exception as e:
                print(f"Send error: {e}")
                for c in connections:
                    c.close()
                return None
        
        # Receive responses
        eof_received = False
        for i, conn in enumerate(connections):
            try:
                response = conn.recv(1024).decode().strip()
                responses.append(response)
                
                if response == "EOF" or "EOF" in response.split(','):
                    eof_received = True
            except Exception as e:
                print(f"Receive error: {e}")
                responses.append("")
            finally:
                conn.close()
        
        # Process responses
        for response in responses:
            if response == "EOF":
                continue
                
            parts = response.split(',')
            for word in parts:
                if word == "EOF":
                    eof_received = True
                    break
                words.append(word)
            
            if eof_received:
                break
        
        if eof_received:
            break
            
        offset += batch_size * K
    
    end_time = time.time()
    completion_time = end_time - start_time
    
    # Count word frequencies
    word_count = {}
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1
    
    # Print word frequencies
    for word, count in word_count.items():
        print(f"{word}, {count}")
    
    # Save completion time to log file
    with open(f"logs/{client_id}.log", "w") as f:
        f.write(f"{completion_time}")
    
    return completion_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1, help="Number of parallel requests")
    parser.add_argument("--client-id", type=str, default="client", help="Client identifier")
    args = parser.parse_args()
    
    download_file(args.batch_size, args.client_id)