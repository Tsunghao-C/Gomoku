"""
Minimax algorithm with optimizations for Gomoku AI.
Includes alpha-beta pruning, iterative deepening, transposition table, and delta heuristic.
"""

import math
import time


class MinimaxAlgorithm:
    """
    Implements the minimax algorithm with various optimizations.
    """

    def __init__(self, max_depth, time_limit, win_score):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.win_score = win_score

        # Transposition table for caching positions
        self.transposition_table = {}

        # Search state
        self.time_limit_reached = False
        self.search_start_time = 0
        self.current_depth = 0

    def clear_transposition_table(self):
        """Clears the transposition table."""
        self.transposition_table.clear()

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
                                   is_legal_func, check_terminal_func):
        """
        Performs iterative deepening search.

        Args:
            game_state: The current game state (board, captures, etc.)
            ai_player: The AI player number
            initial_board_score: The initial evaluation of the board
            ordered_moves_func: Function to get ordered moves
            make_move_func: Function to make a move and get delta
            undo_move_func: Function to undo a move
            is_legal_func: Function to check if a move is legal
            check_terminal_func: Function to check terminal state

        Returns:
            tuple: (best_move, best_score, search_depth_reached)
        """
        self.reset_search_state()

        best_move_so_far = None
        best_score_so_far = -math.inf
        depth_reached = 0

        for depth in range(1, self.max_depth + 1):
            self.current_depth = depth

            best_move_this_depth, best_score_this_depth = self.minimax_root(
                game_state, ai_player, initial_board_score, depth,
                ordered_moves_func, make_move_func, undo_move_func,
                is_legal_func, check_terminal_func
            )

            if self.time_limit_reached:
                print(f"Search at depth {depth} timed out. Using result from depth {depth - 1}.")
                break

            best_move_so_far = best_move_this_depth
            best_score_so_far = best_score_this_depth
            depth_reached = depth

            print(f"Completed search to depth {depth}. Best move: {best_move_so_far}, Score: {best_score_so_far:.0f}")

            if best_score_so_far >= self.win_score:
                print("Found a winning move. Stopping search.")
                break

            if self.check_timeout():
                print("Time limit reached after completing depth. Stopping.")
                break

        return best_move_so_far, best_score_so_far, depth_reached

    def minimax_root(self, game_state, ai_player, current_board_score, depth,
                    ordered_moves_func, make_move_func, undo_move_func,
                    is_legal_func, check_terminal_func):
        """
        Root call of the minimax algorithm (maximizing player's turn).
        """
        board, captures, zobrist_hash = game_state
        best_score = -math.inf
        best_move = None

        alpha = -math.inf
        beta = math.inf

        ordered_moves = ordered_moves_func(board, captures, ai_player)

        if not ordered_moves:
            return (None, 0)

        for (r, c) in ordered_moves:
            if self.time_limit_reached:
                return None, 0

            is_legal, _ = is_legal_func(r, c, ai_player, board)
            if not is_legal:
                continue

            # Make move and get delta
            delta, captured_pieces, old_cap_count, new_hash = make_move_func(
                r, c, ai_player, board, captures, zobrist_hash
            )
            captures[ai_player] = old_cap_count + len(captured_pieces)

            # Check for immediate win
            if check_terminal_func(board, captures, ai_player, r, c):
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
                return None, 0

            if score > best_score:
                best_score = score
                best_move = (r, c)

            alpha = max(alpha, best_score)

        return best_move, best_score

    def minimax(self, game_state, depth, alpha, beta, is_maximizing_player,
               current_score, ai_player, ordered_moves_func, make_move_func,
               undo_move_func, is_legal_func, check_terminal_func):
        """
        Recursive minimax algorithm with alpha-beta pruning and delta heuristic.

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
                return 0

        if self.time_limit_reached:
            return 0

        # Check transposition table
        full_hash = hash((zobrist_hash, tuple(captures.items())))
        if full_hash in self.transposition_table:
            tt_score, tt_depth = self.transposition_table[full_hash]
            if tt_depth >= depth:
                return tt_score

        # Base case: leaf node
        if depth == 0:
            return current_score

        # Determine current player
        player = ai_player if is_maximizing_player else (2 if ai_player == 1 else 1)

        ordered_moves = ordered_moves_func(board, captures, player)

        if not ordered_moves:
            return 0

        # Maximizing player
        if is_maximizing_player:
            best_score = -math.inf
            for (r, c) in ordered_moves:
                is_legal, _ = is_legal_func(r, c, player, board)
                if not is_legal:
                    continue

                # Make move and get delta
                delta, captured_pieces, old_cap_count, new_hash = make_move_func(
                    r, c, player, board, captures, zobrist_hash
                )
                captures[player] = old_cap_count + len(captured_pieces)

                if check_terminal_func(board, captures, player, r, c):
                    score = self.win_score
                else:
                    score = self.minimax(
                        (board, captures, new_hash), depth - 1, alpha, beta, False,
                        current_score + delta, ai_player,
                        ordered_moves_func, make_move_func, undo_move_func,
                        is_legal_func, check_terminal_func
                    )

                # Undo move
                undo_move_func(r, c, player, board, captured_pieces, old_cap_count, captures, zobrist_hash)

                if self.time_limit_reached:
                    return 0

                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break

            self.transposition_table[full_hash] = (best_score, depth)
            return best_score

        # Minimizing player
        else:
            best_score = math.inf
            for (r, c) in ordered_moves:
                is_legal, _ = is_legal_func(r, c, player, board)
                if not is_legal:
                    continue

                # Make move and get delta
                delta, captured_pieces, old_cap_count, new_hash = make_move_func(
                    r, c, player, board, captures, zobrist_hash
                )
                captures[player] = old_cap_count + len(captured_pieces)

                if check_terminal_func(board, captures, player, r, c):
                    score = -self.win_score
                else:
                    # When minimizer moves, delta is subtracted from AI's perspective
                    score = self.minimax(
                        (board, captures, new_hash), depth - 1, alpha, beta, True,
                        current_score - delta, ai_player,
                        ordered_moves_func, make_move_func, undo_move_func,
                        is_legal_func, check_terminal_func
                    )

                # Undo move
                undo_move_func(r, c, player, board, captured_pieces, old_cap_count, captures, zobrist_hash)

                if self.time_limit_reached:
                    return 0

                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break

            self.transposition_table[full_hash] = (best_score, depth)
            return best_score
