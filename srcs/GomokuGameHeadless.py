"""
Headless version of Gomoku game for automated testing.
No pygame GUI - pure game logic for fast automated testing.
"""


from srcs.GomokuAI import GomokuAI


class GomokuGameHeadless:
    """
    Headless Gomoku game engine for automated testing.
    Supports AI vs AI games without GUI overhead.
    """

    def __init__(self, config, player1_config=None, player2_config=None):
        """
        Initialize headless game.
        
        Args:
            config: Base game configuration
            player1_config: Optional separate config for player 1 AI
            player2_config: Optional separate config for player 2 AI
        """
        self.config = config

        # Extract game settings
        game_cfg = config["game_settings"]
        self.BOARD_SIZE = game_cfg["board_size"]
        self.EMPTY = game_cfg["empty"]
        self.BLACK_PLAYER = game_cfg["black_player"]
        self.WHITE_PLAYER = game_cfg["white_player"]
        self.WIN_BY_CAPTURES = game_cfg["win_by_captures"]

        # Initialize game state
        self.board = [[self.EMPTY for _ in range(self.BOARD_SIZE)]
                      for _ in range(self.BOARD_SIZE)]
        self.captures = {self.BLACK_PLAYER: 0, self.WHITE_PLAYER: 0}
        self.current_player = self.BLACK_PLAYER
        self.move_count = 0
        self.game_over = False
        self.winner = None

        # Game history for analysis
        self.move_history = []
        self.time_history = []
        self.depth_history = []

        # Initialize AIs with separate configs if provided
        self.ai1 = GomokuAI(player1_config or config)
        self.ai2 = GomokuAI(player2_config or config)

        # Zobrist hashing
        self.zobrist_table = None
        self.current_hash = None
        self.init_zobrist()
        self.current_hash = self.compute_initial_hash()

    def init_zobrist(self):
        """Initialize Zobrist hash table."""
        import random
        random.seed(42)  # Consistent seed for reproducibility

        self.zobrist_table = [
            [
                [random.getrandbits(64) for _ in range(3)]
                for _ in range(self.BOARD_SIZE)
            ]
            for _ in range(self.BOARD_SIZE)
        ]

    def compute_initial_hash(self):
        """Compute initial hash for empty board."""
        h = 0
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                piece = self.board[r][c]
                if piece != self.EMPTY:
                    h ^= self.zobrist_table[r][c][piece]
        return h

    def apply_move(self, row, col, player):
        """
        Make a move and apply captures (for actual gameplay).
        
        Returns:
            bool: True if move was successful
        """
        is_legal, _ = self.is_legal_move(row, col, player, self.board)
        if not is_legal:
            return False

        # Place stone
        old_hash = self.current_hash
        self.board[row][col] = player
        self.current_hash ^= self.zobrist_table[row][col][player]

        # Apply captures
        captured_pieces = self.check_and_apply_captures(row, col, player, self.board)
        self.captures[player] += len(captured_pieces)

        # Record move
        self.move_history.append((row, col, player, len(captured_pieces)))
        self.move_count += 1

        # Check win condition
        if self.check_win(row, col, player):
            self.game_over = True
            self.winner = player
        elif self.captures[player] >= self.WIN_BY_CAPTURES * 2:
            self.game_over = True
            self.winner = player

        return True

    def is_legal_move(self, row, col, player, board):
        """Check if move is legal."""
        if not (0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE):
            return False, "Out of bounds"

        if board[row][col] != self.EMPTY:
            return False, "Square occupied"

        # Check double-free-three rule
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER
        board[row][col] = player
        free_threes = self.count_free_threes_at(row, col, player, opponent, board)
        board[row][col] = self.EMPTY

        if free_threes >= 2:
            return False, "Double free three"

        return True, ""

    def count_free_threes_at(self, r, c, player, opponent, board):
        """Count free threes at position."""
        count = 0
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            line = []
            for i in range(-4, 5):
                nr, nc = r + i * dr, c + i * dc
                if 0 <= nr < self.BOARD_SIZE and 0 <= nc < self.BOARD_SIZE:
                    line.append(board[nr][nc])
                else:
                    line.append(-1)

            line_str = ""
            for val in line:
                if val == player:
                    line_str += "P"
                elif val == opponent:
                    line_str += "O"
                elif val == self.EMPTY:
                    line_str += "E"
                else:
                    line_str += "X"

            if "EPPPE" in line_str:
                count += 1

        return count

    def check_and_apply_captures(self, row, col, player, board):
        """Check and apply captures around the placed stone."""
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER
        captured = []

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            r1, c1 = row + dr, col + dc
            r2, c2 = row + 2 * dr, col + 2 * dc
            r3, c3 = row + 3 * dr, col + 3 * dc

            if (0 <= r3 < self.BOARD_SIZE and 0 <= c3 < self.BOARD_SIZE):
                if (board[r1][c1] == opponent and
                    board[r2][c2] == opponent and
                    board[r3][c3] == player):

                    board[r1][c1] = self.EMPTY
                    board[r2][c2] = self.EMPTY
                    # Only update zobrist hash if this is the main board
                    if board is self.board:
                        self.current_hash ^= self.zobrist_table[r1][c1][opponent]
                        self.current_hash ^= self.zobrist_table[r2][c2][opponent]
                    captured.extend([(r1, c1), (r2, c2)])

        return captured

    # Method for minimax search (called by AI)
    def make_move(self, row, col, player, board, zobrist_hash):
        """
        Makes a move on the board and updates the Zobrist hash (for minimax search).
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
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER
        for (cr, cc) in captured_pieces:
            zobrist_hash ^= self.zobrist_table[cr][cc][opponent]
            zobrist_hash ^= self.zobrist_table[cr][cc][self.EMPTY]

        return captured_pieces, zobrist_hash

    def undo_move(self, r, c, player, board, captured_pieces, old_capture_count, captures, zobrist_hash):
        """Undo a move (for minimax search)."""
        opponent = self.WHITE_PLAYER if player == self.BLACK_PLAYER else self.BLACK_PLAYER

        # Restore captured pieces
        if captured_pieces:
            for (cr, cc) in captured_pieces:
                board[cr][cc] = opponent
                zobrist_hash ^= self.zobrist_table[cr][cc][self.EMPTY]
                zobrist_hash ^= self.zobrist_table[cr][cc][opponent]

        captures[player] = old_capture_count

        # Remove the piece
        board[r][c] = self.EMPTY
        zobrist_hash ^= self.zobrist_table[r][c][player]
        zobrist_hash ^= self.zobrist_table[r][c][self.EMPTY]

        return zobrist_hash

    def check_terminal_state(self, board, captures, player, row, col, win_by_captures):
        """
        Check if the game is in a terminal state after a move at (row, col).
        Returns True if the game should end (win by 5-in-a-row or by captures).
        """
        # DEBUG: Check win by captures
        if captures[player] >= win_by_captures * 2:
            print(f"    DEBUG check_terminal_state: Player {player} wins by captures!")
            print(f"      Has {captures[player]} >= {win_by_captures * 2} needed")
            return True

        # Check win by 5-in-a-row
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            count = 1

            for direction in [1, -1]:
                r, c = row + dr * direction, col + dc * direction
                while (0 <= r < self.BOARD_SIZE and
                       0 <= c < self.BOARD_SIZE and
                       board[r][c] == player):
                    count += 1
                    r += dr * direction
                    c += dc * direction

            if count >= 5:
                print(f"    DEBUG check_terminal_state: Player {player} wins by 5-in-a-row!")
                print(f"      At position ({row}, {col}), count: {count}, direction: ({dr}, {dc})")
                # DEBUG: Show the actual line
                line_debug = []
                for i in range(-4, 5):
                    nr, nc = row + i*dr, col + i*dc
                    if 0 <= nr < self.BOARD_SIZE and 0 <= nc < self.BOARD_SIZE:
                        line_debug.append(f"({nr},{nc})={board[nr][nc]}")
                    else:
                        line_debug.append("X")
                print(f"      Line: {' '.join(line_debug)}")
                return True

        return False

    def check_win(self, row, col, player):
        """Check if player won by 5-in-a-row."""
        for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            count = 1

            for direction in [1, -1]:
                r, c = row + dr * direction, col + dc * direction
                while (0 <= r < self.BOARD_SIZE and
                       0 <= c < self.BOARD_SIZE and
                       self.board[r][c] == player):
                    count += 1
                    r += dr * direction
                    c += dc * direction

            if count >= 5:
                return True

        return False

    def get_ai_move(self, player):
        """
        Get AI move for player.
        
        Returns:
            tuple: (row, col, time_taken, depth_reached)
        """
        ai = self.ai1 if player == self.BLACK_PLAYER else self.ai2

        move, _ = ai.get_best_move(
            self.board,
            self.captures,
            self.current_hash,
            player,
            self.WIN_BY_CAPTURES,
            self,
            self.move_count
        )

        time_taken = ai.last_move_time
        depth_reached = ai.last_depth_reached

        return move, time_taken, depth_reached

    def play_game(self, verbose=False, max_moves=300):
        """
        Play a complete game.
        
        Args:
            verbose: Print game progress
            max_moves: Maximum moves before draw
        
        Returns:
            dict: Game results with statistics
        """
        if verbose:
            print(f"\n{'='*60}")
            print("Starting new game (Headless Mode)")
            print(f"{'='*60}\n")

        while not self.game_over and self.move_count < max_moves:
            player_name = "Black" if self.current_player == self.BLACK_PLAYER else "White"

            if verbose:
                print(f"\nTurn {(self.move_count + 2) // 2} - {player_name}'s move")

            # Get AI move
            move_result = self.get_ai_move(self.current_player)

            if move_result is None or move_result[0] is None:
                if verbose:
                    print(f"❌ {player_name} has no legal moves!")
                self.game_over = True
                self.winner = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                              else self.BLACK_PLAYER)
                break

            move, time_taken, depth_reached = move_result

            if move is None:
                if verbose:
                    print(f"❌ {player_name} returned None move!")
                self.game_over = True
                self.winner = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                              else self.BLACK_PLAYER)
                break

            row, col = move

            # Make move
            if not self.apply_move(row, col, self.current_player):
                if verbose:
                    print(f"❌ Illegal move attempted: ({row}, {col})")
                self.game_over = True
                self.winner = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                              else self.BLACK_PLAYER)
                break

            # Record stats
            self.time_history.append(time_taken)
            self.depth_history.append(depth_reached)

            if verbose:
                captures_made = self.move_history[-1][3]
                print(f"  Move: ({row}, {col})")
                print(f"  Time: {time_taken:.2f}s, Depth: {depth_reached}")
                print(f"  Captures: {self.captures[self.current_player]} total"
                      f"{f' (+{captures_made})' if captures_made > 0 else ''}")

            # Switch player
            self.current_player = (self.WHITE_PLAYER if self.current_player == self.BLACK_PLAYER
                                  else self.BLACK_PLAYER)

        # Handle draw
        if not self.game_over:
            self.game_over = True
            self.winner = None

        # Generate results
        results = self.generate_results(verbose)

        return results

    def generate_results(self, verbose=False):
        """Generate game results and statistics."""
        results = {
            'winner': self.winner,
            'total_moves': self.move_count,
            'black_captures': self.captures[self.BLACK_PLAYER],
            'white_captures': self.captures[self.WHITE_PLAYER],
            'avg_time': sum(self.time_history) / len(self.time_history) if self.time_history else 0,
            'max_time': max(self.time_history) if self.time_history else 0,
            'avg_depth': sum(self.depth_history) / len(self.depth_history) if self.depth_history else 0,
            'max_depth': max(self.depth_history) if self.depth_history else 0,
            'move_history': self.move_history.copy(),
            'time_history': self.time_history.copy(),
            'depth_history': self.depth_history.copy(),
        }

        if verbose:
            print(f"\n{'='*60}")
            print("GAME OVER")
            print(f"{'='*60}")

            if self.winner is None:
                print("Result: DRAW")
            else:
                winner_name = "Black" if self.winner == self.BLACK_PLAYER else "White"
                print(f"Winner: {winner_name}")

            print("\nStatistics:")
            print(f"  Total moves: {results['total_moves']}")
            print(f"  Black captures: {results['black_captures']}")
            print(f"  White captures: {results['white_captures']}")
            print(f"  Avg time/move: {results['avg_time']:.2f}s")
            print(f"  Max time: {results['max_time']:.2f}s")
            print(f"  Avg depth: {results['avg_depth']:.1f}")
            print(f"  Max depth: {results['max_depth']}")
            print(f"{'='*60}\n")

        return results

