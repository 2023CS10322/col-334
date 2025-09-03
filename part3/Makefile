# Part 3 Makefile

PYTHON := python3
SERVER := server.py
CLIENT := client.py
RUNNER := runner.py
PLOTTER := plot_results.py
RESULTS := results_p3.csv
PLOT := p3_plot.png

.PHONY: all clean run-fcfs plot

all: run-fcfs

# Run a single FCFS experiment with parameters from config.json
run-fcfs:
	sudo $(PYTHON) $(RUNNER) --mode fcfs

# Run experiments for varying c and plot JFI
plot:
	@rm -f $(RESULTS)
	sudo $(PYTHON) $(RUNNER) --mode fcfs
	$(PYTHON) $(PLOTTER)

# Remove generated results/plots
clean:
	rm -f $(RESULTS) $(PLOT)
