"""
Gomoku AI Engine
Implements MiniMax algorithm with Alpha-Beta pruning for Gomoku AI
"""

import copy
import time
from enum import Enum

from srcs.pattern_manager import PatternManager


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
        self.current_search_info = {"current_depth": 0, "current_move": None, "moves_evaluated": 0, "best_move_so_far": None, "best_score_so_far": 0}
        self.pattern_manager = PatternManager()

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
        stone_count = sum(1 for row in board for cell in row if cell != Player.EMPTY)

        # Opening strategy - first few moves
        if stone_count <= 2:
            return self.get_opening_moves(board, player)

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

        # Prioritize defensive moves if there are critical threats
        opponent = self.get_opponent(player)
        critical_threats = self.pattern_manager.find_critical_threats(board, opponent)

        if critical_threats:
            # Critical threats have highest priority
            critical_moves = [move for move in moves if move in critical_threats]
            other_moves = [move for move in moves if move not in critical_threats]
            return critical_moves + other_moves

        return moves

    def get_opening_moves(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """Get strategic opening moves based on Gomoku theory."""
        stone_count = sum(1 for row in board for cell in row if cell != Player.EMPTY)

        if stone_count == 0:
            # First move - center is optimal
            return [(9, 9)]

        elif stone_count == 1:
            # Second move - find where opponent played and respond strategically
            opponent_moves = []
            for row in range(len(board)):
                for col in range(len(board[row])):
                    if board[row][col] != Player.EMPTY:
                        opponent_moves.append((row, col))

            if opponent_moves:
                opponent_row, opponent_col = opponent_moves[0]
                # If opponent played near center, play near center
                if 6 <= opponent_row <= 12 and 6 <= opponent_col <= 12:
                    return self.get_center_area_moves(board)
                # If opponent played on edge, control center
                else:
                    return self.get_center_control_moves(board, opponent_row, opponent_col)

        elif stone_count == 2:
            # Third move - more strategic positioning
            return self.get_early_strategic_moves(board, player)

        # Fallback to normal priority moves
        return self.get_valid_moves(board)

    def get_center_area_moves(self, board: list[list[Player]]) -> list[tuple[int, int]]:
        """Get moves in the center area (7x7 around center)."""
        center_moves = []
        for row in range(6, 13):
            for col in range(6, 13):
                if board[row][col] == Player.EMPTY:
                    center_moves.append((row, col))
        return center_moves[:10]  # Limit to top 10 center moves

    def get_center_control_moves(self, board: list[list[Player]], opponent_row: int, opponent_col: int) -> list[tuple[int, int]]:
        """Get moves that control the center when opponent plays on edge."""
        # Prioritize center and near-center positions
        center_moves = []

        # Strong center positions
        center_positions = [(9, 9), (8, 9), (10, 9), (9, 8), (9, 10), (8, 8), (10, 10), (8, 10), (10, 8)]

        for row, col in center_positions:
            if board[row][col] == Player.EMPTY:
                center_moves.append((row, col))

        # Add some strategic positions based on opponent's edge move
        if opponent_row < 6 or opponent_row > 12:  # Opponent on top/bottom edge
            # Control horizontal center
            for col in range(7, 12):
                if board[9][col] == Player.EMPTY:
                    center_moves.append((9, col))

        if opponent_col < 6 or opponent_col > 12:  # Opponent on left/right edge
            # Control vertical center
            for row in range(7, 12):
                if board[row][9] == Player.EMPTY:
                    center_moves.append((row, 9))

        return center_moves[:15]  # Limit to top 15 moves

    def get_early_strategic_moves(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """Get strategic moves for early game (3rd+ move)."""
        # Find existing stones
        existing_stones = []
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] != Player.EMPTY:
                    existing_stones.append((row, col))

        strategic_moves = []

        # Look for patterns and opportunities
        for row, col in existing_stones:
            # Add moves that create or extend patterns
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < len(board) and 0 <= new_col < len(board[0]) and board[new_row][new_col] == Player.EMPTY:
                        strategic_moves.append((new_row, new_col))

        # Remove duplicates and limit
        unique_moves = list(set(strategic_moves))
        return unique_moves[:20]  # Limit to top 20 strategic moves

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

        # Fast evaluation for early game
        stone_count = sum(1 for row in board for cell in row if cell != Player.EMPTY)
        if stone_count <= 6:
            return self.evaluate_early_game(board, player)

        # Use comprehensive pattern evaluation
        return self.evaluate_comprehensive_patterns(board, player)

    def evaluate_comprehensive_patterns(self, board: list[list[Player]], player: Player) -> float:
        """Comprehensive pattern evaluation using pattern manager."""
        score = 0
        opponent = self.get_opponent(player)

        # Check all positions for patterns using pattern manager
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] != Player.EMPTY:
                    # Evaluate patterns from this stone using pattern manager
                    stone_score = self.pattern_manager.evaluate_position_patterns(board, row, col, player)
                    if board[row][col] == player:
                        score += stone_score
                    else:
                        score -= stone_score

        # Check for critical threats that need immediate blocking
        critical_threats = self.pattern_manager.find_critical_threats(board, opponent)
        if critical_threats:
            score -= 100000  # Massive penalty for not blocking critical threats

        return score

    def evaluate_early_game(self, board: list[list[Player]], player: Player) -> float:
        """Fast evaluation for early game positions."""
        score = 0
        opponent = self.get_opponent(player)

        # Center control bonus
        center_bonus = 0
        center_positions = [(9, 9), (8, 9), (10, 9), (9, 8), (9, 10), (8, 8), (10, 10), (8, 10), (10, 8)]

        for row, col in center_positions:
            if board[row][col] == player:
                center_bonus += 100
            elif board[row][col] == opponent:
                center_bonus -= 100

        score += center_bonus

        # Simple pattern evaluation for early game
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == player:
                    # Check for simple patterns
                    score += self.evaluate_simple_pattern(board, row, col, player)
                elif board[row][col] == opponent:
                    score -= self.evaluate_simple_pattern(board, row, col, opponent)

        return score

    def evaluate_simple_pattern(self, board: list[list[Player]], row: int, col: int, player: Player) -> float:
        """Simple pattern evaluation for early game."""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            # Check 3 positions in each direction
            count = 1
            for i in range(1, 3):
                r, c = row + i * dr, col + i * dc
                if 0 <= r < len(board) and 0 <= c < len(board[0]) and board[r][c] == player:
                    count += 1
                else:
                    break

            # Simple scoring
            if count == 2:
                score += 10
            elif count == 3:
                score += 50

        return score

    def find_immediate_threats(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """Find positions where the player has immediate winning threats (4 in a row) or critical broken patterns."""
        threats = []

        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    # Check if placing a stone here would create a threat
                    board[row][col] = player
                    if self.check_win(board, player):
                        threats.append((row, col))
                    board[row][col] = Player.EMPTY

                    # Check for critical broken patterns that would be dangerous
                    if self.has_critical_broken_pattern(board, row, col, player):
                        threats.append((row, col))

        return threats

    def has_critical_broken_pattern(self, board: list[list[Player]], row: int, col: int, player: Player) -> bool:
        """Check if placing a stone at this position would create a critical broken pattern."""
        # Temporarily place the stone
        board[row][col] = player

        # Check all directions for critical patterns
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        has_critical = False

        for dr, dc in directions:
            # Check for broken three patterns in this direction
            if self.check_broken_three_in_direction(board, row, col, dr, dc, player):
                has_critical = True
                break

        # Remove the stone
        board[row][col] = Player.EMPTY

        return has_critical

    def check_broken_three_in_direction(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> bool:
        """Check if there's a broken three pattern in a specific direction."""
        # Check 4-position patterns that include this position
        for start in range(4):
            pattern = []
            valid = True

            for i in range(4):
                r, c = row + (i - start) * dr, col + (i - start) * dc
                if 0 <= r < len(board) and 0 <= c < len(board[0]):
                    pattern.append(board[r][c])
                else:
                    valid = False
                    break

            if valid and len(pattern) == 4:
                # Check if this is a critical broken pattern
                pattern_str = ""
                for cell in pattern:
                    if cell == player:
                        pattern_str += "P"
                    elif cell == Player.EMPTY:
                        pattern_str += "E"
                    else:
                        pattern_str += "O"

                # Critical patterns that are dangerous
                critical_patterns = ["PPEP", "PEPP", "EPPP", "PPPE"]
                if pattern_str in critical_patterns:
                    return True

        return False

    def find_critical_broken_threats(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """Find positions where the player has critical broken patterns that must be blocked."""
        threats = []

        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    # Check if this position would complete a critical broken pattern
                    if self.would_complete_critical_broken_pattern(board, row, col, player):
                        threats.append((row, col))

        return threats

    def would_complete_critical_broken_pattern(self, board: list[list[Player]], row: int, col: int, player: Player) -> bool:
        """Check if placing a stone here would complete a critical broken pattern."""
        # Check all directions for broken patterns
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            # Check for the specific pattern [1, 1, 0, 1] or [1, 0, 1, 1]
            if self.check_specific_broken_pattern(board, row, col, dr, dc, player):
                return True

        return False

    def check_specific_broken_pattern(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> bool:
        """Check for the specific broken three pattern [1, 1, 0, 1] or [1, 0, 1, 1]."""
        # Check 4-position patterns that include this position
        for start in range(4):
            pattern = []
            positions = []
            valid = True

            for i in range(4):
                r, c = row + (i - start) * dr, col + (i - start) * dc
                if 0 <= r < len(board) and 0 <= c < len(board[0]):
                    pattern.append(board[r][c])
                    positions.append((r, c))
                else:
                    valid = False
                    break

            if valid and len(pattern) == 4:
                # Check if this matches the critical broken pattern
                # Pattern should be [player, player, empty, player] or [player, empty, player, player]
                if pattern[0] == player and pattern[1] == player and pattern[2] == Player.EMPTY and pattern[3] == player:
                    return True
                if pattern[0] == player and pattern[1] == Player.EMPTY and pattern[2] == player and pattern[3] == player:
                    return True

        return False

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

        # Check for critical broken patterns that need immediate attention
        total_score += self.evaluate_broken_patterns(board, row, col, dr, dc, player)

        return total_score

    def evaluate_broken_patterns(self, board: list[list[Player]], row: int, col: int, dr: int, dc: int, player: Player) -> float:
        """Evaluate critical broken patterns that need immediate defensive attention."""
        score = 0

        # Check for broken three patterns: [opponent, opponent, empty, opponent] or [opponent, empty, opponent, opponent]
        # These are extremely dangerous and must be blocked immediately

        # Check 4-position patterns in this direction
        for start in range(4):
            pattern = []
            valid = True

            for i in range(4):
                r, c = row + (i - start) * dr, col + (i - start) * dc
            if 0 <= r < len(board) and 0 <= c < len(board[0]):
                pattern.append(board[r][c])
            else:
                valid = False
                break

            if valid and len(pattern) == 4:
                score += self.score_broken_pattern(pattern, player)

        return score

    def score_broken_pattern(self, pattern: list[Player], player: Player) -> float:
        """Score broken patterns that are critical for defense."""
        opponent = self.get_opponent(player)

        # Convert pattern to simple representation
        pattern_str = ""
        for cell in pattern:
            if cell == player:
                pattern_str += "P"
            elif cell == opponent:
                pattern_str += "O"
            else:
                pattern_str += "E"

        # Critical broken patterns that must be blocked
        critical_patterns = {
            "OOEO": 50000,  # [opponent, opponent, empty, opponent] - broken three
            "OEOO": 50000,  # [opponent, empty, opponent, opponent] - broken three
            "EOOO": 50000,  # [empty, opponent, opponent, opponent] - three with space
            "OOOE": 50000,  # [opponent, opponent, opponent, empty] - three with space
            "OOE": 10000,  # [opponent, opponent, empty] - broken two
            "EOO": 10000,  # [empty, opponent, opponent] - two with space
            "OEO": 5000,  # [opponent, empty, opponent] - broken two
        }

        # Check for critical defensive patterns
        if pattern_str in critical_patterns:
            return -critical_patterns[pattern_str]  # Negative because it's opponent's threat

        # Check for our own opportunities
        our_patterns = {
            "PPEP": 25000,  # [player, player, empty, player] - our broken three
            "PEPP": 25000,  # [player, empty, player, player] - our broken three
            "EPPP": 25000,  # [empty, player, player, player] - our three with space
            "PPPE": 25000,  # [player, player, player, empty] - our three with space
            "PPE": 5000,  # [player, player, empty] - our broken two
            "EPP": 5000,  # [empty, player, player] - our two with space
            "PEP": 2500,  # [player, empty, player] - our broken two
        }

        if pattern_str in our_patterns:
            return our_patterns[pattern_str]

        return 0

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
            return 10000  # Four in a row with one empty - immediate threat
        elif stone_count == 3 and empty_count == 2:
            return 1000  # Three in a row with two empty - strong threat
        elif stone_count == 2 and empty_count == 3:
            return 100  # Two in a row with three empty - potential threat
        elif stone_count == 1 and empty_count == 4:
            return 10  # One stone with four empty - weak potential
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
            return 10000  # Immediate threat
        elif count == 3:
            return 1000  # Strong threat
        elif count == 2:
            return 100  # Potential threat
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

        # Adaptive depth based on game phase
        game_phase = self.get_game_phase(board)
        max_depth_for_phase = self.get_max_depth_for_phase(game_phase)

        for depth in range(1, min(max_depth_for_phase, self.max_depth) + 1):
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
                    self.thinking_visualization.append(
                        {
                            "depth": depth,
                            "best_move": move,
                            "score": score,
                            "nodes_evaluated": self.nodes_evaluated,
                            "time_elapsed": time.time() - start_time,
                        }
                    )
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
            "current_search": self.current_search_info,
        }

        return best_move, best_score, stats

    def get_game_phase(self, board: list[list[Player]]) -> str:
        """Determine the current game phase based on number of stones."""
        stone_count = sum(1 for row in board for cell in row if cell != Player.EMPTY)

        if stone_count <= 4:
            return "opening"  # First few moves
        elif stone_count <= 20:
            return "early"  # Early game
        elif stone_count <= 50:
            return "mid"  # Mid game
        else:
            return "end"  # End game

    def get_max_depth_for_phase(self, phase: str) -> int:
        """Get maximum search depth based on game phase."""
        depth_limits = {
            "opening": 3,  # Very shallow for opening moves
            "early": 4,  # Shallow for early game
            "mid": 6,  # Medium depth for mid game
            "end": 8,  # Deeper for end game
        }
        return depth_limits.get(phase, 4)

    def board_to_string(self, board: list[list[Player]]) -> str:
        """Convert board to string for caching."""
        return "".join(str(cell.value) for row in board for cell in row)
