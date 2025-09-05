.PHONY: build run run-rr plot clean

build:
	@echo "No compilation needed for Python files"

run: build
	python3 runner.py --single

run-rr: build
	python3 runner.py --round-robin
	python3 runner.py --single

plot: build
	python3 runner.py

clean:
	rm -rf logs __pycache__
	rm -f *.png results.csv