"""
Deep dive into why AI prefers 5-in-a-row over capture win.
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


def test_capture_vs_five():
    """Debug the capture vs 5-in-a-row decision."""
    print("="*80)
    print("DEBUG: Capture Win vs Five-in-a-Row")
    print("="*80)

    with open('config.json') as f:
        config = json.load(f)

    logic = GomokuLogic(config)
    ai = GomokuAI(config)

    pieces = {
        (9, 8): 1, (9, 9): 1,      # Black pair (capturable)
        (9, 7): 2, (9, 11): 2,     # White surrounding
        (10, 7): 2, (10, 8): 2, (10, 9): 2, (10, 10): 2,  # White 4-in-a-row
        (8, 8): 1, (11, 11): 1,    # Filler
    }

    captures = {1: 0, 2: 8}
    board, captures, zobrist_hash = setup_board(logic, pieces, captures)

    print("\nScenario:")
    print("  White has 8 captures (needs 10 to win)")
    print("  Option 1: Play (9,10) -> capture -> 10 pieces -> TERMINAL WIN")
    print("  Option 2: Play (10,6) or (10,11) -> 5-in-a-row -> PENDING WIN")
    print()

    # Test capture move
    print("-" * 80)
    print("Testing CAPTURE move (9,10):")
    print("-" * 80)

    test_board1 = board[:]
    test_captures1 = captures.copy()
    captured, new_hash1 = logic.make_move(9, 10, 2, test_board1, zobrist_hash)
    test_captures1[2] += len(captured)

    print(f"  Captured: {captured} ({len(captured)} pieces)")
    print(f"  White now has: {test_captures1[2]} captures")

    is_terminal1 = logic.check_terminal_state(test_board1, test_captures1, 2, 9, 10, 5)
    print(f"  Is terminal? {is_terminal1}")

    if is_terminal1:
        print(f"  -> Should return win_score = {ai.heuristic.WIN_SCORE:,}")
    else:
        eval1 = ai.heuristic.evaluate_board(test_board1, test_captures1, 2, 5)
        print(f"  -> Heuristic eval: {eval1:,}")

    # Test 5-in-a-row move (10,11)
    print("\n" + "-" * 80)
    print("Testing 5-IN-A-ROW move (10,11):")
    print("-" * 80)

    test_board2 = board[:]
    test_captures2 = captures.copy()
    captured2, new_hash2 = logic.make_move(10, 11, 2, test_board2, zobrist_hash)
    test_captures2[2] += len(captured2)

    print(f"  Captured: {captured2} ({len(captured2)} pieces)")

    is_terminal2 = logic.check_terminal_state(test_board2, test_captures2, 2, 10, 11, 5)
    print(f"  Is terminal? {is_terminal2}")

    if is_terminal2:
        print(f"  -> Should return win_score = {ai.heuristic.WIN_SCORE:,}")
    else:
        eval2 = ai.heuristic.evaluate_board(test_board2, test_captures2, 2, 5)
        print(f"  -> Heuristic eval: {eval2:,}")
        print(f"  -> This is pending_win_score + bonuses")

    # Test 5-in-a-row move (10,6)
    print("\n" + "-" * 80)
    print("Testing 5-IN-A-ROW move (10,6):")
    print("-" * 80)

    test_board3 = board[:]
    test_captures3 = captures.copy()
    captured3, new_hash3 = logic.make_move(10, 6, 2, test_board3, zobrist_hash)
    test_captures3[2] += len(captured3)

    print(f"  Captured: {captured3} ({len(captured3)} pieces)")

    is_terminal3 = logic.check_terminal_state(test_board3, test_captures3, 2, 10, 6, 5)
    print(f"  Is terminal? {is_terminal3}")

    if is_terminal3:
        print(f"  -> Should return win_score = {ai.heuristic.WIN_SCORE:,}")
    else:
        eval3 = ai.heuristic.evaluate_board(test_board3, test_captures3, 2, 5)
        print(f"  -> Heuristic eval: {eval3:,}")

    # Now run full minimax
    print("\n" + "=" * 80)
    print("RUNNING MINIMAX (depth=2):")
    print("=" * 80)

    # Manually call minimax for each candidate move
    alpha = float('-inf')
    beta = float('inf')

    moves_to_test = [(9, 10), (10, 11), (10, 6)]

    for move in moves_to_test:
        r, c = move
        test_board = board[:]
        test_captures = captures.copy()

        captured, new_hash = logic.make_move(r, c, 2, test_board, zobrist_hash)
        test_captures[2] += len(captured)

        is_terminal = logic.check_terminal_state(test_board, test_captures, 2, r, c, 5)

        if is_terminal:
            score = ai.heuristic.WIN_SCORE
            print(f"\nMove {move}: TERMINAL WIN")
            print(f"  Score: {score:,}")
        else:
            # Call minimax for opponent's response
            score = -ai.algorithm.minimax(
                test_board, test_captures, new_hash, 1, 1, 2,
                -beta, -alpha, logic, ai.heuristic, ai
            )
            print(f"\nMove {move}: PENDING (opponent gets to respond)")
            print(f"  Score after minimax depth=2: {score:,}")

        logic.undo_move(r, c, 2, test_board, captured, test_captures[2] - len(captured),
                       test_captures, new_hash)

    print("\n" + "=" * 80)
    print("ISSUE IDENTIFIED:")
    print("=" * 80)
    print("If capture move shows lower score than 5-in-a-row after minimax,")
    print("the problem is in how terminal wins are propagated through the tree.")
    print("=" * 80)


if __name__ == "__main__":
    test_capture_vs_five()

