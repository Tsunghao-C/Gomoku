"""
Quick test utility for rapid configuration testing.

Run a few games quickly to validate config changes before full tuning.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config_tuner import ConfigTuner


def quick_test(config_path="config.json", num_games=3, verbose=True):
    """
    Run a quick test of current configuration.
    
    Args:
        config_path: Path to config file to test
        num_games: Number of games to play (default 3)
        verbose: Print detailed game logs
    """
    print(f"\n{'='*70}")
    print("QUICK TEST")
    print(f"{'='*70}")
    print(f"Config: {config_path}")
    print(f"Games: {num_games}")
    print(f"{'='*70}\n")

    tuner = ConfigTuner(config_path)

    # Test config against itself (AI vs AI with same config)
    results = tuner.run_match(
        tuner.base_config, "Config",
        tuner.base_config, "Config (mirror)",
        num_games=num_games,
        verbose=verbose
    )

    print(f"\n{'='*70}")
    print("QUICK TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Games completed: {len(results['games'])}")
    print(f"Average moves per game: {sum(g['total_moves'] for g in results['games']) / len(results['games']):.1f}")
    print(f"Average depth: {results['config1_stats']['avg_depth']:.1f}")
    print(f"Average time per move: {results['config1_stats']['avg_time']:.2f}s")
    print(f"Max depth reached: {max(max(g['depth_history']) for g in results['games'])}")
    print(f"{'='*70}\n")

    return results


def compare_two_configs(config1_path, config2_path, num_games=6, verbose=False):
    """
    Quickly compare two configuration files.
    
    Args:
        config1_path: Path to first config
        config2_path: Path to second config
        num_games: Number of games to play
        verbose: Print detailed game logs
    """
    print(f"\n{'='*70}")
    print("CONFIG COMPARISON")
    print(f"{'='*70}")
    print(f"Config 1: {config1_path}")
    print(f"Config 2: {config2_path}")
    print(f"Games: {num_games}")
    print(f"{'='*70}\n")

    tuner = ConfigTuner(config1_path)

    with open(config2_path) as f:
        config2 = json.load(f)

    results = tuner.run_match(
        tuner.base_config, Path(config1_path).stem,
        config2, Path(config2_path).stem,
        num_games=num_games,
        verbose=verbose
    )

    return results


def test_single_change(param_path, new_value, num_games=4, verbose=False):
    """
    Test a single parameter change against baseline.
    
    Args:
        param_path: Dot-separated path to parameter
        new_value: New value to test
        num_games: Number of games to play
        verbose: Print detailed game logs
    
    Example:
        test_single_change(
            'heuristic_settings.capture_defense.trap_detection_penalty',
            500000,
            num_games=4
        )
    """
    print(f"\n{'='*70}")
    print("SINGLE PARAMETER TEST")
    print(f"{'='*70}")
    print(f"Parameter: {param_path}")
    print(f"New value: {new_value}")
    print(f"Games: {num_games}")
    print(f"{'='*70}\n")

    tuner = ConfigTuner("config.json")

    # Create modified config
    modified = tuner.create_config_variant(
        f"{param_path.split('.')[-1]}={new_value}",
        {param_path: new_value}
    )

    # Compare against baseline
    results = tuner.run_match(
        tuner.base_config, "baseline",
        modified, f"{param_path.split('.')[-1]}={new_value}",
        num_games=num_games,
        verbose=verbose
    )

    # Print recommendation
    print(f"\n{'='*70}")
    print("RECOMMENDATION")
    print(f"{'='*70}")

    if results['config2_wins'] > results['config1_wins']:
        print(f"✅ New value ({new_value}) performs BETTER than baseline!")
        print(f"   Win rate: {results['config2_wins']/(results['config1_wins']+results['config2_wins']+results['draws'])*100:.1f}%")
        print("   Consider updating config.json")
    elif results['config1_wins'] > results['config2_wins']:
        print(f"❌ New value ({new_value}) performs WORSE than baseline.")
        print(f"   Win rate: {results['config2_wins']/(results['config1_wins']+results['config2_wins']+results['draws'])*100:.1f}%")
        print("   Keep current value")
    else:
        print("⚖️  No significant difference detected.")
        print("   May need more games to determine impact")

    print(f"{'='*70}\n")

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "compare" and len(sys.argv) >= 4:
            # Compare two configs
            compare_two_configs(sys.argv[2], sys.argv[3], num_games=int(sys.argv[4]) if len(sys.argv) > 4 else 6)
        elif sys.argv[1] == "test" and len(sys.argv) >= 4:
            # Test single parameter change
            param_path = sys.argv[2]
            new_value = float(sys.argv[3]) if '.' in sys.argv[3] else int(sys.argv[3])
            num_games = int(sys.argv[4]) if len(sys.argv) > 4 else 4
            test_single_change(param_path, new_value, num_games)
        else:
            print("Usage:")
            print("  python quick_test.py                           # Quick test current config")
            print("  python quick_test.py compare config1 config2 [games]")
            print("  python quick_test.py test param_path value [games]")
    else:
        # Default: quick test
        quick_test()

