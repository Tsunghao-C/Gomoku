import copy  # We will need this for move simulation
import sys
import time

import pygame

# --- Constants ---
# (Same as M2)
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
# --- New for M3 ---
COLOR_ILLEGAL = (255, 0, 0, 150) # For visualizing illegal moves

EMPTY = 0
BLACK_PLAYER = 1
WHITE_PLAYER = 2

class GomokuGame:
    """
    Main class to manage the Gomoku game state and logic.
    Milestone 3: Added Forbidden Double-Three rule (Rule 9 & 10).
                 Refactored core logic to be stateless (for AI).
    """
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Gomoku AI Project - Milestone 3")
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

        # --- New for M3: Hover & Illegal Move UI ---
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""
        # Create a semi-transparent surface for the illegal 'X'
        self.illegal_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.line(self.illegal_surface, COLOR_ILLEGAL, (5, 5), (SQUARE_SIZE - 5, SQUARE_SIZE - 5), 4)
        pygame.draw.line(self.illegal_surface, COLOR_ILLEGAL, (5, SQUARE_SIZE - 5), (SQUARE_SIZE - 5, 5), 4)


    def run_game(self):
        """Main game loop."""
        clock = pygame.time.Clock()

        while True:
            # --- M3: Update hover position ---
            if not self.game_over:
                self.update_hover(pygame.mouse.get_pos())
            else:
                self.hover_pos = None

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    # M3: We now use the stored hover position
                    self.handle_mouse_click(self.hover_pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()

            # Drawing
            self.draw_board()
            self.draw_pieces()
            self.draw_status()
            self.draw_captures()
            self.draw_hover() # New for M3

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

    def update_hover(self, pos):
        """ --- New for M3 ---
        Checks the board position under the mouse and determines if it's an illegal move.
        """
        x, y = pos
        col = round((x - MARGIN - SQUARE_SIZE // 2) / SQUARE_SIZE)
        row = round((y - MARGIN - SQUARE_SIZE // 2) / SQUARE_SIZE)

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.board[row][col] == EMPTY:
                self.hover_pos = (row, col)
                # Check legality using the *main* game board
                is_legal, reason = self.is_legal_move(row, col, self.current_player, self.board)
                self.hover_is_illegal = not is_legal
                self.illegal_reason = reason
                return

        # If not a valid empty square, clear hover info
        self.hover_pos = None
        self.hover_is_illegal = False
        self.illegal_reason = ""

    def handle_mouse_click(self, board_pos):
        """ --- Updated for M3 ---
        Uses the pre-calculated hover_pos to make a move.
        """
        if board_pos is None:
            # User clicked off-board
            return

        row, col = board_pos

        if self.hover_is_illegal:
            print(f"Invalid move: ({row}, {col}) is illegal ({self.illegal_reason}).")
            return

        if self.board[row][col] == EMPTY:
            start_time = time.time()

            # --- M3 Refactor: Call stateless functions with self.board ---
            # We are now modifying the *main* board
            captured_pieces = self.make_move(row, col, self.current_player, self.board)

            end_time = time.time()
            self.last_move_time = end_time - start_time

            player_name = "Black" if self.current_player == BLACK_PLAYER else "White"
            print(f"[Human] {player_name} moved to ({row}, {col})")

            if captured_pieces:
                print(f"!!! Captured {len(captured_pieces)} pieces at: {captured_pieces}")
                self.captures[self.current_player] += len(captured_pieces)

            print(f"Move calculation time: {self.last_move_time:.6f} seconds")

            # --- M3 Refactor: Check win using self.board ---
            # 1. Check for win by 5-in-a-row
            # (In M4, this will change to a "pending win")
            if self.check_win(row, col, self.current_player, self.board):
                self.game_over = True
                self.winner = self.current_player
                print(f"--- Game Over! {player_name} wins by 5-in-a-row! ---")

            # 2. Check for win by captures
            elif self.captures[self.current_player] >= (self.WIN_BY_CAPTURES * 2):
                self.game_over = True
                self.winner = self.current_player
                print(f"--- Game Over! {player_name} wins by {self.WIN_BY_CAPTURES} captures! ---")

            else:
                # Switch player
                self.current_player = WHITE_PLAYER if self.current_player == BLACK_PLAYER else BLACK_PLAYER
                # Clear hover info after move
                self.hover_pos = None
                self.hover_is_illegal = False
        else:
            print(f"Invalid move: ({row}, {col}) is already occupied.")

    # ---
    # Milestones 2 & 3: Core Game Logic Functions
    # These functions are now "stateless" - they operate on the
    # 'board' you pass them. This is CRITICAL for the AI.
    # ---

    def make_move(self, row, col, player, board):
        """
        (M3 Refactor)
        Places a piece on the *given* board and applies captures.
        Returns a list of (r, c) tuples of captured pieces.
        """
        if board[row][col] != EMPTY:
            return []

        board[row][col] = player
        # Call the refactored capture check
        captured_pieces = self.check_and_apply_captures(row, col, player, board)
        return captured_pieces

    def check_and_apply_captures(self, last_row, last_col, player, board):
        """
        (M3 Refactor)
        Checks for captures on the *given* board.
        If a capture occurs, it modifies the *given* board.
        """
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

                # Capture! Modify the board
                board[r1][c1] = EMPTY
                board[r2][c2] = EMPTY

                all_captured.append((r1, c1))
                all_captured.append((r2, c2))
        return all_captured

    def check_win(self, last_row, last_col, player, board):
        """
        (M3 Refactor)
        Checks for 5-in-a-row on the *given* board.
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1
            # Check positive direction
            for i in range(1, 5):
                r, c = last_row + dr * i, last_col + dc * i
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    count += 1
                else:
                    break
            # Check negative direction
            for i in range(1, 5):
                r, c = last_row - dr * i, last_col - dc * i
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    count += 1
                else:
                    break
            if count >= 5:
                return True
        return False

    # ---
    # Milestone 3: New Rule-Checking Functions
    # ---

    def is_legal_move(self, row, col, player, board):
        """
        (New for M3)
        Checks if a move is legal according to Rule 10 (Forbidden Double-Three).
        Returns (bool, reason_string)
        """
        if board[row][col] != EMPTY:
            return (False, "Occupied")

        # --- Rule 10: "No double-threes" ---
        # We must simulate the move to see what it creates.

        # 1. Create a deep copy of the board to simulate on.
        # This is essential.
        sim_board = copy.deepcopy(board)

        # 2. Simulate the move
        sim_board[row][col] = player

        # 3. Check for captures.
        # (This is here for the *original* rule. Based on your new
        # clarification, we IGNORE this check for legality)
        # sim_captures = self.check_and_apply_captures(row, col, player, sim_board)
        # if len(sim_captures) > 0:
        #     return (True, "Legal (Capture)") # <-- This is the old "exception" logic

        # 4. As per new clarification, *always* check for double-threes.
        # We check on the 'sim_board' *after* the piece was placed.
        free_threes_count = self.count_free_threes_at(row, col, player, sim_board)

        if free_threes_count >= 2:
            return (False, "Illegal (Double-Three)")

        # We could add checks for double-fours and overlines here if needed.
        # For now, we only check what was requested.

        return (True, "Legal")

    def count_free_threes_at(self, r, c, player, board):
        """
        (New for M3)
        Counts the number of "free-three" patterns (Rule 9)
        that are *completed* or *created* by the piece at (r,c).
        This function checks the 'board' *after* the piece has been placed.
        """
        count = 0
        opponent = WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

        # Check all 4 axes (horizontal, vertical, 2 diagonals)
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:

            # Get a string representation of the line in this axis,
            # centered on the new move (r,c).
            line = self.get_line_string(r, c, dr, dc, board, player, opponent)

            # 'line' is a string like "..OEEPPPEE..P"
            # The piece at (r,c) is *always* at index 15.

            # --- Check for '01110' (EPPPE) ---
            # e.g., "EEPPPEE" - new move could be P at idx 2, 3, or 4
            # We just need to find the pattern and see if it includes index 15
            idx = line.find('EPPPE')
            found_this_axis = False
            while idx != -1:
                # Check if this pattern includes our move (center index 15)
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break # Only count 1 per direction
                idx = line.find('EPPPE', idx + 1)

            if found_this_axis:
                continue # Found one, skip to next direction

            # --- Check for '01101' (EPPEP) ---
            # e.g., "EEPPEPE"
            idx = line.find('EPPEP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    found_this_axis = True
                    break
                idx = line.find('EPPEP', idx + 1)

            if found_this_axis:
                continue

            # --- Check for '01011' (EPEPP) ---
            # e.g., "EEPEPPE"
            idx = line.find('EPEPP')
            while idx != -1:
                if idx <= 15 < (idx + 5):
                    count += 1
                    # found_this_axis = True # No need, it's the last check
                    break
                idx = line.find('EPEPP', idx + 1)

        return count


    def get_line_string(self, r, c, dr, dc, board, player, opponent):
        """
        (New for M3) Helper for pattern matching.
        Gets a string representation of a line (max 15 back, 15 fwd)
        centered at (r,c).
        'P' = player, 'O' = opponent, 'E' = empty, 'X' = off-board
        The piece at (r,c) will be at index 15.
        """
        line = [''] * 31 # 15 back, 1 center, 15 forward

        for i in range(-15, 16):
            cr, cc = r + dr * i, c + dc * i

            idx = i + 15 # Center index (0-30)

            if not (0 <= cr < BOARD_SIZE and 0 <= cc < BOARD_SIZE):
                line[idx] = 'X' # Off-board
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
    # M1/M2 Drawing Functions (Updated for M3)
    # ---

    def draw_board(self):
        """(Same as M2, just adjusted height)"""
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
        """(Same as M2)"""
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

    def draw_status(self):
        """(Same as M2)"""
        if self.game_over:
            winner_name = "Black" if self.winner == BLACK_PLAYER else "White"
            message = f"Game Over! {winner_name} wins! (Press 'R' to Reset)"
            color = (180, 0, 0)
        else:
            player_name = "Black" if self.current_player == BLACK_PLAYER else "White"
            message = f"{player_name}'s Turn"
            color = COLOR_BLACK if self.current_player == BLACK_PLAYER else COLOR_TEXT

        status_text = self.font.render(message, True, color)
        text_rect = status_text.get_rect(center=(WIDTH // 2, MARGIN // 2))
        self.screen.blit(status_text, text_rect)

    def draw_captures(self):
        """(Same as M2)"""
        black_cap_text = self.font.render(f"Black Captures: {self.captures[BLACK_PLAYER]}", True, COLOR_BLACK)
        self.screen.blit(black_cap_text, (MARGIN, HEIGHT - 35))

        white_cap_text = self.font.render(f"White Captures: {self.captures[WHITE_PLAYER]}", True, COLOR_BLACK)
        text_rect = white_cap_text.get_rect(right=WIDTH - MARGIN)
        self.screen.blit(white_cap_text, (text_rect.x, HEIGHT - 35))

    def draw_hover(self):
        """ --- New for M3 ---
        Draws a preview of the piece or an illegal 'X'
        """
        if self.hover_pos is None:
            return

        r, c = self.hover_pos
        cx = MARGIN + SQUARE_SIZE // 2 + c * SQUARE_SIZE
        cy = MARGIN + SQUARE_SIZE // 2 + r * SQUARE_SIZE

        if self.hover_is_illegal:
            # Draw the 'X'
            self.screen.blit(self.illegal_surface, (cx - SQUARE_SIZE // 2, cy - SQUARE_SIZE // 2))
        else:
            # Draw a faint preview of the piece
            radius = SQUARE_SIZE // 2 - 3
            # We need a temporary surface for transparency
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
