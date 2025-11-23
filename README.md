# Gomoku AI Project

A sophisticated Gomoku (Five in a Row) game with an intelligent AI opponent, featuring multiple optimizations and a modular architecture.

## 🎮 Game Features

- **Capture Rule**: Capture opponent's pairs using the P-O-O-P pattern
- **Win Conditions**: Win by 5 captures or 5-in-a-row
- **Pending Win State**: When a player creates 5-in-a-row, opponent gets one turn to break it
- **Double-Three Rule**: Cannot create two open threes simultaneously (illegal move)
- **Interactive UI**: Clean pygame-based interface with hover indicators and visual feedback

## 🏗️ Modular Architecture

The code has been refactored into a clean, maintainable modular structure:

```
gomoku/
├── Gomoku.py                    # Entry point - starts the game
├── srcs/
│   ├── __init__.py              # Package initialization
│   ├── GomokuGame.py            # Game state, rules, and UI rendering
│   ├── GomokuAI.py              # AI operations and move generation
│   ├── algorithm.py             # Minimax with optimizations
│   ├── heuristic.py             # Pattern evaluation and scoring
│   └── utils.py                 # Shared utility functions
├── old/                         # Previous optimization iterations
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

### Module Responsibilities

#### **Gomoku.py** - Entry Point
- Initializes and runs the game
- Simple, clean entry point

#### **srcs/GomokuGame.py** - Game UI
- Major game instance orchestrator
- UI rendering with pygame
- Event handling (mouse, keyboard)

#### **srcs/GomokuLogic.py** - Game Logic
- Game state management: Optimized with 1D array
- Zobrist hashing: A unique ID used to cache and compare board state
- Move validation and execution
- Capture detection
- Win condition checking

#### **srcs/GomokuAI.py** - AI Coordination
- Coordinates algorithm and heuristic modules
- Move generation and ordering
- Delta heuristic calculation
- Relevant move filtering (reduces branching factor)
- AI state management

#### **srcs/algorithm.py** - AI Thinking
- Minimax algorithm implementation
- Alpha-beta pruning optimization
- Iterative deepening search
- Transposition table for position caching
- Time management and timeout handling

#### **srcs/heuristic.py** - AI Brain
- Pattern recognition (open four, closed four, broken patterns, etc.)
- Position evaluation
- Scoring constants and weights
- Line analysis and threat detection

#### **srcs/utils.py** - Shared Utilities
- Line string generation for pattern matching
- Coordinate calculations
- Helper functions used across modules

## 🚀 Running the Game

```bash
# Using uv (recommended)
uv run Gomoku.py

# Or using python directly
python3 Gomoku.py
```

## 🎯 Controls

- **Mouse Click**: Place a piece (Human player)
- **R**: Reset game
- **M**: Toggle game mode (Player vs AI / Player vs Player)

## 🧠 AI Optimizations

### 1. **Minimax Algorithm**
Core decision-making algorithm where AI (maximizer) seeks best moves while simulating opponent (minimizer) responses.

### 2. **Alpha-Beta Pruning**
Eliminates branches that cannot affect the final decision, dramatically reducing search space.

### 3. **Iterative Deepening**
Progressively searches deeper levels, ensuring best move is found within time limit.

### 4. **Delta Heuristic** ⭐
Instead of re-evaluating the entire board at each node, calculates only the *change* (delta) in evaluation. This optimization allows searching to depth 14+ instead of 4-6.

### 5. **Zobrist Hashing**
Fast board position hashing for efficient transposition table lookups.

### 6. **Transposition Table**
Caches previously evaluated positions to avoid redundant calculations.

### 7. **Move Ordering**
Evaluates and orders moves locally before searching, ensuring best moves are examined first for better pruning.

### 8. **Relevance Range Filtering**
Only considers moves within range of existing pieces, reducing branching factor from 225 to typically 20-40 moves.

### 9. **Enhanced Pattern Recognition**
- Open Four: `_OOOO_` (immediate threat)
- Broken Four: `_OO_OO_`, `_O_OOO_` (forcing moves)
- Capture Threats: `POOE`, `EOOP` (setup captures)
- Capture Setups: `POEP` (bridge patterns)
- Open Three: `_OOO_`
- Broken Three: `_O_O_O_`
- And more...

## 📊 Performance

- **Search Depth**: 14 levels (with delta heuristic)
- **Time Limit**: 2 seconds per move
- **Branching Factor**: Reduced from ~225 to ~20-40 through relevance filtering
- **Positions Evaluated**: Thousands per move with caching

## 🔧 Configuration

Key constants in `srcs/GomokuGame.py`:

```python
BOARD_SIZE = 15              # Board dimensions
AI_MAX_DEPTH = 14            # Maximum search depth
AI_TIME_LIMIT = 2.0          # Time limit per move (seconds)
AI_RELEVANCE_RANGE = 2       # Move filtering range
WIN_BY_CAPTURES = 5          # Pairs needed to win
```

## 📈 Development History

The project evolved through multiple optimization iterations:

1. **M1-M4**: Basic game logic and UI
2. **M5-M6**: Initial AI with basic minimax
3. **M7**: Alpha-beta pruning
4. **M8**: Improved heuristics
5. **M9**: Zobrist hashing and transposition tables
6. **M10**: Delta heuristic (major performance boost)
7. **M11**: Enhanced pattern recognition
8. **Current**: Modular refactoring for maintainability

Previous versions are preserved in the `old/` directory.

## 🎓 Key Concepts

### Minimax Algorithm
Two-player zero-sum game algorithm where one player maximizes score and the other minimizes it.

### Alpha-Beta Pruning
Ignores branches that are proven to be worse than previously examined moves.

### Depth Limiting
Limits recursion depth to balance computation time, using evaluation functions at leaf nodes.

### Evaluation Function
Calculates position advantage by analyzing patterns, threats, and strategic positions. Can be enhanced with machine learning.

### Delta Heuristic
Incremental evaluation technique that calculates only the change in score rather than full board re-evaluation.

## 📝 Future Enhancements

1. **Machine Learning Integration**: Train neural networks for better position evaluation
2. **Opening Book**: Pre-computed strong opening sequences
3. **Endgame Tablebase**: Perfect play in endgame positions
4. **Monte Carlo Tree Search**: Alternative to minimax for certain positions
5. **Parallel Search**: Multi-threaded move exploration
6. **Move History**: Undo/redo functionality
7. **Game Analysis**: Post-game review and analysis tools

## 📜 License

See LICENSE file for details.

## 🤝 Contributing

This is an educational project. Feel free to fork and experiment with your own optimizations!

---

**42 AI Project** - Building intelligent game-playing systems
