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

        # Store capture defense config for position evaluation
        self.capture_defense_cfg = heuristic_cfg.get("capture_defense", {})

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
        Includes capture vulnerability penalties.
        Returns: my_score - opponent_score * 1.1 - vulnerability_penalty
        """
        opponent = 2 if player == 1 else 1
        my_score = self.calculate_player_score(board, captures, player, win_by_captures)
        opponent_score = self.calculate_player_score(board, captures, opponent, win_by_captures)

        # Calculate vulnerability penalty for this position
        vulnerability_penalty = self._calculate_position_vulnerability(
            board, captures, player, opponent, win_by_captures
        )

        return my_score - (opponent_score * 1.1) - vulnerability_penalty

    def _calculate_position_vulnerability(self, board, captures, player, opponent, win_by_captures):
        """
        Calculates vulnerability penalty for the current board position.
        This is called for EVERY position in the minimax tree.

        Returns:
            int: Penalty to subtract from position evaluation
        """
        # Get capture defense config
        if not hasattr(self, 'capture_defense_cfg') or not self.capture_defense_cfg.get('enable', True):
            return 0

        vulnerability_score = 0
        opponent_stones_captured = captures[opponent]

        # Count vulnerable AI stones on the board
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == player:
                    # Check if this stone is in a vulnerable position
                    if self._is_stone_in_vulnerable_position(r, c, player, opponent, board):
                        vulnerability_score += 1

        # Apply escalating penalties based on game state
        winning_threshold = win_by_captures * 2
        critical_threshold = self.capture_defense_cfg.get('critical_threshold', 8)
        warning_threshold = self.capture_defense_cfg.get('warning_threshold', 6)
        early_warning_threshold = self.capture_defense_cfg.get('early_warning_threshold', 4)

        critical_penalty = self.capture_defense_cfg.get('critical_penalty', 800000)
        warning_penalty = self.capture_defense_cfg.get('warning_penalty', 300000)
        early_warning_penalty = self.capture_defense_cfg.get('early_warning_penalty', 150000)
        desperate_penalty = self.capture_defense_cfg.get('desperate_penalty', 3000000)
        trap_penalty = self.capture_defense_cfg.get('trap_detection_penalty', 400000)

        # Base penalty (always applied)
        base_penalty = trap_penalty * vulnerability_score

        # Escalating penalties based on capture count
        if opponent_stones_captured >= winning_threshold - 2:
            return base_penalty + (desperate_penalty * vulnerability_score)
        elif opponent_stones_captured >= critical_threshold:
            return base_penalty + (critical_penalty * vulnerability_score)
        elif opponent_stones_captured >= warning_threshold:
            return base_penalty + (warning_penalty * vulnerability_score)
        elif opponent_stones_captured >= early_warning_threshold:
            return base_penalty + (early_warning_penalty * vulnerability_score)
        else:
            return base_penalty

    def _is_stone_in_vulnerable_position(self, r, c, player, opponent, board):
        """
        Check if a stone at (r, c) is in a position where opponent could capture it.

        Vulnerable patterns:
        - O-P-P-E (opponent can play at E to capture)
        - E-P-P-O (opponent can play at E to capture)
        - Surrounded by 2+ opponent stones
        """
        # Check all 8 directions for capture patterns
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            for direction in [1, -1]:
                dr_check = dr * direction
                dc_check = dc * direction

                # Look for O-P-P-E or E-P-P-O patterns
                r1, c1 = r + dr_check, c + dc_check
                r_before, c_before = r - dr_check, c - dc_check
                r_after, c_after = r + 2 * dr_check, c + 2 * dc_check

                if not (0 <= r1 < self.board_size and 0 <= c1 < self.board_size):
                    continue

                # Pattern: O-[this stone]-P-E or E-P-[this stone]-O
                if board[r1][c1] == player:
                    # Check for opponent on one side and empty on other
                    if (0 <= r_before < self.board_size and 0 <= c_before < self.board_size and
                        0 <= r_after < self.board_size and 0 <= c_after < self.board_size):

                        if (board[r_before][c_before] == opponent and board[r_after][c_after] == 0):
                            return True
                        if (board[r_after][c_after] == opponent and board[r_before][c_before] == 0):
                            return True

        # Check if surrounded by opponent stones
        adjacent_opponent = 0
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < self.board_size and 0 <= nc < self.board_size and
                board[nr][nc] == opponent):
                adjacent_opponent += 1

        return adjacent_opponent >= 2
