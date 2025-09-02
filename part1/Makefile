CXX = g++
CXXFLAGS = -std=c++11 -Wall

SERVER = server
CLIENT = client

SRC_SERVER = server.cpp
SRC_CLIENT = client.cpp

PY_RUNNER = run_experiments.py
PY_PLOT   = plot_results.py

all: build

# Build server and client
build: $(SERVER) $(CLIENT)

$(SERVER): $(SRC_SERVER)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(CLIENT): $(SRC_CLIENT)
	$(CXX) $(CXXFLAGS) -o $@ $^

# Run one iteration (server in background, client connects once)
run: build
	./server & \
	SRV_PID=$$!; \
	sleep 1; \
	./client; \
	kill $$SRV_PID

# Run experiments for varying k and generate plot
plot: build
	python3 $(PY_RUNNER)
	python3 $(PY_PLOT)

# Clean binaries and outputs
clean:
	rm -f $(SERVER) $(CLIENT) results.csv p1_plot.png
