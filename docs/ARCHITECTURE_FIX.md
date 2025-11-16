# Architectural Fix: Integrated Capture Vulnerability

## 🎯 The Problem

The AI was still easily captured and made "stupid" moves once the human started capturing stones, despite having explicit capture defense logic.

### Root Cause

The capture vulnerability penalties were only applied **during move ordering** (depth 0), but **disappeared in the minimax search** (depth 1-12).

```
BEFORE (Broken Architecture):
┌─────────────────────────────┐
│ Move Ordering (Depth 0)     │
│  ✅ Check vulnerability     │
│  ✅ Apply penalties         │
└─────────────────────────────┘
            ↓
┌─────────────────────────────┐
│ Minimax Search (Depth 1-12) │
│  ❌ NO vulnerability check  │
│  ❌ Penalties disappeared   │
│  ❌ Walked into traps       │
└─────────────────────────────┘
```

This created a **blind spot**: the AI would rank moves defensively at the top level, but when evaluating deeper positions, it couldn't see the capture dangers anymore.

## ✅ The Solution

**Integrated capture vulnerability directly into the heuristic evaluation function.**

Now every single board position evaluated in the minimax tree (at any depth) automatically includes capture vulnerability penalties.

```
AFTER (Fixed Architecture):
┌────────────────────────────────────────┐
│ Every Minimax Node (All Depths)       │
│  ✅ Pattern evaluation                │
│  ✅ Capture scoring                   │
│  ✅ Vulnerability penalties ← NEW!    │
└────────────────────────────────────────┘
```

### Implementation

**Modified `heuristic.py`:**

```python
def evaluate_board(self, board, captures, player, win_by_captures):
    """
    Evaluates the entire board from the perspective of the given player.
    Includes capture vulnerability penalties.
    """
    opponent = 2 if player == 1 else 1
    my_score = self.calculate_player_score(board, captures, player, win_by_captures)
    opponent_score = self.calculate_player_score(board, captures, opponent, win_by_captures)
    
    # NEW: Calculate vulnerability penalty for this position
    vulnerability_penalty = self._calculate_position_vulnerability(
        board, captures, player, opponent, win_by_captures
    )
    
    return my_score - (opponent_score * 1.1) - vulnerability_penalty
```

**Added two new methods to `heuristic.py`:**

1. **`_calculate_position_vulnerability()`**
   - Scans entire board for vulnerable AI stones
   - Applies escalating penalties based on capture count
   - Returns total penalty to subtract from position score

2. **`_is_stone_in_vulnerable_position()`**
   - Detects O-P-P-E and E-P-P-O capture patterns
   - Checks if stone is surrounded by 2+ opponent stones
   - Returns True if stone is vulnerable

**Removed from `GomokuAI.py` (~200 lines):**
- ❌ `_count_vulnerable_pairs_at_move()` - Pattern detection at move level
- ❌ `_is_stone_vulnerable()` - Stone vulnerability checks
- ❌ `_calculate_capture_defense_penalty()` - Complex penalty calculation
- ❌ Special vulnerability checking in `get_ordered_moves()`

## 🎨 Why This Is Better

### 1. Architecturally Sound
- **Single Source of Truth**: All position evaluation happens in `heuristic.py`
- **No Special Cases**: Move ordering uses the same evaluation as minimax
- **Clear Separation**: AI logic (move ordering) vs heuristic evaluation (scoring)

### 2. Correct at All Depths
```
Depth 1: Score = +10,000 - 400,000 (vuln) = -390,000
Depth 2: Score = +10,000 - 400,000 (vuln) = -390,000  
Depth 3: Score = +10,000 - 400,000 (vuln) = -390,000
Depth 4+: Score = +10,000 - 400,000 (vuln) = -390,000

✅ Consistent evaluation throughout entire search tree
✅ AI naturally avoids vulnerable positions at all depths
✅ No blind spots in the search
```

### 3. Simpler and More Maintainable
- **Before**: 200 lines of complex vulnerability logic spread across move ordering
- **After**: 90 lines of clean, focused code in the heuristic module
- **Easier to tune**: All penalties configured in one place (`config.json`)

## 📊 Evaluation Flow

```
For Every Position in Minimax Tree:
  1. Calculate pattern scores (open fours, threes, etc.)
  2. Add capture bonuses
  3. Check win conditions
  4. Scan board for vulnerable stones ← NEW!
  5. Calculate vulnerability penalty ← NEW!
  6. Return: my_score - (opp_score * 1.1) - vulnerability ← UPDATED!
```

## 🎮 Expected Behavior Changes

### Before Fix
- **Depth 1**: "This move looks dangerous!" (penalty applied)
- **Depth 4**: "This move looks great!" (no penalty, walks into trap)
- **Result**: AI makes moves that lead to captures

### After Fix
- **All Depths**: "This move creates vulnerable positions = -400k"
- **Result**: AI naturally avoids moves that create capture opportunities

## 🔧 Tuning

All vulnerability penalties are in `config.json` under `heuristic_settings.capture_defense`:

```json
{
  "trap_detection_penalty": 400000,        // Base penalty per vulnerable stone
  "early_warning_penalty": 150000,         // 4+ stones captured
  "warning_penalty": 300000,               // 6+ stones captured
  "critical_penalty": 800000,              // 8+ stones captured
  "desperate_penalty": 3000000             // 9+ stones captured
}
```

**Total Penalty Formula:**
```
penalty = trap_penalty * vulnerable_count + threat_penalty * vulnerable_count
```

Where `threat_penalty` escalates based on how many stones the opponent has captured.

## 🧪 Testing

Test the integrated capture defense:

```bash
uv run Gomoku.py
```

**What to look for:**

✅ **Early Game (0-3 captures)**
- AI maintains safe distance from your stones
- Avoids creating capturable pairs
- Base penalty: 400k per vulnerable stone

✅ **Mid Game (4-7 captures)**
- AI becomes increasingly defensive
- Actively protects vulnerable stones
- Penalty: 550k-1,200k per vulnerable stone

✅ **Late Game (8+ captures)**
- AI is highly defensive
- Won't walk into any capture opportunities
- Penalty: 1,200k-3,400k per vulnerable stone

✅ **All Search Depths**
- Depth 1, 2, 3, 4... all see the same penalties
- No blind spots in the search tree
- Consistent defensive behavior

## 📝 Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Where** | Move ordering only | Every minimax node |
| **When** | Depth 0 | All depths 1-12 |
| **Lines of Code** | ~200 lines | ~90 lines |
| **Architecture** | Special case logic | Integrated in heuristic |
| **Maintainability** | Complex, spread out | Clean, centralized |
| **Correctness** | Blind spots | Fully aware |

## 🎯 The Key Insight

**Capture vulnerability isn't a special case to handle during move ordering—it's a fundamental property of every board position that should be evaluated consistently throughout the entire search tree.**

By moving this logic into the heuristic evaluation function, we've made the AI's capture awareness a **core part of its intelligence** rather than a **band-aid applied at the top level**.

---

*This architectural fix was implemented on 2025-11-16 to address persistent issues with the AI making moves that led to captures.*

