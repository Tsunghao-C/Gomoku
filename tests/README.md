# Gomoku AI Configuration Tuning Framework

This directory contains tools for automated testing and tuning of AI heuristic parameters.

## 🎯 Overview

The tuning framework allows you to:
- **Run automated AI vs AI games** (headless, no GUI)
- **Compare different configurations** systematically
- **Find optimal parameter values** through various search strategies
- **Track detailed performance metrics** (win rate, depth, time, captures)

## 📁 Files

### Core Framework

- **`config_tuner.py`** - Main tuning framework
  - Run tournaments between different configurations
  - Track detailed statistics and generate reports
  - Save results for analysis

- **`../srcs/GomokuGameHeadless.py`** - Headless game engine
  - Fast AI vs AI games without GUI overhead
  - Full game logic with statistics tracking

### Tuning Utilities

- **`parameter_sweep.py`** - Systematic parameter exploration
  - Single parameter sweep (test one parameter across multiple values)
  - Multi-parameter grid search (test combinations)
  - Binary search for optimal value within range

- **`quick_test.py`** - Rapid testing for development
  - Quick validation of config changes (3-6 games)
  - Compare two config files
  - Test single parameter changes

## 🚀 Quick Start

### 1. Quick Test Current Configuration

Test your current `config.json` with 3 quick games:

```bash
cd tests
python quick_test.py
```

### 2. Test a Single Parameter Change

Test if a new value improves performance:

```bash
python quick_test.py test \
  "heuristic_settings.capture_defense.trap_detection_penalty" \
  500000 \
  4
```

This runs 4 games comparing the new value (500000) against baseline.

### 3. Run a Parameter Sweep

Test multiple values for one parameter:

```bash
python parameter_sweep.py capture
```

This tests different capture defense penalty levels.

### 4. Run a Full Tournament

Test multiple configurations in a round-robin tournament:

```bash
python config_tuner.py
```

## 📊 Usage Examples

### Example 1: Tune Capture Defense Penalties

```python
from tests.parameter_sweep import ParameterSweep

sweep = ParameterSweep("config.json")

# Test different trap detection penalties
results = sweep.sweep_single_parameter(
    param_path='heuristic_settings.capture_defense.trap_detection_penalty',
    values=[200000, 300000, 400000, 500000, 600000],
    num_games=10
)

sweep.tuner.save_results(results)
```

### Example 2: Grid Search Multiple Parameters

```python
results = sweep.sweep_multiple_parameters(
    param_specs={
        'heuristic_settings.scores.open_four': [800000, 1000000, 1200000],
        'heuristic_settings.scores.broken_four': [300000, 400000, 500000],
    },
    num_games=6
)
```

### Example 3: Binary Search for Optimal Value

```python
optimal_value, results = sweep.binary_search_parameter(
    param_path='heuristic_settings.capture_defense.critical_penalty',
    min_val=400000,
    max_val=1200000,
    num_iterations=5,
    games_per_test=8
)

print(f"Optimal value: {optimal_value}")
```

### Example 4: Custom Tournament

```python
from tests.config_tuner import ConfigTuner

tuner = ConfigTuner("config.json")

# Create config variants
configs = {
    'baseline': tuner.base_config,
    
    'aggressive': tuner.create_config_variant('aggressive', {
        'heuristic_settings.scores.open_four': 1200000,
        'heuristic_settings.scores.broken_four': 500000,
    }),
    
    'defensive': tuner.create_config_variant('defensive', {
        'heuristic_settings.capture_defense.trap_detection_penalty': 600000,
        'heuristic_settings.capture_defense.critical_penalty': 1000000,
    }),
}

# Run tournament
results = tuner.run_tournament(configs, num_games_per_match=10)

# Save results
tuner.save_results(results)
```

## 📈 Metrics Tracked

For each game:
- **Winner** (Black/White/Draw)
- **Total moves**
- **Captures** (by each player)
- **Time statistics** (avg, max time per move)
- **Depth statistics** (avg, max depth reached)
- **Move history** (complete game record)

For each configuration:
- **Win rate** (percentage of games won)
- **Average performance** (depth, time, captures)
- **Head-to-head records** (vs each other config)

## 🎮 Tuning Strategies

### 1. **Single Parameter Sweep**
Best for: Initial exploration, understanding parameter impact

```bash
python parameter_sweep.py capture
```

Tests one parameter across multiple values to find the best.

### 2. **Grid Search**
Best for: Tuning related parameters together

```python
sweep.sweep_multiple_parameters({
    'heuristic_settings.scores.open_four': [800000, 1000000, 1200000],
    'heuristic_settings.scores.broken_four': [300000, 400000, 500000],
})
```

Tests all combinations (3 × 3 = 9 configs in this example).

### 3. **Binary Search**
Best for: Finding optimal value in continuous range

```python
sweep.binary_search_parameter(
    'heuristic_settings.capture_defense.critical_penalty',
    min_val=400000,
    max_val=1200000,
    num_iterations=5
)
```

Efficiently narrows down to best value.

### 4. **A/B Testing**
Best for: Comparing two specific configurations

```bash
python quick_test.py compare config1.json config2.json 10
```

Direct comparison with statistical significance.

## 🔧 Recommended Tuning Workflow

### Phase 1: Quick Validation (5 minutes)
```bash
# Test your changes quickly
python quick_test.py test "heuristic_settings.scores.open_four" 1200000 4
```

### Phase 2: Single Parameter Optimization (30 minutes)
```bash
# Find optimal values for key parameters
python parameter_sweep.py capture
```

### Phase 3: Multi-Parameter Tuning (2-4 hours)
```python
# Test combinations of promising values
sweep.sweep_multiple_parameters({...})
```

### Phase 4: Final Tournament (1-2 hours)
```python
# Compare top configurations extensively
tuner.run_tournament(top_configs, num_games_per_match=20)
```

## 📊 Reading Results

Results are saved in `tests/results/tournament_TIMESTAMP.json`:

```json
{
  "standings": {
    "config_name": {
      "wins": 15,
      "losses": 3,
      "draws": 2,
      "points": 47
    }
  },
  "matches": [...detailed match data...]
}
```

**Points system:**
- Win = 3 points
- Draw = 1 point
- Loss = 0 points

## ⚡ Performance Tips

### Speed Up Testing

1. **Reduce games per match** for initial exploration:
   ```python
   num_games_per_match=4  # Instead of 10
   ```

2. **Use quick_test for rapid iteration**:
   ```bash
   python quick_test.py test param value 3
   ```

3. **Reduce time limit** for faster games:
   ```json
   "algorithm_settings": {
     "time_limit": 2.0  // Instead of 3.0
   }
   ```

### Ensure Statistical Significance

1. **Use enough games** (10+ per match for final tuning)
2. **Test as both colors** (framework does this automatically)
3. **Run multiple rounds** if results are close

## 🎯 What to Tune

### High Impact Parameters

1. **Capture Defense Penalties**
   - `trap_detection_penalty` (400000)
   - `critical_penalty` (800000)
   - `warning_penalty` (300000)

2. **Pattern Scores**
   - `open_four` (1000000)
   - `broken_four` (400000)
   - `open_three` (10000)

3. **Capture Thresholds**
   - `critical_threshold` (8)
   - `warning_threshold` (6)

### Lower Impact (tune later)

- Closed patterns scores
- Two-stone patterns
- Time limit adjustments

## 🐛 Troubleshooting

### Games are too slow
- Reduce `time_limit` in config
- Reduce `num_games` in tournament
- Use `quick_test.py` instead

### Results are inconsistent
- Increase `num_games_per_match`
- Check if configs are too similar
- Ensure proper seed randomization

### AI makes illegal moves
- Check `is_legal_move()` implementation
- Verify config parameters are valid
- Test with `verbose=True` to see details

## 📚 Further Reading

- `../docs/CONFIG_GUIDE.md` - Configuration file documentation
- `../docs/ARCHITECTURE_FIX.md` - Recent architectural improvements
- `../REFACTORING_COMPLETE.md` - Latest changes summary

---

**Happy tuning! 🎯**

Start with `python quick_test.py` and iterate from there.

