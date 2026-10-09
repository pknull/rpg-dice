# Objective

rpg-dice is a Python package for RPG dice: DiceThrower rolls rpg-dice notation
(2d6+3, 10d10>=8x>=10, groups such as (1d10>=6)+(1d8>=6)) and
DiceProbability.exact returns the exact joint distribution of a roll's fields
for rpg-skills. pk.asha calls only DiceThrower().throw(). Requirements:
rpg-skills/docs/rpg-dice-requirements.md (approved 2026-10-09).

# State

Verified 2026-10-09. Version 0.5.0 on master, pushed to origin after Keeper
approval: afc4c0b exact engine, strict parser, groups and pool sums; 1ad1efe
docs; c426cf4 version 0.5.0; then this Memory commit. Implements D1-D4 and
S1-S4: dice_roller/notation.py (strict tree parser), dice_roller/exact.py
(Fraction joint over total/success/fail/ns/nf/pass, explosion residual
reported as unresolved, keep/drop DP, subroll mixtures, opt-in bounded faces).
Fixed e179458 defects: reroll-every-face hang, certain-explosion crash, eval of
** in throw_string, total modifier lost on empty pools. Suite 739 passed;
10d6kh3 1.1 ms, 10d10kh3 2.2 ms. No runtime dependencies; icepool test-only.
Released as tag v0.5.0 (on 7a06b3b) and GitHub release v0.5.0; dependents
pin git+https://github.com/pknull/rpg-dice.git@v0.5.0. The older v0.2 and v0.3
tags exist only in the local clone. Evidence: Work/reports/exact-engine.md
(local, gitignored).

# Next

- rpg-skills dice_odds.py must catch DiceException from parse_input (D3 now
  raises); outside this repo.
- pk.asha still pins 1b2f163. Moving the pin brings pool sums; wrapping each
  dice term in parentheses there gives conventional 2d6+3 = 10.

# Blockers

- None.
