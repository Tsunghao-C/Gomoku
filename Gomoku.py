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

from srcs.GomokuGame import GomokuGame


def main():
    """Entry point for the Gomoku game."""
    game = GomokuGame()
    game.run_game()


if __name__ == "__main__":
    main()
