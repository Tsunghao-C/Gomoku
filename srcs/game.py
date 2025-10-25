import sys
from enum import Enum

import pygame

from srcs.ai_engine import GomokuAI
from srcs.ai_engine import Player as AIPlayer

# Constants
BOARD_SIZE = 19
CELL_SIZE = 30
BOARD_OFFSET = 50
WINDOW_WIDTH = BOARD_SIZE * CELL_SIZE + 400  # Extra space for AI visualization
WINDOW_HEIGHT = BOARD_SIZE * CELL_SIZE + 100


class Player(Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2


class GomokuGame:
    def __init__(self):
        # board 19 x 19 metrix representing the board state (0 = Empty, 1 = Black, 2 = White)
        self.board = [[Player.EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = Player.BLACK
        self.game_over = False
        self.winner = None

    def reset(self):
        self.board = [[Player.EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = Player.BLACK
        self.game_over = False
        self.winner = None

    def make_move(self, row: int, col: int) -> bool:
        """Make a move on the board. Returns True if move is valid."""
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] == Player.EMPTY and not self.game_over:
            self.board[row][col] = self.current_player
            # Check win status, otherwise change current player.
            if self.check_win(row, col):
                self.game_over = True
                self.winner = self.current_player
            else:
                self.current_player = Player.WHITE if self.current_player == Player.BLACK else Player.BLACK
            return True
        return False

    def check_win(self, row: int, col: int) -> bool:
        """Check if the last move resulted in a win (5 in a row)."""
        player = self.board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonal

        for dr, dc in directions:
            count = 1  # Count the current stone

            # Check in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == player:
                count += 1
                r, c = r + dr, c + dc

            # Check in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == player:
                count += 1
                r, c = r - dr, c - dc

            if count >= 5:
                return True

        return False


class GomokuUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Gomoku AI Game - Thinking Visualization")
        self.clock = pygame.time.Clock()
        self.game = GomokuGame()
        self.ai = GomokuAI(max_depth=10)  # Start with smaller depth for faster initial moves
        self.ai_thinking = False
        self.last_ai_stats = {}
        self.thinking_progress = []

    def draw_board(self):
        """Draw the game board."""
        self.screen.fill((222, 184, 135))  # Wood color background

        # Draw grid lines
        for i in range(BOARD_SIZE):
            # Vertical lines
            pygame.draw.line(
                self.screen,
                (0, 0, 0), # Black lines
                (BOARD_OFFSET + i * CELL_SIZE, BOARD_OFFSET),
                (BOARD_OFFSET + i * CELL_SIZE, BOARD_OFFSET + (BOARD_SIZE - 1) * CELL_SIZE),
            )
            # Horizontal lines
            pygame.draw.line(
                self.screen,
                (0, 0, 0),
                (BOARD_OFFSET, BOARD_OFFSET + i * CELL_SIZE),
                (BOARD_OFFSET + (BOARD_SIZE - 1) * CELL_SIZE, BOARD_OFFSET + i * CELL_SIZE),
            )

        # Draw stones
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.game.board[row][col] != Player.EMPTY:
                    x = BOARD_OFFSET + col * CELL_SIZE
                    y = BOARD_OFFSET + row * CELL_SIZE
                    color = (0, 0, 0) if self.game.board[row][col] == Player.BLACK else (255, 255, 255)
                    pygame.draw.circle(self.screen, color, (x, y), CELL_SIZE // 2 - 2)
                    pygame.draw.circle(self.screen, (0, 0, 0), (x, y), CELL_SIZE // 2 - 2, 2)

    def get_board_position(self, mouse_pos: tuple[int, int]) -> tuple[int, int] | None:
        """Convert mouse position to board coordinates."""
        x, y = mouse_pos
        col = round((x - BOARD_OFFSET) / CELL_SIZE)
        row = round((y - BOARD_OFFSET) / CELL_SIZE)

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return (row, col)
        return None

    def make_ai_move(self):
        """Make AI move and update stats."""
        import threading

        def ai_thread():
            # Convert board to AI format
            ai_board = [[AIPlayer.EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.game.board[row][col] == Player.BLACK:
                        ai_board[row][col] = AIPlayer.BLACK
                    elif self.game.board[row][col] == Player.WHITE:
                        ai_board[row][col] = AIPlayer.WHITE

            # Get AI move
            ai_player = AIPlayer.WHITE if self.game.current_player == Player.WHITE else AIPlayer.BLACK
            move, score, stats = self.ai.get_best_move(ai_board, ai_player)

            if move:
                self.game.make_move(move[0], move[1])
                self.last_ai_stats = stats
                self.thinking_progress = stats.get("thinking_process", [])

            self.ai_thinking = False

        # Run AI in separate thread to avoid blocking UI
        thread = threading.Thread(target=ai_thread)
        thread.daemon = True
        thread.start()

    def draw_ai_visualization(self):
        """Draw AI thinking process visualization."""
        if not self.last_ai_stats:
            return

        # Position for AI panel (right side of board)
        panel_x = BOARD_SIZE * CELL_SIZE + 20
        panel_y = 10
        panel_width = 350
        panel_height = WINDOW_HEIGHT - 20

        # Draw background panel
        pygame.draw.rect(self.screen, (240, 240, 240), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (0, 0, 0), (panel_x, panel_y, panel_width, panel_height), 2)

        # Title
        font_title = pygame.font.Font(None, 24)
        title = font_title.render("AI Thinking Process", True, (0, 0, 0))
        self.screen.blit(title, (panel_x + 10, panel_y + 10))

        y_offset = panel_y + 40

        # Basic stats
        font_small = pygame.font.Font(None, 18)
        stats = [
            f"Time: {self.last_ai_stats.get('calculation_time', 0):.3f}s",
            f"Nodes: {self.last_ai_stats.get('nodes_evaluated', 0):,}",
            f"Cache Hits: {self.last_ai_stats.get('cache_hits', 0):,}",
            f"Depth: {self.last_ai_stats.get('depth_searched', 0)}",
        ]

        for stat in stats:
            stat_surface = font_small.render(stat, True, (0, 0, 0))
            self.screen.blit(stat_surface, (panel_x + 10, y_offset))
            y_offset += 25

        # Performance indicator
        calculation_time = self.last_ai_stats.get('calculation_time', 0)
        if calculation_time > 0.5:
            color = (255, 0, 0)  # Red - too slow
            status = "SLOW"
        elif calculation_time > 0.2:
            color = (255, 165, 0)  # Orange - moderate
            status = "MODERATE"
        else:
            color = (0, 255, 0)  # Green - fast
            status = "FAST"

        perf_text = font_small.render(f"Performance: {status}", True, color)
        self.screen.blit(perf_text, (panel_x + 10, y_offset))
        y_offset += 30

        # Thinking process by depth
        if self.thinking_progress:
            font_smaller = pygame.font.Font(None, 16)
            header = font_smaller.render("Depth Analysis:", True, (0, 0, 0))
            self.screen.blit(header, (panel_x + 10, y_offset))
            y_offset += 20

            for i, step in enumerate(self.thinking_progress[-8:]):  # Show last 8 depths
                depth = step.get('depth', 0)
                move = step.get('best_move', (0, 0))
                score = step.get('score', 0)
                nodes = step.get('nodes_evaluated', 0)
                time_elapsed = step.get('time_elapsed', 0)

                # Color code based on score
                if score > 1000:
                    score_color = (0, 150, 0)  # Green - very good
                elif score > 100:
                    score_color = (0, 100, 0)  # Dark green - good
                elif score > 0:
                    score_color = (100, 100, 0)  # Yellow - neutral
                else:
                    score_color = (150, 0, 0)  # Red - bad

                depth_text = f"D{depth}: ({move[0]},{move[1]}) Score:{score:.0f}"
                depth_surface = font_smaller.render(depth_text, True, score_color)
                self.screen.blit(depth_surface, (panel_x + 20, y_offset))

                # Additional info
                info_text = f"  Nodes:{nodes:,} Time:{time_elapsed:.2f}s"
                info_surface = font_smaller.render(info_text, True, (100, 100, 100))
                self.screen.blit(info_surface, (panel_x + 20, y_offset + 15))
                y_offset += 35

        # Current thinking indicator
        if self.ai_thinking:
            thinking_text = font_small.render("AI is thinking...", True, (0, 100, 0))
            self.screen.blit(thinking_text, (panel_x + 10, y_offset))

            # Show current search progress if available
            current_search = self.last_ai_stats.get('current_search', {})
            if current_search:
                current_depth = current_search.get('current_depth', 0)
                current_move = current_search.get('current_move', (0, 0))
                moves_evaluated = current_search.get('moves_evaluated', 0)
                best_move_so_far = current_search.get('best_move_so_far', (0, 0))
                best_score_so_far = current_search.get('best_score_so_far', 0)

                progress_text = f"Searching depth {current_depth}..."
                progress_surface = font_smaller.render(progress_text, True, (0, 100, 0))
                self.screen.blit(progress_surface, (panel_x + 10, y_offset + 25))

                if current_move != (0, 0):
                    move_text = f"Evaluating: ({current_move[0]},{current_move[1]})"
                    move_surface = font_smaller.render(move_text, True, (0, 0, 150))
                    self.screen.blit(move_surface, (panel_x + 10, y_offset + 45))

                if best_move_so_far != (0, 0):
                    best_text = f"Best so far: ({best_move_so_far[0]},{best_move_so_far[1]}) Score:{best_score_so_far:.0f}"
                    best_surface = font_smaller.render(best_text, True, (0, 150, 0))
                    self.screen.blit(best_surface, (panel_x + 10, y_offset + 65))

                moves_text = f"Moves evaluated: {moves_evaluated}"
                moves_surface = font_smaller.render(moves_text, True, (100, 100, 100))
                self.screen.blit(moves_surface, (panel_x + 10, y_offset + 85))

    def run(self):
        """Main game loop."""
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.game.game_over and not self.ai_thinking:
                        pos = self.get_board_position(event.pos)
                        if pos:
                            if self.game.make_move(pos[0], pos[1]):
                                # If human made a move, let AI make a move
                                if not self.game.game_over:
                                    self.ai_thinking = True
                                    self.make_ai_move()
                elif event.type == pygame.KEYDOWN:
                    # if key is "R" for reset, reset everything
                    if event.key == pygame.K_r:
                        self.game.reset()
                        self.ai_thinking = False
                        self.last_ai_stats = {}
                        self.thinking_progress = []

            self.draw_board()

            # Display game status
            font = pygame.font.Font(None, 36)
            if self.game.game_over:
                winner_text = "Black Wins!" if self.game.winner == Player.BLACK else "White Wins!"
                text = font.render(winner_text, True, (255, 0, 0))
            elif self.ai_thinking:
                text = font.render("AI Thinking...", True, (0, 100, 0))
            else:
                player_text = "Black's Turn" if self.game.current_player == Player.BLACK else "White's Turn"
                text = font.render(player_text, True, (0, 0, 0))

            self.screen.blit(text, (10, 10))

            # Display AI stats and thinking process
            self.draw_ai_visualization()

            # Instructions
            font_small = pygame.font.Font(None, 24)
            instructions = font_small.render("Press R to reset", True, (0, 0, 0))
            self.screen.blit(instructions, (10, WINDOW_HEIGHT - 30))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()
