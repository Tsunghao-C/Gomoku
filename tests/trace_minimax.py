"""
Trace minimax decision-making for capture vs 5-in-a-row.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srcs.GomokuLogic import GomokuLogic
from srcs.GomokuAI import GomokuAI


def setup_board(logic, pieces, captures_dict):
    """Setup board directly."""
    board = [0] * (logic.BOARD_SIZE * logic.BOARD_SIZE)
    zobrist_hash = logic.compute_initial_hash()

    for (r, c), player in pieces.items():
        idx = r * logic.BOARD_SIZE + c
        board[idx] = player
        zobrist_hash ^= logic.zobrist_table[idx][player]

    return board, captures_dict.copy(), zobrist_hash


def test_trace():
    """Trace minimax for capture vs 5-in-a-row."""
    with open('config.json') as f:
        config = json.load(f)

    # Enable verbose
    config['ai_settings']['debug']['verbose'] = True

    logic = GomokuLogic(config)
    ai = GomokuAI(config)

    pieces = {
        (9, 8): 1, (9, 9): 1,
        (9, 7): 2, (9, 11): 2,
        (10, 7): 2, (10, 8): 2, (10, 9): 2, (10, 10): 2,
        (8, 8): 1, (11, 11): 1,
    }

    captures = {1: 0, 2: 8}
    board, captures, zobrist_hash = setup_board(logic, pieces, captures)

    print("=" * 80)
    print("SCENARIO: White has 8 captures")
    print("  Option 1: Capture at (9,10) -> terminal win")
    print("  Option 2: 5-in-a-row at (10,11) or (10,6) -> pending win")
    print("=" * 80)
    print()

    # Extend time limit to see more depth
    config['algorithm_settings']['time_limit'] = 10.0
    ai2 = GomokuAI(config)

    move, time_taken = ai2.get_best_move(board, captures, zobrist_hash, 2, 5, logic, 10)

    print()
    print("=" * 80)
    print(f"AI chose: {move}")
    print("=" * 80)


if __name__ == "__main__":
    test_trace()

