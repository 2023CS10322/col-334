.PHONY: build run run-fcfs plot clean

build:
	@echo "No compilation needed for Python files"

run: build
	python3 runner.py --single

run-fcfs: build
	python3 runner.py --single

plot: build
	python3 runner.py

clean:
	rm -rf logs/*.log
	rm -f *.png results.csv