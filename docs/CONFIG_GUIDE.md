# Configuration Guide

## Overview

The Gomoku game now uses a centralized `config.json` file for all settings, making it easy to adjust game parameters without modifying code.

## Configuration File Location

The `config.json` file is located in the project root directory.

## Configuration Sections

### 1. `game_settings`

Basic game rules and board setup:

- `board_size`: Size of the board (default: 15)
- `win_by_captures`: Number of captures needed to win (default: 5 pairs = 10 pieces)
- `empty`, `black_player`, `white_player`: Player identifiers
- `default_game_mode`: Starting game mode ("P_VS_AI" or "P_VS_P")

### 2. `player_settings`

Player configuration:

- `ai_player`: Which player the AI controls (1=Black, 2=White)
- `human_player`: Which player the human controls
- `starting_player`: Who moves first

### 3. `algorithm_settings`

AI search algorithm configuration:

- `max_depth`: Maximum search depth (default: 12)
- `time_limit`: Time limit per move in seconds (default: 3.0)
- `enable_iterative_deepening`: Enable/disable iterative deepening
- `enable_aspiration_windows`: Enable/disable aspiration window optimization
- `enable_null_move_pruning`: Enable/disable null move pruning
- `enable_late_move_reductions`: Enable/disable late move reductions
- `enable_killer_moves`: Enable/disable killer moves heuristic

**Adaptive Starting Depth:**
Controls which depth the iterative deepening starts from based on game phase:
- `enable`: Enable adaptive starting depth
- `early_game_moves`: Move count threshold for early game (default: 8)
- `early_game_depth`: Starting depth for early game (default: 1)
- `mid_early_moves`: Move count threshold for mid-early game (default: 15)
- `mid_early_depth`: Starting depth for mid-early game (default: 3)
- `mid_game_moves`: Move count threshold for mid game (default: 25)
- `mid_game_depth`: Starting depth for mid game (default: 4)
- `late_game_depth`: Starting depth for late game (default: 5)

### 4. `heuristic_settings`

Pattern evaluation scores:

**`scores`** sub-section defines point values for different board patterns:

- `win_score`: Score for winning position (default: 1,000,000,000)
- `pending_win_score`: Score for 5-in-a-row (default: 50,000,000)
- `open_four`: Score for open four (_OOOO_) (default: 1,000,000)
- `broken_four`: Score for broken four (default: 400,000)
- `closed_four`: Score for closed four (default: 50,000)
- `open_three`: Score for open three (_OOO_) (default: 10,000)
- `broken_three`: Score for broken three (default: 4,000)
- `closed_three`: Score for closed three (default: 5,000)
- `open_two`: Score for open two (default: 100)
- `closed_two`: Score for closed two (default: 10)
- `capture_threat_open`: Score for capture threat (default: 30,000)
- `capture_score`: Score per captured pair (default: 2,500)
- `capture_setup_bridge`: Score for capture setup (default: 1,000)

### 5. `ai_settings`

AI-specific behavior configuration:

- `relevance_range`: Distance from existing pieces to consider (default: 1)

**`move_ordering`** sub-section:
- `enable_windowed_search`: Enable bounded search space
- `windowed_search_from_move`: Start windowed search from this move (default: 10)
- `bounding_box_margin`: Margin around pieces for bounding box (default: 2)
- **`adaptive_move_limits`**: Number of moves to consider at each game phase
  - `early_game_moves`, `early_game_limit`
  - `mid_game_moves`, `mid_game_limit`
  - `late_game_limit`
- **`priority_move_limits`**: Limits for each priority tier
  - `winning_moves`, `blocking_moves`
  - `high_priority_early`, `high_priority_mid`
  - `mid_priority_factor`

### 6. `ui_settings`

Visual appearance and UI configuration:

**`window`**:
- `square_size`: Size of each board square in pixels (default: 40)
- `margin`: Margin around the board (default: 40)
- `bottom_bar_height`: Height of capture display bar (default: 40)

**`colors`**: RGB color values for various UI elements
- `board`, `black`, `white`, `grid`, `text`, `capture_bg`, `illegal`, `highlight`

**`fonts`**:
- `main_font`: Font family (default: "Inter")
- `main_font_size`: Font size (default: 24)

**`animation`**:
- `pulse_speed`: Speed of pulsing animation for pending win (default: 4)

## Customization Tips

### Making AI Stronger
- Increase `max_depth` (but this will slow down moves)
- Increase `time_limit` to allow deeper search
- Enable all optimization flags
- Adjust `adaptive_starting_depth` to start deeper

### Making AI Faster
- Decrease `max_depth`
- Decrease `time_limit`
- Reduce `adaptive_move_limits` values
- Enable `windowed_search` earlier

### Tuning Heuristics
- Adjust pattern scores to change AI's playing style
- Increase `capture_score` to make AI more aggressive with captures
- Increase `open_four` to make AI prioritize four-in-a-row threats

### UI Customization
- Change `colors` to customize the look
- Adjust `square_size` and `margin` to change board size
- Change `font` settings for different text appearance

## Validation

The game validates the config file on startup. If the JSON is invalid or missing required fields, it will display an error message and exit.

## Example: Quick Game Mode

For fast testing, you can create a `config_fast.json`:

```json
{
  "algorithm_settings": {
    "max_depth": 6,
    "time_limit": 1.0,
    ...
  }
}
```

Then modify `Gomoku.py` to load your custom config file.

