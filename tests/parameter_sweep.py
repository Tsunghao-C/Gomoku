"""
Parameter sweep utility for systematic heuristic tuning.

Provides tools to sweep through parameter ranges and find optimal values.
"""

import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config_tuner import ConfigTuner


class ParameterSweep:
    """
    Systematic parameter sweep for finding optimal configurations.
    """

    def __init__(self, base_config_path="config.json"):
        """Initialize with base configuration."""
        self.tuner = ConfigTuner(base_config_path)

    def sweep_single_parameter(self, param_path, values, baseline_name="baseline",
                               num_games=10, verbose=False):
        """
        Sweep a single parameter through different values.
        
        Args:
            param_path: Path to parameter (e.g., "heuristic_settings.scores.open_four")
            values: List of values to test
            baseline_name: Name for baseline config
            num_games: Games per match
            verbose: Print detailed progress
        
        Returns:
            dict: Results for each value tested
        """
        print(f"\n{'='*70}")
        print(f"PARAMETER SWEEP: {param_path}")
        print(f"{'='*70}")
        print(f"Testing {len(values)} values: {values}")
        print(f"{'='*70}\n")

        configs = {baseline_name: self.tuner.base_config}

        # Create config for each value
        for value in values:
            config_name = f"{param_path.split('.')[-1]}={value}"
            configs[config_name] = self.tuner.create_config_variant(
                config_name,
                {param_path: value}
            )

        # Run tournament
        results = self.tuner.run_tournament(configs, num_games, verbose)

        # Analyze results
        print(f"\n{'='*70}")
        print(f"PARAMETER SWEEP RESULTS: {param_path}")
        print(f"{'='*70}")
        print(f"{'Value':<20} {'Win Rate':<12} {'Points':<10}")
        print(f"{'-'*70}")

        for name, stats in results['ranked']:
            if name == baseline_name:
                value_str = "baseline"
            else:
                value_str = name.split('=')[1]

            total_games = stats['wins'] + stats['losses'] + stats['draws']
            win_rate = stats['wins'] / total_games * 100 if total_games > 0 else 0

            print(f"{value_str:<20} {win_rate:>6.1f}%      {stats['points']:<10}")

        print(f"{'='*70}\n")

        return results

    def sweep_multiple_parameters(self, param_specs, num_games=6, verbose=False):
        """
        Sweep multiple parameters simultaneously (grid search).
        
        Args:
            param_specs: Dict of {param_path: list_of_values}
            num_games: Games per match
            verbose: Print detailed progress
        
        Returns:
            dict: Tournament results
        
        Example:
            sweep_multiple_parameters({
                'heuristic_settings.scores.open_four': [800000, 1000000, 1200000],
                'heuristic_settings.scores.broken_four': [300000, 400000, 500000],
            })
        """
        print(f"\n{'='*70}")
        print("MULTI-PARAMETER GRID SEARCH")
        print(f"{'='*70}")
        print(f"Parameters: {len(param_specs)}")
        for param, values in param_specs.items():
            print(f"  {param}: {len(values)} values")

        # Generate all combinations
        param_names = list(param_specs.keys())
        param_values = list(param_specs.values())
        combinations = list(product(*param_values))

        print(f"Total combinations: {len(combinations)}")
        print(f"{'='*70}\n")

        configs = {'baseline': self.tuner.base_config}

        # Create config for each combination
        for combo in combinations:
            modifications = {param: value for param, value in zip(param_names, combo, strict=False)}

            # Generate name from combo
            name_parts = [f"{p.split('.')[-1]}={v}" for p, v in zip(param_names, combo, strict=False)]
            config_name = "_".join(name_parts)

            configs[config_name] = self.tuner.create_config_variant(
                config_name,
                modifications
            )

        # Run tournament
        results = self.tuner.run_tournament(configs, num_games, verbose)

        return results

    def binary_search_parameter(self, param_path, min_val, max_val,
                                num_iterations=5, games_per_test=10):
        """
        Binary search to find optimal parameter value within range.
        
        Progressively narrows down to the best value by testing midpoints.
        
        Args:
            param_path: Path to parameter
            min_val: Minimum value to test
            max_val: Maximum value to test
            num_iterations: Number of binary search iterations
            games_per_test: Games per comparison
        
        Returns:
            tuple: (optimal_value, results)
        """
        print(f"\n{'='*70}")
        print(f"BINARY SEARCH: {param_path}")
        print(f"{'='*70}")
        print(f"Range: [{min_val}, {max_val}]")
        print(f"Iterations: {num_iterations}")
        print(f"{'='*70}\n")

        current_min = min_val
        current_max = max_val
        best_value = None

        for iteration in range(num_iterations):
            print(f"\n--- Iteration {iteration + 1}/{num_iterations} ---")
            print(f"Testing range: [{current_min}, {current_max}]")

            mid = (current_min + current_max) / 2

            # Test three points: min, mid, max
            configs = {
                'baseline': self.tuner.base_config,
                f'value={current_min}': self.tuner.create_config_variant(
                    f'value={current_min}',
                    {param_path: current_min}
                ),
                f'value={mid}': self.tuner.create_config_variant(
                    f'value={mid}',
                    {param_path: mid}
                ),
                f'value={current_max}': self.tuner.create_config_variant(
                    f'value={current_max}',
                    {param_path: current_max}
                ),
            }

            results = self.tuner.run_tournament(configs, games_per_test, verbose=False)

            # Find best performer
            best = max(results['ranked'], key=lambda x: x[1]['points'])
            best_name = best[0]

            if best_name == 'baseline':
                print("Baseline is best. Using default value.")
                break

            best_value = float(best_name.split('=')[1])
            print(f"Best value this iteration: {best_value}")

            # Narrow range
            if best_value == current_min:
                # Best is at lower end, shift range down
                current_max = mid
            elif best_value == current_max:
                # Best is at upper end, shift range up
                current_min = mid
            else:
                # Best is in middle, narrow both sides
                range_size = (current_max - current_min) / 4
                current_min = max(min_val, best_value - range_size)
                current_max = min(max_val, best_value + range_size)

        print(f"\n{'='*70}")
        print("BINARY SEARCH COMPLETE")
        print(f"{'='*70}")
        print(f"Optimal value: {best_value}")
        print(f"{'='*70}\n")

        return best_value, results


def example_capture_defense_tuning():
    """Example: Tune capture defense penalties."""
    sweep = ParameterSweep("config.json")

    # Test different trap detection penalties
    results = sweep.sweep_single_parameter(
        param_path='heuristic_settings.capture_defense.trap_detection_penalty',
        values=[200000, 300000, 400000, 500000, 600000],
        num_games=8
    )

    sweep.tuner.save_results(results, "tests/results")


def example_pattern_score_tuning():
    """Example: Tune pattern scores."""
    sweep = ParameterSweep("config.json")

    # Grid search for open_four and broken_four scores
    results = sweep.sweep_multiple_parameters(
        param_specs={
            'heuristic_settings.scores.open_four': [800000, 1000000, 1200000],
            'heuristic_settings.scores.broken_four': [300000, 400000, 500000],
        },
        num_games=6
    )

    sweep.tuner.save_results(results, "tests/results")


def example_binary_search():
    """Example: Binary search for optimal critical_penalty."""
    sweep = ParameterSweep("config.json")

    optimal, results = sweep.binary_search_parameter(
        param_path='heuristic_settings.capture_defense.critical_penalty',
        min_val=400000,
        max_val=1200000,
        num_iterations=4,
        games_per_test=8
    )

    print(f"\nOptimal critical_penalty: {optimal}")
    sweep.tuner.save_results(results, "tests/results")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "capture":
            example_capture_defense_tuning()
        elif sys.argv[1] == "patterns":
            example_pattern_score_tuning()
        elif sys.argv[1] == "binary":
            example_binary_search()
        else:
            print("Usage: python parameter_sweep.py [capture|patterns|binary]")
    else:
        print("Running default capture defense tuning...")
        example_capture_defense_tuning()

