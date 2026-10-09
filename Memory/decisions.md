# Decisions

- No eval or sympify on user-controlled input; comparisons and arithmetic go
  through the whitelisted operators in dice_roller/safe_compare.py, and
  expressions are parsed by the recursive-descent parser in
  dice_roller/notation.py.
- Parsing is strict: any unplaced or misplaced token raises DiceException;
  throw() maps it to 'Bad roll expression - ...'. NdX+NdY is a pool sum.
- Whitespace never changes meaning (README: spaces for readability only):
  +N right after the sides is per die in 2d6+3 and 2d6 + 3 alike; =+N is the
  total modifier. Keeper decision 2026-10-09; a space-significant rule was
  rejected as dangerous and non-intuitive.
- The exact engine never rolls. Explosions are followed to explode_depth extra
  dice per die and deeper mass is reported as unresolved, never folded into an
  outcome. Non-compounding explode with keep/drop is supported that way
  (measured 2026-10-09), not rejected.
- An empty kept pool still takes its total modifier (0d6=+5 totals 5), in the
  roller and the engine alike.
- icepool is a test-only dependency (requirements-test.txt); rpg-dice has no
  runtime dependencies. Game rules stay in rpg-skills.
- Memory/ is exactly the v2 pair; `.asha/config.json` is tracked; harness
  state and event logs stay local.
