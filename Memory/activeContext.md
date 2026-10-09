# Objective

rpg-dice is a Python package for RPG dice: DiceThrower rolls rpg-dice notation
(2d6+3, 10d10>=8x>=10, groups such as (1d10>=6)+(1d8>=6)) and
DiceProbability.exact returns the exact joint distribution of a roll's fields
for rpg-skills. pk.asha calls only DiceThrower().throw(). Requirements:
rpg-skills/docs/rpg-dice-requirements.md (approved 2026-10-09).

# State

Verified 2026-10-09. master d8d4ea8 = origin/master, tree clean. Version 0.5.0
released: afc4c0b exact engine, strict parser, groups and pool sums; 1ad1efe
docs; c426cf4 version 0.5.0; 7a06b3b Memory; annotated tag v0.5.0 on 7a06b3b
and GitHub release v0.5.0 (installs from the tag with no other packages);
d8d4ea8 Memory records the release. Implements D1-D4 and S1-S4:
dice_roller/notation.py (strict tree parser), dice_roller/exact.py (Fraction
joint over total/success/fail/ns/nf/pass, explosion residual reported as
unresolved, keep/drop DP, subroll mixtures, opt-in bounded faces). Fixed
e179458 defects: reroll-every-face hang, certain-explosion crash, eval of ** in
throw_string, total modifier lost on empty pools. Suite 739 passed; 10d6kh3
1.1 ms, 10d10kh3 2.2 ms. No runtime dependencies; icepool test-only. Tags v0.2
and v0.3 exist only in the local clone. Evidence: Work/reports/exact-engine.md
(local, gitignored).

# Next

- rpg-skills dice_odds.py must catch DiceException from parse_input (D3 now
  raises); outside this repo.
- pk.asha still pins 1b2f163. Pin @v0.5.0 for pool sums; wrapping each dice
  term in parentheses there gives conventional 2d6+3 = 10.

# Blockers

- None.
