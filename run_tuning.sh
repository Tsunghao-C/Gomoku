#!/bin/bash

# Gomoku AI Configuration Tuning Runner
# Wrapper script for easy execution of tuning utilities

cd "$(dirname "$0")"

case "$1" in
  quick)
    echo "Running quick test..."
    uv run python tests/quick_test.py
    ;;
  
  test)
    if [ -z "$2" ] || [ -z "$3" ]; then
      echo "Usage: ./run_tuning.sh test PARAM_PATH VALUE [NUM_GAMES]"
      echo "Example: ./run_tuning.sh test 'heuristic_settings.scores.open_four' 1200000 4"
      exit 1
    fi
    echo "Testing parameter change..."
    uv run python tests/quick_test.py test "$2" "$3" "${4:-4}"
    ;;
  
  sweep)
    echo "Running parameter sweep..."
    uv run python tests/parameter_sweep.py "${2:-capture}"
    ;;
  
  tournament)
    echo "Running tournament..."
    uv run python tests/config_tuner.py
    ;;
  
  compare)
    if [ -z "$2" ] || [ -z "$3" ]; then
      echo "Usage: ./run_tuning.sh compare CONFIG1 CONFIG2 [NUM_GAMES]"
      exit 1
    fi
    echo "Comparing configurations..."
    uv run python tests/quick_test.py compare "$2" "$3" "${4:-6}"
    ;;
  
  *)
    echo "Gomoku AI Configuration Tuning"
    echo ""
    echo "Usage: ./run_tuning.sh COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  quick                          Run quick test (3 games)"
    echo "  test PARAM VALUE [GAMES]       Test single parameter change"
    echo "  sweep [capture|patterns|binary] Run parameter sweep"
    echo "  tournament                     Run full tournament"
    echo "  compare CONFIG1 CONFIG2 [GAMES] Compare two configs"
    echo ""
    echo "Examples:"
    echo "  ./run_tuning.sh quick"
    echo "  ./run_tuning.sh test 'heuristic_settings.scores.open_four' 1200000 4"
    echo "  ./run_tuning.sh sweep capture"
    echo "  ./run_tuning.sh tournament"
    echo ""
    ;;
esac

