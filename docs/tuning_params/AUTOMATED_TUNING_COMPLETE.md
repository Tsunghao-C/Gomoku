# 🎯 Automated AI Tuning Framework - Complete!

## ✅ What's Been Created

You now have a **complete automated testing and tuning framework** for systematically finding optimal heuristic parameters!

### 📦 Framework Components

**Core System:**
- ✅ `srcs/GomokuGameHeadless.py` - Fast AI vs AI engine (no GUI)
- ✅ `tests/config_tuner.py` - Main tuning framework
- ✅ `tests/parameter_sweep.py` - Systematic parameter exploration
- ✅ `tests/quick_test.py` - Rapid testing utility
- ✅ `run_tuning.sh` - Easy-to-use wrapper script

**Documentation:**
- ✅ `tests/README.md` - Framework documentation
- ✅ `TUNING_GUIDE.md` - Complete usage guide
- ✅ `AUTOMATED_TUNING_COMPLETE.md` - This file

**Infrastructure:**
- ✅ `tests/results/` - Directory for storing results

## 🚀 Quick Start (30 seconds)

Test your current configuration:

```bash
./run_tuning.sh quick
```

This runs 3 AI vs AI games and shows performance metrics!

## 🎮 Usage Examples

### 1. Test a Single Parameter Change

```bash
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 \
  6
```

**Output:**
```
✅ New value (500000) performs BETTER than baseline!
   Win rate: 66.7%
   Consider updating config.json
```

### 2. Find Optimal Value (Parameter Sweep)

```bash
./run_tuning.sh sweep capture
```

Tests multiple capture defense penalty levels and ranks them by win rate.

### 3. Compare Multiple Configurations

```bash
./run_tuning.sh tournament
```

Runs a round-robin tournament between different configurations.

### 4. A/B Test Two Configs

```bash
./run_tuning.sh compare config1.json config2.json 10
```

## 🎯 Tuning Strategies Implemented

### 1. **Single Parameter Sweep**
Test one parameter across multiple values:

```python
from tests.parameter_sweep import ParameterSweep

sweep = ParameterSweep("config.json")
results = sweep.sweep_single_parameter(
    param_path='heuristic_settings.capture_defense.trap_detection_penalty',
    values=[200000, 300000, 400000, 500000, 600000],
    num_games=10
)
```

### 2. **Multi-Parameter Grid Search**
Test combinations of multiple parameters:

```python
results = sweep.sweep_multiple_parameters(
    param_specs={
        'heuristic_settings.scores.open_four': [800000, 1000000, 1200000],
        'heuristic_settings.scores.broken_four': [300000, 400000, 500000],
    },
    num_games=6
)
```

### 3. **Binary Search**
Efficiently find optimal value in a range:

```python
optimal_value, results = sweep.binary_search_parameter(
    param_path='heuristic_settings.capture_defense.critical_penalty',
    min_val=400000,
    max_val=1200000,
    num_iterations=5,
    games_per_test=8
)
```

### 4. **Tournament Mode**
Round-robin competition between multiple configs:

```python
from tests.config_tuner import ConfigTuner

tuner = ConfigTuner("config.json")

configs = {
    'baseline': tuner.base_config,
    'aggressive': tuner.create_config_variant('aggressive', {...}),
    'defensive': tuner.create_config_variant('defensive', {...}),
}

results = tuner.run_tournament(configs, num_games_per_match=10)
```

## 📊 Metrics Tracked

The framework automatically tracks:

**Game-Level:**
- Winner (Black/White/Draw)
- Total moves
- Captures by each player
- Move history

**Performance:**
- Average depth reached
- Maximum depth reached
- Average time per move
- Maximum time per move

**Statistics:**
- Win rate (%)
- Points (3 for win, 1 for draw, 0 for loss)
- Head-to-head records

## 🔧 Key Features

### ⚡ Fast Headless Games
- No pygame GUI overhead
- Pure game logic for maximum speed
- Parallel processing ready

### 🎯 Statistical Rigor
- Each config plays as both Black and White
- Eliminates first-player advantage
- Configurable number of games for significance

### 💾 Result Persistence
- All results saved to JSON
- Detailed match history
- Complete game logs for analysis

### 🔄 Easy Iteration
- Quick validation (3 games, 30 seconds)
- Parameter testing (4-6 games, 2-3 minutes)
- Full tuning (10+ games, 10-30 minutes)

## 📈 Recommended Workflow

### Phase 1: Quick Validation (2 minutes)
```bash
# Test current config
./run_tuning.sh quick

# Output: depth 7.2, time 1.85s → looks good!
```

### Phase 2: Identify Issues (manual testing)
Play games and observe:
- "AI is captured too easily" → Tune capture defense
- "AI too passive" → Tune pattern scores
- "Search too shallow" → Tune time/depth limits

### Phase 3: Test Quick Fixes (5-10 minutes)
```bash
# Try higher capture penalty
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 \
  6

# Result: ✅ 67% win rate → significant improvement!
```

### Phase 4: Systematic Tuning (30-60 minutes)
```bash
# Find optimal values
./run_tuning.sh sweep capture
```

### Phase 5: Final Validation (1-2 hours)
```bash
# Tournament with best configs
./run_tuning.sh tournament
```

### Phase 6: Update Config
Edit `config.json` with winning values and repeat from Phase 1!

## 🎯 What to Tune First

### High Priority (Tune First)

**1. Capture Defense Penalties**
- Most impact on AI survival
- Current issue: AI easily captured
- Parameters:
  - `trap_detection_penalty` (400000)
  - `critical_penalty` (800000)
  - `warning_penalty` (300000)

**2. Pattern Scores**
- Affects AI strategy balance
- Parameters:
  - `open_four` (1000000)
  - `broken_four` (400000)
  - `open_three` (10000)

### Medium Priority (Tune Later)

**3. Capture Thresholds**
- When penalties activate
- Parameters:
  - `critical_threshold` (8)
  - `warning_threshold` (6)

**4. Search Parameters**
- Performance vs quality tradeoff
- Parameters:
  - `time_limit` (3.0)
  - `max_depth` (12)

### Low Priority (Fine-Tuning)

**5. Closed Pattern Scores**
- Minor tactical adjustments
- Two-stone patterns
- Edge case handling

## 💡 Example Tuning Session

```bash
# 1. Baseline (1 min)
./run_tuning.sh quick
# Result: depth 7.2, AI captured easily

# 2. Test higher penalty (2 min)
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  500000 6
# Result: ✅ 67% win rate!

# 3. Test even higher (2 min)
./run_tuning.sh test \
  'heuristic_settings.capture_defense.trap_detection_penalty' \
  600000 6
# Result: ⚖️ 50% win rate, no improvement

# 4. Confirm with sweep (15 min)
./run_tuning.sh sweep capture
# Result: 500000 is optimal

# 5. Update config.json
# trap_detection_penalty: 400000 → 500000

# 6. Validate (1 min)
./run_tuning.sh quick
# Result: AI much more defensive! ✅
```

## 📁 File Structure

```
gomoku/
├── run_tuning.sh           # Easy wrapper script
├── TUNING_GUIDE.md         # Complete usage guide
├── config.json             # Your config to tune
├── srcs/
│   └── GomokuGameHeadless.py  # Fast headless engine
└── tests/
    ├── README.md           # Framework docs
    ├── config_tuner.py     # Main framework
    ├── parameter_sweep.py  # Sweep utilities
    ├── quick_test.py       # Quick testing
    └── results/            # Saved results
        └── tournament_*.json
```

## 🔍 Advanced Usage

### Custom Tuning Script

Create `tests/my_tuning.py`:

```python
from tests.parameter_sweep import ParameterSweep

sweep = ParameterSweep("config.json")

# Test your specific parameters
results = sweep.sweep_multiple_parameters(
    param_specs={
        'heuristic_settings.capture_defense.trap_detection_penalty': 
            [400000, 500000, 600000],
        'heuristic_settings.capture_defense.critical_penalty': 
            [700000, 800000, 900000],
    },
    num_games=10
)

sweep.tuner.save_results(results)
```

Run with:
```bash
uv run python tests/my_tuning.py
```

### Analyze Saved Results

```bash
# List results
ls tests/results/

# View tournament standings
cat tests/results/tournament_20251117_123456.json | \
  jq '.standings'

# Find best config
cat tests/results/tournament_20251117_123456.json | \
  jq '.ranked[0]'
```

## 🎓 Learning from Results

### Good Signs ✅
- **Win rate >60%**: Significant improvement
- **Depth 7-10**: Good search performance
- **Time <2.5s avg**: Within constraints
- **Consistent wins**: Robust strategy

### Warning Signs ⚠️
- **Win rate ~50%**: No clear improvement
- **Depth <6**: Not searching deep enough
- **Time >3s avg**: Exceeding time limit
- **Inconsistent results**: Need more games

### Problem Signs ❌
- **Win rate <40%**: Configuration worse than baseline
- **Depth <4**: Serious performance issues
- **Illegal moves**: Parameter values broken
- **Crashes**: Config syntax errors

## 🆘 Troubleshooting

### "Tests are too slow"
```bash
# Reduce games
./run_tuning.sh test param value 3  # Instead of 6

# Or reduce time limit temporarily
# Edit config: "time_limit": 2.0
```

### "Results are inconsistent"
```bash
# Increase games for more reliable results
./run_tuning.sh test param value 10  # Instead of 4
```

### "AI makes illegal moves"
Check parameter values are reasonable:
- Not negative
- Not zero (for penalties)
- Maintain score hierarchy (open_four > broken_four > open_three)

## 📚 Next Steps

### Immediate (Today)
1. **Run quick test**: `./run_tuning.sh quick`
2. **Test one change**: Try higher capture penalty
3. **Read results**: Understand the output format

### This Week
1. **Run parameter sweep**: Find optimal capture defense
2. **Update config.json**: Apply winning values
3. **Validate improvement**: Play manually to confirm

### Ongoing
1. **Regular tuning**: Test after code changes
2. **Track progress**: Save best configs
3. **Document learnings**: What works, what doesn't

## 🎯 Success Criteria

**Short Term:**
- [ ] Framework runs successfully
- [ ] Can test single parameters
- [ ] Understand result interpretation

**Medium Term:**
- [ ] Find optimal capture defense penalties
- [ ] AI survives longer against captures
- [ ] Consistent depth 7-9 achieved

**Long Term:**
- [ ] Balanced offense and defense
- [ ] Win rate >70% vs old configs
- [ ] No obvious exploitable weaknesses

## 🎉 Summary

You now have a **professional-grade AI tuning framework** that:

✅ Runs automated AI vs AI games  
✅ Tests parameter changes systematically  
✅ Tracks detailed performance metrics  
✅ Provides clear recommendations  
✅ Saves results for analysis  
✅ Supports multiple tuning strategies  
✅ Works seamlessly with your existing code  

**Start tuning now:**

```bash
./run_tuning.sh quick
```

Then iterate based on what you learn! 🚀

---

**Framework Status:** ✅ Complete and Ready  
**Documentation:** ✅ Comprehensive  
**Testing:** ✅ Verified Working  
**Next Action:** Run `./run_tuning.sh quick`

Happy tuning! 🎯🎮

