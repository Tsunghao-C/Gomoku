# Makefile for building the project

SHELL := /bin/bash
PROJECT_ROOT := $(shell pwd)
PYTHON_VERSION := 3.12

.PHONY: all clean install help re

all: help

# Help target
help:
	@echo "Makefile for building the project"
	@echo "Available targets:"
	@echo "  install - Install the project dependencies"
	@echo "  start   - Start Gomoku game"
	@echo "  clean   - Clean up build artifacts"
	@echo "  fclean  - Clean everything"
	@echo "  re      - remove and recomplie"

# Install project dependencies
install:
	@echo "Installing dependencies for all projects with pyproject.toml..."
	@find . -type f -name pyproject.toml | while read file; do \
		dir=$$(dirname $$file); \
		echo "🔧 Processing: $$dir"; \
		cd $$dir && \
		pyenv local $(PYTHON_VERSION) && \
		uv sync; \
		cd - > /dev/null; \
	done
	@echo "Dependencies installed successfully."

start:
	@export PYTHONPATH=$(PROJECT_ROOT)
	@echo "Starting Gomoku game..."
	@uv run Gomoku.py

clean:
	-rm -rf models
	-rm -rf trainings
	-rm -rf results
	-rm predictions_*.csv

fclean:
	clean

re:
	fclean
	start

%:
	@echo "No target specified. Use 'make help' to see available targets."