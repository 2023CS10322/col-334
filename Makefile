# Makefile for Part1: builds server and client; run launches server in background and runs client.
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall

SERVER = server
CLIENT = client
CONFIG = config.json

.PHONY: all build run clean plot

all: build

build: $(SERVER) $(CLIENT)

$(SERVER): server.cpp
	$(CXX) $(CXXFLAGS) server.cpp -o $(SERVER)

$(CLIENT): client.cpp
	$(CXX) $(CXXFLAGS) client.cpp -o $(CLIENT)

# Run a single server-client iteration:
# starts server in background (writes PID to server.pid), sleeps 0.8s,
# runs client, then kills the server.
run: build
	@echo "Starting server (background)..."
	@./$(SERVER) $(CONFIG) & echo $$! > server.pid
	@sleep 0.8
	@echo "Running client..."
	@./$(CLIENT) $(CONFIG)
	@echo "Stopping server..."
	@kill `cat server.pid` 2>/dev/null || true
	@rm -f server.pid

# If you have runner scripts for experiments/plotting, call them here.
# We assume you uploaded run_experiments.py and plot_results.py. Adjust as needed.
plot:
	@echo "Running experiments and plotting (requires python3 and run_experiments.py / plot_results.py)..."
	@if [ -f run_experiments.py ] && [ -f plot_results.py ]; then \
		python3 run_experiments.py $(CONFIG); \
		python3 plot_results.py; \
	else \
		echo "run_experiments.py or plot_results.py not found in current directory."; \
	fi

clean:
	@rm -f $(SERVER) $(CLIENT) server.pid
