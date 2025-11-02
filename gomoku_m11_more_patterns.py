import copy  # Still needed for one-off copies, but not in the main loop
import math  # For pulsing highlight
import random  # For AI move tie-breaking
import sys
import time

import pygame

# --- Constants ---
BOARD_SIZE = 15
SQUARE_SIZE = 40
MARGIN = 40
WIDTH = BOARD_SIZE * SQUARE_SIZE + 2 * MARGIN
HEIGHT = BOARD_SIZE * SQUARE_SIZE + 2 * MARGIN + 40
COLOR_BOARD = (240, 217, 181)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRID = (0, 0, 0)
COLOR_TEXT = (40, 40, 40)
COLOR_CAPTURE_BG = (220, 220, 220)
COLOR_ILLEGAL = (255, 0, 0, 150)
COLOR_HIGHLIGHT = (255, 255, 0)

EMPTY = 0
BLACK_PLAYER = 1
WHITE_PLAYER = 2

# --- AI Configuration ---
AI_PLAYER = WHITE_PLAYER
HUMAN_PLAYER = BLACK_PLAYER

# --- Optimization 4: Delta Heuristic ---
# With the delta heuristic, we should be able to search *much* deeper.
AI_MAX_DEPTH = 14 # Increased from 10
AI_TIME_LIMIT = 2.0 # (seconds)
AI_RELEVANCE_RANGE = 2

# --- Optimization 5: Expanded Heuristic Scores ---
WIN_SCORE = 1000000000
PENDING_WIN_SCORE = 50000000
# (Opt 4) A "broken" four, e.g., _OO_OO_ or _O_OOO_
BROKEN_FOUR = 400000
OPEN_FOUR = 1000000 # _OOOO_
CLOSED_FOUR = 50000 # XOOOO_
# (Opt 5) 1-move-to-capture threat
CAPTURE_THREAT_OPEN = 30000 # (E.g., P O O E)
OPEN_THREE = 10000 # _OOO_
# (Opt 4) A "broken" three, e.g., _O_OO_
BROKEN_THREE = 4000
# (Opt 4 Increased)
CLOSED_THREE = 5000 # XOOO_
# (Opt 5) A 'net' or 'bridge' setup
CAPTURE_SETUP_BRIDGE = 1000 # (E.g., P O E P)
OPEN_TWO = 100 # _OO_
CLOSED_TWO = 10 # XOO_
CAPTURE_SCORE = 2500 # Score *per pair* (so *2)


class GomokuGame:
    """
    Main class to manage the Gomoku game state and logic.
    Optimization 5: Added explicit heuristics for
    setting up capture threats (CAPTURE_THREAT_OPEN)
    and capture 'nets' (CAPTURE_SETUP_BRIDGE).
    """
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"Gomoku AI Project - Optimization 5 (Capture Threats @ {AI_MAX_DEPTH}d)")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.SysFont("Inter", 24)

        self.game_mode = "P_VS_AI"

        # Game state
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK_PLAYER
        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
        self.captures = {BLACK_PLAYER: 0, WHITE_PLAYER: 0}
        self.WIN_BY_CAPTURES = 5

        # M3 Hover UI
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        self.illegal_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.line(self.illegal_surface, COLOR_ILLEGAL, (5, 5), (SQUARE_SIZE - 5, SQUARE_SIZE - 5), 4)
        pygame.draw.line(self.illegal_surface, COLOR_ILLEGAL, (5, SQUARE_SIZE - 5), (SQUARE_SIZE - 5, 5), 4)

        # M4 Pending Win State
        self.game_state = "NORMAL"
        self.pending_win_player = None
        self.pending_win_line = []
        self.pulse_alpha = 0

        # Zobrist Hashing
        self.zobrist_table = []
        self.current_hash = 0
        self.init_zobrist()

        # Transposition Table
        self.transposition_table = {}

        # AI State
        self.ai_is_thinking = False
        self.ai_start_time = 0
        self.time_limit_reached = False
        self.current_search_depth = 0

        # Center square (7,7) is a good opening move
        self.board[7][7] = HUMAN_PLAYER
        self.current_player = AI_PLAYER # AI plays first after human's center move

        # Must be called *after* board is set
        self.current_hash = self.compute_initial_hash()

    # ---
    # Zobrist Hashing (Same as Opt 3)
    # ---

    def init_zobrist(self):
        # ... (Same as Opt 3) ...
        self.zobrist_table = [[[0] * 3 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                for p in [EMPTY, BLACK_PLAYER, WHITE_PLAYER]:
                    self.zobrist_table[r][c][p] = random.randint(0, 2**64 - 1)

    def compute_initial_hash(self):
        # ... (Same as Opt 3) ...
        h = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                h ^= self.zobrist_table[r][c][piece]
        return h

    # ---
    # Game Loop and State (Same as Opt 3)
    # ---

    def run_game(self):
        # ... (Same as Opt 3) ...
        clock = pygame.time.Clock()

        while True:
            if (self.game_mode == "P_VS_AI" and
                self.current_player == AI_PLAYER and
                not self.game_over and
                not self.ai_is_thinking):

                self.ai_is_thinking = True
                self.run_ai_move()

            if self.game_state == "PENDING_WIN":
                self.pulse_alpha = (math.sin(time.time() * 4) + 1) / 2 * 255

            is_human_turn = (self.game_mode == "P_VS_P") or \
                            (self.game_mode == "P_VS_AI" and self.current_player == HUMAN_PLAYER)

            if not self.game_over and is_human_turn:
                self.update_hover(pygame.mouse.get_pos())
            else:
                self.hover_pos = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

                if (event.type == pygame.MOUSEBUTTONDOWN and
                    not self.game_over and
                    is_human_turn):

                    self.handle_mouse_click(self.hover_pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_m:
                        self.game_mode = "P_VS_AI" if self.game_mode == "P_VS_P" else "P_VS_P"
                        print(f"--- Game Mode Switched to: {self.game_mode} ---")

            self.draw_board()
            self.draw_pieces()
            self.draw_highlights()
            self.draw_status()
            self.draw_captures()
            self.draw_hover()

            pygame.display.flip()
            clock.tick(30)

    def reset_game(self):
        # ... (Same as Opt 3) ...
        print("--- Game Reset ---")
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
        self.captures = {BLACK_PLAYER: 0, WHITE_PLAYER: 0}
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        self.game_state = "NORMAL"
        self.pending_win_player = None
        self.pending_win_line = []

        self.ai_is_thinking = False
        self.board[7][7] = HUMAN_PLAYER
        self.current_player = AI_PLAYER
        self.game_mode = "P_VS_AI"

        self.transposition_table.clear()
        self.current_hash = self.compute_initial_hash()
        self.time_limit_reached = False
        self.current_search_depth = 0
        self.ai_start_time = 0


    def update_hover(self, pos):
        # ... (Same as Opt 3) ...
        x, y = pos
        col = round((x - MARGIN - SQUARE_SIZE // 2) / SQUARE_SIZE)
        row = round((y - MARGIN - SQUARE_SIZE // 2) / SQUARE_SIZE)

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.board[row][col] == EMPTY:
                self.hover_pos = (row, col)
                # Use a *copy* of the board for this check
                is_legal, reason = self.is_legal_move(row, col, self.current_player, self.board)
                self.hover_is_illegal = not is_legal
                self.illegal_reason = reason
                return

        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""

    def handle_move(self, row, col, player):
        # ... (Same as Opt 3) ...
        player_name = "Black" if player == BLACK_PLAYER else "White"
        opponent_player = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        print(f"[{player_name}] moved to ({row}, {col})")
        print(f"Move calculation time: {self.last_move_time:.6f} seconds")

        # --- 1. MAKE THE MOVE ---
        # We can't use the delta function here, we need the *actual* move.
        # This function updates self.board and self.current_hash
        captured_pieces = self.make_move(row, col, player, self.board)

        if captured_pieces:
            print(f"!!! Captured {len(captured_pieces)} pieces at: {captured_pieces}")
            self.captures[player] += len(captured_pieces)

        # --- 2. CHECK FOR IMMEDIATE CAPTURE WIN ---
        if self.captures[player] >= (self.WIN_BY_CAPTURES * 2):
            self.game_over = True
            self.winner = player
            print(f"--- Game Over! {player_name} wins by {self.WIN_BY_CAPTURES} captures! ---")
            return

        # --- 3. CHECK IF THIS MOVE RESOLVED A "PENDING WIN" ---
        if self.game_state == "PENDING_WIN":
            move_broke_line = False
            if captured_pieces:
                for r_cap, c_cap in captured_pieces:
                    if (r_cap, c_cap) in self.pending_win_line:
                        move_broke_line = True
                        break

            if move_broke_line:
                print(f"!!! {player_name} broke the 5-in-a-row! Game continues.")
                self.game_state = "NORMAL"
                self.pending_win_line = []
                self.pending_win_player = None
            else:
                self.game_over = True
                self.winner = self.pending_win_player
                pending_winner_name = "Black" if self.pending_win_player == BLACK_PLAYER else "White"
                print(f"--- Game Over! {player_name} failed to break the line.")
                print(f"--- {pending_winner_name} wins by 5-in-a-row! ---")
                return

        # --- 4. CHECK IF THIS MOVE *CREATED* A 5-IN-A-ROW ---
        win_line = self.check_win(row, col, player, self.board)
        if win_line and not self.game_over:
            print(f"!!! {player_name} created a 5-in-a-row! Pending Win!")
            self.game_state = "PENDING_WIN"
            self.pending_win_player = player
            self.pending_win_line = win_line

        # --- 5. SWITCH PLAYER ---
        if not self.game_over:
            self.current_player = opponent_player
            if self.game_mode == "P_VS_AI" and self.current_player == AI_PLAYER:
                self.ai_is_thinking = False # AI's turn to think
            self.hover_pos = None
            self.hover_is_illegal = False

    def handle_mouse_click(self, board_pos):
        # ... (Same as Opt 3) ...
        if board_pos is None: return
        row, col = board_pos

        if self.hover_is_illegal:
            print(f"Invalid move: ({row}, {col}) is illegal ({self.illegal_reason}).")
            return

        self.last_move_time = 0.0
        self.handle_move(row, col, self.current_player)

    # ---
    # Core Game Logic Functions (Updated for Delta Heuristic)
    # ---

    def make_move_and_get_delta(self, r, c, player, board, captures_dict):
        """
        (Optimization 4: Delta Heuristic)
        This is the core of the Delta Heuristic.
        It makes a move, updates the Zobrist hash, AND
        calculates the *change in score* (delta) all at once.
        """
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER
        delta = 0

        # --- 1. Get score BEFORE the move ---
        # Get score for 4 lines originating from (r,c)
        score_before_me = self.score_lines_at(r, c, board, player, opponent)
        score_before_opp = self.score_lines_at(r, c, board, opponent, player)

        # --- 2. Make the move (updates board & hash) ---
        captured_pieces = self.make_move(r, c, player, board)

        # --- 3. Get score AFTER the move ---
        score_after_me = self.score_lines_at(r, c, board, player, opponent)
        score_after_opp = self.score_lines_at(r, c, board, opponent, player)

        # --- 4. Calculate Delta ---

        # Delta from my line scores
        delta_my_lines = score_after_me - score_before_me
        # Delta from opponent's line scores (from my move)
        delta_opp_lines = score_after_opp - score_before_opp

        # Delta from my captures
        old_capture_count = captures_dict[player]
        new_capture_count = old_capture_count + len(captured_pieces)
        delta_my_captures = (new_capture_count // 2 * CAPTURE_SCORE) - (old_capture_count // 2 * CAPTURE_SCORE)

        # Delta from opponent's captures (which is 0, since I moved)
        # But we must account for the pieces *I* captured, which *reduces*
        # the opponent's potential line scores. This is handled
        # by the `delta_opp_lines` calculation.

        # Final delta is MyGains - OpponentGains
        # (My line gains + my capture gains) - (Opponent line gains)
        # We weight the opponent's score by 1.1, as in evaluate_board
        delta = (delta_my_lines + delta_my_captures) - (delta_opp_lines * 1.1)

        return delta, captured_pieces, old_capture_count


    def make_move(self, row, col, player, board):
        # (Same as Opt 3)
        if board[row][col] != EMPTY:
            return []
        self.current_hash ^= self.zobrist_table[row][col][EMPTY]
        board[row][col] = player
        self.current_hash ^= self.zobrist_table[row][col][player]
        captured_pieces = self.check_and_apply_captures(row, col, player, board)

        if captured_pieces:
            opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER
            for (r_cap, c_cap) in captured_pieces:
                self.current_hash ^= self.zobrist_table[r_cap][c_cap][opponent]
                self.current_hash ^= self.zobrist_table[r_cap][c_cap][EMPTY]

        return captured_pieces

    def check_and_apply_captures(self, last_row, last_col, player, board):
        # ... (Same as M6) ...
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER
        all_captured = []
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]:
            r1, c1 = last_row + dr, last_col + dc
            r2, c2 = last_row + 2 * dr, last_col + 2 * dc
            r3, c3 = last_row + 3 * dr, last_col + 3 * dc
            if not (0 <= r1 < BOARD_SIZE and 0 <= c1 < BOARD_SIZE and
                    0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE and
                    0 <= r3 < BOARD_SIZE and 0 <= c3 < BOARD_SIZE):
                continue
            if (board[r1][c1] == opponent and
                board[r2][c2] == opponent and
                board[r3][c3] == player):
                board[r1][c1] = EMPTY
                board[r2][c2] = EMPTY
                all_captured.append((r1, c1))
                all_captured.append((r2, c2))
        return all_captured

    def check_win(self, last_row, last_col, player, board):
        # ... (Same as M6) ...
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            win_line = [(last_row, last_col)]
            for i in range(1, 5):
                r, c = last_row + dr * i, last_col + dc * i
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    win_line.append((r, c))
                else:
                    break
            for i in range(1, 5):
                r, c = last_row - dr * i, last_col - dc * i
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    win_line.append((r, c))
                else:
                    break
            if len(win_line) >= 5:
                return win_line
        return None

    def is_legal_move(self, row, col, player, board):
        # ... (Same as Opt 3) ...
        if board[row][col] != EMPTY:
            return (False, "Occupied")

        # --- Must use a deepcopy for this check ---
        # The main AI search uses the 'real' board, but
        # this check (for hover and move ordering) needs
        # to be non-destructive.
        board_copy = copy.deepcopy(board)

        # 1. Make move on copy
        # We must check captures *from* the new (r,c) position
        captured_pieces = self.check_and_apply_captures(row, col, player, board_copy)
        board_copy[row][col] = player # Place piece *after* checking captures

        # 2. Check for double-threes
        free_threes_count = self.count_free_threes_at(row, col, player, board_copy)

        # 3. No undo needed, we used a copy.

        if free_threes_count >= 2:
            return (False, "Illegal (Double-Three)")

        return (True, "Legal")

    def count_free_threes_at(self, r, c, player, board):
        # ... (Same as M6) ...
        count = 0
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            line = self.get_line_string(r, c, dr, dc, board, player, opponent)

            # Pattern: _OOO_ (EPPPE)
            idx = line.find('EPPPE')
            found_this_axis = False
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break
                idx = line.find('EPPPE', idx + 1)
            if found_this_axis: continue

            # Pattern: _O_OO_ (EPPEP)
            idx = line.find('EPPEP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break
                idx = line.find('EPPEP', idx + 1)
            if found_this_axis: continue

            # Pattern: _OO_O_ (EPEPP)
            idx = line.find('EPEPP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    break
                idx = line.find('EPEPP', idx + 1)
        return count

    def get_line_string(self, r, c, dr, dc, board, player, opponent):
        # ... (Same as M6) ...
        line = [''] * 31
        for i in range(-15, 16):
            cr, cc = r + dr * i, c + dc * i
            idx = i + 15
            if not (0 <= cr < BOARD_SIZE and 0 <= cc < BOARD_SIZE):
                line[idx] = 'X'
            else:
                piece = board[cr][cc]
                if piece == EMPTY: line[idx] = 'E'
                elif piece == player: line[idx] = 'P'
                elif piece == opponent: line[idx] = 'O'
        return "".join(line)

    # ---
    # AI Functions (Updated for Optimization 4)
    # ---

    def run_ai_move(self):
        """
        (Optimization 4: Delta Heuristic)
        
        Calls evaluate_board() *once* to get the initial score,
        then starts the Iterative Deepening loop.
        """
        print(f"[{'Black' if AI_PLAYER == BLACK_PLAYER else 'White'}] is thinking...")

        # --- 1. Setup Iterative Deepening ---
        self.ai_start_time = time.time()
        self.time_limit_reached = False

        best_move_so_far = None
        best_score_so_far = -math.inf

        self.transposition_table.clear()

        # --- 2. Calculate Initial Score (ONCE) ---
        # This is the base score that all deltas will be added to.
        initial_board_score = self.evaluate_board(self.board, self.captures, AI_PLAYER)

        # --- 3. Iterative Deepening Loop ---
        for depth in range(1, AI_MAX_DEPTH + 1):
            self.current_search_depth = depth
            self.draw_status()
            pygame.display.flip()

            # --- Pass the initial score to the root ---
            best_move_this_depth, best_score_this_depth = self.minimax_root(depth, initial_board_score)

            if self.time_limit_reached:
                print(f"Search at depth {depth} timed out. Using result from depth {depth - 1}.")
                break

            best_move_so_far = best_move_this_depth
            best_score_so_far = best_score_this_depth

            print(f"Completed search to depth {depth}. Best move: {best_move_so_far}, Score: {best_score_so_far:.0f}")

            if best_score_so_far >= WIN_SCORE:
                print("Found a winning move. Stopping search.")
                break

            if time.time() - self.ai_start_time > AI_TIME_LIMIT:
                print("Time limit reached after completing depth. Stopping.")
                break

        # --- 4. Make the Move ---
        self.last_move_time = time.time() - self.ai_start_time
        self.current_search_depth = 0

        if best_move_so_far is None:
            print("AI has no legal moves left!")
            return

        self.handle_move(best_move_so_far[0], best_move_so_far[1], AI_PLAYER)

    def minimax_root(self, depth, current_board_score):
        """
        (Optimization 4: Delta Heuristic)
        Passes the current_board_score to recursive calls.
        """
        best_score = -math.inf
        best_move = None

        alpha = -math.inf
        beta = math.inf

        # Move ordering is CRITICAL for speed.
        # This still uses the fast 'score_move_locally'
        ordered_moves = self.get_ordered_moves(self.board, self.captures, AI_PLAYER)

        if not ordered_moves:
             return (None, 0)

        for (r, c) in ordered_moves:
            if self.time_limit_reached:
                return None, 0

            is_legal, _ = self.is_legal_move(r, c, AI_PLAYER, self.board)
            if not is_legal:
                continue

            # --- 1. MAKE MOVE & GET DELTA ---
            delta, captured_pieces, old_cap_count = self.make_move_and_get_delta(r, c, AI_PLAYER, self.board, self.captures)
            self.captures[AI_PLAYER] = old_cap_count + len(captured_pieces)

            # 2. Check for an immediate terminal state (win)
            if self.check_terminal_state(self.board, self.captures, AI_PLAYER, r, c):
                score = WIN_SCORE
            else:
                # 3. Call the recursive Minimax
                # --- Pass the NEW score (current + delta) ---
                score = self.minimax(self.board, self.captures, depth - 1, alpha, beta, False, current_board_score + delta)

            # --- 4. UNDO MOVE ---
            self.undo_move(r, c, AI_PLAYER, self.board, captured_pieces, old_cap_count, self.captures)

            if self.time_limit_reached:
                return None, 0

            # 5. Update best move
            if score > best_score:
                best_score = score
                best_move = (r, c)

            alpha = max(alpha, best_score)

        return best_move, best_score

    def minimax(self, board, captures, depth, alpha, beta, is_maximizing_player, current_score):
        """
        (Optimization 4: Delta Heuristic)
        
        - Takes `current_score` as a parameter.
        - Base case (depth == 0) just returns this score.
        - Recursive calls pass `current_score + delta`.
        """

        # --- 0. Check for Timeout ---
        if depth % 4 == 0:
             if time.time() - self.ai_start_time > AI_TIME_LIMIT:
                 self.time_limit_reached = True
                 return 0

        if self.time_limit_reached:
            return 0

        # --- 1. Check Transposition Table (Using Zobrist) ---
        full_hash = hash((self.current_hash, tuple(captures.items())))

        if full_hash in self.transposition_table:
            tt_score, tt_depth = self.transposition_table[full_hash]
            if tt_depth >= depth:
                return tt_score

        # --- 2. Base Case: Depth 0 ---
        if depth == 0:
            # --- THIS IS THE DELTA HEURISTIC ---
            # No more 'evaluate_board'. Just return the score
            # that was passed down and calculated via deltas.
            return current_score

        player = AI_PLAYER if is_maximizing_player else HUMAN_PLAYER

        ordered_moves = self.get_ordered_moves(board, captures, player)

        if not ordered_moves:
            return 0

        # --- 3. Recursive Step ---
        if is_maximizing_player:
            best_score = -math.inf
            for (r, c) in ordered_moves:
                is_legal, _ = self.is_legal_move(r, c, player, board)
                if not is_legal:
                    continue

                # --- MAKE MOVE & GET DELTA ---
                delta, captured_pieces, old_cap_count = self.make_move_and_get_delta(r, c, player, board, captures)
                captures[player] = old_cap_count + len(captured_pieces)

                if self.check_terminal_state(board, captures, player, r, c):
                    score = WIN_SCORE
                else:
                    score = self.minimax(board, captures, depth - 1, alpha, beta, False, current_score + delta)

                # --- UNDO MOVE ---
                self.undo_move(r, c, player, board, captured_pieces, old_cap_count, captures)

                if self.time_limit_reached: return 0

                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break

            self.transposition_table[full_hash] = (best_score, depth)
            return best_score

        else: # Minimizing player
            best_score = math.inf
            for (r, c) in ordered_moves:
                is_legal, _ = self.is_legal_move(r, c, player, board)
                if not is_legal:
                    continue

                # --- MAKE MOVE & GET DELTA ---
                # Note: The 'delta' is from the *perspective* of the
                # AI player. So when the opponent (minimizer) makes a
                # move, we *subtract* the delta.
                delta, captured_pieces, old_cap_count = self.make_move_and_get_delta(r, c, player, board, captures)
                captures[player] = old_cap_count + len(captured_pieces)

                if self.check_terminal_state(board, captures, player, r, c):
                    score = -WIN_SCORE
                else:
                    # When minimizer moves, the delta is *subtracted*
                    # from the main player's score.
                    score = self.minimax(board, captures, depth - 1, alpha, beta, True, current_score - delta)

                # --- UNDO MOVE ---
                self.undo_move(r, c, player, board, captured_pieces, old_cap_count, captures)

                if self.time_limit_reached: return 0

                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break

            self.transposition_table[full_hash] = (best_score, depth)
            return best_score

    def undo_move(self, r, c, player, board, captured_pieces, old_capture_count, captures_dict):
        # (Same as Opt 3)
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        if captured_pieces:
            for (cr, cc) in captured_pieces:
                board[cr][cc] = opponent
                self.current_hash ^= self.zobrist_table[cr][cc][EMPTY]
                self.current_hash ^= self.zobrist_table[cr][cc][opponent]

        captures_dict[player] = old_capture_count

        board[r][c] = EMPTY
        self.current_hash ^= self.zobrist_table[r][c][player]
        self.current_hash ^= self.zobrist_table[r][c][EMPTY]

    def check_terminal_state(self, board, captures, player_who_just_moved, r, c):
        # ... (Same as M6) ...
        if captures[player_who_just_moved] >= (self.WIN_BY_CAPTURES * 2):
            return True
        if self.check_win(r, c, player_who_just_moved, board) is not None:
            return True
        return False

    def get_ordered_moves(self, board, captures, player):
        """
        (Updated for Optimization 5)
        Uses `score_move_locally` which now benefits from
        the new capture threat patterns.
        """
        moves_with_scores = []
        legal_moves = self.get_relevant_moves(board)

        # We need a *copy* of captures for the local scorer
        captures_copy = captures.copy()

        for (r, c) in legal_moves:
            is_legal, _ = self.is_legal_move(r, c, player, board)
            if not is_legal:
                continue

            # --- Uses a copy of the board for scoring ---
            board_copy = copy.deepcopy(board)
            score = self.score_move_locally(r, c, player, board_copy, captures_copy)
            moves_with_scores.append((score, (r, c)))

        moves_with_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in moves_with_scores]

    def score_move_locally(self, r, c, player, board, captures):
        """
        (Optimization 4: Delta Heuristic)
        This is for *move ordering*. It must be fast.
        It does a quick simulation *on a copy* to get a score.
        It now benefits from the new heuristic patterns.
        """
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        # --- Fast simulation on a board copy ---
        captured_pieces = self.check_and_apply_captures(r, c, player, board)
        board[r][c] = player

        my_score = len(captured_pieces) * CAPTURE_SCORE
        opponent_score = 0

        my_score += self.score_lines_at(r, c, board, player, opponent)
        opponent_score += self.score_lines_at(r, c, board, opponent, player)

        # No undo needed, we used a copy.

        # We return a simple score: my gains - opponent's gains
        # This will order forcing moves (like captures and fours)
        # much higher.
        return (my_score - opponent_score * 1.1)

    def get_relevant_moves(self, board):
        # ... (Same as M6) ...
        relevant_moves = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != EMPTY:
                    for dr in range(-AI_RELEVANCE_RANGE, AI_RELEVANCE_RANGE + 1):
                        for dc in range(-AI_RELEVANCE_RANGE, AI_RELEVANCE_RANGE + 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < BOARD_SIZE and
                                0 <= nc < BOARD_SIZE and
                                board[nr][nc] == EMPTY):
                                relevant_moves.add((nr, nc))
        return list(relevant_moves)

    # ---
    # Heuristic Scoring (Updated for Opt 5)
    # ---

    def score_lines_at(self, r, c, board, player, opponent):
        """
        (Optimization 4: Delta Heuristic)
        Scores the 4 lines (H, V, D1, D2) passing through (r,c)
        for the given `player`.
        """
        score = 0
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            line_str = self.get_line_string(r, c, dr, dc, board, player, opponent)
            score += self.score_line_string(line_str)
        return score

    def evaluate_board(self, board, captures, player):
        """ 
        (Optimization 4: Delta Heuristic)
        This is now *ONLY* called once, at the
        start of the AI's turn.
        """
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER
        my_score = self.calculate_player_score(board, captures, player)
        opponent_score = self.calculate_player_score(board, captures, opponent)
        return my_score - opponent_score * 1.1

    def calculate_player_score(self, board, captures, player):
        """ 
        (Optimization 5: Capture Threats)
        This full-board scan is now only called ONCE per turn.
        It benefits from the new `score_line_string`.
        """
        score = 0
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        if captures[player] >= (self.WIN_BY_CAPTURES * 2):
            return WIN_SCORE

        score += (captures[player] // 2) * CAPTURE_SCORE

        lines_seen = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                # This is already optimized to only scan from pieces!
                if board[r][c] != EMPTY: # Scan from *any* piece
                    for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                        line_coords = self.get_line_coords(r, c, dr, dc)
                        line_key = tuple(sorted(line_coords))

                        if line_key not in lines_seen:
                            lines_seen.add(line_key)
                            # We must score the line from *our* perspective
                            line_str_p = self.get_line_string(r, c, dr, dc, board, player, opponent)
                            score += self.score_line_string(line_str_p)
        return score

    def get_line_coords(self, r, c, dr, dc):
        # ... (Same as M6) ...
        coords = []
        for i in range(-4, 5):
             cr, cc = r + dr * i, c + dc * i
             if 0 <= cr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
                 coords.append((cr, cc))
        return coords


    def score_line_string(self, line):
        """
        (Updated for Optimization 5)
        Greatly expanded heuristic patterns for smarter AI.
        Now includes explicit capture threats.
        'P' = Player, 'O' = Opponent, 'E' = Empty, 'X' = Bound
        """
        score = 0

        # --- 5-in-a-row (Win) ---
        if "PPPPP" in line:
            return PENDING_WIN_SCORE # Not a full win, but a pending win

        # --- Open Fours (1,000,000) ---
        if "EPPPPE" in line:
            score += OPEN_FOUR

        # --- Broken Fours (400,000) ---
        if "EPPEP E" in line or "E PEPPE" in line: # _O_OOO_
            score += BROKEN_FOUR
        if "EPP EPE" in line or "EPE PPE" in line: # _OO_OO_
            score += BROKEN_FOUR

        # --- Closed Fours (50,000) ---
        if ("XPPPPE" in line or "EPPPPX" in line or
            "OPPPPE" in line or "EPPPPO" in line):
            score += CLOSED_FOUR

        # --- Optimization 5: Capture Threats (30,000) ---
        if "POOE" in line or "EOOP" in line:
            score += CAPTURE_THREAT_OPEN

        # --- Open Threes (10,000) ---
        if "EPPPE" in line: # _OOO_
            score += OPEN_THREE
        # (These are technically also broken threes, but Pente
        # counts them as 'open threes' so we will too)
        if "EPPEP" in line: # _O_OO
            score += OPEN_THREE
        if "EPEPP" in line: # _OO_O
            score += OPEN_THREE

        # --- Closed Threes (5,000) ---
        if ("XPPPE" in line or "EPPPX" in line or
            "OPPPE" in line or "EPPPO" in line):
            score += CLOSED_THREE
        if ("XPPEP" in line or "EPPX" in line or
            "OPPEP" in line or "EPPO" in line):
            score += CLOSED_THREE

        # --- Broken Threes (4.000) ---
        if "EPEP E" in line or "E PEP E" in line: # _O_O_O_
            score += BROKEN_THREE

        # --- Optimization 5: Capture Setups (1,000) ---
        if "POEP" in line:
            score += CAPTURE_SETUP_BRIDGE

        # --- Open Twos (100) ---
        if "EPPE" in line: # _OO_
            score += OPEN_TWO
        if "EPEP" in line: # _O_O_
            score += OPEN_TWO

        # --- Closed Twos (10) ---
        if ("XPPE" in line or "EPPX" in line or
            "OPPE" in line or "EPPO" in line):
            score += CLOSED_TWO

        return score

    # ---
    # Drawing Functions (Same as Opt 3)
    # ---

    def draw_board(self):
        # ... (Same as M6) ...
        self.screen.fill(COLOR_BOARD)
        for i in range(BOARD_SIZE):
            start_pos_h = (MARGIN + SQUARE_SIZE // 2, MARGIN + SQUARE_SIZE // 2 + i * SQUARE_SIZE)
            end_pos_h = (WIDTH - MARGIN - SQUARE_SIZE // 2, MARGIN + SQUARE_SIZE // 2 + i * SQUARE_SIZE)
            pygame.draw.line(self.screen, COLOR_GRID, start_pos_h, end_pos_h, 1)
            label = self.font.render(str(i), True, COLOR_TEXT)
            self.screen.blit(label, (MARGIN - 30, MARGIN + SQUARE_SIZE // 2 + i * SQUARE_SIZE - label.get_height() // 2))
            start_pos_v = (MARGIN + SQUARE_SIZE // 2 + i * SQUARE_SIZE, MARGIN + SQUARE_SIZE // 2)
            end_pos_v = (MARGIN + SQUARE_SIZE // 2 + i * SQUARE_SIZE, HEIGHT - MARGIN - SQUARE_SIZE // 2 - 40)
            pygame.draw.line(self.screen, COLOR_GRID, start_pos_v, end_pos_v, 1)
            label = self.font.render(chr(ord('A') + i), True, COLOR_TEXT)
            self.screen.blit(label, (MARGIN + SQUARE_SIZE // 2 + i * SQUARE_SIZE - label.get_width() // 2, MARGIN - 30))
        star_points = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]
        for r, c in star_points:
            cx = MARGIN + SQUARE_SIZE // 2 + c * SQUARE_SIZE
            cy = MARGIN + SQUARE_SIZE // 2 + r * SQUARE_SIZE
            pygame.draw.circle(self.screen, COLOR_GRID, (cx, cy), 5)
        pygame.draw.rect(self.screen, COLOR_CAPTURE_BG, (0, HEIGHT - 40, WIDTH, 40))

    def draw_pieces(self):
        # ... (Same as M6) ...
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                player = self.board[r][c]
                if player != EMPTY:
                    cx = MARGIN + SQUARE_SIZE // 2 + c * SQUARE_SIZE
                    cy = MARGIN + SQUARE_SIZE // 2 + r * SQUARE_SIZE
                    radius = SQUARE_SIZE // 2 - 3
                    color = COLOR_BLACK if player == BLACK_PLAYER else COLOR_WHITE
                    pygame.draw.circle(self.screen, color, (cx, cy), radius)
                    if player == WHITE_PLAYER:
                        pygame.draw.circle(self.screen, COLOR_BLACK, (cx, cy), radius, 1)

    def draw_highlights(self):
        # ... (Same as M6) ...
        if self.game_state != "PENDING_WIN":
            return
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        color = (*COLOR_HIGHLIGHT, int(self.pulse_alpha))
        radius = SQUARE_SIZE // 2 - 1
        pygame.draw.circle(highlight_surface, color, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), radius, 3)
        for r, c in self.pending_win_line:
            cx = MARGIN + SQUARE_SIZE // 2 + c * SQUARE_SIZE
            cy = MARGIN + SQUARE_SIZE // 2 + r * SQUARE_SIZE
            self.screen.blit(highlight_surface, (cx - SQUARE_SIZE // 2, cy - SQUARE_SIZE // 2))

    def draw_status(self):
        # (Same as Opt 3)
        if self.game_over:
            winner_name = "Black" if self.winner == BLACK_PLAYER else "White"
            message = f"Game Over! {winner_name} wins! (Press 'R' to Reset)"
            color = (180, 0, 0)

        elif self.game_state == "PENDING_WIN":
            pending_winner_name = "Black" if self.pending_win_player == BLACK_PLAYER else "White"
            opponent_name = "Black" if self.current_player == BLACK_PLAYER else "White"
            message = f"PENDING WIN for {pending_winner_name}! {opponent_name} must capture the line!"
            color = (200, 150, 0)

        elif (self.game_mode == "P_VS_AI" and
              self.current_player == AI_PLAYER):
            message = f"AI is thinking... (Depth: {self.current_search_depth} / {AI_MAX_DEPTH})"
            color = (0, 0, 180)

        else:
            player_name = "Black" if self.current_player == BLACK_PLAYER else "White"
            message = f"{player_name}'s Turn (Mode: {self.game_mode} - 'M' to toggle)"
            color = COLOR_BLACK if self.current_player == BLACK_PLAYER else COLOR_TEXT

        status_text = self.font.render(message, True, color)
        text_rect = status_text.get_rect(center=(WIDTH // 2, MARGIN // 2))
        self.screen.blit(status_text, text_rect)

    def draw_captures(self):
        # ... (Same as M6) ...
        black_cap_text = self.font.render(f"Black Captures: {self.captures[BLACK_PLAYER]}", True, COLOR_BLACK)
        self.screen.blit(black_cap_text, (MARGIN, HEIGHT - 35))

        white_cap_text = self.font.render(f"White Captures: {self.captures[WHITE_PLAYER]}", True, COLOR_BLACK)
        text_rect = white_cap_text.get_rect(right=WIDTH - MARGIN)
        self.screen.blit(white_cap_text, (text_rect.x, HEIGHT - 35))

    def draw_hover(self):
        # ... (Same as M6) ...
        if self.hover_pos is None: return
        r, c = self.hover_pos
        cx = MARGIN + SQUARE_SIZE // 2 + c * SQUARE_SIZE
        cy = MARGIN + SQUARE_SIZE // 2 + r * SQUARE_SIZE

        if self.hover_is_illegal:
            self.screen.blit(self.illegal_surface, (cx - SQUARE_SIZE // 2, cy - SQUARE_SIZE // 2))
        else:
            radius = SQUARE_SIZE // 2 - 3
            temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = (*COLOR_BLACK, 100) if self.current_player == BLACK_PLAYER else (*COLOR_WHITE, 100)
            pygame.draw.circle(temp_surface, color, (radius, radius), radius)
            if self.current_player == WHITE_PLAYER:
                 pygame.draw.circle(temp_surface, (*COLOR_BLACK, 100), (radius, radius), radius, 1)
            self.screen.blit(temp_surface, (cx - radius, cy - radius))

    def quit_game(self):
        pygame.quit()
        sys.exit()

# --- Main Execution ---
if __name__ == "__main__":
    game = GomokuGame()
    game.run_game()
