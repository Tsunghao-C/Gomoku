"""
Core game logic for Gomoku.
Encapsulates board state, rules, move validation, and win conditions.
"""

import copy
import random

from srcs.utils import get_line_string


class GomokuLogic:
    """
    Manages the board state and enforces Gomoku rules.
    Shared between GUI game and Headless game/AI.
    """

    def __init__(self, config):
        self.config = config

        # Extract game settings
        game_cfg = config["game_settings"]
        self.BOARD_SIZE = game_cfg["board_size"]
        self.EMPTY = game_cfg["empty"]
        self.BLACK_PLAYER = game_cfg["black_player"]
        self.WHITE_PLAYER = game_cfg["white_player"]
        self.WIN_BY_CAPTURES = game_cfg["win_by_captures"]

        # Initialize board and state
        self.board = [[self.EMPTY for _ in range(self.BOARD_SIZE)]
                      for _ in range(self.BOARD_SIZE)]
        self.captures = {self.BLACK_PLAYER: 0, self.WHITE_PLAYER: 0}

        # Zobrist Hashing
        self.zobrist_table = []
        self.current_hash = 0
        self.init_zobrist()
        self.current_hash = self.compute_initial_hash()

        # Debug flags
        self.debug_terminal_states = False
        if "ai_settings" in config and "debug" in config["ai_settings"]:
            self.debug_terminal_states = config["ai_settings"]["debug"].get("show_terminal_states", False)

    def init_zobrist(self):
        """Initializes the Zobrist hash table with random values."""
        # Use fixed seed for reproducibility across runs if desired,
        # but GomokuGame used random.randint without seed and Headless used seed 42.
        # We'll stick to random.randint but maybe seed it if strictly needed.
        # Headless sets seed 42, let's respect that if we want consistent tests.
        # However, for normal play random is fine.

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
                if piece != self.EMPTY: # Should be empty initially, but good for robustness
                    h ^= self.zobrist_table[r][c][piece]
        return h

    def reset(self):
        """Resets the board and state."""
        self.board = [[self.EMPTY for _ in range(self.BOARD_SIZE)]
                      for _ in range(self.BOARD_SIZE)]
        self.captures = {self.BLACK_PLAYER: 0, self.WHITE_PLAYER: 0}
        self.current_hash = self.compute_initial_hash()

    # --- Move Execution (Low Level) ---

    def make_move(self, row, col, player, board, zobrist_hash):
        """
        Makes a move on the board and updates the Zobrist hash.
        Used by AI for search (stateless regarding self.board usually).

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

    # --- Rules & Validation ---

    def is_legal_move(self, row, col, player, board):
        """
        Checks if a move is legal (not occupied and doesn't create double-three).
        Returns: (is_legal, reason)
        """
        if not (0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE):
             return (False, "Out of bounds")

        if board[row][col] != self.EMPTY:
            return (False, "Occupied")

        # Use a copy to check for double-three
        # Note: deeply copying board can be slow. Ideally we'd just set/unset,
        # but count_free_threes_at might be complex.
        board_copy = copy.deepcopy(board)

        # Check captures from this position (captures might affect free threes?)
        # The original code did check_and_apply_captures on the copy first.
        captured_pieces = self.check_and_apply_captures(row, col, player, board_copy) # noqa: F841
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

    # --- Win Checking ---

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
            return True

        return False
