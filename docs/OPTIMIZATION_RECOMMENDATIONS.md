# Quick Optimization Guide - Recommended Improvements

## Summary

Instead of multithreading/multiprocessing (complex with limited gains), implement these **high-ROI single-threaded optimizations**:

---

## 🥇 Priority 1: Enhanced Move Ordering (2-3x speedup)

### Current Issue
Move ordering is basic - doesn't prioritize high-value moves enough.

### Solution: Multi-tier Move Ordering

```python
# In GomokuAI.py - enhance get_ordered_moves()

def get_ordered_moves(self, board, captures, player):
    """Enhanced move ordering with threat prioritization."""
    
    # Tier 1: Immediate threats (check first!)
    winning_moves = []
    blocking_moves = []
    
    # Tier 2: High-value tactical moves
    high_priority = []  # Open fours, broken fours, captures
    
    # Tier 3: Good positional moves
    medium_priority = []  # Open threes, closed fours
    
    # Tier 4: Normal developing moves
    low_priority = []  # Twos, proximity moves
    
    opponent = 2 if player == 1 else 1
    candidates = self._get_relevant_positions(board)
    
    for (r, c) in candidates:
        if board[r][c] != 0:
            continue
        
        # Quick evaluation without full minimax
        my_score = self.heuristic.score_lines_at(r, c, board, player, opponent)
        opp_score = self.heuristic.score_lines_at(r, c, board, opponent, player)
        
        # Categorize by threat level
        if my_score >= WIN_SCORE * 0.5:
            winning_moves.append((my_score, (r, c)))
        elif opp_score >= WIN_SCORE * 0.5:
            blocking_moves.append((opp_score, (r, c)))
        elif my_score >= 400000 or opp_score >= 400000:  # Fours
            high_priority.append((max(my_score, opp_score * 1.1), (r, c)))
        elif my_score >= 10000 or opp_score >= 10000:  # Threes
            medium_priority.append((max(my_score, opp_score * 1.1), (r, c)))
        else:
            low_priority.append((my_score, (r, c)))
    
    # Sort each tier by score (descending)
    for tier in [winning_moves, blocking_moves, high_priority, medium_priority, low_priority]:
        tier.sort(reverse=True)
    
    # Concatenate tiers (best first)
    result = []
    for tier in [winning_moves, blocking_moves, high_priority, medium_priority, low_priority]:
        result.extend([move for score, move in tier])
    
    return result[:40]  # Limit to top 40 moves
```

**Expected gain:** 2-3x speedup (better pruning)

---

## 🥈 Priority 2: Killer Move Heuristic (1.5x speedup)

### Concept
Moves that caused cutoffs at one node often cause cutoffs at sibling nodes.

### Implementation

```python
# Add to MinimaxAlgorithm class:

class MinimaxAlgorithm:
    def __init__(self, max_depth, time_limit, win_score):
        # ... existing code ...
        
        # Killer move table: killer_moves[depth] = [move1, move2]
        self.killer_moves = [[] for _ in range(max_depth + 1)]
    
    def reset_search_state(self):
        # ... existing code ...
        # Reset killer moves
        for depth in range(len(self.killer_moves)):
            self.killer_moves[depth] = []
    
    def store_killer_move(self, move, depth):
        """Store a killer move at given depth."""
        if depth >= len(self.killer_moves):
            return
        
        # Keep top 2 killer moves per depth
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            if len(self.killer_moves[depth]) > 2:
                self.killer_moves[depth].pop()
    
    def minimax(self, game_state, depth, alpha, beta, is_maximizing_player,
               current_score, ai_player, ordered_moves_func, ...):
        # ... existing code until move ordering ...
        
        ordered_moves = ordered_moves_func(board, captures, player)
        
        # ENHANCEMENT: Prioritize killer moves
        if depth < len(self.killer_moves):
            killer_moves_at_depth = self.killer_moves[depth]
            # Move killers to front
            for killer in reversed(killer_moves_at_depth):
                if killer in ordered_moves:
                    ordered_moves.remove(killer)
                    ordered_moves.insert(0, killer)
        
        # ... rest of minimax ...
        
        # When a cutoff occurs:
        if beta <= alpha:
            self.store_killer_move((r, c), depth)  # Store as killer
            break
```

**Expected gain:** 1.5x speedup (better move ordering at all depths)

---

## 🥉 Priority 3: History Heuristic (1.3x speedup)

### Concept
Track which moves historically performed well.

### Implementation

```python
# Add to MinimaxAlgorithm:

class MinimaxAlgorithm:
    def __init__(self, max_depth, time_limit, win_score):
        # ... existing code ...
        
        # History table: history[move] = score
        self.history = {}
    
    def update_history(self, move, depth):
        """Increase history score for moves that are good."""
        if move not in self.history:
            self.history[move] = 0
        self.history[move] += depth * depth  # Deeper = more valuable
    
    def get_history_score(self, move):
        """Get history score for a move."""
        return self.history.get(move, 0)
    
    def sort_with_history(self, moves):
        """Sort moves using history heuristic."""
        move_scores = [(self.get_history_score(m), m) for m in moves]
        move_scores.sort(reverse=True)
        return [m for _, m in move_scores]
```

**Usage in move ordering:**
```python
# After basic ordering, apply history heuristic:
ordered_moves = self.algorithm.sort_with_history(ordered_moves)
```

**Expected gain:** 1.3x speedup

---

## 🎯 Priority 4: Aspiration Windows (1.2x speedup)

### Concept
Use a narrow α-β window based on previous search score.

### Implementation

```python
# Modify iterative_deepening_search:

def iterative_deepening_search(self, game_state, ai_player, ...):
    # ... existing code ...
    
    best_score_so_far = -math.inf
    
    for depth in range(1, self.max_depth + 1):
        if depth == 1:
            # Full window for depth 1
            alpha, beta = -math.inf, math.inf
        else:
            # Aspiration window based on previous score
            window = 500  # Adjustable
            alpha = best_score_so_far - window
            beta = best_score_so_far + window
        
        best_move, best_score = self.minimax_root_with_window(
            game_state, ai_player, initial_board_score, depth,
            alpha, beta, ...
        )
        
        # If search failed (score outside window), re-search with full window
        if best_score <= alpha or best_score >= beta:
            print(f"Aspiration window failed, re-searching with full window...")
            alpha, beta = -math.inf, math.inf
            best_move, best_score = self.minimax_root_with_window(
                game_state, ai_player, initial_board_score, depth,
                alpha, beta, ...
            )
        
        # ... rest of code ...
```

**Expected gain:** 1.2x speedup (saves ~20% of nodes)

---

## 📊 Combined Impact

Applying all optimizations:

```
Current performance (depth 5): 15 seconds
After Priority 1 (move ordering): 15s → 5s
After Priority 2 (killer moves): 5s → 3.3s
After Priority 3 (history): 3.3s → 2.5s
After Priority 4 (aspiration): 2.5s → 2.1s

Total improvement: 7x faster! 🚀
```

---

## 🛠️ Implementation Order

1. **Day 1:** Enhanced move ordering (biggest gain, easiest)
2. **Day 2:** Killer move heuristic (medium complexity)
3. **Day 3:** History heuristic (easy once you have killer moves)
4. **Day 4:** Aspiration windows (medium complexity)

---

## 🧪 Testing Each Optimization

```python
# Add timing to algorithm.py:

def iterative_deepening_search(self, ...):
    self.reset_search_state()
    
    # Performance metrics
    nodes_evaluated = 0
    cutoffs_occurred = 0
    
    for depth in range(1, self.max_depth + 1):
        depth_start = time.time()
        # ... search ...
        depth_time = time.time() - depth_start
        
        print(f"Depth {depth}: {depth_time:.2f}s, "
              f"{nodes_evaluated} nodes, "
              f"{cutoffs_occurred} cutoffs")
```

**Benchmark before and after each optimization!**

---

## 🎓 Learning Resources

- **Alpha-Beta Pruning:** https://www.chessprogramming.org/Alpha-Beta
- **Move Ordering:** https://www.chessprogramming.org/Move_Ordering
- **Killer Heuristic:** https://www.chessprogramming.org/Killer_Heuristic
- **History Heuristic:** https://www.chessprogramming.org/History_Heuristic
- **Aspiration Windows:** https://www.chessprogramming.org/Aspiration_Windows

---

## ⚡ Quick Wins (Can Implement Today)

### 1. Limit Move Candidates (Immediate 2x speedup)

```python
# In get_ordered_moves, after ordering:
return result[:30]  # Only evaluate top 30 moves instead of all
```

### 2. Increase Relevance Range for Later Game

```python
# More aggressive move pruning
if move_count < 10:
    self.relevance_range = 2  # Wide search early
else:
    self.relevance_range = 1  # Narrow search later
```

### 3. Early Termination for Obvious Wins

```python
# In minimax_root:
if best_score >= self.win_score * 0.9:
    return best_move, best_score  # Found winning move, stop!
```

---

**Want me to implement any of these optimizations? Just let me know which one to start with!** 🚀

