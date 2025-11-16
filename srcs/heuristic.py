"""
Heuristic evaluation module for Gomoku AI.
Contains all scoring constants and pattern recognition functions.
"""


class HeuristicEvaluator:
    """
    Evaluates board positions using pattern recognition and scoring.
    """

    def __init__(self, config):
        # Extract settings from config
        game_cfg = config["game_settings"]
        heuristic_cfg = config["heuristic_settings"]
        scores = heuristic_cfg["scores"]

        self.board_size = game_cfg["board_size"]

        # Load all heuristic scores from config
        self.WIN_SCORE = scores["win_score"]
        self.PENDING_WIN_SCORE = scores["pending_win_score"]
        self.OPEN_FOUR = scores["open_four"]
        self.BROKEN_FOUR = scores["broken_four"]
        self.CLOSED_FOUR = scores["closed_four"]
        self.OPEN_THREE = scores["open_three"]
        self.BROKEN_THREE = scores["broken_three"]
        self.CLOSED_THREE = scores["closed_three"]
        self.OPEN_TWO = scores["open_two"]
        self.CLOSED_TWO = scores["closed_two"]
        self.CAPTURE_THREAT_OPEN = scores["capture_threat_open"]
        self.CAPTURE_SCORE = scores["capture_score"]
        self.CAPTURE_SETUP_BRIDGE = scores["capture_setup_bridge"]

    def score_line_string(self, line):
        """
        Scores a line string based on pattern recognition.
        'P' = Player, 'O' = Opponent, 'E' = Empty, 'X' = Bound
        """
        score = 0

        # --- 5-in-a-row (Win) ---
        if "PPPPP" in line:
            return self.PENDING_WIN_SCORE

        # --- Open Fours (1,000,000) ---
        if "EPPPPE" in line:
            score += self.OPEN_FOUR

        # --- Broken Fours (400,000) ---
        # Pattern: 4 pieces with one gap (creates forcing threats)
        if "EPEPPPE" in line or "EPPPEPE" in line:  # _O_OOO_ or _OOO_O_
            score += self.BROKEN_FOUR
        if "EPPEPPE" in line:  # _OO_OO_
            score += self.BROKEN_FOUR

        # --- Closed Fours (50,000) ---
        if ("XPPPPE" in line or "EPPPPX" in line or
            "OPPPPE" in line or "EPPPPO" in line):
            score += self.CLOSED_FOUR

        # --- Capture Threats (30,000) ---
        if "POOE" in line or "EOOP" in line:
            score += self.CAPTURE_THREAT_OPEN

        # --- Open Threes (10,000) ---
        if "EPPPE" in line:  # _OOO_
            score += self.OPEN_THREE
        if "EPPEP" in line:  # _O_OO
            score += self.OPEN_THREE
        if "EPEPP" in line:  # _OO_O
            score += self.OPEN_THREE

        # --- Closed Threes (5,000) ---
        # Three consecutive pieces, one end blocked
        if ("XPPPE" in line or "EPPPX" in line or
            "OPPPE" in line or "EPPPO" in line):
            score += self.CLOSED_THREE
        # Three pieces with one gap, one end blocked
        if ("XPPEP" in line or "EPEPX" in line or
            "OPPEP" in line or "EPEPO" in line):
            score += self.CLOSED_THREE

        # --- Broken Threes (4,000) ---
        # Pattern: 3 pieces with gaps between them
        if "EPEPEPE" in line:  # _O_O_O_
            score += self.BROKEN_THREE
        if "EPEEPPE" in line or "EPPEEPE" in line:  # _O__OO_ or _OO__O_
            score += self.BROKEN_THREE

        # --- Capture Setups (1,000) ---
        if "POEP" in line:
            score += self.CAPTURE_SETUP_BRIDGE

        # --- Open Twos (100) ---
        if "EPPE" in line:  # _OO_
            score += self.OPEN_TWO
        if "EPEP" in line:  # _O_O_
            score += self.OPEN_TWO

        # --- Closed Twos (10) ---
        if ("XPPE" in line or "EPPX" in line or
            "OPPE" in line or "EPPO" in line):
            score += self.CLOSED_TWO

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
            return self.WIN_SCORE

        score += (captures[player] // 2) * self.CAPTURE_SCORE

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
