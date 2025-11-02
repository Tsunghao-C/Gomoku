"""
Heuristic evaluation module for Gomoku AI.
Contains all scoring constants and pattern recognition functions.
"""

# --- Heuristic Score Constants ---
WIN_SCORE = 1000000000
PENDING_WIN_SCORE = 50000000
OPEN_FOUR = 1000000  # _OOOO_
BROKEN_FOUR = 400000  # _OO_OO_ or _O_OOO_
CLOSED_FOUR = 50000  # XOOOO_
OPEN_THREE = 10000  # _OOO_
BROKEN_THREE = 4000  # _O_OO_
CLOSED_THREE = 5000  # XOOO_
OPEN_TWO = 100  # _OO_
CLOSED_TWO = 10  # XOO_
CAPTURE_THREAT_OPEN = 30000  # (E.g., P O O E)
CAPTURE_SCORE = 2500  # Score per pair (so *2)
CAPTURE_SETUP_BRIDGE = 1000  # (E.g., P O E P)


class HeuristicEvaluator:
    """
    Evaluates board positions using pattern recognition and scoring.
    """

    def __init__(self, board_size):
        self.board_size = board_size

    def score_line_string(self, line):
        """
        Scores a line string based on pattern recognition.
        'P' = Player, 'O' = Opponent, 'E' = Empty, 'X' = Bound
        """
        score = 0

        # --- 5-in-a-row (Win) ---
        if "PPPPP" in line:
            return PENDING_WIN_SCORE

        # --- Open Fours (1,000,000) ---
        if "EPPPPE" in line:
            score += OPEN_FOUR

        # --- Broken Fours (400,000) ---
        # Pattern: 4 pieces with one gap (creates forcing threats)
        if "EPEPPPE" in line or "EPPPEPE" in line:  # _O_OOO_ or _OOO_O_
            score += BROKEN_FOUR
        if "EPPEPPE" in line:  # _OO_OO_
            score += BROKEN_FOUR

        # --- Closed Fours (50,000) ---
        if ("XPPPPE" in line or "EPPPPX" in line or
            "OPPPPE" in line or "EPPPPO" in line):
            score += CLOSED_FOUR

        # --- Capture Threats (30,000) ---
        if "POOE" in line or "EOOP" in line:
            score += CAPTURE_THREAT_OPEN

        # --- Open Threes (10,000) ---
        if "EPPPE" in line:  # _OOO_
            score += OPEN_THREE
        if "EPPEP" in line:  # _O_OO
            score += OPEN_THREE
        if "EPEPP" in line:  # _OO_O
            score += OPEN_THREE

        # --- Closed Threes (5,000) ---
        # Three consecutive pieces, one end blocked
        if ("XPPPE" in line or "EPPPX" in line or
            "OPPPE" in line or "EPPPO" in line):
            score += CLOSED_THREE
        # Three pieces with one gap, one end blocked
        if ("XPPEP" in line or "EPEPX" in line or
            "OPPEP" in line or "EPEPO" in line):
            score += CLOSED_THREE

        # --- Broken Threes (4,000) ---
        # Pattern: 3 pieces with gaps between them
        if "EPEPEPE" in line:  # _O_O_O_
            score += BROKEN_THREE
        if "EPEEPPE" in line or "EPPEEPE" in line:  # _O__OO_ or _OO__O_
            score += BROKEN_THREE

        # --- Capture Setups (1,000) ---
        if "POEP" in line:
            score += CAPTURE_SETUP_BRIDGE

        # --- Open Twos (100) ---
        if "EPPE" in line:  # _OO_
            score += OPEN_TWO
        if "EPEP" in line:  # _O_O_
            score += OPEN_TWO

        # --- Closed Twos (10) ---
        if ("XPPE" in line or "EPPX" in line or
            "OPPE" in line or "EPPO" in line):
            score += CLOSED_TWO

        return score

    def score_lines_at(self, r, c, board, player, opponent):
        """
        Scores the 4 lines (H, V, D1, D2) passing through (r,c)
        for the given player.
        """
        from srcs.utils import get_line_string

        score = 0
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            line_str = get_line_string(r, c, dr, dc, board, player, opponent, self.board_size)
            score += self.score_line_string(line_str)
        return score

    def calculate_player_score(self, board, captures, player, win_by_captures):
        """
        Calculates the total score for a player across the entire board.
        """
        from srcs.utils import get_line_coords, get_line_string

        score = 0
        opponent = 2 if player == 1 else 1

        if captures[player] >= (win_by_captures * 2):
            return WIN_SCORE

        score += (captures[player] // 2) * CAPTURE_SCORE

        lines_seen = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] != 0:  # Scan from any piece
                    for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                        line_coords = get_line_coords(r, c, dr, dc, self.board_size)
                        line_key = tuple(sorted(line_coords))

                        if line_key not in lines_seen:
                            lines_seen.add(line_key)
                            line_str_p = get_line_string(r, c, dr, dc, board, player, opponent, self.board_size)
                            score += self.score_line_string(line_str_p)
        return score

    def evaluate_board(self, board, captures, player, win_by_captures):
        """
        Evaluates the entire board from the perspective of the given player.
        Returns: my_score - opponent_score * 1.1
        """
        opponent = 2 if player == 1 else 1
        my_score = self.calculate_player_score(board, captures, player, win_by_captures)
        opponent_score = self.calculate_player_score(board, captures, opponent, win_by_captures)
        return my_score - opponent_score * 1.1
