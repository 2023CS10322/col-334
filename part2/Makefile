PY_SERVER = server.py
PY_CLIENT = client.py
CONFIG = config.json

# These will be provided/written similar to part1
PY_RUNNER = run_experiments_part2.py
PY_PLOT   = plot_results_part2.py
TOPO      = world_topocount.py

# Run one experiment (server + num_clients from config.json)
run:
	python3 $(PY_SERVER) & \
	SRV_PID=$$!; \
	sleep 1; \
	for i in `seq 1 $$(jq '.num_clients' $(CONFIG))`; do \
		python3 $(PY_CLIENT) & \
	done; \
	wait; \
	kill $$SRV_PID

# Run experiments varying num_clients and generate plot
plot:
	sudo python3 $(PY_RUNNER)
	python3 $(PY_PLOT)

clean:
	rm -f results_p2.csv p2_plot.png
