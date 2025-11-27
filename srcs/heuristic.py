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

        # Pre-allocated buffer for line values (avoid repeated allocations)
        self._line_buffer = [0] * 13

        # Numeric Pattern Constants
        # 0=Empty, 1=Player, 2=Opponent, 3=Boundary
        # We pre-compile these as tuples for fast matching
        self._init_patterns()

    def _init_patterns(self):
        """Initialize numeric patterns for scoring."""
        P = 1  # Player
        OPP = 2  # Opponent
        E = 0  # Empty
        X = 3  # Boundary

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
        # Ends with X or OPP
        self.PATS_CLOSED_FOUR = []
        for blocker in [X, OPP]:
            self.PATS_CLOSED_FOUR.append(make_pattern(blocker, P, P, P, P, E))
            self.PATS_CLOSED_FOUR.append(make_pattern(E, P, P, P, P, blocker))

        # --- Capture Threats ---
        self.PATS_CAPTURE_THREAT = [
            make_pattern(P, OPP, OPP, E),
            make_pattern(E, OPP, OPP, P)
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
        for blocker in [X, OPP]:
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
        for blocker in [X, OPP]:
            self.PATS_CLOSED_TWO.append(make_pattern(blocker, P, P, E))
            self.PATS_CLOSED_TWO.append(make_pattern(E, P, P, blocker))

    def score_line_numeric(self, line, current_captures=0, is_critical=False):
        """
        Scores a line using optimized single-pass pattern matching.
        Scans the line once and checks all relevant patterns at each position.
        """
        score = 0
        length = len(line)

        # Track what we've found to avoid duplicate counting
        found_win = False
        found_open_four = False
        found_broken_four = False
        found_closed_four = False
        found_capture_threat = False
        found_open_three = False
        found_closed_three = False
        found_broken_three = False
        found_open_two = False
        found_closed_two = False

        # Single pass through the line - check patterns at each position
        for i in range(length):
            # Five-in-a-row check
            # Note: In our variant with captures, 5-in-a-row is a PENDING win (can be broken)
            # Not a terminal win. So we return PENDING_WIN_SCORE, not WIN_SCORE.
            # Terminal wins (capture = 10 pieces) are handled in check_terminal_state.
            if not found_win and i <= length - 5:
                if (line[i] == 1 and line[i+1] == 1 and line[i+2] == 1 and
                    line[i+3] == 1 and line[i+4] == 1):
                    return self.PENDING_WIN_SCORE

            # Open Four: _OOOO_ (pattern length 6)
            if not found_open_four and i <= length - 6:
                if (line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and
                    line[i+3] == 1 and line[i+4] == 1 and line[i+5] == 0):
                    score += self.OPEN_FOUR_SCORE
                    found_open_four = True

            # Broken Fours (pattern length 7)
            if not found_broken_four and i <= length - 7:
                if ((line[i] == 0 and line[i+1] == 1 and line[i+2] == 0 and
                     line[i+3] == 1 and line[i+4] == 1 and line[i+5] == 1 and line[i+6] == 0) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and
                     line[i+3] == 1 and line[i+4] == 0 and line[i+5] == 1 and line[i+6] == 0) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and
                     line[i+3] == 0 and line[i+4] == 1 and line[i+5] == 1 and line[i+6] == 0)):
                    score += self.BROKEN_FOUR
                    found_broken_four = True

            # Closed Fours (pattern length 6)
            if not found_closed_four and i <= length - 6:
                blocker = line[i]
                if blocker in (2, 3):  # Opponent or boundary
                    if (line[i+1] == 1 and line[i+2] == 1 and
                        line[i+3] == 1 and line[i+4] == 1 and line[i+5] == 0):
                        score += self.CLOSED_FOUR
                        found_closed_four = True
                if line[i] == 0:
                    blocker_end = line[i+5]
                    if blocker_end in (2, 3):
                        if (line[i+1] == 1 and line[i+2] == 1 and
                            line[i+3] == 1 and line[i+4] == 1):
                            score += self.CLOSED_FOUR
                            found_closed_four = True

            # Capture Threats: POOE or EOOP (pattern length 4)
            if not found_capture_threat and i <= length - 4:
                if ((line[i] == 1 and line[i+1] == 2 and line[i+2] == 2 and line[i+3] == 0) or
                    (line[i] == 0 and line[i+1] == 2 and line[i+2] == 2 and line[i+3] == 1)):
                    if is_critical:
                        score += self.PENDING_WIN_SCORE
                    else:
                        pairs = current_captures // 2
                        if pairs >= 3:
                            score += 2000000
                        else:
                            multiplier = 1 + pairs
                            score += self.CAPTURE_THREAT_OPEN * multiplier * 1.5
                    found_capture_threat = True

            # Open Threes (pattern length 5)
            if not found_open_three and i <= length - 5:
                if ((line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and
                     line[i+3] == 1 and line[i+4] == 0) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and
                     line[i+3] == 0 and line[i+4] == 1) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 0 and
                     line[i+3] == 1 and line[i+4] == 1)):
                    score += self.OPEN_THREE
                    found_open_three = True

            # Closed Threes (pattern length 5)
            if not found_closed_three and i <= length - 5:
                blocker = line[i]
                if blocker in (2, 3):
                    if ((line[i+1] == 1 and line[i+2] == 1 and line[i+3] == 1 and line[i+4] == 0) or
                        (line[i+1] == 1 and line[i+2] == 1 and line[i+3] == 0 and line[i+4] == 1) or
                        (line[i+1] == 1 and line[i+2] == 0 and line[i+3] == 1 and line[i+4] == 1)):
                        score += self.CLOSED_THREE
                        found_closed_three = True
                if line[i] == 0:
                    blocker_end = line[i+4]
                    if blocker_end in (2, 3):
                        if ((line[i+1] == 1 and line[i+2] == 1 and line[i+3] == 1) or
                            (line[i+1] == 1 and line[i+2] == 0 and line[i+3] == 1) or
                            (line[i+1] == 1 and line[i+2] == 1 and line[i+3] == 0)):
                            score += self.CLOSED_THREE
                            found_closed_three = True

            # Broken Threes (pattern length 7)
            if not found_broken_three and i <= length - 7:
                if ((line[i] == 0 and line[i+1] == 1 and line[i+2] == 0 and
                     line[i+3] == 1 and line[i+4] == 0 and line[i+5] == 1 and line[i+6] == 0) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 0 and
                     line[i+3] == 0 and line[i+4] == 1 and line[i+5] == 1 and line[i+6] == 0) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and
                     line[i+3] == 0 and line[i+4] == 0 and line[i+5] == 1 and line[i+6] == 0)):
                    score += self.BROKEN_THREE
                    found_broken_three = True

            # Open Twos (pattern length 4)
            if not found_open_two and i <= length - 4:
                if ((line[i] == 0 and line[i+1] == 1 and line[i+2] == 1 and line[i+3] == 0) or
                    (line[i] == 0 and line[i+1] == 1 and line[i+2] == 0 and line[i+3] == 1)):
                    score += self.OPEN_TWO
                    found_open_two = True

            # Closed Twos (pattern length 4)
            if not found_closed_two and i <= length - 4:
                blocker = line[i]
                if blocker in (2, 3):
                    if line[i+1] == 1 and line[i+2] == 1 and line[i+3] == 0:
                        score += self.CLOSED_TWO
                        found_closed_two = True
                if line[i] == 0:
                    blocker_end = line[i+3]
                    if blocker_end in (2, 3) and line[i+1] == 1 and line[i+2] == 1:
                        score += self.CLOSED_TWO
                        found_closed_two = True

        return score

    def score_lines_at(self, r, c, board, player, opponent, is_critical=False, current_captures=0):
        """
        Scores the 4 lines (H, V, D1, D2) passing through (r,c).
        Uses numeric evaluation with optimized inline line extraction.
        """
        score = 0

        # Evaluate 4 directions with inline line extraction (avoids function calls)
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            # Fill the reusable line buffer
            for i in range(-6, 7):
                cr, cc = r + dr * i, c + dc * i
                idx = i + 6
                if not (0 <= cr < self.board_size and 0 <= cc < self.board_size):
                    self._line_buffer[idx] = 3  # Out of bounds
                else:
                    piece = board[cr * self.board_size + cc]
                    if piece == 0:
                        self._line_buffer[idx] = 0  # Empty
                    elif piece == player:
                        self._line_buffer[idx] = 1  # Player
                    else:  # piece == opponent
                        self._line_buffer[idx] = 2  # Opponent

            # Score the line (reads from self._line_buffer)
            score += self.score_line_numeric(self._line_buffer, current_captures, is_critical)

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
                            line_score = self.score_line_numeric(line_vals, my_captures, is_critical)
                            score += line_score

                            # If we found a 5-in-a-row (PENDING_WIN_SCORE), return immediately
                            # Don't accumulate multiple scores from the same 5-in-a-row pattern
                            # Note: We return PENDING_WIN_SCORE, not WIN_SCORE, because
                            # a 5-in-a-row can still be broken by capture in our variant
                            if line_score >= self.PENDING_WIN_SCORE:
                                return self.PENDING_WIN_SCORE

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
