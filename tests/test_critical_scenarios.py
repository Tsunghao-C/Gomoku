"""
Critical test scenarios to verify AI makes optimal decisions in edge cases.
These tests check:
1. Win by capture vs 5-in-a-row preference
2. Breaking opponent's pending win (5-in-a-row) via capture
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srcs.GomokuAI import GomokuAI
from srcs.GomokuLogic import GomokuLogic


def setup_board_directly(logic, pieces_dict, captures_dict):
    """
    Setup board directly by placing pieces.
    
    Args:
        logic: GomokuLogic instance
        pieces_dict: {(r,c): player, ...}
        captures_dict: {player: count}
    
    Returns:
        tuple: (board, captures, zobrist_hash)
    """
    board = [0] * (logic.BOARD_SIZE * logic.BOARD_SIZE)
    zobrist_hash = logic.compute_initial_hash()

    for (r, c), player in pieces_dict.items():
        idx = r * logic.BOARD_SIZE + c
        board[idx] = player
        # Update zobrist
        zobrist_hash ^= logic.zobrist_table[idx][player]

    captures = captures_dict.copy()

    return board, captures, zobrist_hash


def test_win_by_capture_vs_five():
    """
    Test: AI has 8 captures and can either:
    1. Capture 2 more to win immediately (no pending win)
    2. Make 5-in-a-row (pending win, can be broken)
    
    AI should prefer capture win (more certain).
    """
    print("\n" + "="*70)
    print("TEST: Win by Capture vs Five-in-a-Row")
    print("="*70)

    with open('config.json') as f:
        config = json.load(f)

    logic = GomokuLogic(config)
    ai = GomokuAI(config)

    # Setup:
    # White has 8 captures already
    # White can capture Black pair at (9,8)-(9,9) by playing (9,10)
    # OR White can make 5-in-a-row at (10,7)-(10,11) by playing (10,12)
    pieces = {
        # Black pair capturable
        (9, 8): 1, (9, 9): 1,
        (9, 7): 2,  # White on one side
        (9, 11): 2,  # White on other side - capture at (9,10)

        # White 4-in-a-row (can complete to 5)
        (10, 7): 2, (10, 8): 2, (10, 9): 2, (10, 10): 2,
        # Can complete at (10,11) or (10,12)

        # Filler pieces
        (8, 8): 1, (11, 11): 1,
    }

    captures = {1: 0, 2: 8}  # White has 8 captures!

    board, captures, zobrist_hash = setup_board_directly(logic, pieces, captures)

    print("White has 8 captures (needs 10 to win)")
    print("Option 1: Capture at (9,10) → WIN by capture (immediate, certain)")
    print("Option 2: Complete 5-in-a-row at (10,11) → Pending win (can be broken)")
    print("")
    print("AI should choose CAPTURE (more certain win)!")

    move, time_taken = ai.get_best_move(
        board, captures, zobrist_hash, 2, 5, logic, 10
    )

    print(f"\nAI chose: {move}")

    # Check if the chosen move results in a capture win
    test_board = board[:]
    test_captures = captures.copy()
    test_hash = zobrist_hash
    captured_pieces, _ = logic.make_move(move[0], move[1], 2, test_board, test_hash)
    test_captures[2] += len(captured_pieces)
    is_terminal = logic.check_terminal_state(test_board, test_captures, 2, move[0], move[1], 5)

    if is_terminal and test_captures[2] >= 10:
        print(f"✅ PASS: AI correctly chose capture win at {move}!")
        print(f"   Captured {len(captured_pieces)} pieces, total: {test_captures[2]}")
        return True
    elif move in [(10, 11), (10, 12), (10, 6)]:
        print("❌ FAIL: AI chose 5-in-a-row over capture win!")
        print("   Problem: Capture win is more certain (no pending win status)")
        return False
    else:
        print(f"❌ FAIL: AI chose unexpected move: {move}")
        print("   Expected: Any capture win move (e.g., (9,10), (7,7), (7,8))")
        return False


def test_break_opponent_pending_win():
    """
    Test: Opponent has 5-in-a-row (pending win).
    AI can either:
    1. Capture to break the 5-in-a-row
    2. Make own 5-in-a-row
    
    AI should capture to break (survival > offense).
    
    Setup: Black has 5-in-a-row on row 9.
    White can capture two Black pieces that are part of the 5-in-a-row.
    Capture pattern: W-B-B-? where ? is where White plays to capture the two B's.
    """
    print("\n" + "="*70)
    print("TEST: Break Opponent's Pending Win via Capture")
    print("="*70)

    with open('config.json') as f:
        config = json.load(f)

    logic = GomokuLogic(config)
    ai = GomokuAI(config)

    pieces = {
        # Black vertical 5-in-a-row on column 9
        (5, 9): 1, (6, 9): 1, (7, 9): 1, (8, 9): 1, (9, 9): 1,  # (9,9) is also part of capture pattern below

        # White capture pattern on row 9: W-B-B-? where ? is (9,10)
        (9, 7): 2,   # White before
        (9, 8): 1,   # Black (part of capture pair)
        # (9, 9): already defined above as part of vertical 5-in-a-row
        # (9, 10): empty - White can play here to capture (9,8) and (9,9)
        (9, 11): 2,  # White after

        # White also has 4-in-a-row elsewhere and can complete to 5
        (10, 7): 2, (10, 8): 2, (10, 9): 2, (10, 10): 2,
        # Can complete at (10,6) or (10,11)

        # Filler pieces
        (8, 8): 2,
    }

    captures = {1: 0, 2: 0}

    board, captures, zobrist_hash = setup_board_directly(logic, pieces, captures)

    print("Black has 5-in-a-row vertically: (5,9), (6,9), (7,9), (8,9), (9,9)")
    print("White can capture (9,8) and (9,9) by playing (9,10)")
    print("This breaks Black's 5-in-a-row! (removes (9,9) which is part of the line)")
    print("")
    print("White also has 4-in-a-row and can make own 5-in-a-row")
    print("But should prioritize BREAKING opponent's threat!")

    move, time_taken = ai.get_best_move(
        board, captures, zobrist_hash, 2, 5, logic, 10
    )

    print(f"\nAI chose: {move}")

    # Check if AI captures to break the 5-in-a-row
    # The 5-in-a-row is at: (5,9), (6,9), (7,9), (8,9), (9,9)
    five_in_a_row_set = {(5, 9), (6, 9), (7, 9), (8, 9), (9, 9)}

    # Verify the move captures pieces that are part of the 5-in-a-row
    test_board = board[:]
    test_hash = zobrist_hash
    captured, _ = logic.make_move(move[0], move[1], 2, test_board, test_hash)

    if len(captured) >= 2:
        # Check if any captured piece is part of the 5-in-a-row
        captured_set = set(captured)
        breaks_line = bool(captured_set & five_in_a_row_set)

        if breaks_line:
            print(f"✅ PASS: AI captured {len(captured)} pieces to break 5-in-a-row!")
            print(f"   Captured pieces: {captured}")
            print(f"   Pieces in 5-in-a-row that were captured: {captured_set & five_in_a_row_set}")
            return True
        else:
            print(f"❌ FAIL: Move {move} captured {len(captured)} pieces but none are in the 5-in-a-row!")
            print(f"   Captured: {captured}")
            print(f"   5-in-a-row: {five_in_a_row_set}")
            return False
    else:
        print(f"❌ FAIL: Move {move} didn't capture enough pieces (got {len(captured)})")
        print("   AI must capture to break opponent's 5-in-a-row!")
        return False


def run_tests():
    """Run critical scenario tests."""
    print("\n" + "="*70)
    print("CRITICAL SCENARIO TESTS")
    print("="*70)

    tests = [
        ("Win by Capture vs Five", test_win_by_capture_vs_five),
        ("Break Opponent Pending Win", test_break_opponent_pending_win),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    print(f"\nTotal: {passed_count}/{total} passed")
    print("="*70)

    return passed_count == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

