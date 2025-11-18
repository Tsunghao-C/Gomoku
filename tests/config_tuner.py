"""
Automated configuration tuning framework for Gomoku AI.

This module provides tools to systematically test and tune heuristic parameters
by running automated AI vs AI games and comparing results.
"""

import copy
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from srcs.GomokuGameHeadless import GomokuGameHeadless


class ConfigTuner:
    """
    Framework for automated configuration testing and tuning.
    """

    def __init__(self, base_config_path="config.json"):
        """Initialize tuner with base configuration."""
        with open(base_config_path) as f:
            self.base_config = json.load(f)

        self.results = []
        self.test_name = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def create_config_variant(self, name, modifications):
        """
        Create a configuration variant by modifying the base config.
        
        Args:
            name: Name for this variant
            modifications: Dict of modifications (nested dict structure)
                          e.g. {"heuristic_settings.scores.open_four": 2000000}
        
        Returns:
            dict: Modified configuration
        """
        config = copy.deepcopy(self.base_config)

        for path, value in modifications.items():
            # Navigate nested dict structure
            keys = path.split('.')
            current = config
            for key in keys[:-1]:
                current = current[key]
            current[keys[-1]] = value

        return config

    def run_single_game(self, config1, config2, game_num, verbose=False):
        """
        Run a single game between two configurations.
        
        Args:
            config1: Configuration for player 1 (Black)
            config2: Configuration for player 2 (White)
            game_num: Game number for logging
            verbose: Print detailed game progress
        
        Returns:
            dict: Game results
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"GAME {game_num}")
            print(f"{'='*70}")

        game = GomokuGameHeadless(
            self.base_config,
            player1_config=config1,
            player2_config=config2
        )

        results = game.play_game(verbose=verbose, max_moves=300)

        return results

    def run_match(self, config1, config1_name, config2, config2_name,
                  num_games=10, verbose=False):
        """
        Run a match (multiple games) between two configurations.
        
        Each config plays as both Black and White to eliminate first-player advantage.
        
        Args:
            config1: First configuration
            config1_name: Name of first configuration
            config2: Second configuration
            config2_name: Name of second configuration
            num_games: Number of games to play (must be even)
            verbose: Print detailed progress
        
        Returns:
            dict: Match results with statistics
        """
        if num_games % 2 != 0:
            num_games += 1  # Ensure even number

        print(f"\n{'='*70}")
        print(f"MATCH: {config1_name} vs {config2_name}")
        print(f"{'='*70}")
        print(f"Playing {num_games} games ({num_games//2} as each color)...\n")

        match_results = {
            'config1_name': config1_name,
            'config2_name': config2_name,
            'config1_wins': 0,
            'config2_wins': 0,
            'draws': 0,
            'games': [],
            'config1_stats': {
                'avg_time': 0,
                'avg_depth': 0,
                'total_captures': 0,
            },
            'config2_stats': {
                'avg_time': 0,
                'avg_depth': 0,
                'total_captures': 0,
            },
        }

        start_time = time.time()

        # Play half games with config1 as Black, half with config2 as Black
        for i in range(num_games):
            game_num = i + 1

            if i < num_games // 2:
                # Config1 is Black, Config2 is White
                results = self.run_single_game(config1, config2, game_num, verbose)

                if results['winner'] == 1:  # Black won
                    match_results['config1_wins'] += 1
                    winner = config1_name
                elif results['winner'] == 2:  # White won
                    match_results['config2_wins'] += 1
                    winner = config2_name
                else:
                    match_results['draws'] += 1
                    winner = "Draw"

                # Update stats
                match_results['config1_stats']['total_captures'] += results['black_captures']
                match_results['config2_stats']['total_captures'] += results['white_captures']
            else:
                # Config2 is Black, Config1 is White
                results = self.run_single_game(config2, config1, game_num, verbose)

                if results['winner'] == 1:  # Black won
                    match_results['config2_wins'] += 1
                    winner = config2_name
                elif results['winner'] == 2:  # White won
                    match_results['config1_wins'] += 1
                    winner = config1_name
                else:
                    match_results['draws'] += 1
                    winner = "Draw"

                # Update stats
                match_results['config2_stats']['total_captures'] += results['black_captures']
                match_results['config1_stats']['total_captures'] += results['white_captures']

            match_results['games'].append(results)

            print(f"Game {game_num}/{num_games}: {winner} "
                  f"({results['total_moves']} moves, "
                  f"depth: {results['avg_depth']:.1f})")

        total_time = time.time() - start_time

        # Calculate final statistics
        config1_times = []
        config2_times = []
        config1_depths = []
        config2_depths = []

        for i, game in enumerate(match_results['games']):
            if i < num_games // 2:
                # Config1 was Black
                config1_times.extend(game['time_history'][::2])  # Black moves
                config2_times.extend(game['time_history'][1::2])  # White moves
                config1_depths.extend(game['depth_history'][::2])
                config2_depths.extend(game['depth_history'][1::2])
            else:
                # Config2 was Black
                config2_times.extend(game['time_history'][::2])
                config1_times.extend(game['time_history'][1::2])
                config2_depths.extend(game['depth_history'][::2])
                config1_depths.extend(game['depth_history'][1::2])

        match_results['config1_stats']['avg_time'] = (
            sum(config1_times) / len(config1_times) if config1_times else 0
        )
        match_results['config2_stats']['avg_time'] = (
            sum(config2_times) / len(config2_times) if config2_times else 0
        )
        match_results['config1_stats']['avg_depth'] = (
            sum(config1_depths) / len(config1_depths) if config1_depths else 0
        )
        match_results['config2_stats']['avg_depth'] = (
            sum(config2_depths) / len(config2_depths) if config2_depths else 0
        )

        # Print match summary
        print(f"\n{'='*70}")
        print("MATCH RESULTS")
        print(f"{'='*70}")
        print(f"{config1_name}: {match_results['config1_wins']} wins")
        print(f"{config2_name}: {match_results['config2_wins']} wins")
        print(f"Draws: {match_results['draws']}")
        print("\nWin Rate:")
        total_games = match_results['config1_wins'] + match_results['config2_wins'] + match_results['draws']
        print(f"  {config1_name}: {match_results['config1_wins']/total_games*100:.1f}%")
        print(f"  {config2_name}: {match_results['config2_wins']/total_games*100:.1f}%")
        print("\nPerformance:")
        print(f"  {config1_name}: {match_results['config1_stats']['avg_depth']:.1f} avg depth, "
              f"{match_results['config1_stats']['avg_time']:.2f}s avg time")
        print(f"  {config2_name}: {match_results['config2_stats']['avg_depth']:.1f} avg depth, "
              f"{match_results['config2_stats']['avg_time']:.2f}s avg time")
        print(f"\nTotal match time: {total_time:.1f}s")
        print(f"{'='*70}\n")

        self.results.append(match_results)

        return match_results

    def run_tournament(self, configs, num_games_per_match=10, verbose=False):
        """
        Run a round-robin tournament with multiple configurations.
        
        Args:
            configs: Dict of {name: config} configurations to test
            num_games_per_match: Games per match between each pair
            verbose: Print detailed progress
        
        Returns:
            dict: Tournament results with rankings
        """
        print(f"\n{'='*70}")
        print("TOURNAMENT")
        print(f"{'='*70}")
        print(f"Configurations: {len(configs)}")
        print(f"Games per match: {num_games_per_match}")
        print(f"Total matches: {len(configs) * (len(configs) - 1) // 2}")
        print(f"{'='*70}\n")

        config_names = list(configs.keys())
        standings = {name: {'wins': 0, 'losses': 0, 'draws': 0, 'points': 0}
                    for name in config_names}

        # Play all pairs
        for i, name1 in enumerate(config_names):
            for name2 in config_names[i+1:]:
                match = self.run_match(
                    configs[name1], name1,
                    configs[name2], name2,
                    num_games_per_match, verbose
                )

                # Update standings (3 points for win, 1 for draw)
                standings[name1]['wins'] += match['config1_wins']
                standings[name1]['losses'] += match['config2_wins']
                standings[name1]['draws'] += match['draws']
                standings[name1]['points'] += match['config1_wins'] * 3 + match['draws']

                standings[name2]['wins'] += match['config2_wins']
                standings[name2]['losses'] += match['config1_wins']
                standings[name2]['draws'] += match['draws']
                standings[name2]['points'] += match['config2_wins'] * 3 + match['draws']

        # Sort by points
        ranked = sorted(standings.items(), key=lambda x: x[1]['points'], reverse=True)

        # Print final standings
        print(f"\n{'='*70}")
        print("TOURNAMENT STANDINGS")
        print(f"{'='*70}")
        print(f"{'Rank':<6} {'Config':<25} {'W':<4} {'L':<4} {'D':<4} {'Points':<8}")
        print(f"{'-'*70}")

        for rank, (name, stats) in enumerate(ranked, 1):
            print(f"{rank:<6} {name:<25} {stats['wins']:<4} {stats['losses']:<4} "
                  f"{stats['draws']:<4} {stats['points']:<8}")

        print(f"{'='*70}\n")

        return {
            'standings': standings,
            'ranked': ranked,
            'matches': self.results,
        }

    def save_results(self, results, output_dir="tests/results"):
        """Save tournament results to JSON file."""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"tournament_{timestamp}.json")

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✅ Results saved to: {output_file}")

        return output_file


def main():
    """Example usage of the tuning framework."""
    print("Gomoku AI Configuration Tuner")
    print("="*70)

    tuner = ConfigTuner("config.json")

    # Example: Test different capture defense penalty levels
    configs = {
        'baseline': tuner.base_config,

        'low_penalty': tuner.create_config_variant(
            'low_penalty',
            {
                'heuristic_settings.capture_defense.trap_detection_penalty': 200000,
                'heuristic_settings.capture_defense.critical_penalty': 400000,
            }
        ),

        'high_penalty': tuner.create_config_variant(
            'high_penalty',
            {
                'heuristic_settings.capture_defense.trap_detection_penalty': 600000,
                'heuristic_settings.capture_defense.critical_penalty': 1200000,
            }
        ),
    }

    # Run tournament
    results = tuner.run_tournament(configs, num_games_per_match=6, verbose=False)

    # Save results
    tuner.save_results(results)


if __name__ == "__main__":
    main()

