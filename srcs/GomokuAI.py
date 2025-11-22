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

        # Heuristic scores (for move ordering)
        self.WIN_SCORE = heuristic_cfg["scores"]["win_score"]
        self.BROKEN_FOUR = heuristic_cfg["scores"]["broken_four"]
        self.CAPTURE_SCORE = heuristic_cfg["scores"]["capture_score"]
        self.OPEN_THREE = heuristic_cfg["scores"]["open_three"]
        self.OPEN_TWO = heuristic_cfg["scores"]["open_two"]

        # Debug settings
        debug_cfg = ai_cfg.get("debug", {})
        self.debug_verbose = debug_cfg.get("verbose", False)
        self.debug_critical_moves = debug_cfg.get("show_critical_moves", False)
        self.debug_move_scores = debug_cfg.get("show_move_scores", False)
        self.debug_move_categories = debug_cfg.get("show_move_categories", False)

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

        if self.debug_verbose:
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

    def _find_critical_moves(self, board, player):
        """
        Find critical moves: positions that complete or block 4-in-a-row.
        These moves MUST always be considered regardless of windowing.

        Returns:
            tuple: (winning_positions, blocking_positions)
        """
        winning_positions = set()
        blocking_positions = set()

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == 0:
                    continue

                current_player = board[r][c]

                # Check all 4 directions for potential 4-in-a-row
                for dr, dc in directions:
                    count = 1
                    empty_positions = []

                    # Look forward: count consecutive stones, note first empty
                    nr, nc = r + dr, c + dc
                    found_empty_forward = False
                    for _ in range(4):
                        if not (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                            break
                        if board[nr][nc] == current_player:
                            count += 1
                        elif board[nr][nc] == 0 and not found_empty_forward:
                            # Only add the FIRST empty square (adjacent to the run)
                            empty_positions.append((nr, nc))
                            found_empty_forward = True
                            break  # Stop after first empty
                        else:
                            break  # Hit opponent or second empty
                        nr += dr
                        nc += dc

                    # Look backward: count consecutive stones, note first empty
                    nr, nc = r - dr, c - dc
                    found_empty_backward = False
                    for _ in range(4):
                        if not (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                            break
                        if board[nr][nc] == current_player:
                            count += 1
                        elif board[nr][nc] == 0 and not found_empty_backward:
                            # Only add the FIRST empty square (adjacent to the run)
                            empty_positions.append((nr, nc))
                            found_empty_backward = True
                            break  # Stop after first empty
                        else:
                            break  # Hit opponent or second empty
                        nr -= dr
                        nc -= dc

                    # If 4 in a row with at least 1 empty spot, ALL empties are critical
                    # This handles:
                    # - O-X-X-X-X-E (1 empty, blocked on one side)
                    # - E-X-X-X-X-E (2 empties, open on both sides - BOTH are critical!)
                    if count == 4 and len(empty_positions) >= 1:
                        for critical_pos in empty_positions:
                            if current_player == player:
                                winning_positions.add(critical_pos)
                            else:
                                blocking_positions.add(critical_pos)

        return list(winning_positions), list(blocking_positions)

    def get_ordered_moves(self, board, captures, player, game_logic, num_moves):
        """
        Gets moves ordered by their local score (for move ordering optimization).
        OPTIMIZED: Uses static evaluation for initial sorting, simulating captures only when needed.
        """
        opponent = 2 if player == 1 else 1

        # CRITICAL: Always find moves that complete or block 4-in-a-row
        winning_positions, blocking_positions = self._find_critical_moves(board, player)

        # Get legal moves
        legal_moves = self.get_relevant_moves_windowed(board, num_moves)

        # Add critical moves to ensure they're evaluated
        critical_moves = set(winning_positions + blocking_positions)
        legal_moves_set = set(legal_moves)
        legal_moves_set.update(critical_moves)
        legal_moves = list(legal_moves_set)

        # Tier lists
        winning_moves = []
        blocking_moves = []
        high_priority = []
        mid_priority = []
        low_priority = []

        for (r, c) in legal_moves:
            # Fast legality check
            if board[r][c] != 0:
                continue

            # For the static sort, we check legality but skip double-three for now if expensive?
            # Actually, double-three check is relatively fast with new numeric patterns.
            # But maybe we can defer it? No, better to filter illegal moves early.
            is_legal, _ = game_logic.is_legal_move(r, c, player, board)
            if not is_legal:
                continue

            # STATIC EVALUATION (Lighter Heuristic)
            # Instead of simulating captures, just score the position as if we placed a stone.
            # This ignores capture effects on score, but is much faster.

            # Score for ME (Offense)
            # We temporarily place the stone to score lines, but using a helper that doesn't modify board?
            # heuristic.score_lines_at reads the board.
            # We can just pretend the board has the piece.
            board[r][c] = player
            score_attack = self.heuristic.score_lines_at(r, c, board, player, opponent)
            board[r][c] = 0 # Restore

            # Score for OPPONENT (Defense/Blocking)
            # If opponent played here, how good would it be for them?
            board[r][c] = opponent
            score_defend = self.heuristic.score_lines_at(r, c, board, opponent, player)
            board[r][c] = 0 # Restore

            # Estimate capture potential (fast check)
            # Just check if this move captures anything
            capture_score = 0
            # Only do full capture check if it looks promising or critical?
            # For now, let's do a quick check.
            # _get_capture_positions is reasonably fast (8 directions, simple checks)
            captures_possible = self._get_capture_positions(r, c, player, board)
            if captures_possible:
                capture_score = len(captures_possible) // 2 * self.CAPTURE_SCORE

            # Combined Score
            # Attack score + Blocking score (weighted) + Capture bonus
            total_score = score_attack + score_defend + capture_score

            # Categorize
            if (r, c) in winning_positions:
                winning_moves.append((total_score, (r, c)))
            elif (r, c) in blocking_positions:
                blocking_moves.append((total_score, (r, c)))
            elif score_attack >= self.OPEN_THREE or score_defend >= self.OPEN_THREE:
                high_priority.append((total_score, (r, c)))
            elif score_attack >= self.OPEN_TWO or score_defend >= self.OPEN_TWO:
                mid_priority.append((total_score, (r, c)))
            else:
                low_priority.append((total_score, (r, c)))

        # Sort tiers
        winning_moves.sort(reverse=True)
        blocking_moves.sort(reverse=True)
        high_priority.sort(reverse=True)
        mid_priority.sort(reverse=True)
        low_priority.sort(reverse=True)

        # Adaptive Limits
        if winning_moves:
            return [move for score, move in winning_moves] # All winning moves

        # If we have blocking moves, prioritize them but include some attacks
        if blocking_moves:
            result = [move for score, move in blocking_moves[:6]]
            result.extend([move for score, move in high_priority[:4]])
            return result[:10]

        if num_moves < 10:
            max_moves = 18
        elif num_moves < 25:
            max_moves = 14
        else:
            max_moves = 12

        result = []
        result.extend([move for score, move in high_priority])

        if len(result) < max_moves:
            result.extend([move for score, move in mid_priority])

        if len(result) < max_moves:
            result.extend([move for score, move in low_priority])

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

        # Special case: empty board (first move)
        # Return center and nearby positions
        board_has_pieces = False
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] != 0:
                    board_has_pieces = True
                    break
            if board_has_pieces:
                break

        if not board_has_pieces:
            # Return center region for first move
            center = self.board_size // 2
            for r in range(max(0, center - 2), min(self.board_size, center + 3)):
                for c in range(max(0, center - 2), min(self.board_size, center + 3)):
                    relevant_moves.add((r, c))
            return list(relevant_moves)

        # Normal case: find moves around existing pieces
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
