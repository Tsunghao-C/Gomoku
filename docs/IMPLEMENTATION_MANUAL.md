# Gomoku Game Implementation Manual

This document summarizes the technical implementation, optimizations, and configuration parameters of the Gomoku AI project.

## 1. Game Implementation Strategy

The game is built using a modular architecture with a clear separation of concerns:

-   **`GomokuLogic.py`**: The core "Game Engine". It handles board state (1D array), rule validation, move execution, capture logic (P-O-O-P pattern), and win condition checking (5-in-a-row or 5 capture pairs). It uses a bitboard-like 1D representation for performance.
-   **`GomokuAI.py`**: The "AI Brain". It orchestrates the decision-making process, managing move generation, ordering, and invoking the search algorithm.
-   **`algorithm.py`**: The "Search Engine". It implements the Minimax algorithm with Alpha-Beta pruning and various enhancements.
-   **`heuristic.py`**: The "Evaluator". It assigns a numerical score to a board state based on pattern recognition (lines, threats, captures).
-   **`GomokuGame.py`**: The "GUI". It manages the Pygame window, user input, menu system, and rendering.
-   **`config.json`**: The "Control Panel". Centralized configuration for all game parameters.

## 2. Optimizations & Enhancements

### A. Performance Optimizations
1.  **1D Board Representation**: Converted the board from a 2D list to a flat 1D array (`size * size`). This improves cache locality and simplifies indexing logic.
2.  **Numeric Pattern Matching**: Replaced slow string-based pattern matching (regex/substring) with tuple-based numeric matching. Patterns are pre-compiled as tuples of integers (0, 1, 2, 3), significantly speeding up `heuristic.py`.
3.  **Optimized Move Ordering (Static Eval)**: Instead of fully simulating every candidate move (which is expensive due to capture checks), we use a "lightweight" static evaluation to sort moves. We only perform full simulation for the most promising moves during the actual search.
4.  **Zobrist Hashing**: Implemented for fast transposition table lookups, allowing the AI to reuse results for identical board states found via different move orders.

### B. Algorithmic Enhancements
1.  **Iterative Deepening**: The AI searches at depth 1, then 2, then 3, etc., until the time limit is reached. This ensures a best move is always available and allows for better move ordering in deeper searches.
2.  **Transposition Table**: Caches evaluation results to avoid re-calculating the same positions.
3.  **Principal Variation Search (PVS)**: (Implied via alpha-beta with ordering) Focuses search on the most likely "best" moves first.
4.  **Late Move Reductions (LMR)**: Reduces the search depth for moves that are late in the sorted list (likely bad moves), allowing the AI to search deeper on good moves.
5.  **Null Move Pruning**: The AI effectively "passes" to see if the opponent can still do damage. If not, the branch is pruned.
6.  **History Heuristic**: Keeps track of moves that caused beta-cutoffs (good moves) and prioritizes them in future sorting.
7.  **Windowed Search**: Restricts the search space to rectangular bounding boxes around existing piece clusters, ignoring the vast empty areas of the 19x19 board.
8.  **Critical Capture Logic**: The AI now treats "Capture Threats" as "Winning Moves" (50M score) if the player has 4 capture pairs, ensuring it defends against losing by captures with the same urgency as 5-in-a-row.

### C. Game Features
1.  **Menu System**: Allows choosing between "Player vs AI", "Player vs Player", and "PvP (Suggested Mode)".
2.  **Suggested Mode**: In PvP, the AI runs in the background for the White player and visually suggests the best move.
3.  **Capture Rules**: Fully implements the standard P-O-O-P capture rule and "Win by 5 Captures".

## 3. Configuration Guide

All configuration parameters are defined in `config.json`.
For a detailed explanation of every parameter and its effect on the game, please refer to:

👉 **[Configuration Reference (docs/CONFIG_REFERENCE.md)](CONFIG_REFERENCE.md)**

