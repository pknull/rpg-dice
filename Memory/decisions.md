# Decisions

- No eval or sympify on user-controlled input; comparisons and arithmetic go
  through the whitelisted operators in dice_roller/safe_compare.py.
- Memory/ is exactly the v2 pair; `.asha/config.json` is tracked; harness
  state and event logs stay local.
