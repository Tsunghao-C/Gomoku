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
        Get moves prioritized by relevance (near existing stones) and defensive needs.
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

        moves = list(priority_moves) if priority_moves else self.get_valid_moves(board)

        # Prioritize defensive moves if there are immediate threats
        opponent = self.get_opponent(player)
        immediate_threats = self.find_immediate_threats(board, opponent)

        if immediate_threats:
            # Move threat positions to the front for immediate evaluation
            defensive_moves = [move for move in moves if move in immediate_threats]
            other_moves = [move for move in moves if move not in immediate_threats]
            return defensive_moves + other_moves

        return moves

    def evaluate_position(self, board: list[list[Player]], player: Player) -> float:
        """
        Evaluate the current board position for the given player.
        Returns a score where positive means advantage for the player.
        """
        self.nodes_evaluated += 1

        # Check for immediate win/loss
        if self.check_win(board, player):
            return 100000  # Massive bonus for winning
        if self.check_win(board, self.get_opponent(player)):
            return -100000  # Massive penalty for losing

        score = 0
        opponent = self.get_opponent(player)

        # First, check for immediate threats that must be blocked
        immediate_threats = self.find_immediate_threats(board, opponent)
        if immediate_threats:
            # If opponent has immediate threats, prioritize blocking them
            score -= 50000  # Large penalty for not blocking threats

        # Evaluate all positions on the board
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    # Evaluate this empty position for both players
                    player_score = self.evaluate_position_for_player(board, row, col, player)
                    opponent_score = self.evaluate_position_for_player(board, row, col, opponent)

                    # The position's value is the difference
                    score += player_score - opponent_score

        return score

    def find_immediate_threats(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """Find positions where the player has immediate winning threats (4 in a row)."""
        threats = []

        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    # Check if placing a stone here would create a threat
                    board[row][col] = player
                    if self.check_win(board, player):
                        threats.append((row, col))
                    board[row][col] = Player.EMPTY

        return threats

    def evaluate_position_for_player(self, board: list[list[Player]], row: int, col: int, player: Player) -> float:
        """Evaluate how good this position would be for the given player."""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonal

        for dr, dc in directions:
            pattern_score = self.evaluate_pattern_advanced(board, row, col, dr, dc, player)
            score += pattern_score

        return score

    def evaluate_pattern_advanced(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> float:
        """Advanced pattern evaluation that recognizes threats and opportunities."""
        # Check patterns of length 5 in this direction
        patterns = []

        # Get all 5-position patterns that include this position
        for start in range(5):
            pattern = []
            valid = True

            for i in range(5):
                r, c = row + (i - start) * dr, col + (i - start) * dc
                if 0 <= r < len(board) and 0 <= c < len(board[0]):
                    pattern.append(board[r][c])
                else:
                    valid = False
                    break

            if valid:
                patterns.append(pattern)

        # Evaluate each pattern
        total_score = 0
        for pattern in patterns:
            total_score += self.score_pattern(pattern, player)

        return total_score

    def score_pattern(self, pattern: list[Player], player: Player) -> float:
        """Score a 5-position pattern for the given player."""
        opponent = self.get_opponent(player)

        # Count stones in pattern
        player_count = pattern.count(player)
        opponent_count = pattern.count(opponent)
        empty_count = pattern.count(Player.EMPTY)

        # If both players have stones, it's blocked
        if player_count > 0 and opponent_count > 0:
            return 0

        # Score based on player stones
        if player_count > 0:
            return self.get_pattern_score(player_count, empty_count)
        elif opponent_count > 0:
            return -self.get_pattern_score(opponent_count, empty_count)

        return 0

    def get_pattern_score(self, stone_count: int, empty_count: int) -> float:
        """Get score for a pattern with given stone and empty counts."""
        # Pattern scoring based on Gomoku strategy
        if stone_count == 5:
            return 100000  # Five in a row - immediate win
        elif stone_count == 4 and empty_count == 1:
            return 10000   # Four in a row with one empty - immediate threat
        elif stone_count == 3 and empty_count == 2:
            return 1000    # Three in a row with two empty - strong threat
        elif stone_count == 2 and empty_count == 3:
            return 100     # Two in a row with three empty - potential threat
        elif stone_count == 1 and empty_count == 4:
            return 10      # One stone with four empty - weak potential
        else:
            return 0

    def evaluate_threat_level(self, board: list[list[Player]], player: Player) -> float:
        """Evaluate the overall threat level for the given player."""
        threat_score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == player:
                    # Check all directions from this stone
                    for dr, dc in directions:
                        threat_score += self.evaluate_threat_in_direction(board, row, col, dr, dc, player)

        return threat_score

    def evaluate_threat_in_direction(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> float:
        """Evaluate threat level in a specific direction."""
        # Count consecutive stones in this direction
        count = 1
        r, c = row + dr, col + dc
        while 0 <= r < len(board) and 0 <= c < len(board[0]) and board[r][c] == player:
            count += 1
            r, c = r + dr, c + dc

        # Count consecutive stones in opposite direction
        r, c = row - dr, col - dc
        while 0 <= r < len(board) and 0 <= c < len(board[0]) and board[r][c] == player:
            count += 1
            r, c = r - dr, c - dc

        # Score based on threat level
        if count >= 5:
            return 100000  # Already won
        elif count == 4:
            return 10000   # Immediate threat
        elif count == 3:
            return 1000    # Strong threat
        elif count == 2:
            return 100     # Potential threat
        else:
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

    def get_best_move(self, board: list[list[Player]], player: Player, time_limit: float = 0.5) -> tuple[tuple[int, int], float, dict]:
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
