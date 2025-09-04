# ===========================
# Part 3 Makefile — FCFS
# - make run-fcfs : run one FCFS experiment using config.json
# - make plot     : sweep c and produce p3_plot.png
# ===========================

PY        ?= python3
SERVER    ?= server.py
CLIENT    ?= client.py
TOPO      ?= topology.py
CONFIG    ?= config.json
RESULTS   ?= results_part3
PLOT      ?= p3_plot.png
LOGDIR    ?= logs_part3
MN        ?= 0
C_START   ?= 1
C_END     ?= 10

.PHONY: run-fcfs run-fcfs-local run-fcfs-mn plot clean veryclean help

help:
	@echo "Targets:"
	@echo "  make run-fcfs        # one FCFS experiment (uses config.json)"
	@echo "  make plot            # sweeps c=C_START..C_END, generates $(PLOT)"
	@echo "Options:"
	@echo "  MN=1                 # use Mininet via topology.py"
	@echo "  C_START=1 C_END=10   # range for c sweep"

run-fcfs: $(RESULTS) $(LOGDIR)
ifeq ($(MN),1)
	@$(MAKE) --no-print-directory run-fcfs-mn
else
	@$(MAKE) --no-print-directory run-fcfs-local
endif

$(RESULTS) $(LOGDIR):
	@mkdir -p $@

# -------- Local mode ----------
run-fcfs-local:
	@echo "[FCFS][LOCAL] Starting server..."
	@$(PY) $(SERVER) > $(LOGDIR)/server.out 2>&1 & echo $$! > $(LOGDIR)/server.pid
	@sleep 0.5
	@echo "[FCFS][LOCAL] Launching clients..."
	@$(PY) runner_part3.py > $(RESULTS)/last_times.txt
	@echo "[FCFS][LOCAL] Shutting down server..."
	-@kill -TERM `cat $(LOGDIR)/server.pid` >/dev/null 2>&1 || true
	-@rm -f $(LOGDIR)/server.pid
	@echo "[FCFS][LOCAL] Results in $(RESULTS)/last_times.txt"

# -------- Mininet mode --------
run-fcfs-mn:
	@if [ ! -f "$(TOPO)" ]; then \
	  echo "ERROR: $(TOPO) not found. Provide a Mininet topology runner or use MN=0."; \
	  exit 1; \
	fi
	@echo "[FCFS][MN] Running via $(TOPO)..."
	@sudo $(PY) $(TOPO)

# -------- Sweep & Plot --------
plot: $(RESULTS)
	@echo "[PLOT] Sweeping c=$(C_START)..$(C_END)"
	@rm -f $(RESULTS)/results.csv
	@for c in `seq $(C_START) $(C_END)`; do \
	  echo "  - c=$$c"; \
	  sed -i "s/\"c\": *[0-9][0-9]*/\"c\": $$c/" $(CONFIG); \
	  $(MAKE) --no-print-directory run-fcfs; \
	done
	@echo "[PLOT] Generating $(PLOT)"
	@$(PY) plot_results_part3.py

clean:
	@rm -rf $(LOGDIR)

veryclean: clean
	@rm -rf $(RESULTS) $(PLOT)
