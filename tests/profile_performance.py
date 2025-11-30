"""
Performance profiling script to identify bottlenecks in the Gomoku AI.
Uses cProfile to measure where time is spent during AI decision-making.
"""

import cProfile
import io
import json
import pstats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srcs.GomokuGameHeadless import GomokuGameHeadless


def profile_ai_game(num_moves=20):
    """
    Profile an AI vs AI game for a specified number of moves.
    Returns profiling statistics.
    """
    print(f"\n{'='*70}")
    print(f"PROFILING AI PERFORMANCE ({num_moves} moves)")
    print(f"{'='*70}\n")

    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    game = GomokuGameHeadless(config)

    # Create profiler
    profiler = cProfile.Profile()

    # Profile the game
    profiler.enable()

    for move_num in range(num_moves):
        player = 1 if game.current_player == 1 else 2

        # Get AI move
        move, time_taken, depth_reached = game.get_ai_move(player)

        if move is None:
            print(f"Game ended early at move {move_num}")
            break

        # Make the move
        success = game.apply_move(*move, player)
        if not success:
            print(f"Illegal move at move {move_num}")
            break

        game.current_player = 3 - player  # Switch player

        # Check if game is over
        if game.game_over:
            print(f"Game ended with winner at move {move_num}")
            break

    profiler.disable()

    return profiler


def analyze_profile(profiler, top_n=30):
    """
    Analyze profiling results and print key statistics.
    """
    # Create string buffer for stats
    s = io.StringIO()

    # Sort by cumulative time
    ps = pstats.Stats(profiler, stream=s)
    ps.strip_dirs()
    ps.sort_stats('cumulative')

    print(f"\n{'='*70}")
    print("TOP FUNCTIONS BY CUMULATIVE TIME")
    print(f"{'='*70}\n")
    ps.print_stats(top_n)
    print(s.getvalue())

    # Sort by time spent in function itself (not including subcalls)
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.strip_dirs()
    ps.sort_stats('tottime')

    print(f"\n{'='*70}")
    print("TOP FUNCTIONS BY SELF TIME (excluding subcalls)")
    print(f"{'='*70}\n")
    ps.print_stats(top_n)
    print(s.getvalue())

    # Get specific function stats
    print(f"\n{'='*70}")
    print("KEY COMPONENT ANALYSIS")
    print(f"{'='*70}\n")

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.strip_dirs()
    ps.sort_stats('cumulative')

    # Look for specific components
    components = [
        'minimax',
        'get_ordered_moves',
        'score_position',
        'score_lines_at',
        'score_line_numeric',
        '_find_critical_moves',
        'check_winner',
        'is_legal_move',
        'make_move',
        'undo_move',
    ]

    for component in components:
        ps.print_stats(component)

    print(s.getvalue())


def compare_function_costs(profiler):
    """
    Compare relative costs of different components.
    """
    stats = pstats.Stats(profiler)

    # Extract key metrics
    total_time = 0
    component_times = {
        'minimax': 0,
        'move_ordering': 0,
        'evaluation': 0,
        'move_generation': 0,
        'legal_checking': 0,
        'other': 0
    }

    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        total_time += tt

        filename, line, func_name = func

        if 'minimax' in func_name:
            component_times['minimax'] += tt
        elif 'get_ordered_moves' in func_name or '_evaluate_move' in func_name:
            component_times['move_ordering'] += tt
        elif 'score_' in func_name or 'evaluate' in func_name:
            component_times['evaluation'] += tt
        elif 'is_legal' in func_name:
            component_times['legal_checking'] += tt
        elif 'make_move' in func_name or 'undo_move' in func_name:
            component_times['move_generation'] += tt
        else:
            component_times['other'] += tt

    print(f"\n{'='*70}")
    print("COMPONENT TIME BREAKDOWN")
    print(f"{'='*70}\n")
    print(f"{'Component':<30} {'Time (s)':<15} {'Percentage':<15}")
    print(f"{'-'*70}")

    for component, time_spent in sorted(component_times.items(), key=lambda x: x[1], reverse=True):
        percentage = (time_spent / total_time * 100) if total_time > 0 else 0
        print(f"{component:<30} {time_spent:<15.3f} {percentage:<15.1f}%")

    print(f"{'-'*70}")
    print(f"{'TOTAL':<30} {total_time:<15.3f} {'100.0%':<15}")


def main():
    """
    Run performance profiling and analysis.
    """
    print("\n" + "="*70)
    print("GOMOKU AI PERFORMANCE PROFILING")
    print("="*70)
    print("\nThis will profile 20 moves of AI vs AI gameplay.")
    print("Please wait...\n")

    # Profile the game
    profiler = profile_ai_game(num_moves=20)

    # Analyze results
    analyze_profile(profiler, top_n=30)
    compare_function_costs(profiler)

    print(f"\n{'='*70}")
    print("PROFILING COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

