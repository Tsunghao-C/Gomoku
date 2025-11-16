"""
Gomoku Game - Entry Point

A sophisticated Gomoku (Five in a Row) game with AI opponent.
Includes optimizations: Delta Heuristic, Alpha-Beta Pruning,
Iterative Deepening, Zobrist Hashing, and Transposition Tables.

Controls:
- Click to place a piece (Human player)
- R: Reset game
- M: Toggle game mode (P_VS_AI / P_VS_P)

Features:
- Capture rule: Capture opponent's pairs (P-O-O-P pattern)
- Win by 5 captures or 5-in-a-row
- Pending win state: Opponent must break the line
- Double-three rule: Cannot create two open threes simultaneously
"""

import json
import os
import sys

from srcs.GomokuGame import GomokuGame


def load_config(config_path="config.json"):
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path) as f:
            config = json.load(f)
        print(f"✓ Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{config_path}' not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in configuration file: {e}")
        sys.exit(1)


def main():
    """Entry point for the Gomoku game."""
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    # Load configuration
    config = load_config(config_path)

    # Create and run game with configuration
    game = GomokuGame(config)
    game.run_game()


if __name__ == "__main__":
    main()
