"""
Gomoku AI Engine
Implements MiniMax algorithm with Alpha-Beta pruning for Gomoku AI
"""

import copy
import time
from enum import Enum


class Player(Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2


class GomokuAI:
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.nodes_evaluated = 0
        self.cache_hits = 0
        self.transposition_table: dict[str, tuple[float, int]] = {}
        self.thinking_visualization = []
        self.current_depth = 0
        self.best_moves_at_depth = {}
        self.current_search_info = {
            "current_depth": 0,
            "current_move": None,
            "moves_evaluated": 0,
            "best_move_so_far": None,
            "best_score_so_far": 0
        }

    def get_opponent(self, player: Player) -> Player:
        """Get the opponent player."""
        return Player.WHITE if player == Player.BLACK else Player.BLACK

    def get_valid_moves(self, board: list[list[Player]]) -> list[tuple[int, int]]:
        """Get all valid moves on the board."""
        moves = []
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    moves.append((row, col))
        return moves

    def get_priority_moves(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """
        Get moves prioritized by relevance (near existing stones).
        This is a key optimization - we don't need to consider all 361 positions!
        """
        if not any(Player.EMPTY != cell for row in board for cell in row):
            # First move - return center
            return [(9, 9)]

        # Find all empty positions near existing stones
        priority_moves = set()
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] != Player.EMPTY:
                    # Add positions within 2 cells of existing stones
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            new_row, new_col = row + dr, col + dc
                            if 0 <= new_row < len(board) and 0 <= new_col < len(board[0]) and board[new_row][new_col] == Player.EMPTY:
                                priority_moves.add((new_row, new_col))

        return list(priority_moves) if priority_moves else self.get_valid_moves(board)

    def evaluate_position(self, board: list[list[Player]], player: Player) -> float:
        """
        Evaluate the current board position for the given player.
        Returns a score where positive means advantage for the player.
        """
        self.nodes_evaluated += 1

        # Check for immediate win/loss
        if self.check_win(board, player):
            return 10000
        if self.check_win(board, self.get_opponent(player)):
            return -10000

        score = 0

        # Evaluate all possible 5-in-a-row patterns
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    # Check all directions from this position
                    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
                    for dr, dc in directions:
                        pattern_score = self.evaluate_pattern(board, row, col, dr, dc, player)
                        score += pattern_score

        return score

    def evaluate_pattern(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> float:
        """Evaluate a specific 5-in-a-row pattern."""
        # Count consecutive stones in both directions
        player_count = 0
        opponent_count = 0
        empty_count = 0

        # Check 5 positions in the direction
        for i in range(5):
            r, c = row + i * dr, col + i * dc
            if 0 <= r < len(board) and 0 <= c < len(board[0]):
                if board[r][c] == player:
                    player_count += 1
                elif board[r][c] == self.get_opponent(player):
                    opponent_count += 1
                else:
                    empty_count += 1
            else:
                # Out of bounds counts as opponent (blocked)
                opponent_count += 1

        # If both players have stones in this pattern, it's blocked
        if player_count > 0 and opponent_count > 0:
            return 0

        # Score based on player stones
        if player_count > 0:
            return player_count**3  # Exponential scoring for longer sequences
        elif opponent_count > 0:
            return -(opponent_count**3)  # Penalty for opponent sequences

        return 0

    def check_win(self, board: list[list[Player]], player: Player) -> bool:
        """Check if the given player has won."""
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == player:
                    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
                    for dr, dc in directions:
                        if self.count_consecutive(board, row, col, dr, dc, player) >= 5:
                            return True
        return False

    def count_consecutive(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> int:
        """Count consecutive stones in a direction."""
        count = 0
        r, c = row, col
        while 0 <= r < len(board) and 0 <= c < len(board[0]) and board[r][c] == player:
            count += 1
            r, c = r + dr, c + dc
        return count

    def minimax(
        self, board: list[list[Player]], depth: int, player: Player, alpha: float = float("-inf"), beta: float = float("inf")
    ) -> tuple[float, tuple[int, int] | None]:
        """
        MiniMax algorithm with Alpha-Beta pruning.
        Returns (score, best_move)
        """
        # Check cache first
        board_key = self.board_to_string(board)
        if board_key in self.transposition_table:
            cached_score, cached_depth = self.transposition_table[board_key]
            if cached_depth >= depth:
                self.cache_hits += 1
                return cached_score, None

        # Terminal conditions
        if depth == 0 or self.check_win(board, player) or self.check_win(board, self.get_opponent(player)):
            score = self.evaluate_position(board, player)
            return score, None

        # Get priority moves (optimization)
        moves = self.get_priority_moves(board, player)
        if not moves:
            return 0, None

        best_score = float("-inf") if player == Player.BLACK else float("inf")
        best_move = None

        for move in moves:
            row, col = move
            # Make move
            board[row][col] = player
            self.current_search_info["current_move"] = move
            self.current_search_info["moves_evaluated"] += 1

            # Recursive call
            score, _ = self.minimax(board, depth - 1, self.get_opponent(player), alpha, beta)

            # Undo move
            board[row][col] = Player.EMPTY

            # Update best move
            if player == Player.BLACK:  # Maximizing player
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            else:  # Minimizing player
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)
                if beta <= alpha:
                    break  # Alpha-beta pruning

        # Cache the result
        self.transposition_table[board_key] = (best_score, depth)

        return best_score, best_move

    def get_best_move(self, board: list[list[Player]], player: Player, time_limit: float = 0.4) -> tuple[tuple[int, int], float, dict]:
        """
        Get the best move for the given player.
        Returns (move, score, stats)
        """
        start_time = time.time()
        self.nodes_evaluated = 0
        self.cache_hits = 0
        self.thinking_visualization = []
        self.best_moves_at_depth = {}

        # Use iterative deepening for better performance
        best_move = None
        best_score = float("-inf") if player == Player.BLACK else float("inf")

        for depth in range(1, self.max_depth + 1):
            try:
                # Check time limit
                if time.time() - start_time > time_limit:
                    print(f"Time limit reached at depth {depth}")
                    break

                self.current_depth = depth
                self.current_search_info["current_depth"] = depth
                self.current_search_info["moves_evaluated"] = 0

                score, move = self.minimax(copy.deepcopy(board), depth, player)
                if move is not None:
                    best_move = move
                    best_score = score
                    self.best_moves_at_depth[depth] = (move, score)
                    self.current_search_info["best_move_so_far"] = move
                    self.current_search_info["best_score_so_far"] = score

                    # Add visualization entry
                    self.thinking_visualization.append({
                        "depth": depth,
                        "best_move": move,
                        "score": score,
                        "nodes_evaluated": self.nodes_evaluated,
                        "time_elapsed": time.time() - start_time
                    })
            except Exception as e:
                print(f"Error at depth {depth}: {e}")
                break  # If we run out of time or memory, use the best move so far

        end_time = time.time()
        calculation_time = end_time - start_time

        stats = {
            "calculation_time": calculation_time,
            "nodes_evaluated": self.nodes_evaluated,
            "cache_hits": self.cache_hits,
            "depth_searched": self.max_depth,
            "thinking_process": self.thinking_visualization,
            "best_moves_by_depth": self.best_moves_at_depth,
            "current_search": self.current_search_info
        }

        return best_move, best_score, stats

    def board_to_string(self, board: list[list[Player]]) -> str:
        """Convert board to string for caching."""
        return "".join(str(cell.value) for row in board for cell in row)
