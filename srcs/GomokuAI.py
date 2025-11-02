"""
Gomoku AI module that coordinates the algorithm and heuristic evaluation.
"""

import time

from srcs.algorithm import MinimaxAlgorithm
from srcs.heuristic import BROKEN_FOUR, CAPTURE_SCORE, OPEN_THREE, WIN_SCORE, HeuristicEvaluator


class GomokuAI:
    """
    Manages AI decision-making, move generation, and evaluation.
    """

    def __init__(self, board_size, max_depth, time_limit, relevance_range):
        self.board_size = board_size
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.relevance_range = relevance_range

        # Initialize algorithm and heuristic
        self.algorithm = MinimaxAlgorithm(max_depth, time_limit, WIN_SCORE)
        self.heuristic = HeuristicEvaluator(board_size)

        # AI state
        self.ai_is_thinking = False
        self.current_search_depth = 0
        self.last_move_time = 0.0

    def get_best_move(self, board, captures, zobrist_hash, ai_player, win_by_captures,
                     game_logic):
        """
        Gets the best move for the AI using iterative deepening minimax.

        Args:
            board: The current board state
            captures: Dictionary of captures for each player
            zobrist_hash: Current Zobrist hash
            ai_player: The AI player number
            win_by_captures: Number of pairs needed to win
            game_logic: Reference to game logic functions

        Returns:
            tuple: (best_move, time_taken)
        """
        print(f"[{'Black' if ai_player == 1 else 'White'}] is thinking...")

        start_time = time.time()

        # Clear transposition table for new move
        self.algorithm.clear_transposition_table()

        # Calculate initial board score (only once)
        initial_board_score = self.heuristic.evaluate_board(
            board, captures, ai_player, win_by_captures
        )

        # Create wrapper functions for game logic
        def ordered_moves_wrapper(board, captures, player):
            return self.get_ordered_moves(board, captures, player, game_logic)

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

        # Perform iterative deepening search
        game_state = (board, captures, zobrist_hash)
        best_move, best_score, depth_reached = self.algorithm.iterative_deepening_search(
            game_state, ai_player, initial_board_score,
            ordered_moves_wrapper, make_move_wrapper, undo_move_wrapper,
            is_legal_wrapper, check_terminal_wrapper
        )

        time_taken = time.time() - start_time
        self.last_move_time = time_taken
        self.current_search_depth = 0

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
            (new_capture_count // 2 * CAPTURE_SCORE) -
            (old_capture_count // 2 * CAPTURE_SCORE)
        )

        # Final delta: MyGains - OpponentGains (weighted)
        delta = (delta_my_lines + delta_my_captures) - (delta_opp_lines * 1.1)

        return delta, captured_pieces, old_capture_count, new_hash

    def get_ordered_moves(self, board, captures, player, game_logic):
        """
        Gets moves ordered by their local score (for move ordering optimization).
        ENHANCED: Uses capture simulation to evaluate resulting board state.
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
        # Tier 4: Normal developing moves
        low_priority = []

        legal_moves = self.get_relevant_moves(board)

        for (r, c) in legal_moves:
            is_legal, _ = game_logic.is_legal_move(r, c, player, board)
            if not is_legal:
                continue

            # ENHANCED: Evaluate WITH capture simulation
            # This shows us what the board looks like AFTER captures
            my_score, my_capture_pairs = self._evaluate_with_captures(
                r, c, player, board
            )
            opp_score, opp_capture_pairs = self._evaluate_with_captures(
                r, c, opponent, board
            )

            # Add bonus for captures
            if my_capture_pairs > 0:
                my_score += my_capture_pairs * CAPTURE_SCORE

            # Check if this wins by captures
            if captures[player] + (my_capture_pairs * 2) >= win_by_captures * 2:
                my_score = WIN_SCORE * 0.95  # Almost as good as 5-in-a-row

            # Check if opponent could win by captures (defensive)
            if captures[opponent] + (opp_capture_pairs * 2) >= win_by_captures * 2:
                opp_score = WIN_SCORE * 0.95

            # Categorize by threat level
            if my_score >= WIN_SCORE * 0.5:
                winning_moves.append((my_score, (r, c)))
            elif opp_score >= WIN_SCORE * 0.5:
                blocking_moves.append((opp_score, (r, c)))
            elif my_score >= BROKEN_FOUR or opp_score >= BROKEN_FOUR:
                high_priority.append((max(my_score, opp_score * 1.1), (r, c)))
            elif my_score >= OPEN_THREE or opp_score >= OPEN_THREE:
                mid_priority.append((max(my_score, opp_score * 1.1), (r, c)))
            else:
                low_priority.append((my_score, (r, c)))

        # Sort each tier by score (highest first)
        winning_moves.sort(reverse=True)
        blocking_moves.sort(reverse=True)
        high_priority.sort(reverse=True)
        mid_priority.sort(reverse=True)
        low_priority.sort(reverse=True)

        # Combine tiers (best moves first)
        result = []
        for tier in [winning_moves, blocking_moves, high_priority, mid_priority, low_priority]:
            result.extend([move for score, move in tier])

        # Limit to top 40 moves
        return result[:40]

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
                - score: Heuristic score after simulating captures
                - num_capture_pairs: Number of pairs captured (for win-by-capture check)
        """
        opponent = 2 if player == 1 else 1

        # Step 1: Find what would be captured (read-only operation)
        capture_positions = self._get_capture_positions(r, c, player, board)

        if not capture_positions:
            # No captures, just evaluate normally (read-only)
            score = self.heuristic.score_lines_at(r, c, board, player, opponent)
            return score, 0

        # Step 2: Temporarily simulate the move (MODIFY board)
        board[r][c] = player
        for (cr, cc) in capture_positions:
            board[cr][cc] = 0  # Remove captured pieces

        # Step 3: Evaluate the resulting position
        score = self.heuristic.score_lines_at(r, c, board, player, opponent)

        # Step 4: RESTORE board to original state (CRITICAL!)
        board[r][c] = 0
        for (cr, cc) in capture_positions:
            board[cr][cc] = opponent

        # Return score and number of capture pairs
        num_pairs = len(capture_positions) // 2
        return score, num_pairs

    def get_relevant_moves(self, board):
        """
        Gets moves that are within RELEVANCE_RANGE of existing pieces.
        This dramatically reduces the branching factor.
        """
        relevant_moves = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] != 0:  # Found a piece
                    # Add all empty squares around it
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
