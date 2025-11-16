"""
Gomoku AI module that coordinates the algorithm and heuristic evaluation.
"""

import time

from srcs.algorithm import MinimaxAlgorithm
from srcs.heuristic import HeuristicEvaluator


class GomokuAI:
    """
    Manages AI decision-making, move generation, and evaluation.
    """

    def __init__(self, config):
        # Store configuration
        self.config = config

        # Parse configuration sections
        game_cfg = config["game_settings"]
        algo_cfg = config["algorithm_settings"]
        ai_cfg = config["ai_settings"]
        heuristic_cfg = config["heuristic_settings"]

        # Extract constants
        self.board_size = game_cfg["board_size"]
        self.max_depth = algo_cfg["max_depth"]
        self.time_limit = algo_cfg["time_limit"]
        self.relevance_range = ai_cfg["relevance_range"]

        # Heuristic scores
        self.WIN_SCORE = heuristic_cfg["scores"]["win_score"]
        self.BROKEN_FOUR = heuristic_cfg["scores"]["broken_four"]
        self.CAPTURE_SCORE = heuristic_cfg["scores"]["capture_score"]
        self.OPEN_THREE = heuristic_cfg["scores"]["open_three"]

        # Initialize algorithm and heuristic with config
        self.algorithm = MinimaxAlgorithm(config)
        self.heuristic = HeuristicEvaluator(config)

        # AI state
        self.ai_is_thinking = False
        self.current_search_depth = 0
        self.last_move_time = 0.0
        self.last_depth_reached = 0

    def get_best_move(self, board, captures, zobrist_hash, ai_player, win_by_captures,
                     game_logic, num_moves):
        """
        Gets the best move for the AI using iterative deepening minimax.

        Args:
            board: The current board state
            captures: Dictionary of captures for each player
            zobrist_hash: Current Zobrist hash
            ai_player: The AI player number
            win_by_captures: Number of pairs needed to win
            game_logic: Reference to game logic functions
            num_moves: Total number of moves played so far

        Returns:
            tuple: (best_move, time_taken)
        """
        turn_num = (num_moves + 2) // 2
        print(f"[{'Black' if ai_player == 1 else 'White'}] is thinking... (Turn {turn_num}, Move #{num_moves + 1})")

        start_time = time.time()

        # Clear transposition table for new move
        self.algorithm.clear_transposition_table()

        # Calculate initial board score (only once)
        initial_board_score = self.heuristic.evaluate_board(
            board, captures, ai_player, win_by_captures
        )

        # Create wrapper functions for game logic
        def ordered_moves_wrapper(board, captures, player):
            return self.get_ordered_moves(board, captures, player, game_logic, num_moves)

        def make_move_wrapper(r, c, player, board, captures, zobrist_hash):
            return self.make_move_and_get_delta(
                r, c, player, board, captures, zobrist_hash,
                game_logic, win_by_captures
            )

        def undo_move_wrapper(r, c, player, board, captured_pieces,
                            old_cap_count, captures, zobrist_hash):
            return game_logic.undo_move(
                r, c, player, board, captured_pieces, old_cap_count,
                captures, zobrist_hash
            )

        def is_legal_wrapper(r, c, player, board):
            return game_logic.is_legal_move(r, c, player, board)

        def check_terminal_wrapper(board, captures, player, r, c):
            return game_logic.check_terminal_state(
                board, captures, player, r, c, win_by_captures
            )

        # Perform iterative deepening search with adaptive starting depth
        game_state = (board, captures, zobrist_hash)
        best_move, best_score, depth_reached = self.algorithm.iterative_deepening_search(
            game_state, ai_player, initial_board_score,
            ordered_moves_wrapper, make_move_wrapper, undo_move_wrapper,
            is_legal_wrapper, check_terminal_wrapper, num_moves
        )

        time_taken = time.time() - start_time
        self.last_move_time = time_taken
        self.last_depth_reached = depth_reached
        self.current_search_depth = 0

        print(f"Search completed: depth={depth_reached}, time={time_taken:.2f}s")

        return best_move, time_taken

    def make_move_and_get_delta(self, r, c, player, board, captures, zobrist_hash,
                               game_logic, win_by_captures):
        """
        Makes a move and calculates the delta (change in evaluation).
        This is the core of the Delta Heuristic optimization.

        Returns:
            tuple: (delta, captured_pieces, old_capture_count, new_zobrist_hash)
        """
        opponent = 2 if player == 1 else 1

        # Get score BEFORE the move
        score_before_me = self.heuristic.score_lines_at(r, c, board, player, opponent)
        score_before_opp = self.heuristic.score_lines_at(r, c, board, opponent, player)

        # Make the move
        captured_pieces, new_hash = game_logic.make_move(
            r, c, player, board, zobrist_hash
        )

        # Get score AFTER the move
        score_after_me = self.heuristic.score_lines_at(r, c, board, player, opponent)
        score_after_opp = self.heuristic.score_lines_at(r, c, board, opponent, player)

        # Calculate delta
        delta_my_lines = score_after_me - score_before_me
        delta_opp_lines = score_after_opp - score_before_opp

        # Delta from captures
        old_capture_count = captures[player]
        new_capture_count = old_capture_count + len(captured_pieces)
        delta_my_captures = (
            (new_capture_count // 2 * self.CAPTURE_SCORE) -
            (old_capture_count // 2 * self.CAPTURE_SCORE)
        )

        # Final delta: MyGains - OpponentGains (weighted)
        delta = (delta_my_lines + delta_my_captures) - (delta_opp_lines * 1.1)

        return delta, captured_pieces, old_capture_count, new_hash

    def get_ordered_moves(self, board, captures, player, game_logic, num_moves):
        """
        Gets moves ordered by their local score (for move ordering optimization).
        ENHANCED: Uses capture simulation and adaptive move limits.
        """
        opponent = 2 if player == 1 else 1
        win_by_captures = 5  # Standard Gomoku rule

        # Tier 1: Immediate threats (check first)
        winning_moves = []
        blocking_moves = []
        # Tier 2: High-value tactical moves
        high_priority = []
        # Tier 3: Good positional moves
        mid_priority = []
        # Tier 4: Normal developing moves (only used early game)
        low_priority = []

        # ENHANCED: Use windowed move generation for better performance
        legal_moves = self.get_relevant_moves_windowed(board, num_moves)

        for (r, c) in legal_moves:
            is_legal, _ = game_logic.is_legal_move(r, c, player, board)
            if not is_legal:
                continue

            # ENHANCED: Evaluate WITH capture simulation
            my_score, my_capture_pairs = self._evaluate_with_captures(
                r, c, player, board
            )
            opp_score, opp_capture_pairs = self._evaluate_with_captures(
                r, c, opponent, board
            )

            # Add bonus for captures
            if my_capture_pairs > 0:
                my_score += my_capture_pairs * self.CAPTURE_SCORE

            # Check if this wins by captures
            if captures[player] + (my_capture_pairs * 2) >= win_by_captures * 2:
                my_score = self.WIN_SCORE * 0.95

            # Check if opponent could win by captures (defensive)
            if captures[opponent] + (opp_capture_pairs * 2) >= win_by_captures * 2:
                opp_score = self.WIN_SCORE * 0.95

            # Categorize by threat level
            if my_score >= self.WIN_SCORE * 0.5:
                winning_moves.append((my_score, (r, c)))
            elif opp_score >= self.WIN_SCORE * 0.5:
                blocking_moves.append((opp_score, (r, c)))
            elif my_score >= self.BROKEN_FOUR or opp_score >= self.BROKEN_FOUR:
                high_priority.append((max(my_score, opp_score * 1.1), (r, c)))
            elif my_score >= self.OPEN_THREE or opp_score >= self.OPEN_THREE:
                mid_priority.append((max(my_score, opp_score * 1.1), (r, c)))
            else:
                low_priority.append((my_score, (r, c)))

        # Sort each tier by score (highest first)
        winning_moves.sort(reverse=True)
        blocking_moves.sort(reverse=True)
        high_priority.sort(reverse=True)
        mid_priority.sort(reverse=True)
        low_priority.sort(reverse=True)

        # ENHANCED: Aggressive move limiting based on game phase
        if winning_moves:
            # If we have winning moves, only consider those
            return [move for score, move in winning_moves[:5]]

        if blocking_moves:
            # Must block, but also consider our threats
            result = [move for score, move in blocking_moves[:6]]
            result.extend([move for score, move in high_priority[:6]])
            return result[:12]

        # Adaptive max moves based on game phase
        if num_moves < 10:
            max_moves = 18  # Early game: explore more
        elif num_moves < 25:
            max_moves = 14  # Mid game: focused
        else:
            max_moves = 12  # Late game: very focused

        # Combine tiers with limits
        result = []
        result.extend([move for score, move in high_priority[:max_moves // 2]])
        result.extend([move for score, move in mid_priority[:max_moves // 3]])

        # Always include some low priority moves if we don't have enough
        if len(result) < max_moves // 2:
            result.extend([move for score, move in low_priority[:max_moves]])

        # Ensure we always return moves if any exist
        if not result:
            # Fallback: combine all tiers and return best moves
            all_moves = (winning_moves + blocking_moves + high_priority +
                        mid_priority + low_priority)
            if all_moves:
                all_moves.sort(reverse=True)
                result = [move for score, move in all_moves[:max_moves]]

        return result[:max_moves]

    def get_bounding_box(self, board, padding=3):
        """
        Find the minimal rectangle containing all pieces, plus padding.
        Returns: (min_row, max_row, min_col, max_col)
        """
        min_r, max_r = self.board_size, -1
        min_c, max_c = self.board_size, -1

        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] != 0:
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)

        # Add padding
        min_r = max(0, min_r - padding)
        max_r = min(self.board_size - 1, max_r + padding)
        min_c = max(0, min_c - padding)
        max_c = min(self.board_size - 1, max_c + padding)

        return (min_r, max_r, min_c, max_c)

    def get_relevant_moves_windowed(self, board, num_moves):
        """
        Optimized move generation using bounding box.
        Uses adaptive strategy based on game phase.
        """
        relevant_moves = set()

        # Early game (< 12 moves): Use full board with small radius
        if num_moves < 12:
            return self.get_relevant_moves(board)

        # Mid-late game: Use bounding box for efficiency
        padding = 3 if num_moves < 25 else 2
        min_r, max_r, min_c, max_c = self.get_bounding_box(board, padding)

        # Only scan within bounding box
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                if board[r][c] != 0:
                    # Add empty squares around pieces
                    for dr in range(-self.relevance_range, self.relevance_range + 1):
                        for dc in range(-self.relevance_range, self.relevance_range + 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (min_r <= nr <= max_r and
                                min_c <= nc <= max_c and
                                board[nr][nc] == 0):
                                relevant_moves.add((nr, nc))

        return list(relevant_moves)

    def _get_capture_positions(self, r, c, player, board):
        """
        Get positions that would be captured by placing a piece at (r, c).
        Returns list of (row, col) tuples to be captured.
        Does NOT modify the board.
        """
        opponent = 2 if player == 1 else 1
        captured = []

        # Check all 8 directions for capture pattern: P-O-O-P
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1),
                       (0, -1), (-1, 0), (-1, -1), (-1, 1)]:
            nr1, nc1 = r + dr, c + dc
            nr2, nc2 = r + dr * 2, c + dc * 2
            nr3, nc3 = r + dr * 3, c + dc * 3

            if (0 <= nr3 < self.board_size and 0 <= nc3 < self.board_size):
                if (board[nr1][nc1] == opponent and
                    board[nr2][nc2] == opponent and
                    board[nr3][nc3] == player):
                    captured.append((nr1, nc1))
                    captured.append((nr2, nc2))

        return captured

    def _evaluate_with_captures(self, r, c, player, board):
        """
        Evaluate a move INCLUDING the effects of captures.
        Uses make/undo pattern: temporarily modifies board then restores it.

        Returns:
            tuple: (score, num_capture_pairs)
        """
        opponent = 2 if player == 1 else 1

        # Step 1: Find what would be captured
        capture_positions = self._get_capture_positions(r, c, player, board)

        if not capture_positions:
            # No captures, just evaluate normally
            score = self.heuristic.score_lines_at(r, c, board, player, opponent)
            return score, 0

        # Step 2: Temporarily simulate the move
        board[r][c] = player
        for (cr, cc) in capture_positions:
            board[cr][cc] = 0

        # Step 3: Evaluate the resulting position
        score = self.heuristic.score_lines_at(r, c, board, player, opponent)

        # Step 4: RESTORE board to original state
        board[r][c] = 0
        for (cr, cc) in capture_positions:
            board[cr][cc] = opponent

        # Return score and number of capture pairs
        num_pairs = len(capture_positions) // 2
        return score, num_pairs

    def get_relevant_moves(self, board):
        """
        Gets moves that are within RELEVANCE_RANGE of existing pieces.
        Original implementation for early game.
        """
        relevant_moves = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] != 0:
                    for dr in range(-self.relevance_range, self.relevance_range + 1):
                        for dc in range(-self.relevance_range, self.relevance_range + 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.board_size and
                                0 <= nc < self.board_size and
                                board[nr][nc] == 0):
                                relevant_moves.add((nr, nc))
        return list(relevant_moves)
