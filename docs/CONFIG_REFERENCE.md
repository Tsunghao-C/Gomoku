# Gomoku AI Configuration Reference (`config.json`)

This document provides a detailed explanation of every parameter in `config.json` and how it affects the game behavior, AI performance, and user interface.

## 1. Game Settings (`game_settings`)

Controls the core rules and initial state of the game.

| Parameter | Type | Default | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| `board_size` | int | 19 | The dimensions of the game board (19x19). | Changes the playing area size. Standard Gomoku is 15x15 or 19x19. |
| `win_by_captures` | int | 5 | Number of captured pairs needed to win. | Sets the capture victory condition. If a player captures 5 pairs (10 stones), they win immediately. |
| `empty` | int | 0 | Value representing an empty cell. | Internal logic constant. Do not change. |
| `black_player` | int | 1 | Value representing the Black player. | Internal logic constant. Do not change. |
| `white_player` | int | 2 | Value representing the White player. | Internal logic constant. Do not change. |

## 2. Player Settings (`player_settings`)

Defines player roles.

| Parameter | Type | Default | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| `ai_player` | int | 2 | Which player the AI controls. | 1 = Black, 2 = White. |
| `human_player` | int | 1 | Which player the Human controls. | 1 = Black, 2 = White. |
| `starting_player` | int | 1 | Who moves first. | 1 = Black, 2 = White. Black usually moves first in standard rules. |

## 3. Algorithm Settings (`algorithm_settings`)

Controls the Minimax search behavior and pruning optimizations. These are the most critical settings for AI strength and speed.

| Parameter | Type | Default | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| `max_depth` | int | 12 | The hard limit for search depth. | The AI will never search deeper than this, even if time remains. Higher = stronger but slower. |
| `time_limit` | float | 1.5 | Maximum thinking time per move (seconds). | The AI stops searching when this time is exceeded. Lower = faster response, weaker play. |
| `enable_iterative_deepening` | bool | true | Searches depth 1, then 2, then 3... | **Highly Recommended**. Ensures the AI always has a "best move" ready if time runs out and improves move ordering for deeper searches. |
| `enable_aspiration_windows` | bool | true | Uses a narrow search window around the previous score. | **Performance**. If the score is stable, this prune branches massively. If unstable, it triggers a re-search (see logs). |
| `aspiration_window_delta` | int | 500000 | The size of the aspiration window. | Smaller = faster but more re-searches. Larger = safer but slower. |
| `enable_null_move_pruning` | bool | true | AI "passes" to check if it's safe. | **Performance**. Prunes branches where the opponent can't do damage even if we do nothing. Risky in zugzwang games (Chess) but safe in Gomoku. |
| `null_move_reduction` | int | 2 | Depth reduction for null move check. | How much shallower the verification search is. |
| `enable_late_move_reductions` | bool | true | Reduces depth for "bad" moves. | **Performance**. Moves sorted late in the list are searched with reduced depth. |
| `lmr_threshold` | int | 3 | Index of move to start LMR. | The first 3 moves are searched fully. The 4th+ are reduced. |
| `lmr_reduction` | int | 2 | Depth reduction for LMR. | Late moves are searched at `depth - 2`. |
| `adaptive_starting_depth` | dict | - | Config for starting search depth. | **Disabled**. Currently set to start at depth 1 for consistency. |

## 4. Heuristic Settings (`heuristic_settings`)

Defines the "Personality" and strategic understanding of the AI.

### `scores`

Points assigned to board patterns.

| Parameter | Value | Description | Impact |
| :--- | :--- | :--- | :--- |
| `win_score` | 1,000,000,000 | 5-in-a-row or 5th capture. | The ultimate goal. Must be infinitely higher than other scores. |
| `pending_win_score` | 50,000,000 | Unstoppable threat (Open 4) or 4/5 captures with threat. | AI treats this as effectively a win, prioritizing it above everything else except an immediate win. |
| `broken_four` | 400,000 | `_O_OOO_` or `_OO_OO_` | A very strong threat. Forces the opponent to defend. |
| `closed_four` | 50,000 | `XOOOO_` | A blocked 4. Requires one more move to win, but easily blocked. |
| `open_three` | 10,000 | `_OOO_` | A flexible base for attack. Can become Open 4. |
| `broken_three` | 4,000 | `_O_OO_` | weaker than Open 3 but still useful. |
| `closed_three` | 5,000 | `XOOO_` | Blocked 3. Limited potential. |
| `open_two` | 100 | `_OO_` | Basic development. |
| `capture_threat_open` | 15,000 | `POOE` pattern. | A threat to capture a pair. Scored higher than Open 3 to make AI aggressive about captures. |
| `capture_score` | 20,000 | Actual capture bonus. | Bonus added to the board evaluation for *having* captured stones. Incentivizes taking pieces. |

## 5. AI Settings (`ai_settings`)

Controls move generation and high-level strategy.

| Parameter | Type | Default | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| `relevance_range` | int | 1 | Range to look for moves around stones. | **Branching Factor**. 1 = only adjacent empty spots. 2 = up to 2 steps away. Higher = sees more distant connections but drastically slows down search. |

### `move_ordering`

Optimizes which moves are searched first (critical for Alpha-Beta pruning).

| Parameter | Default | Description | Impact |
| :--- | :--- | :--- | :--- |
| `enable_windowed_search` | true | Search only inside stone clusters. | **Performance**. Ignores the empty sides of the 19x19 board. |
| `windowed_search_from_move` | 10 | Turn to start windowing. | Early game searches center. After move 10, focuses on clusters. |
| `bounding_box_margin` | 2 | Buffer around clusters. | Defines how "loose" the window is. |
| `adaptive_move_limits` | dict | - | **CRITICAL**. Limits how many moves are fully searched per branch. |
| `...early_game_limit` | 8 | Moves checked in early game. | Keeps branching factor low (8 instead of ~200). |
| `...mid_game_limit` | 6 | Moves checked in mid game. | Tighter limit as board fills up and threats become more defined. |
| `...late_game_limit` | 6 | Moves checked in late game. | |
| `priority_move_limits` | dict | - | Exceptions to the adaptive limits. |
| `...winning_moves` | 5 | Max winning moves to check. | Always check at least 5 winning candidates. |
| `...blocking_moves` | 4 | Max blocking moves to check. | Always check at least 4 blocking candidates. |

## 6. UI Settings (`ui_settings`)

Purely visual configuration.

| Parameter | Description |
| :--- | :--- |
| `window` | `square_size`, `margin`, `bottom_bar_height` define the window geometry. |
| `colors` | RGB values for board, pieces, grid, text, etc. |
| `fonts` | Font family and size. |
| `animation` | `pulse_speed` for the last move highlight effect. |

