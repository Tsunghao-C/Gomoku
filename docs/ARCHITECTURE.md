# Gomoku Game Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gomoku.py                                │
│                      (Entry Point)                               │
│                   • Initializes game                             │
│                   • Starts game loop                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ imports & runs
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    srcs/GomokuGame.py                            │
│                   (Game Logic & UI)                              │
│                                                                   │
│  • Game State Management                                         │
│    - Board (15x15 grid)                                          │
│    - Current player                                              │
│    - Captures count                                              │
│    - Game over status                                            │
│    - Pending win state                                           │
│                                                                   │
│  • Game Rules                                                    │
│    - Move validation                                             │
│    - Capture detection (P-O-O-P)                                 │
│    - Win checking (5-in-a-row)                                   │
│    - Double-three rule                                           │
│                                                                   │
│  • Zobrist Hashing                                               │
│    - Fast position hashing                                       │
│    - Incremental updates                                         │
│                                                                   │
│  • UI Rendering (pygame)                                         │
│    - Board drawing                                               │
│    - Piece rendering                                             │
│    - Hover indicators                                            │
│    - Status messages                                             │
│                                                                   │
│  • Event Handling                                                │
│    - Mouse clicks                                                │
│    - Keyboard input (R, M)                                       │
│    - Game mode switching                                         │
└──────────────┬────────────────────────┬─────────────────────────┘
               │                        │
               │ delegates AI           │ uses utility
               │ move                   │ functions
               ▼                        ▼
┌─────────────────────────┐    ┌──────────────────┐
│   srcs/GomokuAI.py      │    │  srcs/utils.py   │
│   (AI Coordination)     │    │  (Utilities)     │
│                         │    │                  │
│  • AI State             │    │  Functions:      │
│  • Move Generation      │    │  • get_line_     │
│  • Move Ordering        │    │    string()      │
│  • Delta Calculation    │    │  • get_line_     │
│  • Relevant Moves       │    │    coords()      │
│  • Local Scoring        │    └──────────────────┘
└──────┬──────────┬───────┘
       │          │
       │ uses     │ uses
       ▼          ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│  srcs/algorithm.py      │    │  srcs/heuristic.py      │
│  (AI Thinking)          │    │  (AI Brain)             │
│                         │    │                         │
│  • Minimax Algorithm    │    │  • Scoring Constants    │
│  • Alpha-Beta Pruning   │    │    - WIN_SCORE          │
│  • Iterative Deepening  │    │    - OPEN_FOUR          │
│  • Transposition Table  │    │    - CAPTURE_THREAT     │
│  • Time Management      │    │    - OPEN_THREE         │
│  • Depth Control        │    │    - etc.               │
│                         │    │                         │
│  Features:              │    │  • Pattern Recognition  │
│  • Root search          │    │    - 5-in-a-row         │
│  • Recursive minimax    │    │    - Open fours         │
│  • Position caching     │    │    - Broken fours       │
│  • Timeout handling     │    │    - Capture threats    │
│                         │    │    - Threes, twos       │
│                         │    │                         │
│                         │    │  • Evaluation Functions │
│                         │    │    - score_line_string  │
│                         │    │    - score_lines_at     │
│                         │    │    - evaluate_board     │
└─────────────────────────┘    └─────────────────────────┘
```

## Data Flow

### 1. Human Move Flow
```
User Click
    ↓
GomokuGame.handle_mouse_click()
    ↓
GomokuGame.handle_move()
    ↓
GomokuGame.make_move()
    ├→ Check captures
    ├→ Update Zobrist hash
    ├→ Check win condition
    └→ Switch player
    ↓
Trigger AI move if needed
```

### 2. AI Move Flow
```
GomokuGame.run_ai_move()
    ↓
GomokuAI.get_best_move()
    ├→ HeuristicEvaluator.evaluate_board() [initial score]
    └→ MinimaxAlgorithm.iterative_deepening_search()
        ├→ For depth 1 to MAX_DEPTH:
        │   ├→ MinimaxAlgorithm.minimax_root()
        │   │   └→ For each ordered move:
        │   │       ├→ GomokuAI.make_move_and_get_delta()
        │   │       │   ├→ HeuristicEvaluator.score_lines_at() [before]
        │   │       │   ├→ GomokuGame.make_move()
        │   │       │   └→ HeuristicEvaluator.score_lines_at() [after]
        │   │       │       └→ Calculate delta
        │   │       ├→ MinimaxAlgorithm.minimax() [recursive]
        │   │       │   ├→ Check transposition table
        │   │       │   ├→ Base case: return current_score
        │   │       │   └→ Recursive: try moves, propagate delta
        │   │       └→ GomokuGame.undo_move()
        │   └→ Return best move for this depth
        └→ Return overall best move
    ↓
GomokuGame.handle_move() [with AI move]
```

### 3. Evaluation Flow
```
Position to Evaluate
    ↓
HeuristicEvaluator.evaluate_board()
    ↓
For each player:
    ↓
    HeuristicEvaluator.calculate_player_score()
        ↓
        Scan board for all pieces
            ↓
            For each line direction (H, V, D1, D2):
                ↓
                utils.get_line_string()
                    ↓
                    Convert to pattern string (P, O, E, X)
                ↓
                HeuristicEvaluator.score_line_string()
                    ↓
                    Match patterns:
                    • PPPPP → PENDING_WIN_SCORE
                    • EPPPPE → OPEN_FOUR
                    • POOE → CAPTURE_THREAT
                    • EPPPE → OPEN_THREE
                    • etc.
                ↓
                Accumulate scores
    ↓
Return: my_score - opponent_score * 1.1
```

## Module Dependencies

```
Gomoku.py
    └── imports GomokuGame

GomokuGame
    ├── imports GomokuAI
    └── imports utils

GomokuAI
    ├── imports MinimaxAlgorithm
    ├── imports HeuristicEvaluator
    └── uses GomokuGame methods (passed as callbacks)

MinimaxAlgorithm
    └── (independent, uses callbacks)

HeuristicEvaluator
    └── imports utils

utils
    └── (independent, no imports)
```

## Key Interfaces

### GomokuGame ↔ GomokuAI
```python
# GomokuGame calls GomokuAI:
best_move, time_taken = self.ai.get_best_move(
    board, captures, zobrist_hash, ai_player,
    win_by_captures, game_logic_reference
)

# GomokuAI calls back to GomokuGame:
game_logic.is_legal_move(r, c, player, board)
game_logic.make_move(r, c, player, board, hash)
game_logic.undo_move(r, c, player, board, captured, old_cap, captures, hash)
game_logic.check_terminal_state(board, captures, player, r, c, win_by_captures)
game_logic.check_and_apply_captures(r, c, player, board)
```

### GomokuAI ↔ MinimaxAlgorithm
```python
# GomokuAI calls MinimaxAlgorithm:
best_move, best_score, depth_reached = algorithm.iterative_deepening_search(
    game_state, ai_player, initial_board_score,
    ordered_moves_func, make_move_func, undo_move_func,
    is_legal_func, check_terminal_func
)

# Algorithm uses callbacks provided by AI:
ordered_moves_func(board, captures, player) → list of moves
make_move_func(r, c, player, board, captures, hash) → delta, captured, old_cap, new_hash
undo_move_func(r, c, player, board, captured, old_cap, captures, hash) → new_hash
is_legal_func(r, c, player, board) → (is_legal, reason)
check_terminal_func(board, captures, player, r, c) → bool
```

### GomokuAI ↔ HeuristicEvaluator
```python
# GomokuAI calls HeuristicEvaluator:
score = heuristic.evaluate_board(board, captures, player, win_by_captures)
line_score = heuristic.score_lines_at(r, c, board, player, opponent)

# HeuristicEvaluator uses utils:
line_str = get_line_string(r, c, dr, dc, board, player, opponent, board_size)
coords = get_line_coords(r, c, dr, dc, board_size)
```

## Optimization Stack

```
┌─────────────────────────────────────────────┐
│  Move Ordering (GomokuAI)                   │ ← Examines best moves first
├─────────────────────────────────────────────┤
│  Alpha-Beta Pruning (MinimaxAlgorithm)      │ ← Cuts bad branches
├─────────────────────────────────────────────┤
│  Transposition Table (MinimaxAlgorithm)     │ ← Caches positions
├─────────────────────────────────────────────┤
│  Delta Heuristic (GomokuAI)                 │ ← Incremental evaluation
├─────────────────────────────────────────────┤
│  Zobrist Hashing (GomokuGame)               │ ← Fast position hashing
├─────────────────────────────────────────────┤
│  Relevance Range (GomokuAI)                 │ ← Filters irrelevant moves
├─────────────────────────────────────────────┤
│  Iterative Deepening (MinimaxAlgorithm)     │ ← Progressive depth search
└─────────────────────────────────────────────┘
```

## Pattern Recognition Example

```
Board line: X O E P P P E O X
            ↓
get_line_string()
            ↓
Pattern:    X O E P P P E O X
            ↓
score_line_string()
            ↓
Match "EPPPE" → OPEN_THREE (10,000 points)
            ↓
Accumulate score
```

## State Management

### Game States
```
NORMAL → Player moves
    ↓
    Create 5-in-a-row?
    ↓
PENDING_WIN → Opponent must break line
    ↓
    Did opponent break line?
    ↓
    ├─ Yes → NORMAL (game continues)
    └─ No  → GAME_OVER (win by 5-in-a-row)

Alternate path:
Capture 5 pairs → GAME_OVER (win by captures)
```

### AI States
```
AI_NOT_THINKING
    ↓
AI_THINKING
    ├→ Iterative deepening depth 1
    ├→ Iterative deepening depth 2
    ├→ ...
    └→ Iterative deepening depth N or timeout
    ↓
MOVE_FOUND
    ↓
AI_NOT_THINKING
```

## Concurrency Model

```
Main Thread (pygame event loop)
    ↓
    ├─ UI Rendering (30 FPS)
    ├─ Event Handling
    └─ AI Thinking (blocking, with timeout)
        └─ Minimax search (single-threaded)
```

Note: AI thinking blocks the main thread but respects time limit.
Future enhancement: Move AI to separate thread.

## Memory Management

### Transposition Table
- **Key**: Zobrist hash + captures tuple
- **Value**: (score, depth)
- **Size**: Grows during search, cleared each move
- **Purpose**: Avoid re-evaluating same positions

### Board State
- **Structure**: 15x15 2D list
- **Copied**: During move ordering (deepcopy)
- **Modified**: During minimax (make/undo)
- **Purpose**: Maintain game state

## Configuration Points

Each module has clear configuration points:

### GomokuGame.py
```python
BOARD_SIZE = 15
SQUARE_SIZE = 40
AI_MAX_DEPTH = 14
AI_TIME_LIMIT = 2.0
AI_RELEVANCE_RANGE = 2
WIN_BY_CAPTURES = 5
```

### heuristic.py
```python
WIN_SCORE = 1000000000
OPEN_FOUR = 1000000
BROKEN_FOUR = 400000
CAPTURE_THREAT_OPEN = 30000
OPEN_THREE = 10000
# ... etc
```

### algorithm.py
```python
# Passed in constructor
max_depth = 14
time_limit = 2.0
win_score = 1000000000
```

## Testing Strategy

Each module can be tested independently:

```python
# Test heuristic
evaluator = HeuristicEvaluator(15)
score = evaluator.score_line_string("EPPPPE")
assert score == OPEN_FOUR

# Test algorithm (with mock functions)
algorithm = MinimaxAlgorithm(4, 1.0, 1000000)
best_move = algorithm.iterative_deepening_search(
    mock_game_state, mock_player, mock_score,
    mock_moves_func, mock_make_func, mock_undo_func,
    mock_legal_func, mock_terminal_func
)

# Test AI coordination (with mock game)
ai = GomokuAI(15, 4, 1.0, 2)
move = ai.get_best_move(
    mock_board, mock_captures, mock_hash,
    1, 5, mock_game_logic
)

# Test game logic
game = GomokuGame()
is_legal, reason = game.is_legal_move(7, 7, 1, game.board)
```

## Extension Points

### Add New Heuristic
1. Create new class inheriting HeuristicEvaluator
2. Override score_line_string() or evaluate_board()
3. Inject into GomokuAI

### Add New Algorithm
1. Create new class with same interface as MinimaxAlgorithm
2. Implement iterative_deepening_search()
3. Inject into GomokuAI

### Add New UI
1. Create new class using GomokuGame's logic methods
2. Implement own rendering (e.g., web UI)
3. Call same game logic methods

---

This modular architecture makes the codebase maintainable, extensible, and testable! 🎉

