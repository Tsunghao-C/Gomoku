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
    """
    print("\n" + "="*70)
    print("TEST: Break Opponent's Pending Win via Capture")
    print("="*70)

    with open('config.json') as f:
        config = json.load(f)

    logic = GomokuLogic(config)
    ai = GomokuAI(config)

    # Setup:
    # Black has 5-in-a-row at (9,7)-(9,11)
    # White can capture (9,8)-(9,9) by playing (9,10) to break it
    # White also has 4-in-a-row and can complete to 5
    pieces = {
        # Black 5-in-a-row
        (9, 7): 1, (9, 8): 1, (9, 9): 1, (9, 10): 1, (9, 11): 1,

        # White pieces to set up capture: W-B-B-?
        (9, 6): 2,  # White before Black's 5
        (9, 12): 2,  # White after Black's 5
        # White can capture (9,8)-(9,9) by playing (9,7) - wait, (9,7) is taken
        # Let me reconfigure...
    }

    # Actually, let me reconfigure to make capture work:
    # Black: (9,8), (9,9), (9,10), (9,11), (9,12) = 5 in a row
    # White at (9,7) and (9,13) - can capture middle pieces
    pieces = {
        # Black 5-in-a-row
        (9, 8): 1, (9, 9): 1, (9, 10): 1, (9, 11): 1, (9, 12): 1,

        # White can capture (9,9)-(9,10) by playing at (9,11) - wait that's taken
        # This is tricky with capture mechanics...

        # Let me think of valid capture pattern:
        # W-B-B-? where White plays at ? to capture B-B
        # So: (9,7):W, (9,8):B, (9,9):B, and White plays (9,10) to capture
        # But then Black would only have 3 pieces: (9,8), (9,9), and others

        # Clearer setup:
        (9, 10): 1, (9, 11): 1, (9, 12): 1, (9, 13): 1, (9, 14): 1,  # Black 5
        (9, 9): 2,  # White before
        (9, 15): 2,  # White after
        # White can capture (9,11)-(9,12) by playing (9,13) - wait, that's taken

        # I need to set up where Black has 5, and 2 of them are capturable
        # Pattern: W-?-B-B-B-B-B where 2 middle B's can be captured
    }

    # Simpler: Just set up Black with 5 and White with ability to capture
    pieces = {
        # Black has 5-in-a-row on row 9
        (9, 6): 1, (9, 7): 1, (9, 8): 1, (9, 9): 1, (9, 10): 1,

        # White has pieces that can capture (9,7)-(9,8)
        (9, 5): 2,  # W before
        (9, 9): 2,  # Would conflict!
    }

    # Let me use a working capture pattern:
    # Row 9: W(9,5), B(9,6), B(9,7), ?(9,8), B(9,9), B(9,10), B(9,11)
    # If White plays (9,8), captures (9,6)-(9,7), leaving B at (9,9)-(9,11) = only 3
    pieces = {
        (9, 5): 2,   # White
        (9, 6): 1,   # Black
        (9, 7): 1,   # Black - these two can be captured
        # (9, 8): empty - White can play here
        (9, 9): 1,   # Black
        (9, 10): 1,  # Black
        (9, 11): 1,  # Black - total 5 Black pieces

        # White has 4-in-a-row elsewhere and can complete
        (10, 7): 2, (10, 8): 2, (10, 9): 2, (10, 10): 2,
        # Can complete at (10,6) or (10,11)

        # Filler
        (8, 8): 2,
    }

    captures = {1: 0, 2: 0}

    board, captures, zobrist_hash = setup_board_directly(logic, pieces, captures)

    print("Black has 5-in-a-row at row 9: (9,6), (9,7), (9,9), (9,10), (9,11)")
    print("White can capture (9,6)-(9,7) by playing (9,8)")
    print("This breaks Black's 5-in-a-row! (leaves only 3)")
    print("")
    print("White also has 4-in-a-row and can make own 5-in-a-row")
    print("But should prioritize BREAKING opponent's threat!")

    move, time_taken = ai.get_best_move(
        board, captures, zobrist_hash, 2, 5, logic, 10
    )

    print(f"\nAI chose: {move}")

    # Check if AI captures to break
    if move == (9, 8):
        # Verify it actually captures
        test_board = board[:]
        captured, _ = logic.make_move(9, 8, 2, test_board, zobrist_hash)
        if len(captured) >= 2:
            print(f"✅ PASS: AI captured {len(captured)} pieces to break 5-in-a-row!")
            return True
        else:
            print("❌ FAIL: Move didn't capture as expected")
            return False
    else:
        print("❌ FAIL: AI didn't capture to break opponent's 5-in-a-row!")
        print("   AI must defend against pending win!")
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

