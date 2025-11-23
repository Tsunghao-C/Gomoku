"""
Minimax algorithm with optimizations for Gomoku AI.
Includes alpha-beta pruning, iterative deepening, transposition table, delta heuristic,
null move pruning, and late move reductions.
"""

import math
import time


class MinimaxAlgorithm:
    """
    Implements the minimax algorithm with various optimizations.
    """

    def __init__(self, config):
        # Extract algorithm settings from config
        algo_cfg = config["algorithm_settings"]
        heuristic_cfg = config["heuristic_settings"]

        self.max_depth = algo_cfg["max_depth"]
        self.time_limit = algo_cfg["time_limit"]
        self.win_score = heuristic_cfg["scores"]["win_score"]

        # Aspiration Window
        self.aspiration_delta = algo_cfg.get("aspiration_window_delta", 50000)

        # Optimization flags
        self.enable_null_move_pruning = algo_cfg.get("enable_null_move_pruning", True)
        self.null_move_reduction = algo_cfg.get("null_move_reduction", 2)
        self.enable_lmr = algo_cfg.get("enable_late_move_reductions", True)
        self.lmr_threshold = algo_cfg.get("lmr_threshold", 4)
        self.lmr_reduction = algo_cfg.get("lmr_reduction", 1)
        self.killer_moves_per_depth = algo_cfg.get("killer_moves_per_depth", 2)
        self.enable_killer_moves = algo_cfg.get("enable_killer_moves", True)

        # Adaptive starting depth settings
        self.adaptive_cfg = algo_cfg.get("adaptive_starting_depth", {})

        # Debug settings
        ai_cfg = config.get("ai_settings", {})
        debug_cfg = ai_cfg.get("debug", {})
        self.debug_verbose = debug_cfg.get("verbose", False)
        self.debug_terminal_states = debug_cfg.get("show_terminal_states", False)

        # Transposition table for caching positions
        self.transposition_table = {}

        # Search state
        self.time_limit_reached = False
        self.search_start_time = 0
        self.current_depth = 0

        # Killer moves heuristic
        self.killer_moves = {}  # {depth: [(r1,c1), (r2,c2)]}

        # History Heuristic
        # Stores score for moves that caused a beta cutoff
        # Key: (r, c), Value: score
        self.history_table = {}

    def clear_transposition_table(self):
        """Clears the transposition table."""
        self.transposition_table.clear()
        self.killer_moves.clear()
        # We usually keep history table between moves?
        # Or clear it? Some engines clear, some decay.
        # For simplicity and to adapt to new board state, let's clear or decay.
        # Let's clear for now to be safe against stale history.
        self.history_table.clear()

    def get_history_score(self, r, c):
        """Gets the history score for a move."""
        return self.history_table.get((r, c), 0)

    def reset_search_state(self):
        """Resets the search state for a new move."""
        self.time_limit_reached = False
        self.search_start_time = time.time()
        self.current_depth = 0

    def check_timeout(self):
        """Checks if the time limit has been reached."""
        if time.time() - self.search_start_time > self.time_limit:
            self.time_limit_reached = True
            return True
        return False

    def iterative_deepening_search(self, game_state, ai_player, initial_board_score,
                                   ordered_moves_func, make_move_func, undo_move_func,
                                   is_legal_func, check_terminal_func, num_moves=0):
        """
        Performs iterative deepening search with adaptive starting depth.

        Args:
            game_state: The current game state (board, captures, etc.)
            ai_player: The AI player number
            initial_board_score: The initial evaluation of the board
            ordered_moves_func: Function to get ordered moves
            make_move_func: Function to make a move and get delta
            undo_move_func: Function to undo a move
            is_legal_func: Function to check if a move is legal
            check_terminal_func: Function to check terminal state
            num_moves: Total number of moves played (for adaptive start)

        Returns:
            tuple: (best_move, best_score, search_depth_reached)
        """
        self.reset_search_state()

        best_move_so_far = None
        best_score_so_far = -math.inf
        depth_reached = 0

        # Always start from depth 1 for consistency, unless adaptive is enabled
        # This ensures:
        # 1. Transposition table is populated progressively
        # 2. Move ordering improves iteratively
        # 3. Minimax logic is consistent across all game phases
        # 4. Easier to debug and understand search behavior
        start_depth = 1

        if self.adaptive_cfg.get("enable", False):
            if num_moves < self.adaptive_cfg.get("early_game_moves", 8):
                start_depth = self.adaptive_cfg.get("early_game_depth", 1)
            elif num_moves < self.adaptive_cfg.get("mid_early_moves", 15):
                start_depth = self.adaptive_cfg.get("mid_early_depth", 3)
            elif num_moves < self.adaptive_cfg.get("mid_game_moves", 25):
                start_depth = self.adaptive_cfg.get("mid_game_depth", 4)
            else:
                start_depth = self.adaptive_cfg.get("late_game_depth", 5)

            # Ensure start_depth doesn't exceed max_depth
            start_depth = min(start_depth, self.max_depth)
            print(f"Adaptive starting depth enabled: starting at {start_depth}")

        print(f"Starting iterative deepening from depth {start_depth}")

        for depth in range(start_depth, self.max_depth + 1):
            self.current_depth = depth

            # Use aspiration windows for depths after the first
            if depth > start_depth and best_score_so_far != -math.inf:
                # Narrow window around previous score
                window = self.aspiration_delta
                alpha = best_score_so_far - window
                beta = best_score_so_far + window

                best_move_this_depth, best_score_this_depth = self.minimax_root(
                    game_state, ai_player, initial_board_score, depth,
                    ordered_moves_func, make_move_func, undo_move_func,
                    is_legal_func, check_terminal_func, alpha, beta
                )

                # If we failed outside the window, re-search with full window
                if (not self.time_limit_reached and
                    (best_score_this_depth <= alpha or best_score_this_depth >= beta)):
                    print(f"Aspiration window failed, re-searching depth {depth}")
                    best_move_this_depth, best_score_this_depth = self.minimax_root(
                        game_state, ai_player, initial_board_score, depth,
                        ordered_moves_func, make_move_func, undo_move_func,
                        is_legal_func, check_terminal_func, -math.inf, math.inf
                    )
            else:
                # First iteration or no previous score: use full window
                best_move_this_depth, best_score_this_depth = self.minimax_root(
                    game_state, ai_player, initial_board_score, depth,
                    ordered_moves_func, make_move_func, undo_move_func,
                    is_legal_func, check_terminal_func, -math.inf, math.inf
                )

            if self.time_limit_reached:
                print(f"Search at depth {depth} timed out. Using result from depth {depth_reached}.")
                break

            best_move_so_far = best_move_this_depth
            best_score_so_far = best_score_this_depth
            depth_reached = depth

            if self.debug_verbose:
                print(f"Completed depth {depth}. Best move: {best_move_so_far}, Score: {best_score_so_far:.0f}")

            if best_score_so_far >= self.win_score * 0.9:
                if self.debug_verbose:
                    print(f"Found a winning move at depth {depth}. Score: {best_score_so_far:.0f}")
                    print(f"  Move: {best_move_so_far}")
                break

            if self.check_timeout():
                print("Time limit reached after completing depth. Stopping.")
                break

        # Safety check: if no move found, return any legal move as last resort
        if best_move_so_far is None and depth_reached == 0:
            print("WARNING: No move found in time limit. Returning first legal move.")
            # Get first legal move from ordered moves
            board, captures, zobrist_hash = game_state
            ordered_moves = ordered_moves_func(board, captures, ai_player)
            for (r, c) in ordered_moves:
                is_legal, _ = is_legal_func(r, c, ai_player, board)
                if is_legal:
                    best_move_so_far = (r, c)
                    best_score_so_far = 0
                    print(f"Emergency fallback: returning {best_move_so_far}")
                    break

        return best_move_so_far, best_score_so_far, depth_reached

    def minimax_root(self, game_state, ai_player, current_board_score, depth,
                    ordered_moves_func, make_move_func, undo_move_func,
                    is_legal_func, check_terminal_func, alpha=-math.inf, beta=math.inf):
        """
        Root call of the minimax algorithm (maximizing player's turn).
        """
        board, captures, zobrist_hash = game_state
        best_score = -math.inf
        best_move = None

        ordered_moves = ordered_moves_func(board, captures, ai_player)

        if not ordered_moves:
            return (None, 0)

        for (r, c) in ordered_moves:
            if self.time_limit_reached:
                return best_move if best_move else None, best_score if best_move else 0

            is_legal, _ = is_legal_func(r, c, ai_player, board)
            if not is_legal:
                continue

            # Make move and get delta
            delta, captured_pieces, old_cap_count, new_hash = make_move_func(
                r, c, ai_player, board, captures, zobrist_hash
            )
            captures[ai_player] = old_cap_count + len(captured_pieces)

            # Check for immediate win
            # At root level (maximizing), this IS an immediate win - game would end here
            is_terminal = check_terminal_func(board, captures, ai_player, r, c)
            if is_terminal:
                print(f"  DEBUG minimax_root: Terminal state detected at move ({r}, {c})")
                print(f"    Player: {ai_player}, Captures: {captures}")
                score = self.win_score
            else:
                # Recursive minimax call
                score = self.minimax(
                    (board, captures, new_hash), depth - 1, alpha, beta, False,
                    current_board_score + delta, ai_player,
                    ordered_moves_func, make_move_func, undo_move_func,
                    is_legal_func, check_terminal_func
                )

            # Undo move
            undo_move_func(r, c, ai_player, board, captured_pieces, old_cap_count, captures, zobrist_hash)

            if self.time_limit_reached:
                return best_move if best_move else None, best_score if best_move else 0

            if score > best_score:
                best_score = score
                best_move = (r, c)

            alpha = max(alpha, best_score)
            if beta <= alpha:
                break

        return best_move, best_score

    def minimax(self, game_state, depth, alpha, beta, is_maximizing_player,
               current_score, ai_player, ordered_moves_func, make_move_func,
               undo_move_func, is_legal_func, check_terminal_func):
        """
        Recursive minimax algorithm with alpha-beta pruning, delta heuristic,
        null move pruning, and late move reductions.

        Args:
            game_state: Tuple of (board, captures, zobrist_hash)
            depth: Current search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            is_maximizing_player: Whether this is the maximizing player's turn
            current_score: The current evaluation score (updated via deltas)
            ai_player: The AI player number
            ordered_moves_func: Function to get ordered moves
            make_move_func: Function to make a move and get delta
            undo_move_func: Function to undo a move
            is_legal_func: Function to check if a move is legal
            check_terminal_func: Function to check terminal state

        Returns:
            int: The evaluation score
        """
        board, captures, zobrist_hash = game_state

        # Check for timeout periodically
        if depth % 4 == 0:
            if self.check_timeout():
                return current_score

        if self.time_limit_reached:
            return current_score

        # Check transposition table
        full_hash = hash((zobrist_hash, tuple(captures.items())))
        if full_hash in self.transposition_table:
            tt_score, tt_depth, tt_flag = self.transposition_table[full_hash]
            if tt_depth >= depth:
                if tt_flag == 'EXACT':
                    return tt_score
                elif tt_flag == 'LOWERBOUND':
                    alpha = max(alpha, tt_score)
                elif tt_flag == 'UPPERBOUND':
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        # Base case: leaf node
        if depth == 0:
            return current_score

        # ENHANCED: Null Move Pruning (only for non-critical positions)
        USE_NULL_MOVE = True
        NULL_MOVE_REDUCTION = 2

        if (USE_NULL_MOVE and depth >= 3 and not is_maximizing_player and
            abs(current_score) < self.win_score * 0.3):  # Not in critical position

            # Try a "null move" - opponent passes, we get to move again
            null_score = self.minimax(
                game_state, depth - 1 - NULL_MOVE_REDUCTION,
                alpha, beta, True,
                current_score, ai_player,
                ordered_moves_func, make_move_func, undo_move_func,
                is_legal_func, check_terminal_func
            )

            if null_score >= beta:
                return beta  # Fail-high cutoff

        # Determine current player
        player = ai_player if is_maximizing_player else (2 if ai_player == 1 else 1)

        ordered_moves = ordered_moves_func(board, captures, player)

        if not ordered_moves:
            return current_score

        # Maximizing player
        if is_maximizing_player:
            best_score = -math.inf
            move_number = 0
            flag = 'UPPERBOUND'  # Assume fail-low

            for (r, c) in ordered_moves:
                is_legal, _ = is_legal_func(r, c, player, board)
                if not is_legal:
                    continue

                move_number += 1

                # Make move and get delta
                delta, captured_pieces, old_cap_count, new_hash = make_move_func(
                    r, c, player, board, captures, zobrist_hash
                )
                captures[player] = old_cap_count + len(captured_pieces)

                is_terminal = check_terminal_func(board, captures, player, r, c)
                if is_terminal:
                    # Terminal state detected - this position wins the game
                    score = self.win_score
                else:
                    # ENHANCED: Late Move Reduction
                    reduction = 0
                    if self.enable_lmr and depth >= 3 and move_number > self.lmr_threshold and best_score > -self.win_score * 0.5:
                        reduction = self.lmr_reduction
                        # Increase reduction for very late moves?
                        if move_number > self.lmr_threshold * 2:
                            reduction += 1

                    score = self.minimax(
                        (board, captures, new_hash), depth - 1 - reduction,
                        alpha, beta, False,
                        current_score + delta, ai_player,
                        ordered_moves_func, make_move_func, undo_move_func,
                        is_legal_func, check_terminal_func
                    )

                    # Re-search if LMR found a good move
                    if reduction > 0 and score > alpha:
                        score = self.minimax(
                            (board, captures, new_hash), depth - 1,
                            alpha, beta, False,
                            current_score + delta, ai_player,
                            ordered_moves_func, make_move_func, undo_move_func,
                            is_legal_func, check_terminal_func
                        )

                # Undo move
                undo_move_func(r, c, player, board, captured_pieces, old_cap_count, captures, zobrist_hash)

                if self.time_limit_reached:
                    return current_score

                best_score = max(best_score, score)
                if best_score > alpha:
                    alpha = best_score
                    flag = 'EXACT'

                if beta <= alpha:
                    # Store killer move
                    if self.enable_killer_moves:
                        if depth not in self.killer_moves:
                            self.killer_moves[depth] = []
                        self.killer_moves[depth].append((r, c))
                        if len(self.killer_moves[depth]) > self.killer_moves_per_depth:
                            self.killer_moves[depth].pop(0)

                    # Update History Heuristic
                    # Bonus proportional to depth squared (deeper cutoffs are more valuable)
                    self.history_table[(r, c)] = self.history_table.get((r, c), 0) + depth * depth

                    flag = 'LOWERBOUND'
                    break

            self.transposition_table[full_hash] = (best_score, depth, flag)
            return best_score

        # Minimizing player
        else:
            best_score = math.inf
            move_number = 0
            flag = 'LOWERBOUND'  # Assume fail-high

            for (r, c) in ordered_moves:
                is_legal, _ = is_legal_func(r, c, player, board)
                if not is_legal:
                    continue

                move_number += 1

                # Make move and get delta
                delta, captured_pieces, old_cap_count, new_hash = make_move_func(
                    r, c, player, board, captures, zobrist_hash
                )
                captures[player] = old_cap_count + len(captured_pieces)

                is_terminal = check_terminal_func(board, captures, player, r, c)
                if is_terminal:
                    score = -self.win_score
                else:
                    # ENHANCED: Late Move Reduction
                    reduction = 0
                    if self.enable_lmr and depth >= 3 and move_number > self.lmr_threshold and best_score < self.win_score * 0.5:
                        reduction = self.lmr_reduction
                        if move_number > self.lmr_threshold * 2:
                            reduction += 1

                    score = self.minimax(
                        (board, captures, new_hash), depth - 1 - reduction,
                        alpha, beta, True,
                        current_score - delta, ai_player,
                        ordered_moves_func, make_move_func, undo_move_func,
                        is_legal_func, check_terminal_func
                    )

                    # Re-search if LMR found a good move
                    if reduction > 0 and score < beta:
                        score = self.minimax(
                            (board, captures, new_hash), depth - 1,
                            alpha, beta, True,
                            current_score - delta, ai_player,
                            ordered_moves_func, make_move_func, undo_move_func,
                            is_legal_func, check_terminal_func
                        )

                # Undo move
                undo_move_func(r, c, player, board, captured_pieces, old_cap_count, captures, zobrist_hash)

                if self.time_limit_reached:
                    return current_score

                best_score = min(best_score, score)
                if best_score < beta:
                    beta = best_score
                    flag = 'EXACT'

                if beta <= alpha:
                    # Store killer move
                    if self.enable_killer_moves:
                        if depth not in self.killer_moves:
                            self.killer_moves[depth] = []
                        self.killer_moves[depth].append((r, c))
                        if len(self.killer_moves[depth]) > self.killer_moves_per_depth:
                            self.killer_moves[depth].pop(0)

                    # Update History Heuristic
                    self.history_table[(r, c)] = self.history_table.get((r, c), 0) + depth * depth

                    flag = 'UPPERBOUND'
                    break

            self.transposition_table[full_hash] = (best_score, depth, flag)
            return best_score
