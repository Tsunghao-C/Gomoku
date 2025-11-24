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
        self.OPEN_FOUR_SCORE = scores["open_four"]
        self.BROKEN_FOUR = scores["broken_four"]
        self.CLOSED_FOUR = scores["closed_four"]
        self.OPEN_THREE = scores["open_three"]
        self.BROKEN_THREE = scores["broken_three"]
        self.CLOSED_THREE = scores["closed_three"]
        self.OPEN_TWO = scores["open_two"]
        self.CLOSED_TWO = scores["closed_two"]
        self.CAPTURE_THREAT_OPEN = scores["capture_threat_open"]
        self.CAPTURE_SCORE = scores["capture_score"]

        # Store capture defense config for position evaluation
        self.capture_defense_cfg = heuristic_cfg.get("capture_defense", {})

        # Numeric Pattern Constants
        # 0=Empty, 1=Player, 2=Opponent, 3=Boundary
        # We pre-compile these as tuples for fast matching
        self._init_patterns()

    def _init_patterns(self):
        """Initialize numeric patterns for scoring."""
        P = 1
        O = 2
        E = 0
        X = 3

        # Helper to create pattern variants
        def make_pattern(*args):
            return tuple(args)

        # --- 5-in-a-row ---
        self.PAT_WIN = make_pattern(P, P, P, P, P)

        # --- Open Fours ---
        self.PAT_OPEN_FOUR = make_pattern(E, P, P, P, P, E)

        # --- Broken Fours ---
        self.PATS_BROKEN_FOUR = [
            make_pattern(E, P, E, P, P, P, E),
            make_pattern(E, P, P, P, E, P, E),
            make_pattern(E, P, P, E, P, P, E)
        ]

        # --- Closed Fours ---
        # Ends with X or O
        self.PATS_CLOSED_FOUR = []
        for blocker in [X, O]:
            self.PATS_CLOSED_FOUR.append(make_pattern(blocker, P, P, P, P, E))
            self.PATS_CLOSED_FOUR.append(make_pattern(E, P, P, P, P, blocker))

        # --- Capture Threats ---
        self.PATS_CAPTURE_THREAT = [
            make_pattern(P, O, O, E),
            make_pattern(E, O, O, P)
        ]

        # --- Open Threes ---
        self.PATS_OPEN_THREE = [
            make_pattern(E, P, P, P, E),
            make_pattern(E, P, P, E, P),
            make_pattern(E, P, E, P, P)  # This is actually broken 3? No, standard pattern list treats this as open 3 equivalent in threat
        ]
        # Note: Original code treated EPPEP and EPEPP as Open Three (10,000)
        # EPPEP is _O_OO -> effectively a broken three but treated as high value

        # --- Closed Threes ---
        self.PATS_CLOSED_THREE = []
        for blocker in [X, O]:
            # Consecutive
            self.PATS_CLOSED_THREE.append(make_pattern(blocker, P, P, P, E))
            self.PATS_CLOSED_THREE.append(make_pattern(E, P, P, P, blocker))
            # Gap
            self.PATS_CLOSED_THREE.append(make_pattern(blocker, P, P, E, P))
            self.PATS_CLOSED_THREE.append(make_pattern(E, P, E, P, blocker)) # EPEPX
            self.PATS_CLOSED_THREE.append(make_pattern(blocker, P, E, P, P))
            self.PATS_CLOSED_THREE.append(make_pattern(P, P, E, P, blocker)) # PPEPX?? No, wait.
            # Original: XPPEP, EPEPX, OPPEP, EPEPO
            # Check EPEPX -> E, P, E, P, X
            self.PATS_CLOSED_THREE.append(make_pattern(E, P, E, P, blocker))

        # --- Broken Threes ---
        self.PATS_BROKEN_THREE = [
            make_pattern(E, P, E, P, E, P, E),
            make_pattern(E, P, E, E, P, P, E),
            make_pattern(E, P, P, E, E, P, E)
        ]

        # --- Open Twos ---
        self.PATS_OPEN_TWO = [
            make_pattern(E, P, P, E),
            make_pattern(E, P, E, P)
        ]

        # --- Closed Twos ---
        self.PATS_CLOSED_TWO = []
        for blocker in [X, O]:
            self.PATS_CLOSED_TWO.append(make_pattern(blocker, P, P, E))
            self.PATS_CLOSED_TWO.append(make_pattern(E, P, P, blocker))

    def score_line_numeric(self, line, current_captures=0, is_critical=False):
        """
        Scores a line (list of integers) based on pattern recognition.
        Uses sliding window or fast sequential checks.
        """
        # Convert to tuple for faster matching if needed, or just iterate
        # Since we are searching for sub-sequences, we can convert to string of bytes/chars?
        # Or just iterate. Iterating a list of 13 items is fast.

        score = 0
        length = len(line)

        # Optimization: Convert line to a tuple once
        line_tuple = tuple(line)

        # Helper to search sub-tuple
        def has_pattern(pattern):
            pat_len = len(pattern)
            for i in range(length - pat_len + 1):
                if line_tuple[i:i+pat_len] == pattern:
                    return True
            return False

        # --- Win ---
        if has_pattern(self.PAT_WIN):
            return self.WIN_SCORE

        # --- Open Four ---
        if has_pattern(self.PAT_OPEN_FOUR):
            score += self.OPEN_FOUR_SCORE  # Unstoppable (Open 4)

        # --- Broken Fours ---
        for pat in self.PATS_BROKEN_FOUR:
            if has_pattern(pat):
                score += self.BROKEN_FOUR

        # --- Closed Fours ---
        for pat in self.PATS_CLOSED_FOUR:
            if has_pattern(pat):
                score += self.CLOSED_FOUR

        # --- Capture Threats ---
        for pat in self.PATS_CAPTURE_THREAT:
            if has_pattern(pat):
                if is_critical:
                     score += self.PENDING_WIN_SCORE
                else:
                    # Scale capture threat based on current captures
                    # Logic: As we get closer to losing by captures, threats become exponentially more dangerous.
                    # 0 pairs: Base (15k)
                    # 1 pair:  Base * 2 (30k)
                    # 2 pairs: Base * 4 (60k)
                    # 3 pairs: Base * 8 + Boost (Huge warning before critical)

                    pairs = current_captures // 2

                    # Special check for "Pre-Critical" state (e.g. 3 pairs out of 5 needed)
                    # We want to start panicking BEFORE we hit 4 pairs (which is the critical threshold)
                    if pairs >= 3:
                        score += 2000000  # 2M - prioritize defending this over almost anything except Win/Open4
                    else:
                        multiplier = 1 + pairs
                        score += self.CAPTURE_THREAT_OPEN * multiplier * 1.5

        # --- Open Threes ---
        for pat in self.PATS_OPEN_THREE:
            if has_pattern(pat):
                score += self.OPEN_THREE

        # --- Closed Threes ---
        for pat in self.PATS_CLOSED_THREE:
            if has_pattern(pat):
                score += self.CLOSED_THREE

        # --- Broken Threes ---
        for pat in self.PATS_BROKEN_THREE:
            if has_pattern(pat):
                score += self.BROKEN_THREE

        # --- Open Twos ---
        for pat in self.PATS_OPEN_TWO:
            if has_pattern(pat):
                score += self.OPEN_TWO

        # --- Closed Twos ---
        for pat in self.PATS_CLOSED_TWO:
            if has_pattern(pat):
                score += self.CLOSED_TWO

        return score

    def score_lines_at(self, r, c, board, player, opponent, is_critical=False, current_captures=0):
        """
        Scores the 4 lines (H, V, D1, D2) passing through (r,c).
        Uses numeric evaluation.
        """
        from srcs.utils import get_line_values

        score = 0
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            line_vals = get_line_values(r, c, dr, dc, board, player, opponent, self.board_size)
            score += self.score_line_numeric(line_vals, current_captures, is_critical)
        return score

    def calculate_player_score(self, board, captures, player, win_by_captures):
        """
        Calculates the total score for a player across the entire board.
        """
        from srcs.utils import get_line_coords, get_line_values

        score = 0
        opponent = 2 if player == 1 else 1

        my_captures = captures[player]

        if my_captures >= (win_by_captures * 2):
            return self.WIN_SCORE

        # Non-linear capture scoring
        # Make early captures valuable, but later captures increasingly so.
        # We use an exponential scale to discourage "trading" captures for position too easily.

        pairs = my_captures // 2

        # Exponential curve: 1, 3, 9, 27...
        # 1 pair:  20k * 1.5 = 30k
        # 2 pairs: 20k * 4.0 = 80k
        # 3 pairs: 20k * 10.0 = 200k
        # 4 pairs: 20k * 50.0 = 1M (Almost critical)

        if pairs == 0:
             multiplier = 0 # No score
        elif pairs == 1:
             multiplier = 1.5
        elif pairs == 2:
             multiplier = 4.0
        elif pairs == 3:
             multiplier = 10.0
        else:
             multiplier = 50.0

        score += (pairs * self.CAPTURE_SCORE) * multiplier

        # Critical capture check: if we are 1 pair away from winning, threats are deadly
        is_critical = my_captures >= (win_by_captures * 2 - 2)

        lines_seen = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                idx = r * self.board_size + c
                if board[idx] != 0:
                    for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                        line_coords = get_line_coords(r, c, dr, dc, self.board_size)
                        line_key = tuple(sorted(line_coords))

                        if line_key not in lines_seen:
                            lines_seen.add(line_key)
                            line_vals = get_line_values(r, c, dr, dc, board, player, opponent, self.board_size)
                            score += self.score_line_numeric(line_vals, my_captures, is_critical)

        return score

    def evaluate_board(self, board, captures, player, win_by_captures):
        """
        Evaluates the entire board from the perspective of the given player.
        """
        opponent = 2 if player == 1 else 1
        my_score = self.calculate_player_score(board, captures, player, win_by_captures)
        opponent_score = self.calculate_player_score(board, captures, opponent, win_by_captures)

        # Basic score: My potential - Opponent potential
        final_score = my_score - (opponent_score * 1.1)
        return final_score
