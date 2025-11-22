"""
Main Gomoku game class that manages game state, rules, and UI rendering.
"""

import math
import sys
import time

import pygame

from srcs.GomokuAI import GomokuAI
from srcs.GomokuLogic import GomokuLogic


class GomokuGame:
    """
    Main class to manage the Gomoku game state and logic.
    """

    def __init__(self, config):
        # Store configuration
        self.config = config

        # Initialize Game Logic
        self.logic = GomokuLogic(config)

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
        self.menu_font = pygame.font.SysFont(ui_cfg["fonts"]["main_font"], 48)
        self.small_menu_font = pygame.font.SysFont(ui_cfg["fonts"]["main_font"], 32)

        # Game mode
        self.game_mode = game_cfg["default_game_mode"]

        # Game state
        self.app_state = "MENU"  # Start in menu
        self.menu_buttons = []   # Initialized in draw_menu or init

        # Aliases for logic state to minimize refactoring
        self.board = self.logic.board
        self.captures = self.logic.captures
        self.current_player = self.BLACK_PLAYER
        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
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

        # Suggested Move (for P_VS_P_SUGGESTED mode)
        self.suggested_move = None

        # Zobrist Hashing
        # Managed by GomokuLogic

        # AI
        self.ai = GomokuAI(config)

        # Start with empty board - human can place first move anywhere
        self.current_player = self.HUMAN_PLAYER
        self.logic.current_hash = self.logic.compute_initial_hash()
        self.current_hash = self.logic.current_hash # Keep local reference synced if needed, or property
        self.move_count = 0  # No moves yet

    @property
    def current_hash(self):
        return self.logic.current_hash

    @current_hash.setter
    def current_hash(self, value):
        self.logic.current_hash = value

    # ---
    # Game Loop
    # ---

    def run_game(self):
        """Main game loop."""
        clock = pygame.time.Clock()

        while True:
            # --- MENU STATE ---
            if self.app_state == "MENU":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_menu_click(event.pos)

                self.draw_menu()
                pygame.display.flip()
                clock.tick(30)
                continue

            # AI's turn
            if (self.game_mode == "P_VS_AI" and
                self.current_player == self.AI_PLAYER and
                not self.game_over and
                not self.ai.ai_is_thinking):

                self.ai.ai_is_thinking = True
                # Force status update
                self.draw_status()
                pygame.display.flip()
                self.run_ai_move()

            # AI Suggestion (P_VS_P_SUGGESTED) - White Player
            if (self.game_mode == "P_VS_P_SUGGESTED" and
                self.current_player == self.WHITE_PLAYER and
                not self.game_over and
                self.suggested_move is None and
                not self.ai.ai_is_thinking):

                self.ai.ai_is_thinking = True
                # Force status update
                self.draw_status()
                pygame.display.flip()
                self.generate_suggestion()

            # Update pulsing highlight for pending win
            if self.game_state == "PENDING_WIN":
                self.pulse_alpha = (math.sin(time.time() * self.PULSE_SPEED) + 1) / 2 * 255

            # Check if it's human's turn
            is_human_turn = (self.game_mode == "P_VS_P") or \
                           (self.game_mode == "P_VS_P_SUGGESTED") or \
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
                    if event.key == pygame.K_ESCAPE:
                        self.app_state = "MENU"
                        self.reset_game()

            # Render
            self.draw_board()
            self.draw_pieces()
            self.draw_highlights()
            self.draw_suggestion()
            self.draw_status()
            self.draw_captures()
            self.draw_hover()

            pygame.display.flip()
            clock.tick(30)

    def reset_game(self):
        """Resets the game to initial state."""
        print("--- Game Reset ---")

        # Preserve current game mode
        current_mode = self.game_mode

        self.logic.reset()
        self.board = self.logic.board  # Re-bind alias
        self.captures = self.logic.captures  # Re-bind alias

        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        self.game_state = "NORMAL"
        self.pending_win_player = None
        self.pending_win_line = []
        self.suggested_move = None

        self.ai.ai_is_thinking = False
        self.ai.algorithm.clear_transposition_table()

        self.current_player = self.HUMAN_PLAYER

        # Restore game mode (unless it was explicitly changed before reset)
        # Note: In handle_menu_click, we set self.game_mode BEFORE calling reset_game,
        # so this logic preserves that selection.
        self.game_mode = current_mode

        self.move_count = 0  # Reset to 0 (no initial move)

    def update_hover(self, pos):
        """Updates hover position and checks if move is legal."""
        x, y = pos
        col = round((x - self.MARGIN - self.SQUARE_SIZE // 2) / self.SQUARE_SIZE)
        row = round((y - self.MARGIN - self.SQUARE_SIZE // 2) / self.SQUARE_SIZE)

        if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
            # 1D Access
            idx = row * self.BOARD_SIZE + col
            if self.board[idx] == self.EMPTY:
                self.hover_pos = (row, col)
                is_legal, reason = self.logic.is_legal_move(row, col, self.current_player,
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
        captured_pieces, new_hash = self.logic.make_move(row, col, player, self.board,
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
        win_line = self.logic.check_win(row, col, player, self.board)
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

            # Reset suggestion for new turn
            self.suggested_move = None

            self.hover_pos = None
            self.hover_is_illegal = False

    # ---
    # AI Move
    # ---

    def run_ai_move(self):
        """Runs the AI to get the best move."""
        best_move, time_taken = self.ai.get_best_move(
            self.board, self.captures, self.current_hash, self.AI_PLAYER,
            self.WIN_BY_CAPTURES, self.logic, self.move_count
        )

        self.last_move_time = time_taken

        if best_move is None:
            print("AI has no legal moves left!")
            return

        self.handle_move(best_move[0], best_move[1], self.AI_PLAYER)

    def generate_suggestion(self):
        """Calculates a move for suggestion but doesn't apply it."""
        print("--- generating suggestion ---")
        best_move, time_taken = self.ai.get_best_move(
            self.board, self.captures, self.current_hash, self.WHITE_PLAYER,
            self.WIN_BY_CAPTURES, self.logic, self.move_count
        )

        self.last_move_time = time_taken
        self.suggested_move = best_move
        self.ai.ai_is_thinking = False
        print(f"Suggestion generated: {best_move}")

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
                idx = r * self.BOARD_SIZE + c
                player = self.board[idx]
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

    def draw_suggestion(self):
        """Draws the suggested move (ghost stone)."""
        if self.suggested_move is None:
            return

        r, c = self.suggested_move
        cx = self.MARGIN + self.SQUARE_SIZE // 2 + c * self.SQUARE_SIZE
        cy = self.MARGIN + self.SQUARE_SIZE // 2 + r * self.SQUARE_SIZE

        # Draw a semi-transparent white circle with a distinctive border
        ghost_surface = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
        radius = self.SQUARE_SIZE // 2 - 3

        # Semi-transparent white fill
        pygame.draw.circle(ghost_surface, (*self.COLOR_WHITE, 128), (self.SQUARE_SIZE // 2, self.SQUARE_SIZE // 2), radius)
        # Green border to indicate suggestion
        pygame.draw.circle(ghost_surface, (0, 255, 0), (self.SQUARE_SIZE // 2, self.SQUARE_SIZE // 2), radius, 2)

        self.screen.blit(ghost_surface, (cx - self.SQUARE_SIZE // 2, cy - self.SQUARE_SIZE // 2))

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

        elif (self.game_mode == "P_VS_P_SUGGESTED" and
              self.current_player == self.WHITE_PLAYER and
              self.suggested_move is None):
            max_depth = self.config["algorithm_settings"]["max_depth"]
            message = f"AI is thinking for suggestion... (Depth: {self.ai.algorithm.current_depth} / {max_depth})"
            color = (0, 100, 0)

        else:
            player_name = "Black" if self.current_player == self.BLACK_PLAYER else "White"
            message = f"{player_name}'s Turn (Mode: {self.game_mode} - 'M' to toggle)"
            color = self.COLOR_BLACK if self.current_player == self.BLACK_PLAYER else self.COLOR_TEXT

        status_text = self.font.render(message, True, color)

        text_rect = status_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - self.BOTTOM_BAR_HEIGHT - 15))
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

    # ---
    # Menu Functions
    # ---

    def draw_menu(self):
        """Draws the main menu."""
        self.screen.fill(self.COLOR_BOARD)

        # Title
        title_surf = self.menu_font.render("GOMOKU AI", True, self.COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 4))
        self.screen.blit(title_surf, title_rect)

        # Buttons
        button_width = 300
        button_height = 60
        spacing = 20
        start_y = self.HEIGHT // 2 - 50

        self.menu_buttons = []
        options = [
            ("Player vs AI", "P_VS_AI"),
            ("Player vs Player", "P_VS_P"),
            ("PvP (Suggested)", "P_VS_P_SUGGESTED"),
            ("Quit", "QUIT")
        ]

        for i, (text, mode) in enumerate(options):
            y = start_y + i * (button_height + spacing)
            rect = pygame.Rect((self.WIDTH - button_width) // 2, y, button_width, button_height)
            self.menu_buttons.append((rect, mode))

            # Draw button background
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = rect.collidepoint(mouse_pos)
            color = self.COLOR_HIGHLIGHT if is_hovered else self.COLOR_WHITE

            # Draw shadow
            pygame.draw.rect(self.screen, (100, 100, 100), rect.move(4, 4), border_radius=10)
            # Draw button
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, self.COLOR_BLACK, rect, 2, border_radius=10)

            # Draw text
            text_surf = self.small_menu_font.render(text, True, self.COLOR_BLACK)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

        # Instructions
        info_text = self.font.render("Press ESC during game to return here", True, (100, 100, 100))
        info_rect = info_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 40))
        self.screen.blit(info_text, info_rect)

    def handle_menu_click(self, pos):
        """Handles clicks in the menu."""
        for rect, mode in self.menu_buttons:
            if rect.collidepoint(pos):
                if mode == "QUIT":
                    self.quit_game()
                else:
                    self.game_mode = mode
                    self.app_state = "PLAYING"
                    self.reset_game()  # Reset with new mode
