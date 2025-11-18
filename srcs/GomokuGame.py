"""
Main Gomoku game class that manages game state, rules, and UI rendering.
"""

import copy
import math
import random
import sys
import time

import pygame

from srcs.GomokuAI import GomokuAI
from srcs.utils import get_line_string


class GomokuGame:
    """
    Main class to manage the Gomoku game state and logic.
    """

    def __init__(self, config):
        # Store configuration
        self.config = config

        # Parse configuration sections
        game_cfg = config["game_settings"]
        player_cfg = config["player_settings"]
        ui_cfg = config["ui_settings"]

        # Game constants from config
        self.BOARD_SIZE = game_cfg["board_size"]
        self.EMPTY = game_cfg["empty"]
        self.BLACK_PLAYER = game_cfg["black_player"]
        self.WHITE_PLAYER = game_cfg["white_player"]
        self.AI_PLAYER = player_cfg["ai_player"]
        self.HUMAN_PLAYER = player_cfg["human_player"]
        self.WIN_BY_CAPTURES = game_cfg["win_by_captures"]

        # UI constants from config
        self.SQUARE_SIZE = ui_cfg["window"]["square_size"]
        self.MARGIN = ui_cfg["window"]["margin"]
        self.BOTTOM_BAR_HEIGHT = ui_cfg["window"]["bottom_bar_height"]
        self.WIDTH = self.BOARD_SIZE * self.SQUARE_SIZE + 2 * self.MARGIN
        self.HEIGHT = (self.BOARD_SIZE * self.SQUARE_SIZE +
                      2 * self.MARGIN + self.BOTTOM_BAR_HEIGHT)

        # Colors from config
        self.COLOR_BOARD = tuple(ui_cfg["colors"]["board"])
        self.COLOR_BLACK = tuple(ui_cfg["colors"]["black"])
        self.COLOR_WHITE = tuple(ui_cfg["colors"]["white"])
        self.COLOR_GRID = tuple(ui_cfg["colors"]["grid"])
        self.COLOR_TEXT = tuple(ui_cfg["colors"]["text"])
        self.COLOR_CAPTURE_BG = tuple(ui_cfg["colors"]["capture_bg"])
        self.COLOR_ILLEGAL = tuple(ui_cfg["colors"]["illegal"])
        self.COLOR_HIGHLIGHT = tuple(ui_cfg["colors"]["highlight"])

        # Animation settings
        self.PULSE_SPEED = ui_cfg["animation"]["pulse_speed"]

        # Debug settings
        ai_cfg = config.get("ai_settings", {})
        debug_cfg = ai_cfg.get("debug", {})
        self.debug_verbose = debug_cfg.get("verbose", False)
        self.debug_terminal_states = debug_cfg.get("show_terminal_states", False)

        # Initialize Pygame
        pygame.init()
        algo_cfg = config["algorithm_settings"]
        pygame.display.set_caption(
            f"Gomoku AI Project - Depth {algo_cfg['max_depth']} "
            f"(Time: {algo_cfg['time_limit']}s)"
        )
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.font = pygame.font.SysFont(
            ui_cfg["fonts"]["main_font"],
            ui_cfg["fonts"]["main_font_size"]
        )

        # Game mode
        self.game_mode = game_cfg["default_game_mode"]

        # Game state
        self.board = [[self.EMPTY for _ in range(self.BOARD_SIZE)]
                     for _ in range(self.BOARD_SIZE)]
        self.current_player = self.BLACK_PLAYER
        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
        self.captures = {self.BLACK_PLAYER: 0, self.WHITE_PLAYER: 0}
        self.move_count = 0  # Track total moves for adaptive AI

        # Hover UI
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        self.illegal_surface = pygame.Surface(
            (self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA
        )
        pygame.draw.line(self.illegal_surface, self.COLOR_ILLEGAL, (5, 5),
                        (self.SQUARE_SIZE - 5, self.SQUARE_SIZE - 5), 4)
        pygame.draw.line(self.illegal_surface, self.COLOR_ILLEGAL,
                        (5, self.SQUARE_SIZE - 5),
                        (self.SQUARE_SIZE - 5, 5), 4)

        # Pending Win State
        self.game_state = "NORMAL"
        self.pending_win_player = None
        self.pending_win_line = []
        self.pulse_alpha = 0

        # Zobrist Hashing
        self.zobrist_table = []
        self.current_hash = 0
        self.init_zobrist()

        # AI
        self.ai = GomokuAI(config)

        # Start with empty board - human can place first move anywhere
        self.current_player = self.HUMAN_PLAYER
        self.current_hash = self.compute_initial_hash()
        self.move_count = 0  # No moves yet

    # ---
    # Zobrist Hashing
    # ---

    def init_zobrist(self):
        """Initializes the Zobrist hash table with random values."""
        self.zobrist_table = [[[0] * 3 for _ in range(self.BOARD_SIZE)]
                             for _ in range(self.BOARD_SIZE)]
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                for p in [self.EMPTY, self.BLACK_PLAYER, self.WHITE_PLAYER]:
                    self.zobrist_table[r][c][p] = random.randint(0, 2**64 - 1)

    def compute_initial_hash(self):
        """Computes the initial Zobrist hash of the board."""
        h = 0
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                piece = self.board[r][c]
                h ^= self.zobrist_table[r][c][piece]
        return h

    # ---
    # Game Loop
    # ---

    def run_game(self):
        """Main game loop."""
        clock = pygame.time.Clock()

        while True:
            # AI's turn
            if (self.game_mode == "P_VS_AI" and
                self.current_player == self.AI_PLAYER and
                not self.game_over and
                not self.ai.ai_is_thinking):

                self.ai.ai_is_thinking = True
                self.run_ai_move()

            # Update pulsing highlight for pending win
            if self.game_state == "PENDING_WIN":
                self.pulse_alpha = (math.sin(time.time() * self.PULSE_SPEED) + 1) / 2 * 255

            # Check if it's human's turn
            is_human_turn = (self.game_mode == "P_VS_P") or \
                           (self.game_mode == "P_VS_AI" and
                            self.current_player == self.HUMAN_PLAYER)

            if not self.game_over and is_human_turn:
                self.update_hover(pygame.mouse.get_pos())
            else:
                self.hover_pos = None

            # Event handling
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

            # Render
            self.draw_board()
            self.draw_pieces()
            self.draw_highlights()
            self.draw_status()
            self.draw_captures()
            self.draw_hover()

            pygame.display.flip()
            clock.tick(30)

    def reset_game(self):
        """Resets the game to initial state."""
        print("--- Game Reset ---")
        self.board = [[self.EMPTY for _ in range(self.BOARD_SIZE)]
                     for _ in range(self.BOARD_SIZE)]
        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
        self.captures = {self.BLACK_PLAYER: 0, self.WHITE_PLAYER: 0}
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        self.game_state = "NORMAL"
        self.pending_win_player = None
        self.pending_win_line = []

        self.ai.ai_is_thinking = False
        self.ai.algorithm.clear_transposition_table()

        self.current_player = self.HUMAN_PLAYER
        self.game_mode = self.config["game_settings"]["default_game_mode"]

        self.current_hash = self.compute_initial_hash()
        self.move_count = 0  # Reset to 0 (no initial move)

    def update_hover(self, pos):
        """Updates hover position and checks if move is legal."""
        x, y = pos
        col = round((x - self.MARGIN - self.SQUARE_SIZE // 2) / self.SQUARE_SIZE)
        row = round((y - self.MARGIN - self.SQUARE_SIZE // 2) / self.SQUARE_SIZE)

        if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
            if self.board[row][col] == self.EMPTY:
                self.hover_pos = (row, col)
                is_legal, reason = self.is_legal_move(row, col, self.current_player,
                                                      self.board)
                self.hover_is_illegal = not is_legal
                self.illegal_reason = reason
                return

        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""

    def handle_mouse_click(self, board_pos):
        """Handles mouse click for human player move."""
        if board_pos is None:
            return
        row, col = board_pos

        if self.hover_is_illegal:
            print(f"Invalid move: ({row}, {col}) is illegal ({self.illegal_reason}).")
            return

        self.last_move_time = 0.0
        self.handle_move(row, col, self.current_player)

    # ---
    # Move Handling
    # ---

    def handle_move(self, row, col, player):
        """
        Handles a player's move, including captures, win checking, and state updates.
        """
        player_name = "Black" if player == self.BLACK_PLAYER else "White"
        opponent_player = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER

        # Calculate turn number (each player's move increments by 1, so turn = (move + 1) / 2)
        turn_num = (self.move_count + 2) // 2
        print(f"\n=== Turn {turn_num} ===")
        print(f"[{player_name}] moved to ({row}, {col})")
        if self.last_move_time > 0:
            print(f"Move calculation time: {self.last_move_time:.6f} seconds")

        # Make the move
        captured_pieces, new_hash = self.make_move(row, col, player, self.board,
                                                   self.current_hash)
        self.current_hash = new_hash
        self.move_count += 1  # Increment move counter

        if captured_pieces:
            print(f"!!! Captured {len(captured_pieces)} pieces at: {captured_pieces}")
            self.captures[player] += len(captured_pieces)

        # Check for capture win
        if self.captures[player] >= (self.WIN_BY_CAPTURES * 2):
            self.game_over = True
            self.winner = player
            print(f"--- Game Over! {player_name} wins by {self.WIN_BY_CAPTURES} captures! ---")
            return

        # Check if move resolved a pending win
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
                pending_winner_name = "Black" if self.pending_win_player == self.BLACK_PLAYER else "White"
                print(f"--- Game Over! {player_name} failed to break the line.")
                print(f"--- {pending_winner_name} wins by 5-in-a-row! ---")
                return

        # Check if this move created a 5-in-a-row
        win_line = self.check_win(row, col, player, self.board)
        if win_line and not self.game_over:
            print(f"!!! {player_name} created a 5-in-a-row! Pending Win!")
            self.game_state = "PENDING_WIN"
            self.pending_win_player = player
            self.pending_win_line = win_line

        # Switch player
        if not self.game_over:
            self.current_player = opponent_player
            if self.game_mode == "P_VS_AI" and self.current_player == self.AI_PLAYER:
                self.ai.ai_is_thinking = False
            self.hover_pos = None
            self.hover_is_illegal = False

    # ---
    # AI Move
    # ---

    def run_ai_move(self):
        """Runs the AI to get the best move."""
        best_move, time_taken = self.ai.get_best_move(
            self.board, self.captures, self.current_hash, self.AI_PLAYER,
            self.WIN_BY_CAPTURES, self, self.move_count
        )

        self.last_move_time = time_taken

        if best_move is None:
            print("AI has no legal moves left!")
            return

        self.handle_move(best_move[0], best_move[1], self.AI_PLAYER)

    # ---
    # Game Logic Functions
    # ---

    def make_move(self, row, col, player, board, zobrist_hash):
        """
        Makes a move on the board and updates the Zobrist hash.
        Returns: (captured_pieces, new_zobrist_hash)
        """
        if board[row][col] != self.EMPTY:
            return [], zobrist_hash

        # Update hash for placing the piece
        zobrist_hash ^= self.zobrist_table[row][col][self.EMPTY]
        board[row][col] = player
        zobrist_hash ^= self.zobrist_table[row][col][player]

        # Check for captures
        captured_pieces = self.check_and_apply_captures(row, col, player, board)

        # Update hash for captured pieces
        if captured_pieces:
            opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER
            for (r_cap, c_cap) in captured_pieces:
                zobrist_hash ^= self.zobrist_table[r_cap][c_cap][opponent]
                zobrist_hash ^= self.zobrist_table[r_cap][c_cap][self.EMPTY]

        return captured_pieces, zobrist_hash

    def undo_move(self, r, c, player, board, captured_pieces, old_capture_count,
                 captures_dict, zobrist_hash):
        """Undoes a move on the board and restores the Zobrist hash."""
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER

        # Restore captured pieces
        if captured_pieces:
            for (cr, cc) in captured_pieces:
                board[cr][cc] = opponent
                zobrist_hash ^= self.zobrist_table[cr][cc][self.EMPTY]
                zobrist_hash ^= self.zobrist_table[cr][cc][opponent]

        captures_dict[player] = old_capture_count

        # Remove the piece
        board[r][c] = self.EMPTY
        zobrist_hash ^= self.zobrist_table[r][c][player]
        zobrist_hash ^= self.zobrist_table[r][c][self.EMPTY]

        return zobrist_hash

    def check_and_apply_captures(self, last_row, last_col, player, board):
        """
        Checks for captures after placing a piece and applies them.
        Returns: list of captured piece coordinates
        """
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER
        all_captured = []

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1),
                      (0, -1), (-1, 0), (-1, -1), (-1, 1)]:
            r1, c1 = last_row + dr, last_col + dc
            r2, c2 = last_row + 2 * dr, last_col + 2 * dc
            r3, c3 = last_row + 3 * dr, last_col + 3 * dc

            if not (0 <= r1 < self.BOARD_SIZE and 0 <= c1 < self.BOARD_SIZE and
                   0 <= r2 < self.BOARD_SIZE and 0 <= c2 < self.BOARD_SIZE and
                   0 <= r3 < self.BOARD_SIZE and 0 <= c3 < self.BOARD_SIZE):
                continue

            if (board[r1][c1] == opponent and
                board[r2][c2] == opponent and
                board[r3][c3] == player):
                board[r1][c1] = self.EMPTY
                board[r2][c2] = self.EMPTY
                all_captured.append((r1, c1))
                all_captured.append((r2, c2))

        return all_captured

    def check_win(self, last_row, last_col, player, board):
        """
        Checks if a move creates a 5-in-a-row.
        Returns: list of winning line coordinates or None
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            win_line = [(last_row, last_col)]

            # Check forward
            for i in range(1, 5):
                r, c = last_row + dr * i, last_col + dc * i
                if 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and board[r][c] == player:
                    win_line.append((r, c))
                else:
                    break

            # Check backward
            for i in range(1, 5):
                r, c = last_row - dr * i, last_col - dc * i
                if 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and board[r][c] == player:
                    win_line.append((r, c))
                else:
                    break

            if len(win_line) >= 5:
                return win_line

        return None

    def check_terminal_state(self, board, captures, player_who_just_moved, r, c,
                            win_by_captures):
        """Checks if the game has reached a terminal state (win condition)."""
        # Check captures
        if captures[player_who_just_moved] >= (win_by_captures * 2):
            if self.debug_terminal_states:
                print(f"    DEBUG check_terminal_state: Player {player_who_just_moved} wins by captures!")
                print(f"      Has {captures[player_who_just_moved]} >= {win_by_captures * 2} needed")
            return True

        # Check 5-in-a-row
        win_result = self.check_win(r, c, player_who_just_moved, board)
        if win_result is not None:
            if self.debug_terminal_states:
                print(f"    DEBUG check_terminal_state: Player {player_who_just_moved} wins by 5-in-a-row!")
                print(f"      At position ({r}, {c})")
                print(f"      Win line: {win_result}")
                # Show board around that position (expanded range to see full line)
                print(f"      Board at ({r}, {c}): {board[r][c]}")
                for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                    line_debug = []
                    for i in range(-5, 6):  # Expand to see more positions
                        nr, nc = r + i*dr, c + i*dc
                        if 0 <= nr < self.BOARD_SIZE and 0 <= nc < self.BOARD_SIZE:
                            val = board[nr][nc]
                            marker = ""
                            if (nr, nc) in [(pos[0], pos[1]) for pos in win_result]:
                                marker = "*"  # Mark positions in win line
                            line_debug.append(f"({nr},{nc})={val}{marker}")
                        else:
                            line_debug.append("X")
                    print(f"      Direction ({dr},{dc}): {' '.join(line_debug)}")
            return True

        return False

    def is_legal_move(self, row, col, player, board):
        """
        Checks if a move is legal (not occupied and doesn't create double-three).
        Returns: (is_legal, reason)
        """
        if board[row][col] != self.EMPTY:
            return (False, "Occupied")

        # Use a copy to check for double-three
        board_copy = copy.deepcopy(board)

        # Check captures from this position
        captured_pieces = self.check_and_apply_captures(row, col, player, board_copy)  # noqa: F841
        board_copy[row][col] = player

        # Check for double-threes
        free_threes_count = self.count_free_threes_at(row, col, player, board_copy)

        if free_threes_count >= 2:
            return (False, "Illegal (Double-Three)")

        return (True, "Legal")

    def count_free_threes_at(self, r, c, player, board):
        """Counts the number of free threes created by placing a piece at (r,c)."""
        count = 0
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            line = get_line_string(r, c, dr, dc, board, player, opponent, self.BOARD_SIZE)

            # Pattern: _OOO_ (EPPPE)
            idx = line.find('EPPPE')
            found_this_axis = False
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break
                idx = line.find('EPPPE', idx + 1)
            if found_this_axis:
                continue

            # Pattern: _O_OO_ (EPPEP)
            idx = line.find('EPPEP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break
                idx = line.find('EPPEP', idx + 1)
            if found_this_axis:
                continue

            # Pattern: _OO_O_ (EPEPP)
            idx = line.find('EPEPP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    break
                idx = line.find('EPEPP', idx + 1)

        return count

    # ---
    # Drawing Functions
    # ---

    def draw_board(self):
        """Draws the game board."""
        self.screen.fill(self.COLOR_BOARD)

        # Draw grid lines
        for i in range(self.BOARD_SIZE):
            start_pos_h = (self.MARGIN + self.SQUARE_SIZE // 2,
                          self.MARGIN + self.SQUARE_SIZE // 2 + i * self.SQUARE_SIZE)
            end_pos_h = (self.WIDTH - self.MARGIN - self.SQUARE_SIZE // 2,
                        self.MARGIN + self.SQUARE_SIZE // 2 + i * self.SQUARE_SIZE)
            pygame.draw.line(self.screen, self.COLOR_GRID, start_pos_h, end_pos_h, 1)

            # Row labels
            label = self.font.render(str(i), True, self.COLOR_TEXT)
            self.screen.blit(label, (self.MARGIN - 30, self.MARGIN + self.SQUARE_SIZE // 2 +
                                    i * self.SQUARE_SIZE - label.get_height() // 2))

            start_pos_v = (self.MARGIN + self.SQUARE_SIZE // 2 + i * self.SQUARE_SIZE,
                          self.MARGIN + self.SQUARE_SIZE // 2)
            end_pos_v = (self.MARGIN + self.SQUARE_SIZE // 2 + i * self.SQUARE_SIZE,
                        self.HEIGHT - self.MARGIN - self.SQUARE_SIZE // 2 - self.BOTTOM_BAR_HEIGHT)
            pygame.draw.line(self.screen, self.COLOR_GRID, start_pos_v, end_pos_v, 1)

            # Column labels
            label = self.font.render(chr(ord('A') + i), True, self.COLOR_TEXT)
            self.screen.blit(label, (self.MARGIN + self.SQUARE_SIZE // 2 + i * self.SQUARE_SIZE -
                                    label.get_width() // 2, self.MARGIN - 30))

        # Draw star points
        star_points = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]
        for r, c in star_points:
            cx = self.MARGIN + self.SQUARE_SIZE // 2 + c * self.SQUARE_SIZE
            cy = self.MARGIN + self.SQUARE_SIZE // 2 + r * self.SQUARE_SIZE
            pygame.draw.circle(self.screen, self.COLOR_GRID, (cx, cy), 5)

        # Draw capture display background
        pygame.draw.rect(self.screen, self.COLOR_CAPTURE_BG,
                        (0, self.HEIGHT - self.BOTTOM_BAR_HEIGHT, self.WIDTH, self.BOTTOM_BAR_HEIGHT))

    def draw_pieces(self):
        """Draws the pieces on the board."""
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                player = self.board[r][c]
                if player != self.EMPTY:
                    cx = self.MARGIN + self.SQUARE_SIZE // 2 + c * self.SQUARE_SIZE
                    cy = self.MARGIN + self.SQUARE_SIZE // 2 + r * self.SQUARE_SIZE
                    radius = self.SQUARE_SIZE // 2 - 3
                    color = self.COLOR_BLACK if player == self.BLACK_PLAYER else self.COLOR_WHITE
                    pygame.draw.circle(self.screen, color, (cx, cy), radius)
                    if player == self.WHITE_PLAYER:
                        pygame.draw.circle(self.screen, self.COLOR_BLACK, (cx, cy), radius, 1)

    def draw_highlights(self):
        """Draws highlights for pending win line."""
        if self.game_state != "PENDING_WIN":
            return

        highlight_surface = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
        color = (*self.COLOR_HIGHLIGHT, int(self.pulse_alpha))
        radius = self.SQUARE_SIZE // 2 - 1
        pygame.draw.circle(highlight_surface, color,
                          (self.SQUARE_SIZE // 2, self.SQUARE_SIZE // 2), radius, 3)

        for r, c in self.pending_win_line:
            cx = self.MARGIN + self.SQUARE_SIZE // 2 + c * self.SQUARE_SIZE
            cy = self.MARGIN + self.SQUARE_SIZE // 2 + r * self.SQUARE_SIZE
            self.screen.blit(highlight_surface,
                           (cx - self.SQUARE_SIZE // 2, cy - self.SQUARE_SIZE // 2))

    def draw_status(self):
        """Draws the status message at the top."""
        if self.game_over:
            winner_name = "Black" if self.winner == self.BLACK_PLAYER else "White"
            message = f"Game Over! {winner_name} wins! (Press 'R' to Reset)"
            color = (180, 0, 0)

        elif self.game_state == "PENDING_WIN":
            pending_winner_name = "Black" if self.pending_win_player == self.BLACK_PLAYER else "White"
            opponent_name = "Black" if self.current_player == self.BLACK_PLAYER else "White"
            message = f"PENDING WIN for {pending_winner_name}! {opponent_name} must capture the line!"
            color = (200, 150, 0)

        elif (self.game_mode == "P_VS_AI" and self.current_player == self.AI_PLAYER):
            max_depth = self.config["algorithm_settings"]["max_depth"]
            message = f"AI is thinking... (Depth: {self.ai.algorithm.current_depth} / {max_depth})"
            color = (0, 0, 180)

        else:
            player_name = "Black" if self.current_player == self.BLACK_PLAYER else "White"
            message = f"{player_name}'s Turn (Mode: {self.game_mode} - 'M' to toggle)"
            color = self.COLOR_BLACK if self.current_player == self.BLACK_PLAYER else self.COLOR_TEXT

        status_text = self.font.render(message, True, color)
        text_rect = status_text.get_rect(center=(self.WIDTH // 2, self.MARGIN // 2))
        self.screen.blit(status_text, text_rect)

    def draw_captures(self):
        """Draws the capture count at the bottom."""
        black_cap_text = self.font.render(
            f"Black Captures: {self.captures[self.BLACK_PLAYER]}", True, self.COLOR_BLACK
        )
        self.screen.blit(black_cap_text, (self.MARGIN, self.HEIGHT - 35))

        white_cap_text = self.font.render(
            f"White Captures: {self.captures[self.WHITE_PLAYER]}", True, self.COLOR_BLACK
        )
        text_rect = white_cap_text.get_rect(right=self.WIDTH - self.MARGIN)
        self.screen.blit(white_cap_text, (text_rect.x, self.HEIGHT - 35))

    def draw_hover(self):
        """Draws the hover indicator."""
        if self.hover_pos is None:
            return

        r, c = self.hover_pos
        cx = self.MARGIN + self.SQUARE_SIZE // 2 + c * self.SQUARE_SIZE
        cy = self.MARGIN + self.SQUARE_SIZE // 2 + r * self.SQUARE_SIZE

        if self.hover_is_illegal:
            self.screen.blit(self.illegal_surface,
                           (cx - self.SQUARE_SIZE // 2, cy - self.SQUARE_SIZE // 2))
        else:
            radius = self.SQUARE_SIZE // 2 - 3
            temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = (*self.COLOR_BLACK, 100) if self.current_player == self.BLACK_PLAYER else (*self.COLOR_WHITE, 100)
            pygame.draw.circle(temp_surface, color, (radius, radius), radius)
            if self.current_player == self.WHITE_PLAYER:
                pygame.draw.circle(temp_surface, (*self.COLOR_BLACK, 100),
                                 (radius, radius), radius, 1)
            self.screen.blit(temp_surface, (cx - radius, cy - radius))

    def quit_game(self):
        """Quits the game."""
        pygame.quit()
        sys.exit()

