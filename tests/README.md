# Characterization tests

Golden-master tests that mechanize the refactor acceptance criterion
"same input -> same output".

## Layers
1. `test_corrector.py` — pins the pure functions of `corrector.Corrector`
   on a grid of points.
2. `test_trajectory.py` — pins the delayed / enhanced / raw output CSVs
   of `experiment_data.Trajectory.load_csv()`.
3. `test_create_csv_modes.py` — pins the new 9-column schema produced
   by `Trajectory.create_csv` when `mode='e'` / `mode='d'` is given.

## Regenerating fixtures

Only on first run, or when the baseline is intentionally being updated:

```bash
python tests/regen_fixtures.py
```

## Running

```bash
uv sync                # also installs pytest via the dev dependency group
uv run pytest tests/ -v
```

## Philosophy

- We do **not** judge whether the original code is "correct". We freeze
  the current output and only guarantee that it does not drift.
- Numerical tolerance: `_get_correct_pos` goes through
  `math.atan2`/`cos`/`sin`, so it can wobble at the floating-point
  level. We compare with a tolerance of about `1e-9`.
- Determinism: the original code does not depend on `random`,
  `datetime.now`, or dict-iteration order, so byte-for-byte comparison
  is possible.
