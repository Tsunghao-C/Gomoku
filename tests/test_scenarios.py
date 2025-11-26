"""
Test scenarios for Gomoku AI - specific tactical situations to verify AI competence.

These scenarios test if the AI can:
1. Block immediate threats
2. Recognize winning opportunities  
3. Handle complex tactical positions
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srcs.GomokuLogic import GomokuLogic
from srcs.GomokuAI import GomokuAI


def setup_position(logic, moves):
    """
    Setup a board position from a list of moves.
    
    Args:
        logic: GomokuLogic instance
        moves: List of (row, col, player) tuples
    
    Returns:
        tuple: (board, captures, zobrist_hash)
    """
    board = [0] * (logic.BOARD_SIZE * logic.BOARD_SIZE)
    captures = {1: 0, 2: 0}
    zobrist_hash = logic.compute_initial_hash()
    
    for r, c, player in moves:
        captured_pieces, zobrist_hash = logic.make_move(r, c, player, board, zobrist_hash)
        captures[player] += len(captured_pieces)
    
    return board, captures, zobrist_hash


def test_block_open_three():
    """Test AI blocks an open three-in-a-row."""
    print("\n" + "="*60)
    print("TEST 1: Block Open Three")
    print("="*60)
    
    with open('config.json') as f:
        config = json.load(f)
    
    logic = GomokuLogic(config)
    ai = GomokuAI(config)
    
    # Black has 3 in diagonal
    moves = [
        (9, 9, 1),   # Black
        (9, 8, 2),   # White
        (8, 8, 1),   # Black
        (8, 9, 2),   # White
        (7, 7, 1),   # Black - 3 in diagonal!
    ]
    
    board, captures, zobrist_hash = setup_position(logic, moves)
    
    print("Black has (9,9), (8,8), (7,7) - open three!")
    print("White MUST block at (6,6) or (10,10)")
    
    move, time_taken = ai.get_best_move(
        board, captures, zobrist_hash, 2, 5, logic, len(moves)
    )
    
    print(f"\nAI chose: {move}")
    
    if move in [(6, 6), (10, 10)]:
        print("✅ PASS: AI correctly blocked the threat!")
        return True
    else:
        print("❌ FAIL: AI did not block!")
        return False


def test_recognize_winning_move():
    """Test AI recognizes when it has a winning four-in-a-row."""
    print("\n" + "="*60)
    print("TEST 2: Recognize Winning Move")
    print("="*60)
    
    with open('config.json') as f:
        config = json.load(f)
    
    logic = GomokuLogic(config)
    ai = GomokuAI(config)
    
    # White has 4 in a row, can complete to 5
    moves = [
        (9, 9, 1),
        (10, 9, 2),
        (9, 8, 1),
        (10, 10, 2),
        (9, 7, 1),
        (10, 11, 2),
        (8, 8, 1),
        (10, 12, 2),  # 4 in a row!
    ]
    
    board, captures, zobrist_hash = setup_position(logic, moves)
    
    print("White has (10,9), (10,10), (10,11), (10,12) - four in a row!")
    print("White should complete at (10,8) or (10,13)")
    
    move, time_taken = ai.get_best_move(
        board, captures, zobrist_hash, 2, 5, logic, len(moves)
    )
    
    print(f"\nAI chose: {move}")
    
    if move in [(10, 8), (10, 13)]:
        print("✅ PASS: AI found the winning move!")
        return True
    else:
        print("❌ FAIL: AI missed the win!")
        return False


def test_block_open_four():
    """Test AI blocks an open four (highest priority)."""
    print("\n" + "="*60)
    print("TEST 3: Block Open Four")
    print("="*60)
    
    with open('config.json') as f:
        config = json.load(f)
    
    logic = GomokuLogic(config)
    ai = GomokuAI(config)
    
    # Black has 4 in a row with both ends open
    moves = [
        (9, 9, 1),
        (8, 9, 2),
        (9, 10, 1),
        (8, 10, 2),
        (9, 11, 1),
        (8, 11, 2),
        (9, 12, 1),  # 4 in a row: (9,9), (9,10), (9,11), (9,12)
    ]
    
    board, captures, zobrist_hash = setup_position(logic, moves)
    
    print("Black has (9,9), (9,10), (9,11), (9,12) - open four!")
    print("White MUST block at (9,8) or (9,13) - only two moves possible!")
    
    move, time_taken = ai.get_best_move(
        board, captures, zobrist_hash, 2, 5, logic, len(moves)
    )
    
    print(f"\nAI chose: {move}")
    
    if move in [(9, 8), (9, 13)]:
        print("✅ PASS: AI blocked the open four!")
        return True
    else:
        print("❌ FAIL: AI did not block - game over!")
        return False


def run_all_tests():
    """Run all tactical tests."""
    print("\n" + "="*60)
    print("GOMOKU AI TACTICAL TESTS")
    print("="*60)
    
    tests = [
        ("Block Open Three", test_block_open_three),
        ("Recognize Winning Move", test_recognize_winning_move),
        ("Block Open Four", test_block_open_four),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

