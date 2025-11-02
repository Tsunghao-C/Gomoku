"""
Gomoku AI module that coordinates the algorithm and heuristic evaluation.
"""

import copy
import time

from srcs.algorithm import MinimaxAlgorithm
from srcs.heuristic import CAPTURE_SCORE, WIN_SCORE, HeuristicEvaluator


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
        """
        moves_with_scores = []
        legal_moves = self.get_relevant_moves(board)

        # Copy captures for scoring
        captures_copy = captures.copy()

        for (r, c) in legal_moves:
            is_legal, _ = game_logic.is_legal_move(r, c, player, board)
            if not is_legal:
                continue

            # Score move on a copy of the board
            board_copy = copy.deepcopy(board)
            score = self.score_move_locally(
                r, c, player, board_copy, captures_copy, game_logic
            )
            moves_with_scores.append((score, (r, c)))

        # Sort by score (highest first)
        moves_with_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in moves_with_scores]

    def score_move_locally(self, r, c, player, board, captures, game_logic):
        """
        Quickly scores a move for move ordering.
        Uses a copy of the board for fast simulation.
        """
        opponent = 2 if player == 1 else 1

        # Fast simulation on board copy
        captured_pieces = game_logic.check_and_apply_captures(r, c, player, board)
        board[r][c] = player

        my_score = len(captured_pieces) * CAPTURE_SCORE
        opponent_score = 0

        my_score += self.heuristic.score_lines_at(r, c, board, player, opponent)
        opponent_score += self.heuristic.score_lines_at(r, c, board, opponent, player)

        return my_score - opponent_score * 1.1

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

