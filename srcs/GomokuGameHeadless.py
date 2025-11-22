"""
Headless version of Gomoku game for automated testing.
No pygame GUI - pure game logic for fast automated testing.
"""

import random

from srcs.GomokuAI import GomokuAI
from srcs.GomokuLogic import GomokuLogic


class GomokuGameHeadless:
    """
    Headless Gomoku game engine for automated testing.
    Supports AI vs AI games without GUI overhead.
    """

    def __init__(self, config, player1_config=None, player2_config=None):
        """
        Initialize headless game.

        Args:
            config: Base game configuration
            player1_config: Optional separate config for player 1 AI
            player2_config: Optional separate config for player 2 AI
        """
        self.config = config

        # Set seed for reproducibility (as in original headless)
        random.seed(42)

        # Initialize logic
        self.logic = GomokuLogic(config)

        # Extract game settings (from logic or config)
        game_cfg = config["game_settings"]
        self.BOARD_SIZE = game_cfg["board_size"]
        self.BLACK_PLAYER = game_cfg["black_player"]
        self.WHITE_PLAYER = game_cfg["white_player"]
        self.WIN_BY_CAPTURES = game_cfg["win_by_captures"]

        # State aliases
        self.board = self.logic.board
        self.captures = self.logic.captures
        self.current_player = self.BLACK_PLAYER
        self.move_count = 0
        self.game_over = False
        self.winner = None

        # Game history for analysis
        self.move_history = []
        self.time_history = []
        self.depth_history = []

        # Initialize AIs with separate configs if provided
        self.ai1 = GomokuAI(player1_config or config)
        self.ai2 = GomokuAI(player2_config or config)

        # Zobrist hashing handled by logic
        self.current_hash = self.logic.current_hash

    @property
    def current_hash(self):
        return self.logic.current_hash

    @current_hash.setter
    def current_hash(self, value):
        self.logic.current_hash = value

    def apply_move(self, row, col, player):
        """
        Make a move and apply captures (for actual gameplay).

        Returns:
            bool: True if move was successful
        """
        # Check legality
        is_legal, _ = self.logic.is_legal_move(row, col, player, self.board)
        if not is_legal:
            return False

        captured_pieces, new_hash = self.logic.make_move(
            row, col, player, self.board, self.current_hash
        )

        # Update state
        self.current_hash = new_hash
        self.captures[player] += len(captured_pieces)

        # Record move
        self.move_history.append((row, col, player, len(captured_pieces)))
        self.move_count += 1

        # Check win condition
        win_line = self.logic.check_win(row, col, player, self.board)
        if win_line:
            self.game_over = True
            self.winner = player
        elif self.captures[player] >= self.WIN_BY_CAPTURES * 2:
            self.game_over = True
            self.winner = player

        return True

    def get_ai_move(self, player):
        """
        Get AI move for player.

        Returns:
            tuple: (row, col, time_taken, depth_reached)
        """
        ai = self.ai1 if player == self.BLACK_PLAYER else self.ai2

        move, _ = ai.get_best_move(
            self.board,
            self.captures,
            self.current_hash,
            player,
            self.WIN_BY_CAPTURES,
            self.logic, # Pass the logic instance
            self.move_count
        )

        time_taken = ai.last_move_time
        depth_reached = ai.last_depth_reached

        return move, time_taken, depth_reached

    def play_game(self, verbose=False, max_moves=300):
        """
        Play a complete game.

        Args:
            verbose: Print game progress
            max_moves: Maximum moves before draw

        Returns:
            dict: Game results with statistics
        """
        if verbose:
            print(f"\n{'='*60}")
            print("Starting new game (Headless Mode)")
            print(f"{'='*60}\n")

        while not self.game_over and self.move_count < max_moves:
            player_name = "Black" if self.current_player == self.BLACK_PLAYER else "White"

            if verbose:
                print(f"\nTurn {(self.move_count + 2) // 2} - {player_name}'s move")

            # Get AI move
            move_result = self.get_ai_move(self.current_player)

            if move_result is None or move_result[0] is None:
                if verbose:
                    print(f"❌ {player_name} has no legal moves!")
                self.game_over = True
                self.winner = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                              else self.BLACK_PLAYER)
                break

            move, time_taken, depth_reached = move_result

            if move is None:
                if verbose:
                    print(f"❌ {player_name} returned None move!")
                self.game_over = True
                self.winner = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                              else self.BLACK_PLAYER)
                break

            row, col = move

            # Make move
            if not self.apply_move(row, col, self.current_player):
                if verbose:
                    print(f"❌ Illegal move attempted: ({row}, {col})")
                self.game_over = True
                self.winner = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                              else self.BLACK_PLAYER)
                break

            # Record stats
            self.time_history.append(time_taken)
            self.depth_history.append(depth_reached)

            if verbose:
                captures_made = self.move_history[-1][3]
                print(f"  Move: ({row}, {col})")
                print(f"  Time: {time_taken:.2f}s, Depth: {depth_reached}")
                print(f"  Captures: {self.captures[self.current_player]} total"
                      f"{f' (+{captures_made})' if captures_made > 0 else ''}")

            # Switch player
            self.current_player = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                                  else self.BLACK_PLAYER)

        # Handle draw
        if not self.game_over:
            self.game_over = True
            self.winner = None

        # Generate results
        results = self.generate_results(verbose)

        return results

    def generate_results(self, verbose=False):
        """Generate game results and statistics."""
        results = {
            'winner': self.winner,
            'total_moves': self.move_count,
            'black_captures': self.captures[self.BLACK_PLAYER],
            'white_captures': self.captures[self.WHITE_PLAYER],
            'avg_time': sum(self.time_history) / len(self.time_history) if self.time_history else 0,
            'max_time': max(self.time_history) if self.time_history else 0,
            'avg_depth': sum(self.depth_history) / len(self.depth_history) if self.depth_history else 0,
            'max_depth': max(self.depth_history) if self.depth_history else 0,
            'move_history': self.move_history.copy(),
            'time_history': self.time_history.copy(),
            'depth_history': self.depth_history.copy(),
        }

        if verbose:
            print(f"\n{'='*60}")
            print("GAME OVER")
            print(f"{'='*60}")

            if self.winner is None:
                print("Result: DRAW")
            else:
                winner_name = "Black" if self.winner == self.BLACK_PLAYER else "White"
                print(f"Winner: {winner_name}")

            print("\nStatistics:")
            print(f"  Total moves: {results['total_moves']}")
            print(f"  Black captures: {results['black_captures']}")
            print(f"  White captures: {results['white_captures']}")
            print(f"  Avg time/move: {results['avg_time']:.2f}s")
            print(f"  Max time: {results['max_time']:.2f}s")
            print(f"  Avg depth: {results['avg_depth']:.1f}")
            print(f"  Max depth: {results['max_depth']}")
            print(f"{'='*60}\n")

        return results
