# 🎯 AI Configuration Tuning Guide

## Quick Start

You now have a complete automated testing framework to systematically tune your AI's heuristic parameters!

### Run Your First Test (30 seconds)

```bash
./run_tuning.sh quick
```

This runs 3 quick AI vs AI games to test your current configuration.

## 🎮 Available Commands

### 1. Quick Test
**Purpose:** Rapid validation of config changes  
**Time:** ~30 seconds - 2 minutes

```bash
./run_tuning.sh quick
```

**What it does:**
- Runs 3 AI vs AI games
- Shows average depth, time, and game length
- Perfect for quick iteration during development

### 2. Test Single Parameter
**Purpose:** Check if a parameter change improves performance  
**Time:** ~1-3 minutes

```bash
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 \
  4
```

**What it does:**
- Compares new value against baseline
- Runs 4 games (2 as each color)
- Gives clear recommendation (✅ better, ❌ worse, ⚖️ similar)

### 3. Parameter Sweep
**Purpose:** Find optimal value for a parameter  
**Time:** ~10-30 minutes

```bash
./run_tuning.sh sweep capture    # Tune capture defense
./run_tuning.sh sweep patterns   # Tune pattern scores
./run_tuning.sh sweep binary     # Binary search for optimal value
```

**What it does:**
- Tests multiple values systematically
- Ranks results by win rate
- Identifies best performing value

### 4. Full Tournament
**Purpose:** Compare multiple configurations  
**Time:** ~30-60 minutes

```bash
./run_tuning.sh tournament
```

**What it does:**
- Round-robin tournament between configs
- Tracks detailed statistics
- Saves results to `tests/results/`

### 5. Compare Two Configs
**Purpose:** A/B test two specific configurations  
**Time:** ~2-5 minutes

```bash
./run_tuning.sh compare config1.json config2.json 10
```

## 📊 Recommended Tuning Workflow

### Step 1: Baseline Check (2 minutes)
```bash
# Verify current config works
./run_tuning.sh quick
```

### Step 2: Identify Problem Areas
Play some games manually and identify weaknesses:
- Too aggressive with captures?
- Not defensive enough?
- Pattern recognition issues?

### Step 3: Test Quick Fixes (5-10 minutes)
```bash
# Try increasing capture defense
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 \
  6

# Try adjusting pattern scores
./run_tuning.sh test \
  'heuristic_settings.scores.open_four' \
  1200000 \
  6
```

### Step 4: Systematic Tuning (30-60 minutes)
```bash
# Find optimal capture defense penalties
./run_tuning.sh sweep capture
```

### Step 5: Fine-Tune and Validate (1-2 hours)
```bash
# Run tournament with your best configs
./run_tuning.sh tournament
```

## 🎯 Key Parameters to Tune

### 🛡️ Capture Defense (High Priority)

**When to tune:** AI is being captured too easily

```bash
# Base penalty for vulnerable stones
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 \
  6

# Penalty when opponent has 8+ captures
./run_tuning.sh test \
  'heuristic_settings.capture_defense.critical_penalty' \
  1000000 \
  6

# Penalty when opponent has 6+ captures
./run_tuning.sh test \
  'heuristic_settings.capture_defense.warning_penalty' \
  400000 \
  6
```

**Default values:**
- `trap_detection_penalty`: 400000 (always applied)
- `critical_penalty`: 800000 (8+ captures)
- `warning_penalty`: 300000 (6+ captures)
- `early_warning_penalty`: 150000 (4+ captures)

**Tuning tips:**
- Increase if AI walks into captures
- Decrease if AI is too passive/defensive
- Test in increments of 100000

### 🎯 Pattern Scores (Medium Priority)

**When to tune:** AI strategy seems off-balance

```bash
# Open four (near-winning position)
./run_tuning.sh test \
  'heuristic_settings.scores.open_four' \
  1200000 \
  6

# Broken four (strong threat)
./run_tuning.sh test \
  'heuristic_settings.scores.broken_four' \
  500000 \
  6

# Open three (tactical setup)
./run_tuning.sh test \
  'heuristic_settings.scores.open_three' \
  12000 \
  6
```

**Default values:**
- `open_four`: 1000000
- `broken_four`: 400000
- `open_three`: 10000
- `broken_three`: 4000

**Tuning tips:**
- These should maintain rough hierarchy (open_four >> broken_four >> open_three)
- Increase if AI ignores good opportunities
- Decrease if AI overvalues certain patterns

### ⏱️ Search Parameters (Lower Priority)

```bash
# Time limit per move
./run_tuning.sh test \
  'algorithm_settings.time_limit' \
  2.5 \
  4

# Maximum search depth
./run_tuning.sh test \
  'algorithm_settings.max_depth' \
  14 \
  4
```

## 📈 Reading Results

### Quick Test Output
```
QUICK TEST SUMMARY
================================================================
Games completed: 3
Average moves per game: 87.3
Average depth: 7.2
Average time per move: 1.85s
Max depth reached: 10
```

**What to look for:**
- **Depth 6-10**: Good performance ✅
- **Depth 4-5**: May need more time or optimization ⚠️
- **Time >2.5s avg**: Consider reducing complexity ⚠️

### Single Parameter Test
```
RECOMMENDATION
================================================================
✅ New value (500000) performs BETTER than baseline!
   Win rate: 66.7%
   Consider updating config.json
```

**Interpretation:**
- **>60% win rate**: Significant improvement ✅
- **50-60% win rate**: Slight improvement, test more games
- **<50% win rate**: Keep current value ❌

### Parameter Sweep
```
PARAMETER SWEEP RESULTS: trap_detection_penalty
================================================================
Value                Win Rate     Points    
----------------------------------------------------------------------
500000               75.0%        36        
400000               60.0%        30        
300000               45.0%        24        
```

**What to do:**
1. Look for highest win rate
2. Update `config.json` with best value
3. Run another quick test to confirm

## 🔧 Advanced: Custom Tuning Scripts

### Test Multiple Related Parameters

Create `tests/custom_tune.py`:

```python
from tests.parameter_sweep import ParameterSweep

sweep = ParameterSweep("config.json")

# Test combinations of capture defense parameters
results = sweep.sweep_multiple_parameters(
    param_specs={
        'heuristic_settings.capture_defense.trap_detection_penalty': 
            [300000, 400000, 500000],
        'heuristic_settings.capture_defense.critical_penalty': 
            [600000, 800000, 1000000],
    },
    num_games=6
)

sweep.tuner.save_results(results)
```

Run with:
```bash
uv run python tests/custom_tune.py
```

## 📊 Example: Complete Tuning Session

```bash
# 1. Baseline check (1 min)
./run_tuning.sh quick

# 2. You notice AI is captured too easily
# Test higher trap penalty (2 min)
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 \
  6
# Result: ✅ 67% win rate, significant improvement!

# 3. Test even higher penalty (2 min)
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  600000 \
  6
# Result: ⚖️ 50% win rate, no improvement

# 4. Confirm 500000 is optimal with sweep (15 min)
./run_tuning.sh sweep capture
# Result: 500000 has highest win rate

# 5. Update config.json
# Change trap_detection_penalty from 400000 to 500000

# 6. Final validation (1 min)
./run_tuning.sh quick
# Result: AI now avoids captures much better!
```

## 💡 Tips for Effective Tuning

### Do's ✅
- Test one parameter at a time first
- Use enough games (6-10) for meaningful results
- Test as both Black and White (framework does this)
- Save results before making changes
- Document what you change and why

### Don'ts ❌
- Don't tune too many parameters at once
- Don't trust results from <4 games
- Don't forget to update `config.json` with improvements
- Don't over-tune (diminishing returns after a while)

### Performance Tips 🚀
- Use `quick` for rapid iteration (3 games)
- Use 4-6 games for parameter testing
- Use 10+ games for final validation
- Run tournaments overnight for extensive testing

## 📁 Results Storage

All results are saved in `tests/results/tournament_TIMESTAMP.json`

```bash
# View recent results
ls -lt tests/results/

# Analyze a specific result
cat tests/results/tournament_20251117_123456.json | jq '.standings'
```

## 🎯 Goals

**Immediate goals:**
- Win rate >50% against baseline in self-play
- Consistent depth 7-9 within time limit
- Defensive play when opponent has 6+ captures

**Long-term goals:**
- Win rate >70% against previous versions
- Balanced offense and defense
- No obvious exploits (like systematic captures)

## 🆘 Troubleshooting

### Games take too long
Reduce time limit in your test config:
```json
{"algorithm_settings": {"time_limit": 2.0}}
```

### Results are inconsistent
Increase number of games:
```bash
./run_tuning.sh test param value 10  # Instead of 4
```

### AI makes illegal moves
Check the parameter values are reasonable (not negative, not too extreme)

---

## 🚀 Ready to Start!

Begin with:
```bash
./run_tuning.sh quick
```

Then iterate based on what you observe! 🎮

Happy tuning! 🎯

