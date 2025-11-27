"""
Ablation Study: Test impact of each optimization technique.

This script systematically tests the impact of:
1. Null Move Pruning
2. Late Move Reductions (LMR)
3. Adaptive Starting Depth

For each feature, we measure:
- Average search depth
- Max search depth
- Average time per move
- Game quality (does it make good moves?)
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srcs.GomokuGameHeadless import GomokuGameHeadless


def run_test_games(config, num_games=3, description=""):
    """Run test games with given configuration."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")

    results = []
    for i in range(num_games):
        print(f"  Game {i+1}/{num_games}...", end=" ", flush=True)
        game = GomokuGameHeadless(config)
        start = time.time()
        result = game.play_game(verbose=False, max_moves=50)
        elapsed = time.time() - start
        print(f"Done ({elapsed:.1f}s, depth: {result['avg_depth']:.1f})")
        results.append(result)

    # Aggregate statistics
    avg_depth = sum(r['avg_depth'] for r in results) / len(results)
    max_depth = max(r['max_depth'] for r in results)
    avg_time = sum(r['avg_time'] for r in results) / len(results)
    avg_moves = sum(r['total_moves'] for r in results) / len(results)

    print("\nResults:")
    print(f"  Average depth: {avg_depth:.2f}")
    print(f"  Maximum depth: {max_depth}")
    print(f"  Average time/move: {avg_time:.2f}s")
    print(f"  Average game length: {avg_moves:.1f} moves")

    return {
        'description': description,
        'avg_depth': avg_depth,
        'max_depth': max_depth,
        'avg_time': avg_time,
        'avg_moves': avg_moves,
        'games': num_games
    }


def test_null_move_pruning():
    """Test impact of Null Move Pruning."""
    print("\n" + "="*60)
    print("ABLATION TEST 1: NULL MOVE PRUNING")
    print("="*60)

    # Load base config
    with open('config.json') as f:
        config = json.load(f)

    # Test WITH null move pruning
    config['algorithm_settings']['enable_null_move_pruning'] = True
    results_with = run_test_games(config, num_games=3, description="WITH Null Move Pruning")

    # Test WITHOUT null move pruning
    config['algorithm_settings']['enable_null_move_pruning'] = False
    results_without = run_test_games(config, num_games=3, description="WITHOUT Null Move Pruning")

    # Compare
    print(f"\n{'='*60}")
    print("COMPARISON: Null Move Pruning")
    print(f"{'='*60}")
    print(f"{'Metric':<25} {'WITH':<15} {'WITHOUT':<15} {'Difference':<15}")
    print(f"{'-'*60}")

    depth_diff = results_with['avg_depth'] - results_without['avg_depth']
    time_diff = results_with['avg_time'] - results_without['avg_time']

    print(f"{'Average Depth':<25} {results_with['avg_depth']:<15.2f} {results_without['avg_depth']:<15.2f} {depth_diff:+.2f}")
    print(f"{'Max Depth':<25} {results_with['max_depth']:<15} {results_without['max_depth']:<15} {results_with['max_depth'] - results_without['max_depth']:+d}")
    print(f"{'Average Time':<25} {results_with['avg_time']:<15.2f} {results_without['avg_time']:<15.2f} {time_diff:+.2f}s")

    # Verdict
    print(f"\n{'='*60}")
    if abs(depth_diff) < 0.3 and abs(time_diff) < 0.1:
        print("⚠️  VERDICT: Null Move Pruning has MINIMAL IMPACT")
        print("    Recommendation: REMOVE to simplify code")
    elif depth_diff > 0.5 or time_diff < -0.1:
        print("✅ VERDICT: Null Move Pruning is HELPFUL")
        print("    Recommendation: KEEP")
    else:
        print("⚖️  VERDICT: Null Move Pruning has MARGINAL IMPACT")
        print("    Recommendation: Remove if you prefer simpler code")

    return results_with, results_without


def test_late_move_reductions():
    """Test impact of Late Move Reductions."""
    print("\n" + "="*60)
    print("ABLATION TEST 2: LATE MOVE REDUCTIONS (LMR)")
    print("="*60)

    # Load base config
    with open('config.json') as f:
        config = json.load(f)

    # Test WITH LMR
    config['algorithm_settings']['enable_late_move_reductions'] = True
    results_with = run_test_games(config, num_games=3, description="WITH Late Move Reductions")

    # Test WITHOUT LMR
    config['algorithm_settings']['enable_late_move_reductions'] = False
    results_without = run_test_games(config, num_games=3, description="WITHOUT Late Move Reductions")

    # Compare
    print(f"\n{'='*60}")
    print("COMPARISON: Late Move Reductions")
    print(f"{'='*60}")
    print(f"{'Metric':<25} {'WITH':<15} {'WITHOUT':<15} {'Difference':<15}")
    print(f"{'-'*60}")

    depth_diff = results_with['avg_depth'] - results_without['avg_depth']
    time_diff = results_with['avg_time'] - results_without['avg_time']

    print(f"{'Average Depth':<25} {results_with['avg_depth']:<15.2f} {results_without['avg_depth']:<15.2f} {depth_diff:+.2f}")
    print(f"{'Max Depth':<25} {results_with['max_depth']:<15} {results_without['max_depth']:<15} {results_with['max_depth'] - results_without['max_depth']:+d}")
    print(f"{'Average Time':<25} {results_with['avg_time']:<15.2f} {results_without['avg_time']:<15.2f} {time_diff:+.2f}s")

    # Verdict
    print(f"\n{'='*60}")
    if abs(depth_diff) < 0.3 and abs(time_diff) < 0.1:
        print("⚠️  VERDICT: LMR has MINIMAL IMPACT")
        print("    Recommendation: REMOVE to simplify code")
    elif depth_diff > 0.5 or time_diff < -0.1:
        print("✅ VERDICT: LMR is HELPFUL")
        print("    Recommendation: KEEP")
    else:
        print("⚖️  VERDICT: LMR has MARGINAL IMPACT")
        print("    Recommendation: Remove if you prefer simpler code")

    return results_with, results_without


def test_adaptive_starting_depth():
    """Test impact of Adaptive Starting Depth."""
    print("\n" + "="*60)
    print("ABLATION TEST 3: ADAPTIVE STARTING DEPTH")
    print("="*60)

    # Load base config
    with open('config.json') as f:
        config = json.load(f)

    # Test WITH adaptive starting depth
    config['algorithm_settings']['adaptive_starting_depth']['enable'] = True
    results_with = run_test_games(config, num_games=3, description="WITH Adaptive Starting Depth")

    # Test WITHOUT (always start from depth 1)
    config['algorithm_settings']['adaptive_starting_depth']['enable'] = False
    results_without = run_test_games(config, num_games=3, description="WITHOUT Adaptive Starting (always depth 1)")

    # Compare
    print(f"\n{'='*60}")
    print("COMPARISON: Adaptive Starting Depth")
    print(f"{'='*60}")
    print(f"{'Metric':<25} {'WITH':<15} {'WITHOUT':<15} {'Difference':<15}")
    print(f"{'-'*60}")

    depth_diff = results_with['avg_depth'] - results_without['avg_depth']
    time_diff = results_with['avg_time'] - results_without['avg_time']

    print(f"{'Average Depth':<25} {results_with['avg_depth']:<15.2f} {results_without['avg_depth']:<15.2f} {depth_diff:+.2f}")
    print(f"{'Max Depth':<25} {results_with['max_depth']:<15} {results_without['max_depth']:<15} {results_with['max_depth'] - results_without['max_depth']:+d}")
    print(f"{'Average Time':<25} {results_with['avg_time']:<15.2f} {results_without['avg_time']:<15.2f} {time_diff:+.2f}s")

    # Verdict
    print(f"\n{'='*60}")
    print("NOTE: Adaptive starting depth skips early iterations of iterative deepening.")
    print("      This saves time early game but may hurt transposition table population.")
    print()
    if abs(depth_diff) < 0.3 and time_diff < -0.1:
        print("✅ VERDICT: Adaptive Starting Depth SAVES TIME without hurting depth")
        print("    Recommendation: KEEP")
    elif depth_diff < -0.5:
        print("⚠️  VERDICT: Adaptive Starting Depth HURTS depth")
        print("    Recommendation: REMOVE - consistent depth 1 start is better")
    else:
        print("⚖️  VERDICT: Adaptive Starting Depth has MIXED IMPACT")
        print("    Recommendation: Remove for consistency and simplicity")

    return results_with, results_without


def run_all_ablation_tests():
    """Run all ablation tests and generate final report."""
    print("\n" + "="*60)
    print("ABLATION STUDY: OPTIMIZATION TECHNIQUES")
    print("="*60)
    print("Testing impact of each optimization on performance.")
    print("This will take 5-10 minutes...")
    print()

    all_start = time.time()

    # Run tests
    test1_with, test1_without = test_null_move_pruning()
    test2_with, test2_without = test_late_move_reductions()
    test3_with, test3_without = test_adaptive_starting_depth()

    total_time = time.time() - all_start

    # Final Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY & RECOMMENDATIONS")
    print("="*60)

    print("\n1. NULL MOVE PRUNING:")
    depth_impact_1 = test1_with['avg_depth'] - test1_without['avg_depth']
    time_impact_1 = test1_with['avg_time'] - test1_without['avg_time']
    if abs(depth_impact_1) < 0.3 and abs(time_impact_1) < 0.1:
        print("   ❌ REMOVE - Minimal impact, adds complexity")
    else:
        print(f"   ✅ KEEP - Depth impact: {depth_impact_1:+.2f}, Time impact: {time_impact_1:+.2f}s")

    print("\n2. LATE MOVE REDUCTIONS:")
    depth_impact_2 = test2_with['avg_depth'] - test2_without['avg_depth']
    time_impact_2 = test2_with['avg_time'] - test2_without['avg_time']
    if abs(depth_impact_2) < 0.3 and abs(time_impact_2) < 0.1:
        print("   ❌ REMOVE - Minimal impact, adds complexity")
    else:
        print(f"   ✅ KEEP - Depth impact: {depth_impact_2:+.2f}, Time impact: {time_impact_2:+.2f}s")

    print("\n3. ADAPTIVE STARTING DEPTH:")
    depth_impact_3 = test3_with['avg_depth'] - test3_without['avg_depth']
    time_impact_3 = test3_with['avg_time'] - test3_without['avg_time']
    if depth_impact_3 < -0.3:
        print("   ❌ REMOVE - Hurts search depth")
    elif time_impact_3 < -0.1 and depth_impact_3 > -0.3:
        print(f"   ✅ KEEP - Saves time: {-time_impact_3:.2f}s, minimal depth loss")
    else:
        print("   ⚖️  OPTIONAL - Consider removing for consistency")

    print(f"\nTotal test time: {total_time/60:.1f} minutes")
    print("="*60)


if __name__ == "__main__":
    run_all_ablation_tests()

