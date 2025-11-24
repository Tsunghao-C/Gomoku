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
            return self.get_ordered_moves(
                board, captures, player, game_logic, num_moves, win_by_captures
            )

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

        algo_cfg = self.config["algorithm_settings"]
        if algo_cfg.get("enable_iterative_deepening", True):
            best_move, best_score, depth_reached = self.algorithm.iterative_deepening_search(
                game_state, ai_player, initial_board_score,
                ordered_moves_wrapper, make_move_wrapper, undo_move_wrapper,
                is_legal_wrapper, check_terminal_wrapper, num_moves
            )
        else:
            # Fixed depth search
            print(f"Iterative deepening disabled. Searching directly at depth {self.max_depth}")
            best_move, best_score = self.algorithm.minimax_root(
                game_state, ai_player, initial_board_score, self.max_depth,
                ordered_moves_wrapper, make_move_wrapper, undo_move_wrapper,
                is_legal_wrapper, check_terminal_wrapper
            )
            depth_reached = self.max_depth

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
        is_critical_me = captures[player] >= (win_by_captures * 2 - 2)
        is_critical_opp = captures[opponent] >= (win_by_captures * 2 - 2)

        score_before_me = self.heuristic.score_lines_at(r, c, board, player, opponent, is_critical_me)
        score_before_opp = self.heuristic.score_lines_at(r, c, board, opponent, player, is_critical_opp)

        # Make the move
        captured_pieces, new_hash = game_logic.make_move(
            r, c, player, board, zobrist_hash
        )

        # Get score AFTER the move
        score_after_me = self.heuristic.score_lines_at(r, c, board, player, opponent, is_critical_me)
        score_after_opp = self.heuristic.score_lines_at(r, c, board, opponent, player, is_critical_opp)

        # Calculate delta
        delta_my_lines = score_after_me - score_before_me
        delta_opp_lines = score_after_opp - score_before_opp

        # Correction for captured stones:
        # Removing opponent stones changes the score of lines passing through them.
        # We need to subtract the old score of those lines (where opponent had a stone)
        # and add the new score (where it's empty).
        delta_captured_correction = 0

        if captured_pieces:
            # To acturally reconstruct the "Before" state properly for patterns like 5-in-a-row,
            # we must restore ALL captured stones at once.
            # If we only restore one, a 5-in-a-row might look like a broken 4, which has a totally different score.

            # 1. Restore ALL captured stones
            for (cr, cc) in captured_pieces:
                cap_idx = cr * self.board_size + cc
                board[cap_idx] = opponent

            # 2. Calculate "Before" score for all captured stones
            # We sum the score contributions. Note that this might double-count the shared axis line,
            # but that's consistent with how we will calculate the "After" score below.
            score_caps_before = 0
            for (cr, cc) in captured_pieces:
                score_caps_before += self.heuristic.score_lines_at(cr, cc, board, opponent, player, is_critical_opp)

            # 3. Remove ALL captured stones (Re-empty)
            for (cr, cc) in captured_pieces:
                cap_idx = cr * self.board_size + cc
                board[cap_idx] = 0

            # 4. Calculate "After" score for all captured stones (now empty)
            score_caps_after = 0
            for (cr, cc) in captured_pieces:
                score_caps_after += self.heuristic.score_lines_at(cr, cc, board, opponent, player, is_critical_opp)

            # 5. Delta
            delta_captured_correction = score_caps_after - score_caps_before

        # Delta from captures count (Bonus)
        old_capture_count = captures[player]
        new_capture_count = old_capture_count + len(captured_pieces)
        delta_my_captures = (
            (new_capture_count // 2 * self.CAPTURE_SCORE) -
            (old_capture_count // 2 * self.CAPTURE_SCORE)
        )

        # Final delta: MyGains - OpponentGains (weighted)
        # delta_opp_lines tracks change in opponent score around my NEW stone.
        # delta_captured_correction tracks change in opponent score around CAPTURED stones.

        total_opp_delta = delta_opp_lines + delta_captured_correction

        delta = (delta_my_lines + delta_my_captures) - (total_opp_delta * 1.1)

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
                idx = r * self.board_size + c
                if board[idx] == 0:
                    continue

                current_player = board[idx]

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
                        n_idx = nr * self.board_size + nc
                        if board[n_idx] == current_player:
                            count += 1
                        elif board[n_idx] == 0 and not found_empty_forward:
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
                        n_idx = nr * self.board_size + nc
                        if board[n_idx] == current_player:
                            count += 1
                        elif board[n_idx] == 0 and not found_empty_backward:
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

    def get_ordered_moves(self, board, captures, player, game_logic, num_moves, win_by_captures=5):
        """
        Gets moves ordered by their local score (for move ordering optimization).
        OPTIMIZED: Uses static evaluation for initial sorting, simulating captures only when needed.
        """
        opponent = 2 if player == 1 else 1

        # Check critical status for both players
        is_critical_attack = captures[player] >= (win_by_captures * 2 - 2)
        is_critical_defend = captures[opponent] >= (win_by_captures * 2 - 2)

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
            idx = r * self.board_size + c
            if board[idx] != 0:
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
            board[idx] = player
            score_attack = self.heuristic.score_lines_at(r, c, board, player, opponent, is_critical_attack)
            board[idx] = 0 # Restore

            # Score for OPPONENT (Defense/Blocking)
            # If opponent played here, how good would it be for them?
            board[idx] = opponent
            score_defend = self.heuristic.score_lines_at(r, c, board, opponent, player, is_critical_defend)
            board[idx] = 0 # Restore

            # Estimate capture potential (fast check)
            capture_score = 0

            # 1. Does this move allow ME to capture?
            captures_by_me = self._get_capture_positions(r, c, player, board)
            if captures_by_me:
                if is_critical_attack:
                    # This capture wins the game!
                    capture_score += self.WIN_SCORE
                else:
                    capture_score += len(captures_by_me) // 2 * self.CAPTURE_SCORE

            # 2. Does playing here BLOCK an opponent capture?
            # We check if the opponent playing at this same spot would capture something.
            captures_by_opp = self._get_capture_positions(r, c, opponent, board)
            if captures_by_opp:
                if is_critical_defend:
                    # Opponent capturing here would win them the game! We MUST block.
                    capture_score += self.WIN_SCORE
                else:
                    # Standard defense value for preventing a capture
                    capture_score += len(captures_by_opp) // 2 * self.CAPTURE_SCORE

            # Combined Score
            # Attack score + Blocking score (weighted) + Capture bonus
            total_score = score_attack + score_defend + capture_score

            # History Heuristic Bonus
            # Add history score as a tie-breaker/bias for good moves
            history_score = self.algorithm.get_history_score(r, c)
            if history_score > 0:
                # Cap impact to avoid overshadowing tactical scores (like threats)
                # But allow it to differentiate equal tactical moves
                total_score += min(history_score, 5000)

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

        # Extract dynamic limits from config
        move_ordering_cfg = self.config["ai_settings"]["move_ordering"]
        adaptive_cfg = move_ordering_cfg["adaptive_move_limits"]
        priority_cfg = move_ordering_cfg["priority_move_limits"]

        # Adaptive Limits
        if winning_moves:
            # Return all winning moves (capped at limit if huge, but usually 1-2)
            limit = priority_cfg.get("winning_moves", 5)
            return [move for score, move in winning_moves[:limit]]

        # If we have blocking moves, prioritize them but include some attacks
        if blocking_moves:
            block_limit = priority_cfg.get("blocking_moves", 6)
            attack_limit = priority_cfg.get("high_priority_early", 6)  # Re-using this config for now

            result = [move for score, move in blocking_moves[:block_limit]]
            result.extend([move for score, move in high_priority[:attack_limit]])

            # Ensure we respect global limit roughly?
            # Actually, for blocking scenarios, we want to be sure.
            return result[:adaptive_cfg.get("early_game_limit", 18)]

        # Determine max moves based on game phase
        if num_moves < adaptive_cfg.get("early_game_moves", 10):
            max_moves = adaptive_cfg.get("early_game_limit", 18)
        elif num_moves < adaptive_cfg.get("mid_game_moves", 25):
            max_moves = adaptive_cfg.get("mid_game_limit", 14)
        else:
            max_moves = adaptive_cfg.get("late_game_limit", 12)

        result = []
        result.extend([move for score, move in high_priority])

        if len(result) < max_moves:
            result.extend([move for score, move in mid_priority])

        if len(result) < max_moves:
            result.extend([move for score, move in low_priority])

        return result[:max_moves]

    def get_piece_clusters(self, board, separation_dist=4):
        """
        Identifies clusters of pieces to form multiple bounding boxes.
        Returns list of (min_r, max_r, min_c, max_c) tuples.
        """
        pieces = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r * self.board_size + c] != 0:
                    pieces.append((r, c))

        if not pieces:
            return []

        # Simple clustering
        clusters = []
        unvisited = set(pieces)

        while unvisited:
            # Start a new cluster
            start_node = unvisited.pop()
            cluster = {start_node}
            queue = [start_node]

            # BFS to find connected components within separation_dist
            while queue:
                r, c = queue.pop(0)

                # Find neighbors in unvisited
                # Optimization: if unvisited is large, this is O(N^2).
                # But N (stones) <= 361. Usually < 50 in early game.
                # For 361 stones, simple loop is fine.
                to_remove = []
                for target in unvisited:
                    tr, tc = target
                    if abs(tr - r) <= separation_dist and abs(tc - c) <= separation_dist:
                        cluster.add(target)
                        queue.append(target)
                        to_remove.append(target)

                for item in to_remove:
                    unvisited.remove(item)

            # Calculate bbox for this cluster
            min_r = min(p[0] for p in cluster)
            max_r = max(p[0] for p in cluster)
            min_c = min(p[1] for p in cluster)
            max_c = max(p[1] for p in cluster)
            clusters.append((min_r, max_r, min_c, max_c))

        return clusters

    def get_relevant_moves_windowed(self, board, num_moves):
        """
        Optimized move generation using multiple bounding boxes (windows).
        Satisfies the requirement for "multiple rectangular windows".
        """
        relevant_moves = set()

        # Early game (< windowed_search_from_move): Use standard neighbor search
        window_start_move = self.config["ai_settings"]["move_ordering"].get("windowed_search_from_move", 10)
        if num_moves < window_start_move:
            return self.get_relevant_moves(board)

        # Get multiple windows based on clusters
        # Separation distance ensures we don't merge far-apart groups
        # Padding adds space for 5-in-a-row development
        clusters = self.get_piece_clusters(board, separation_dist=4)

        move_ordering_cfg = self.config["ai_settings"]["move_ordering"]
        if not move_ordering_cfg.get("enable_windowed_search", True):
             return self.get_relevant_moves(board)

        padding = move_ordering_cfg.get("bounding_box_margin", 2)

        if not clusters:
             return self.get_relevant_moves(board) # Fallback

        for min_r, max_r, min_c, max_c in clusters:
            # Apply padding
            start_r = max(0, min_r - padding)
            end_r = min(self.board_size - 1, max_r + padding)
            start_c = max(0, min_c - padding)
            end_c = min(self.board_size - 1, max_c + padding)

            # Scan within this window
            for r in range(start_r, end_r + 1):
                for c in range(start_c, end_c + 1):
                    idx = r * self.board_size + c
                    if board[idx] == 0:
                        # Check if it's close to ANY existing piece (relevance check)
                        # This is still needed to avoid empty corners of the rect
                        # But strictly, if we are in a tight cluster bbox, most empty spots are relevant.
                        # Let's do a quick check: has neighbor within relevance_range?

                        has_neighbor = False
                        # Check 3x3 around it
                        for dr in range(-1, 2):
                            for dc in range(-1, 2):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = r + dr, c + dc
                                if 0<=nr<self.board_size and 0<=nc<self.board_size:
                                    if board[nr * self.board_size + nc] != 0:
                                        has_neighbor = True
                                        break
                            if has_neighbor:
                                break

                        if has_neighbor:
                            relevant_moves.add((r, c))

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
                idx1 = nr1 * self.board_size + nc1
                idx2 = nr2 * self.board_size + nc2
                idx3 = nr3 * self.board_size + nc3

                if (board[idx1] == opponent and
                    board[idx2] == opponent and
                    board[idx3] == player):
                    captured.append((nr1, nc1))
                    captured.append((nr2, nc2))

        return captured

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
                idx = r * self.board_size + c
                if board[idx] != 0:
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
                idx = r * self.board_size + c
                if board[idx] != 0:
                    for dr in range(-self.relevance_range, self.relevance_range + 1):
                        for dc in range(-self.relevance_range, self.relevance_range + 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.board_size and
                                0 <= nc < self.board_size):
                                n_idx = nr * self.board_size + nc
                                if board[n_idx] == 0:
                                    relevant_moves.add((nr, nc))
        return list(relevant_moves)
