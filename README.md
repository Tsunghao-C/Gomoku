# Gomoku AI Project

A sophisticated Gomoku (Five in a Row) game with an intelligent AI opponent, featuring multiple optimizations, a modular architecture, and modern game features.

## 🎮 Game Features

-   **Capture Rule (P-O-O-P)**: You can capture an opponent's pair of stones by flanking them (e.g., `X O O X` -> `X _ _ X`).
-   **Win Conditions**:
    1.  **5-in-a-row**: Standard victory condition.
    2.  **5 Captures**: First player to capture 5 pairs (10 stones) wins.
-   **Win Prevention**: If the opponent makes a move that creates a 5-in-a-row, but you can capture a pair that breaks that line, the win is canceled.
-   **Critical Capture Logic**: The AI recognizes when it (or you) is one pair away from winning by captures and treats capture threats as deadly winning moves.
-   **Game Modes**:
    -   **Player vs AI**: Challenge the minimax engine.
    -   **Player vs Player**: Local multiplayer.
    -   **PvP (Suggested)**: Play against a friend, but with AI suggestions for the White player (great for learning).
-   **Interactive UI**: Pygame-based interface with hover effects, menus, move highlighting, and status displays.

## 🏗️ Modular Architecture

The codebase is organized for clarity and performance:

```
gomoku/
├── Gomoku.py                    # Entry point
├── config.json                  # Centralized configuration (rules, AI, UI)
├── srcs/
│   ├── GomokuLogic.py           # Core Engine: Board state (1D), rules, captures
│   ├── GomokuAI.py              # AI Brain: Move generation, sorting, strategy
│   ├── algorithm.py             # Search: Minimax, Alpha-Beta, PVS, ID
│   ├── heuristic.py             # Evaluation: Pattern matching (Numeric/Tuple based)
│   ├── GomokuGame.py            # GUI: Pygame rendering, input handling, menu
│   └── utils.py                 # Utilities
└── docs/
    ├── IMPLEMENTATION_MANUAL.md # Detailed technical overview
    └── CONFIG_REFERENCE.md      # Explanation of config.json parameters
```

## 🚀 Running the Game

```bash
# Recommended: using uv
uv run Gomoku.py

# Or standard python
python3 Gomoku.py
```

## 🎯 Controls

-   **Mouse Click**: Place stone / Select menu option
-   **ESC**: Return to Main Menu
-   **R**: Reset current game

## 🧠 AI Optimizations

The AI achieves high performance (12+ ply search depth in <1s) using a combination of techniques:

1.  **1D Board Representation**: Optimized memory layout for fast access.
2.  **Numeric Pattern Matching**: Fast tuple-based pattern recognition (replacing slow string regex).
3.  **Iterative Deepening**: Ensures the best move is always ready within the time limit.
4.  **Transposition Table (Zobrist Hashing)**: Caches evaluations of identical board states.
5.  **Principal Variation Search (PVS)**: Searches the most promising moves first.
6.  **Late Move Reductions (LMR)**: Prunes search depth for unlikely moves.
7.  **Null Move Pruning**: Skips branches where passing is safe.
8.  **Windowed Search**: Restricts analysis to relevant areas ("clusters") of the board.
9.  **Static Evaluation Sort**: Rapidly orders candidate moves without full simulation.

## 🔧 Configuration

All game parameters are tweakable in `config.json`.
See [docs/CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md) for a detailed guide on every parameter.

## 📜 License

See LICENSE file for details.

## Noes after evaluation

### heuristic improvement ideas
1. Consider taking the number of stones in evaluation as well
2. Dynamic heuristic weight based on history actions (Monte Carlo heuristic)

### Nice to have features
1. Enable undo a move
2. Enable a mode to visualize what are the candidate moves that are taken into consideration by AI

### Next step
1. Deploy on web to be accessable
2. Add a UI to configure the difficulty of AI (depths for AI)

---

**42 AI Project** - Building intelligent game-playing systems
