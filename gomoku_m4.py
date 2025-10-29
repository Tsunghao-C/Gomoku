import copy  # We will need this for move simulation
import math  # For pulsing highlight
import sys
import time

import pygame

# --- Constants ---
# (Same as M3)
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
# --- New for M4 ---
COLOR_HIGHLIGHT = (255, 255, 0) # Yellow for pending win

EMPTY = 0
BLACK_PLAYER = 1
WHITE_PLAYER = 2

class GomokuGame:
    """
    Main class to manage the Gomoku game state and logic.
    Milestone 4: Added "Endgame Capture" (Pending Win) rule.
    """
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Gomoku AI Project - Milestone 4")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.SysFont("Inter", 24)

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

        # --- New for M4: Pending Win State ---
        self.game_state = "NORMAL" # Can be "NORMAL" or "PENDING_WIN"
        self.pending_win_player = None
        self.pending_win_line = [] # List of (r, c) tuples
        self.pulse_alpha = 0 # For highlight animation


    def run_game(self):
        """Main game loop."""
        clock = pygame.time.Clock()

        while True:
            # --- M4: Update pulse animation ---
            if self.game_state == "PENDING_WIN":
                # Create a pulsing effect (sine wave)
                self.pulse_alpha = (math.sin(time.time() * 4) + 1) / 2 * 255 # 0 -> 255 -> 0

            # --- M3: Update hover position ---
            if not self.game_over:
                self.update_hover(pygame.mouse.get_pos())
            else:
                self.hover_pos = None

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

                # --- M4: Block clicks if game is over, but not if pending ---
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    self.handle_mouse_click(self.hover_pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()

            # Drawing
            self.draw_board()
            self.draw_pieces()
            self.draw_highlights() # New for M4
            self.draw_status()
            self.draw_captures()
            self.draw_hover()

            pygame.display.flip()
            clock.tick(30) # Limit FPS

    def reset_game(self):
        """Resets the game to its initial state."""
        print("--- Game Reset ---")
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK_PLAYER
        self.game_over = False
        self.winner = None
        self.last_move_time = 0.0
        self.captures = {BLACK_PLAYER: 0, WHITE_PLAYER: 0}
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        # --- M4 Reset ---
        self.game_state = "NORMAL"
        self.pending_win_player = None
        self.pending_win_line = []


    def update_hover(self, pos):
        """ (Same as M3) """
        x, y = pos
        col = round((x - MARGIN - SQUARE_SIZE // 2) / SQUARE_SIZE)
        row = round((y - MARGIN - SQUARE_SIZE // 2) / SQUARE_SIZE)

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.board[row][col] == EMPTY:
                self.hover_pos = (row, col)
                is_legal, reason = self.is_legal_move(row, col, self.current_player, self.board)
                self.hover_is_illegal = not is_legal
                self.illegal_reason = reason
                return

        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""

    def handle_mouse_click(self, board_pos):
        """ --- Heavily Updated for M4 ---
        Implements the new game flow with "Pending Win" state.
        """
        if board_pos is None:
            return

        row, col = board_pos

        if self.hover_is_illegal:
            print(f"Invalid move: ({row}, {col}) is illegal ({self.illegal_reason}).")
            return

        # --- 1. MAKE THE MOVE ---
        player_name = "Black" if self.current_player == BLACK_PLAYER else "White"
        opponent_player = WHITE_PLAYER if self.current_player == BLACK_PLAYER else BLACK_PLAYER

        start_time = time.time()
        captured_pieces = self.make_move(row, col, self.current_player, self.board)
        end_time = time.time()
        self.last_move_time = end_time - start_time

        print(f"[{player_name}] moved to ({row}, {col})")
        if captured_pieces:
            print(f"!!! Captured {len(captured_pieces)} pieces at: {captured_pieces}")
            self.captures[self.current_player] += len(captured_pieces)
        print(f"Move calculation time: {self.last_move_time:.6f} seconds")

        # --- 2. CHECK FOR IMMEDIATE CAPTURE WIN ---
        if self.captures[self.current_player] >= (self.WIN_BY_CAPTURES * 2):
            self.game_over = True
            self.winner = self.current_player
            print(f"--- Game Over! {player_name} wins by {self.WIN_BY_CAPTURES} captures! ---")
            return # Game ends immediately

        # --- 3. CHECK IF THIS MOVE RESOLVED A "PENDING WIN" ---
        if self.game_state == "PENDING_WIN":
            # It was the opponent's turn to stop the pending win.
            # 'self.current_player' is the one who just moved (the opponent).
            # 'self.pending_win_player' is the one with the 5-in-a-row.

            move_broke_line = False
            if captured_pieces:
                for r_cap, c_cap in captured_pieces:
                    if (r_cap, c_cap) in self.pending_win_line:
                        move_broke_line = True
                        break

            if move_broke_line:
                # SUCCESS! The opponent broke the line.
                print(f"!!! {player_name} broke the 5-in-a-row! Game continues.")
                self.game_state = "NORMAL"
                self.pending_win_line = []
                self.pending_win_player = None
                # (Fall through to switch player)
            else:
                # FAILURE. The opponent moved, but didn't break the line.
                self.game_over = True
                self.winner = self.pending_win_player
                pending_winner_name = "Black" if self.pending_win_player == BLACK_PLAYER else "White"
                print(f"--- Game Over! {player_name} failed to break the line.")
                print(f"--- {pending_winner_name} wins by 5-in-a-row! ---")
                return # Game ends

        # --- 4. CHECK IF THIS MOVE *CREATED* A 5-IN-A-ROW (AND ISN'T A WIN YET) ---
        win_line = self.check_win(row, col, self.current_player, self.board)
        if win_line and not self.game_over:
            # This player just made a 5-in-a-row.
            print(f"!!! {player_name} created a 5-in-a-row! Pending Win!")
            self.game_state = "PENDING_WIN"
            self.pending_win_player = self.current_player
            self.pending_win_line = win_line
            # (Fall through to switch player so opponent can respond)

        # --- 5. SWITCH PLAYER ---
        if not self.game_over:
            self.current_player = opponent_player
            # Clear hover info
            self.hover_pos = None
            self.hover_is_illegal = False


    # ---
    # Core Game Logic Functions
    # ---

    def make_move(self, row, col, player, board):
        """ (Same as M3) """
        if board[row][col] != EMPTY:
            return []
        board[row][col] = player
        captured_pieces = self.check_and_apply_captures(row, col, player, board)
        return captured_pieces

    def check_and_apply_captures(self, last_row, last_col, player, board):
        """ (Same as M3) """
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
        """ --- Updated for M4 ---
        Checks for 5-in-a-row.
        If found, returns the list of (r, c) coordinates of the winning line.
        If not found, returns None.
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            win_line = [(last_row, last_col)]

            # Check positive direction
            for i in range(1, 5):
                r, c = last_row + dr * i, last_col + dc * i
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    win_line.append((r, c))
                else:
                    break
            # Check negative direction
            for i in range(1, 5):
                r, c = last_row - dr * i, last_col - dc * i
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    win_line.append((r, c))
                else:
                    break

            if len(win_line) >= 5:
                # We found a 5-in-a-row (or more)
                return win_line

        return None # No 5-in-a-row found

    # ---
    # M3 Rule-Checking Functions
    # ---

    def is_legal_move(self, row, col, player, board):
        """ (Same as M3) """
        if board[row][col] != EMPTY:
            return (False, "Occupied")

        sim_board = copy.deepcopy(board)
        sim_board[row][col] = player

        # As per M3, we check for double-threes *always*
        free_threes_count = self.count_free_threes_at(row, col, player, sim_board)

        if free_threes_count >= 2:
            return (False, "Illegal (Double-Three)")

        return (True, "Legal")

    def count_free_threes_at(self, r, c, player, board):
        """ (Same as M3) """
        count = 0
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            line = self.get_line_string(r, c, dr, dc, board, player, opponent)

            # Check for '01110' (EPPPE)
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

            # Check for '01101' (EPPEP)
            idx = line.find('EPPEP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break
                idx = line.find('EPPEP', idx + 1)

            if found_this_axis:
                continue

            # Check for '01011' (EPEPP)
            idx = line.find('EPEPP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    break
                idx = line.find('EPEPP', idx + 1)

        return count

    def get_line_string(self, r, c, dr, dc, board, player, opponent):
        """ (Same as M3) """
        line = [''] * 31
        for i in range(-15, 16):
            cr, cc = r + dr * i, c + dc * i
            idx = i + 15
            if not (0 <= cr < BOARD_SIZE and 0 <= cc < BOARD_SIZE):
                line[idx] = 'X'
            else:
                piece = board[cr][cc]
                if piece == EMPTY:
                    line[idx] = 'E'
                elif piece == player:
                    line[idx] = 'P'
                elif piece == opponent:
                    line[idx] = 'O'
        return "".join(line)


    # ---
    # Drawing Functions
    # ---

    def draw_board(self):
        """(Same as M3)"""
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
        """(Same as M3)"""
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
        """ --- New for M4 ---
        Draws a pulsing highlight over the pending win line.
        """
        if self.game_state != "PENDING_WIN":
            return

        # Use a temporary surface for alpha blending
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        # Set color and alpha
        color = (*COLOR_HIGHLIGHT, int(self.pulse_alpha))
        radius = SQUARE_SIZE // 2 - 1

        # Draw a transparent circle
        pygame.draw.circle(highlight_surface, color, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), radius, 3) # 3px wide line

        for r, c in self.pending_win_line:
            cx = MARGIN + SQUARE_SIZE // 2 + c * SQUARE_SIZE
            cy = MARGIN + SQUARE_SIZE // 2 + r * SQUARE_SIZE
            self.screen.blit(highlight_surface, (cx - SQUARE_SIZE // 2, cy - SQUARE_SIZE // 2))

    def draw_status(self):
        """ --- Updated for M4 ---
        Shows the "Pending Win" message.
        """
        if self.game_over:
            winner_name = "Black" if self.winner == BLACK_PLAYER else "White"
            message = f"Game Over! {winner_name} wins! (Press 'R' to Reset)"
            color = (180, 0, 0)

        elif self.game_state == "PENDING_WIN":
            pending_winner_name = "Black" if self.pending_win_player == BLACK_PLAYER else "White"
            opponent_name = "Black" if self.current_player == BLACK_PLAYER else "White"
            message = f"PENDING WIN for {pending_winner_name}! {opponent_name} must capture the line!"
            color = (200, 150, 0) # Dark yellow

        else: # Normal game state
            player_name = "Black" if self.current_player == BLACK_PLAYER else "White"
            message = f"{player_name}'s Turn"
            color = COLOR_BLACK if self.current_player == BLACK_PLAYER else COLOR_TEXT

        status_text = self.font.render(message, True, color)
        text_rect = status_text.get_rect(center=(WIDTH // 2, MARGIN // 2))
        self.screen.blit(status_text, text_rect)

    def draw_captures(self):
        """(Same as M3)"""
        black_cap_text = self.font.render(f"Black Captures: {self.captures[BLACK_PLAYER]}", True, COLOR_BLACK)
        self.screen.blit(black_cap_text, (MARGIN, HEIGHT - 35))

        white_cap_text = self.font.render(f"White Captures: {self.captures[WHITE_PLAYER]}", True, COLOR_BLACK)
        text_rect = white_cap_text.get_rect(right=WIDTH - MARGIN)
        self.screen.blit(white_cap_text, (text_rect.x, HEIGHT - 35))

    def draw_hover(self):
        """ (Same as M3) """
        if self.hover_pos is None:
            return
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
