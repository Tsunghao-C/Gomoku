# 🛠️ Debug Mode Configuration - Complete

## Summary

Added a comprehensive debug mode system with granular control over logging output. By default, all debug logs are **disabled** for clean gameplay. Enable them selectively for debugging purposes.

---

## Configuration

All debug settings are in `config.json` under `ai_settings.debug`:

```json
"ai_settings": {
  ...
  "debug": {
    "verbose": false,
    "show_critical_moves": false,
    "show_move_scores": false,
    "show_move_categories": false,
    "show_terminal_states": false
  }
}
```

### Debug Flags

| Flag | Description | What It Shows |
|------|-------------|---------------|
| `verbose` | Master verbose flag | Depth completion, search summary, winning moves found |
| `show_critical_moves` | Critical move detection | Which moves are detected as winning/blocking 4-in-a-row |
| `show_move_scores` | Move scoring details | my_score and opp_score for critical moves |
| `show_move_categories` | Move categorization | Which moves go into blocking/high/mid priority lists |
| `show_terminal_states` | Terminal state checks | When minimax detects wins by captures or 5-in-a-row |

---

## Usage Examples

### Normal Play (All Disabled - Default)

```json
"debug": {
  "verbose": false,
  "show_critical_moves": false,
  "show_move_scores": false,
  "show_move_categories": false,
  "show_terminal_states": false
}
```

**Output**: Clean gameplay with only turn announcements and move timing.

```
=== Turn 8 ===
[Black] moved to (5, 6)
!!! Captured 2 pieces at: [(6, 6), (7, 6)]
[White] is thinking... (Turn 8, Move #16)
Starting iterative deepening from depth 1

=== Turn 8 ===
[White] moved to (8, 11)
Move calculation time: 1.234567 seconds
```

---

### Debug Move Ordering Issues

```json
"debug": {
  "verbose": false,
  "show_critical_moves": true,
  "show_move_scores": true,
  "show_move_categories": true,
  "show_terminal_states": false
}
```

**Output**: Shows move detection, scoring, and categorization.

```
[White] is thinking... (Turn 8, Move #16)
Starting iterative deepening from depth 1

🔍 Critical moves for player 2:
  Blocking: [(3, 7), (8, 11)]
  Critical move (3,7): my_score=10, opp_score=50000000
  Critical move (8,11): my_score=5000, opp_score=50000000
📋 Returning 2 blocking moves (showing first 6): [(3, 7), (8, 11)]

=== Turn 8 ===
[White] moved to (3, 7)
Move calculation time: 1.234567 seconds
```

---

### Debug Search Depth Issues

```json
"debug": {
  "verbose": true,
  "show_critical_moves": false,
  "show_move_scores": false,
  "show_move_categories": false,
  "show_terminal_states": false
}
```

**Output**: Shows iterative deepening progress.

```
[White] is thinking... (Turn 8, Move #16)
Starting iterative deepening from depth 1
Completed depth 1. Best move: (3, 7), Score: -50000
Completed depth 2. Best move: (3, 7), Score: -100000
Completed depth 3. Best move: (3, 7), Score: 50000000
Found a winning move at depth 3. Score: 50000000
  Move: (3, 7)
Search completed: depth=3, time=0.45s

=== Turn 8 ===
[White] moved to (3, 7)
Move calculation time: 0.450000 seconds
```

---

### Debug Terminal State Detection (Minimax)

```json
"debug": {
  "verbose": false,
  "show_critical_moves": false,
  "show_move_scores": false,
  "show_move_categories": false,
  "show_terminal_states": true
}
```

**Output**: Shows when minimax detects game-ending positions.

```
[White] is thinking... (Turn 8, Move #16)
Starting iterative deepening from depth 1

DEBUG check_terminal_state: Player 1 wins by 5-in-a-row!
  At position (3, 7)
  Win line: [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7)]
  Board at (3, 7): 1
  Direction (1,0): X X (0,7)=0 (1,7)=0 (2,7)=0 (3,7)=1* (4,7)=1* ...

=== Turn 8 ===
[White] moved to (3, 7)
Move calculation time: 0.567890 seconds
```

---

### Full Debug Mode (All Enabled)

```json
"debug": {
  "verbose": true,
  "show_critical_moves": true,
  "show_move_scores": true,
  "show_move_categories": true,
  "show_terminal_states": true
}
```

**Output**: Maximum information for deep debugging (very verbose!).

---

## Files Modified

1. **`config.json`**:
   - Added `ai_settings.debug` section with 5 granular flags

2. **`srcs/GomokuAI.py`**:
   - Added debug flag initialization in `__init__`
   - Wrapped debug prints with conditional checks:
     - Critical move detection (`show_critical_moves`)
     - Move scoring (`show_move_scores`)
     - Move categorization (`show_move_categories`)
     - Search completion (`verbose`)

3. **`srcs/algorithm.py`**:
   - Added debug flag initialization in `__init__`
   - Wrapped debug prints with conditional checks:
     - Depth completion (`verbose`)
     - Winning moves found (`verbose`)
     - Terminal states (`show_terminal_states`)

4. **`srcs/GomokuGame.py`**:
   - Added debug flag initialization in `__init__`
   - Wrapped terminal state debug prints:
     - Win by captures detection (`show_terminal_states`)
     - Win by 5-in-a-row detection (`show_terminal_states`)

---

## Benefits

1. **Clean Output**: Default gameplay has minimal noise
2. **Targeted Debugging**: Enable only the logs you need
3. **Performance**: No overhead from disabled debug checks (simple boolean)
4. **Maintainable**: All debug settings centralized in config
5. **Flexible**: Mix and match flags for different debugging scenarios

---

## Testing

```bash
# Test with default (all disabled)
uv run Gomoku.py

# Test with verbose mode
# Edit config.json: "verbose": true
uv run Gomoku.py

# Test with full debug
# Edit config.json: enable all flags
uv run Gomoku.py
```

---

**Date**: 2025-11-17  
**Status**: Complete and tested  
**Default**: All debug flags OFF for clean gameplay

