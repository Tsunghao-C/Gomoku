"""
Headless Gomoku game for automated testing and parameter tuning.
Runs AI vs AI games without GUI for fast iteration.
"""

import time
import copy
from srcs.GomokuAI import GomokuAI
from srcs.utils import (
    init_zobrist, compute_initial_hash, is_valid_pos
)


class HeadlessGame:
    """
    Headless version of Gomoku for automated testing.
    Supports AI vs AI matches with configurable parameters.
    """

    def __init__(self, config, player1_config=None, player2_config=None, verbose=False):
        """
        Initialize headless game.
        
        Args:
            config: Base configuration
            player1_config: Optional config overrides for player 1 (Black)
            player2_config: Optional config overrides for player 2 (White)
            verbose: Whether to print game progress
        """
        self.config = config
        self.verbose = verbose
        
        game_cfg = config["game_settings"]
        player_cfg = config["player_settings"]
        
        self.BOARD_SIZE = game_cfg["board_size"]
        self.EMPTY = game_cfg["empty"]
        self.BLACK_PLAYER = game_cfg["black_player"]
        self.WHITE_PLAYER = game_cfg["white_player"]
        self.WIN_BY_CAPTURES = game_cfg["win_by_captures"]
        
        # Initialize board
        self.board = [[self.EMPTY] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]
        self.captures = {self.BLACK_PLAYER: 0, self.WHITE_PLAYER: 0}
        self.move_count = 0
        self.game_over = False
        self.winner = None
        self.move_history = []
        
        # Initialize zobrist hashing
        self.zobrist_table = init_zobrist(self.BOARD_SIZE)
        self.current_hash = compute_initial_hash(self.board, self.BOARD_SIZE, self.zobrist_table)
        
        # Create AI instances with potentially different configs
        config1 = self._merge_configs(config, player1_config) if player1_config else config
        config2 = self._merge_configs(config, player2_config) if player2_config else config
        
        self.ai_black = GomokuAI(config1)
        self.ai_white = GomokuAI(config2)
        
        # Statistics
        self.total_time_black = 0.0
        self.total_time_white = 0.0
        self.depths_black = []
        self.depths_white = []
        self.move_times_black = []
        self.move_times_white = []
        
    def _merge_configs(self, base_config, overrides):
        """Deep merge configuration overrides."""
        merged = copy.deepcopy(base_config)
        
        for section, values in overrides.items():
            if section not in merged:
                merged[section] = values
            elif isinstance(values, dict):
                for key, value in values.items():
                    if isinstance(value, dict) and key in merged[section]:
                        merged[section][key].update(value)
                    else:
                        merged[section][key] = value
            else:
                merged[section] = values
        
        return merged
    
    def play_game(self, max_moves=300):
        """
        Play a full AI vs AI game.
        
        Args:
            max_moves: Maximum number of moves before declaring draw
            
        Returns:
            dict: Game results with statistics
        """
        current_player = self.BLACK_PLAYER
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Starting AI vs AI game")
            print(f"{'='*60}")
        
        while not self.game_over and self.move_count < max_moves:
            ai = self.ai_black if current_player == self.BLACK_PLAYER else self.ai_white
            player_name = "Black" if current_player == self.BLACK_PLAYER else "White"
            
            if self.verbose:
                print(f"\n[Turn {self.move_count + 1}] {player_name}'s move...")
            
            # Get AI move
            start_time = time.time()
            move, depth = ai.get_best_move(
                self.board,
                self.captures,
                current_player,
                2 if current_player == 1 else 1,
                self.WIN_BY_CAPTURES,
                self,
                self.move_count
            )
            elapsed = time.time() - start_time
            
            if move is None:
                if self.verbose:
                    print(f"[{player_name}] No legal moves! Game over.")
                self.game_over = True
                self.winner = 2 if current_player == 1 else 1
                break
            
            # Track statistics
            if current_player == self.BLACK_PLAYER:
                self.total_time_black += elapsed
                self.depths_black.append(depth)
                self.move_times_black.append(elapsed)
            else:
                self.total_time_white += elapsed
                self.depths_white.append(depth)
                self.move_times_white.append(elapsed)
            
            if self.verbose:
                print(f"[{player_name}] Move: {move}, Depth: {depth}, Time: {elapsed:.2f}s")
            
            # Make move
            row, col = move
            self.make_move(row, col, current_player)
            
            # Check win condition
            if self.check_win(row, col, current_player):
                self.game_over = True
                self.winner = current_player
                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"🏆 {player_name} wins!")
                    print(f"{'='*60}")
                break
            
            # Switch player
            current_player = self.WHITE_PLAYER if current_player == self.BLACK_PLAYER else self.BLACK_PLAYER
        
        if not self.game_over:
            if self.verbose:
                print(f"\nGame ended in draw after {max_moves} moves.")
            self.winner = 0  # Draw
        
        return self._get_game_stats()
    
    def make_move(self, row, col, player):
        """Execute a move and update game state."""
        self.board[row][col] = player
        self.move_history.append((row, col, player))
        self.move_count += 1
        
        # Check for captures
        captured = self.check_and_apply_captures(row, col, player)
        
        # Update zobrist hash
        self.current_hash ^= self.zobrist_table[row][col][player]
        for cr, cc in captured:
            opponent = 2 if player == 1 else 1
            self.current_hash ^= self.zobrist_table[cr][cc][opponent]
    
    def check_and_apply_captures(self, row, col, player):
        """Check and apply captures around the placed stone."""
        opponent = 2 if player == 1 else 1
        captured = []
        
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            r1, c1 = row + dr, col + dc
            r2, c2 = row + 2 * dr, col + 2 * dc
            r3, c3 = row + 3 * dr, col + 3 * dc
            
            if (is_valid_pos(r3, c3, self.BOARD_SIZE) and
                self.board[r1][c1] == opponent and
                self.board[r2][c2] == opponent and
                self.board[r3][c3] == player):
                
                self.board[r1][c1] = self.EMPTY
                self.board[r2][c2] = self.EMPTY
                captured.extend([(r1, c1), (r2, c2)])
                self.captures[player] += 2
        
        return captured
    
    def check_win(self, row, col, player):
        """Check if the current move wins the game."""
        # Win by captures
        if self.captures[player] >= self.WIN_BY_CAPTURES * 2:
            return True
        
        # Win by 5 in a row
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            
            # Check positive direction
            r, c = row + dr, col + dc
            while is_valid_pos(r, c, self.BOARD_SIZE) and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while is_valid_pos(r, c, self.BOARD_SIZE) and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 5:
                return True
        
        return False
    
    def is_legal_move(self, row, col, player, board):
        """Check if a move is legal (used by AI)."""
        if not is_valid_pos(row, col, self.BOARD_SIZE):
            return False, "Out of bounds"
        
        if board[row][col] != self.EMPTY:
            return False, "Position occupied"
        
        return True, "Legal"
    
    def check_terminal_state(self, board, captures, player):
        """Check if game is in terminal state (used by AI)."""
        if captures[player] >= self.WIN_BY_CAPTURES * 2:
            return True, player
        
        opponent = 2 if player == 1 else 1
        if captures[opponent] >= self.WIN_BY_CAPTURES * 2:
            return True, opponent
        
        return False, None
    
    def _get_game_stats(self):
        """Compile game statistics."""
        return {
            'winner': self.winner,
            'total_moves': self.move_count,
            'black_captures': self.captures[self.BLACK_PLAYER],
            'white_captures': self.captures[self.WHITE_PLAYER],
            'total_time_black': self.total_time_black,
            'total_time_white': self.total_time_white,
            'avg_time_black': self.total_time_black / len(self.move_times_black) if self.move_times_black else 0,
            'avg_time_white': self.total_time_white / len(self.move_times_white) if self.move_times_white else 0,
            'avg_depth_black': sum(self.depths_black) / len(self.depths_black) if self.depths_black else 0,
            'avg_depth_white': sum(self.depths_white) / len(self.depths_white) if self.depths_white else 0,
            'max_depth_black': max(self.depths_black) if self.depths_black else 0,
            'max_depth_white': max(self.depths_white) if self.depths_white else 0,
            'move_history': self.move_history
        }

