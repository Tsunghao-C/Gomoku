# Gomoku AI Configuration Guide

This manual provides a comprehensive overview of the Gomoku AI configuration settings, explaining how each parameter influences the game's behavior and performance. It reflects the enhanced architecture featuring Delta Heuristic, Alpha-Beta Pruning, Iterative Deepening, and Zobrist Hashing optimizations.

## Table of Contents
1. [Overview](#overview)
2. [Implementation Strategy & Enhancements](#implementation-strategy--enhancements)
3. [Configuration Parameters](#configuration-parameters)
    - [Game Settings](#game-settings)
    - [Player Settings](#player-settings)
    - [Algorithm Settings](#algorithm-settings)
    - [Heuristic Settings](#heuristic-settings)
    - [AI Settings & Move Ordering](#ai-settings--move-ordering)
    - [UI Settings](#ui-settings)

---

## Overview

The Gomoku AI uses a Minimax algorithm enhanced with Alpha-Beta pruning to search for the best move. To handle the large branching factor of Gomoku (19x19 board), we employ several optimizations:
-   **Iterative Deepening:** Searching incrementally deeper (Depth 1, 2, 3...) to ensure we always have a "best guess" if time runs out.
-   **Move Ordering:** Sorting moves by a quick heuristic score so the best moves are searched first, maximizing pruning.
-   **Transposition Table (Zobrist Hashing):** Caching board positions to avoid re-calculating the same state.
-   **Bitboard / 1D Array:** Optimized board representation for fast access.
-   **Late Move Reduction (LMR) & Null Move Pruning:** Aggressive pruning techniques to skip unlikely branches.

---

## Implementation Strategy & Enhancements

### 1. Core Game Logic (`srcs/GomokuLogic.py`)
-   **Centralized Logic:** All rules (captures, double-three, win conditions) are encapsulated here, shared by both the GUI game and Headless AI.
-   **1D Array Optimization:** The board is a flat list `[0..360]` instead of a 2D list, significantly improving cache locality and access speed.
-   **Zobrist Hashing:** An incremental hash of the board state is maintained to instantly identify identical positions in the Transposition Table.

### 2. AI Architecture (`srcs/GomokuAI.py` & `srcs/algorithm.py`)
-   **Iterative Deepening:** The AI strictly respects the `time_limit`. It starts at depth 1 and goes deeper until time runs out.
-   **Aspiration Windows:** Instead of searching $-\infty$ to $+\infty$, we search a narrow window around the previous score. If the score falls outside, we re-search. This works well because board scores usually change gradually.
-   **History Heuristic:** We track moves that caused "cutoffs" (proved a branch was bad) and prioritize them in future searches.
-   **Clustering & Windowed Search:** instead of scanning the whole board, the AI identifies clusters of stones and only searches within those bounding boxes.

### 3. Heuristic Evaluation (`srcs/heuristic.py`)
-   **Numeric Pattern Matching:** Instead of slow string comparisons, we use tuple-based pattern matching on integer arrays.
-   **Evaluation:** We evaluate the board based on patterns (Open 4, Broken 3, etc.) and assign scores defined in `config.json`.

---

## Configuration Parameters (`config.json`)

### Game Settings
```json
"game_settings": {
  "board_size": 19,       // Standard Gomoku board size
  "win_by_captures": 5,   // Number of capture pairs (10 stones) to win
  "empty": 0,             // Internal value for empty cell
  "black_player": 1,      // Internal value for Black
  "white_player": 2,      // Internal value for White
  "default_game_mode": "P_VS_AI" // Default mode on launch
}
```

### Algorithm Settings
These control the depth and speed of the AI search.

| Parameter | Description | Recommended |
| :--- | :--- | :--- |
| `max_depth` | The absolute maximum depth the AI will attempt. | `12` |
| `time_limit` | **CRITICAL**. Maximum time (seconds) the AI can think. | `0.5` - `1.5` |
| `enable_iterative_deepening` | Must be `true` to respect time limits. | `true` |
| `enable_aspiration_windows` | Narrow search window for performance. | `true` |
| `aspiration_window_delta` | How much the score can fluctuate before re-search. | `500000` |
| `enable_null_move_pruning` | Skips turns in search to prove position safety. | `true` |
| `enable_late_move_reductions` | Searches "bad" moves with reduced depth. | `true` |
| `lmr_threshold` | Move index after which LMR starts (e.g., 4th best move). | `3` |
| `lmr_reduction` | How many depth levels to reduce for late moves. | `2` |
| `enable_killer_moves` | Tracks "killer" moves that caused cutoffs. | `true` |
| `killer_moves_per_depth` | Number of killer moves to store per depth. | `2` |

**Adaptive Starting Depth (Optional)**
This section allows the AI to skip early depths (e.g., start at Depth 4) later in the game when the tree is stable.
*   `enable`: Set to `true` to turn on.
*   `*_game_moves`: The turn number defining the phase.
*   `*_game_depth`: The starting depth for that phase.

### Heuristic Settings
Defines the score values for board patterns.

| Pattern | Description | Score Impact |
| :--- | :--- | :--- |
| `win_score` | 5-in-a-row or capture win. | Very High (1B) |
| `pending_win_score` | Unstoppable 5-in-a-row (unless blocked). | High (50M) |
| `open_four` | Four stones open on both ends (immediate win threat). | 1M |
| `broken_four` | Four stones with a gap or blocked on one side. | 400k |
| `open_three` | Three stones open on both ends. | 10k |
| `capture_score` | Bonus for capturing a pair. | 2.5k |

**Capture Defense**
*   `enable`: If `true`, the AI specifically checks for stones vulnerable to capture and penalizes those positions.
*   `critical_penalty`: Score penalty for losing a stone when capture count is high.

### AI Settings & Move Ordering
These settings control **Branching Factor** - how many moves the AI considers at each step.

| Parameter | Description | Optimization Strategy |
| :--- | :--- | :--- |
| `relevance_range` | How far from existing stones to look for moves. | `1` |
| `enable_windowed_search` | Use bounding boxes (clusters) to limit search area. | `true` |
| `bounding_box_margin` | Extra space around stone clusters. | `2` |

**Adaptive Move Limits**
Dynamically adjusts the number of moves checked based on the game phase.
*   `early_game_limit`: Few moves needed early on (e.g., `8`).
*   `mid_game_limit`: More complex, need slightly fewer focused moves or more? Actually fewer is better for depth. (e.g., `6`).
*   `late_game_limit`: Board is crowded, fewer valid good moves (e.g., `6`).

**Priority Move Limits**
*   `winning_moves`: If a winning move is found, how many to check? Usually `5`.
*   `blocking_moves`: If we must block, only check top `4` blocking moves.

### UI Settings
Controls the Pygame window appearance.
*   `square_size`: Size of grid cells in pixels.
*   `margin`: Board margin.
*   `colors`: RGB values for board, pieces, etc.
*   `animation`: Pulse speed for winning line highlight.
