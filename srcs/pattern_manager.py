"""
Gomoku Pattern Manager
Handles all pattern recognition, scoring, and threat detection for Gomoku AI
"""

from enum import Enum


class Player(Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2


class PatternType(Enum):
    """Types of patterns in Gomoku"""
    FIVE_IN_ROW = "five_in_row"           # Immediate win
    FOUR_IN_ROW = "four_in_row"           # Immediate threat
    BROKEN_FOUR = "broken_four"            # Four with one empty
    THREE_IN_ROW = "three_in_row"         # Strong threat
    BROKEN_THREE = "broken_three"          # Three with one empty
    TWO_IN_ROW = "two_in_row"             # Potential threat
    BROKEN_TWO = "broken_two"              # Two with one empty
    SINGLE_STONE = "single_stone"          # Weak potential


class PatternManager:
    """Manages all Gomoku patterns and their scoring"""

    def __init__(self):
        self.pattern_database = self._initialize_pattern_database()
        self.threat_patterns = self._initialize_threat_patterns()
        self.opportunity_patterns = self._initialize_opportunity_patterns()

    def _initialize_pattern_database(self) -> dict[str, dict]:
        """Initialize comprehensive pattern database with all possible patterns"""
        return {
            # 5-stone patterns (immediate win/loss)
            "PPPPP": {
                "type": PatternType.FIVE_IN_ROW,
                "score": 1000000,
                "description": "Five in a row - immediate win",
                "priority": 1
            },
            "OOOOO": {
                "type": PatternType.FIVE_IN_ROW,
                "score": -1000000,
                "description": "Opponent five in a row - immediate loss",
                "priority": 1
            },

            # 4-stone patterns (immediate threats)
            "PPPPE": {
                "type": PatternType.FOUR_IN_ROW,
                "score": 100000,
                "description": "Four with one empty - immediate threat",
                "priority": 2
            },
            "EPPPP": {
                "type": PatternType.FOUR_IN_ROW,
                "score": 100000,
                "description": "Four with one empty - immediate threat",
                "priority": 2
            },
            "PPEPP": {
                "type": PatternType.BROKEN_FOUR,
                "score": 100000,
                "description": "Four with one empty in middle - immediate threat",
                "priority": 2
            },
            "OOOEO": {
                "type": PatternType.FOUR_IN_ROW,
                "score": -100000,
                "description": "Opponent four with one empty - must block",
                "priority": 2
            },
            "EOOOO": {
                "type": PatternType.FOUR_IN_ROW,
                "score": -100000,
                "description": "Opponent four with one empty - must block",
                "priority": 2
            },
            "OOEOO": {
                "type": PatternType.BROKEN_FOUR,
                "score": -100000,
                "description": "Opponent four with one empty in middle - must block",
                "priority": 2
            },

            # 3-stone patterns (strong threats)
            "PPPE": {
                "type": PatternType.THREE_IN_ROW,
                "score": 10000,
                "description": "Three with two empty - strong threat",
                "priority": 3
            },
            "EPPP": {
                "type": PatternType.THREE_IN_ROW,
                "score": 10000,
                "description": "Three with two empty - strong threat",
                "priority": 3
            },
            "PPEP": {
                "type": PatternType.BROKEN_THREE,
                "score": 10000,
                "description": "Three with one empty in middle - strong threat",
                "priority": 3
            },
            "PEPP": {
                "type": PatternType.BROKEN_THREE,
                "score": 10000,
                "description": "Three with one empty in middle - strong threat",
                "priority": 3
            },
            "OOOE": {
                "type": PatternType.THREE_IN_ROW,
                "score": -10000,
                "description": "Opponent three with two empty - must block",
                "priority": 3
            },
            "EOOO": {
                "type": PatternType.THREE_IN_ROW,
                "score": -10000,
                "description": "Opponent three with two empty - must block",
                "priority": 3
            },
            "OOEO": {
                "type": PatternType.BROKEN_THREE,
                "score": -10000,
                "description": "Opponent three with one empty in middle - must block",
                "priority": 3
            },
            "OEOO": {
                "type": PatternType.BROKEN_THREE,
                "score": -10000,
                "description": "Opponent three with one empty in middle - must block",
                "priority": 3
            },

            # 2-stone patterns (potential threats)
            "PPE": {
                "type": PatternType.TWO_IN_ROW,
                "score": 1000,
                "description": "Two with three empty - potential threat",
                "priority": 4
            },
            "EPP": {
                "type": PatternType.TWO_IN_ROW,
                "score": 1000,
                "description": "Two with three empty - potential threat",
                "priority": 4
            },
            "PEP": {
                "type": PatternType.BROKEN_TWO,
                "score": 1000,
                "description": "Two with one empty in middle - potential threat",
                "priority": 4
            },
            "OOE": {
                "type": PatternType.TWO_IN_ROW,
                "score": -1000,
                "description": "Opponent two with three empty - should block",
                "priority": 4
            },
            "EOO": {
                "type": PatternType.TWO_IN_ROW,
                "score": -1000,
                "description": "Opponent two with three empty - should block",
                "priority": 4
            },
            "OEO": {
                "type": PatternType.BROKEN_TWO,
                "score": -1000,
                "description": "Opponent two with one empty in middle - should block",
                "priority": 4
            },

            # 1-stone patterns (weak potential)
            "PE": {
                "type": PatternType.SINGLE_STONE,
                "score": 100,
                "description": "One with four empty - weak potential",
                "priority": 5
            },
            "EP": {
                "type": PatternType.SINGLE_STONE,
                "score": 100,
                "description": "One with four empty - weak potential",
                "priority": 5
            },
            "OE": {
                "type": PatternType.SINGLE_STONE,
                "score": -100,
                "description": "Opponent one with four empty - weak threat",
                "priority": 5
            },
            "EO": {
                "type": PatternType.SINGLE_STONE,
                "score": -100,
                "description": "Opponent one with four empty - weak threat",
                "priority": 5
            }
        }

    def _initialize_threat_patterns(self) -> list[str]:
        """Initialize patterns that represent immediate threats"""
        return [
            "OOOOO",  # Opponent five in a row
            "OOOEO",  # Opponent four with one empty
            "EOOOO",  # Opponent four with one empty
            "OOEOO",  # Opponent four with one empty in middle
            "OOOE",   # Opponent three with two empty
            "EOOO",   # Opponent three with two empty
            "OOEO",   # Opponent three with one empty in middle
            "OEOO",   # Opponent three with one empty in middle
        ]

    def _initialize_opportunity_patterns(self) -> list[str]:
        """Initialize patterns that represent opportunities for us"""
        return [
            "PPPPP",  # Our five in a row
            "PPPPE",  # Our four with one empty
            "EPPPP",  # Our four with one empty
            "PPEPP",  # Our four with one empty in middle
            "PPPE",   # Our three with two empty
            "EPPP",   # Our three with two empty
            "PPEP",   # Our three with one empty in middle
            "PEPP",   # Our three with one empty in middle
        ]

    def get_pattern_score(self, pattern_str: str, player: Player) -> float:
        """Get the score for a specific pattern"""
        if pattern_str in self.pattern_database:
            return self.pattern_database[pattern_str]["score"]

        # If no exact match, use partial pattern scoring
        return self._score_partial_pattern(pattern_str, player)

    def _score_partial_pattern(self, pattern_str: str, player: Player) -> float:
        """Score partial patterns that don't have exact matches"""
        score = 0

        # Count consecutive stones for player
        max_consecutive = self._count_max_consecutive(pattern_str, "P")
        score += self._get_consecutive_score(max_consecutive)

        # Count consecutive stones for opponent (negative scoring)
        max_opponent_consecutive = self._count_max_consecutive(pattern_str, "O")
        score -= self._get_consecutive_score(max_opponent_consecutive)

        return score

    def _count_max_consecutive(self, pattern_str: str, stone_char: str) -> int:
        """Count maximum consecutive stones of a specific type"""
        max_consecutive = 0
        current_consecutive = 0

        for char in pattern_str:
            if char == stone_char:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _get_consecutive_score(self, consecutive_count: int) -> float:
        """Get score based on consecutive stone count"""
        if consecutive_count >= 5:
            return 1000000
        elif consecutive_count == 4:
            return 100000
        elif consecutive_count == 3:
            return 10000
        elif consecutive_count == 2:
            return 1000
        elif consecutive_count == 1:
            return 100
        else:
            return 0

    def is_critical_threat(self, pattern_str: str) -> bool:
        """Check if a pattern represents a critical threat that must be blocked"""
        return pattern_str in self.threat_patterns

    def is_opportunity(self, pattern_str: str) -> bool:
        """Check if a pattern represents an opportunity for us"""
        return pattern_str in self.opportunity_patterns

    def get_pattern_priority(self, pattern_str: str) -> int:
        """Get the priority level of a pattern (lower = higher priority)"""
        if pattern_str in self.pattern_database:
            return self.pattern_database[pattern_str]["priority"]
        else:
            return 6  # Lowest priority for unknown patterns

    def get_all_patterns_by_priority(self) -> list[tuple[str, dict]]:
        """Get all patterns sorted by priority"""
        patterns = list(self.pattern_database.items())
        return sorted(patterns, key=lambda x: x[1]["priority"])

    def add_custom_pattern(self, pattern_str: str, pattern_type: PatternType,
                          score: float, description: str, priority: int = 6):
        """Add a custom pattern to the database"""
        self.pattern_database[pattern_str] = {
            "type": pattern_type,
            "score": score,
            "description": description,
            "priority": priority
        }

        # Update threat/opportunity lists if needed
        if score < 0:
            self.threat_patterns.append(pattern_str)
        elif score > 0:
            self.opportunity_patterns.append(pattern_str)

    def get_pattern_info(self, pattern_str: str) -> dict | None:
        """Get detailed information about a pattern"""
        return self.pattern_database.get(pattern_str)

    def find_patterns_in_direction(self, board: list[list[Player]], row: int, col: int,
                                  dr: int, dc: int, length: int, player: Player) -> list[tuple[str, float]]:
        """Find all patterns of a specific length in a direction from a position"""
        patterns = []

        for start in range(length):
            pattern = []
            valid = True

            for i in range(length):
                r, c = row + (i - start) * dr, col + (i - start) * dc
                if 0 <= r < len(board) and 0 <= c < len(board[0]):
                    pattern.append(board[r][c])
                else:
                    valid = False
                    break

            if valid:
                pattern_str = self._convert_pattern_to_string(pattern, player)
                score = self.get_pattern_score(pattern_str, player)
                patterns.append((pattern_str, score))

        return patterns

    def _convert_pattern_to_string(self, pattern: list[Player], player: Player) -> str:
        """Convert a pattern list to string representation"""
        pattern_str = ""
        opponent = Player.WHITE if player == Player.BLACK else Player.BLACK

        for cell in pattern:
            if cell == player:
                pattern_str += "P"
            elif cell == opponent:
                pattern_str += "O"
            else:
                pattern_str += "E"

        return pattern_str

    def evaluate_position_patterns(self, board: list[list[Player]], row: int, col: int, player: Player) -> float:
        """Evaluate all patterns from a specific position"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonal

        for dr, dc in directions:
            # Check patterns of different lengths
            for length in [3, 4, 5]:
                patterns = self.find_patterns_in_direction(board, row, col, dr, dc, length, player)
                for pattern_str, pattern_score in patterns:
                    score += pattern_score

        return score

    def find_critical_threats(self, board: list[list[Player]], player: Player) -> list[tuple[int, int]]:
        """Find all positions that would create critical threats"""
        threats = []
        opponent = Player.WHITE if player == Player.BLACK else Player.BLACK

        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == Player.EMPTY:
                    if self._would_create_critical_threat(board, row, col, opponent):
                        threats.append((row, col))

        return threats

    def _would_create_critical_threat(self, board: list[list[Player]], row: int, col: int, player: Player) -> bool:
        """Check if placing a stone would create a critical threat"""
        # Temporarily place the stone
        board[row][col] = player

        # Check all directions for critical patterns
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        has_critical = False

        for dr, dc in directions:
            for length in [4, 5]:
                patterns = self.find_patterns_in_direction(board, row, col, dr, dc, length, player)
                for pattern_str, _ in patterns:
                    if self.is_critical_threat(pattern_str):
                        has_critical = True
                        break
                if has_critical:
                    break
            if has_critical:
                break

        # Remove the stone
        board[row][col] = Player.EMPTY

        return has_critical

    def get_pattern_statistics(self) -> dict:
        """Get statistics about the pattern database"""
        total_patterns = len(self.pattern_database)
        threat_count = len(self.threat_patterns)
        opportunity_count = len(self.opportunity_patterns)

        # Count by type
        type_counts = {}
        for pattern_info in self.pattern_database.values():
            pattern_type = pattern_info["type"]
            type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1

        return {
            "total_patterns": total_patterns,
            "threat_patterns": threat_count,
            "opportunity_patterns": opportunity_count,
            "type_distribution": type_counts
        }
