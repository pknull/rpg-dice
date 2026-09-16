# Objective

rpg-dice is a Python package for RPG dice rolling: D&D-style notation
(2d6+3, 10d10>=5), exploding/compounding/penetrating dice, rerolls, success
counting and pool manipulation. Used as a dependency by the pk.shado Discord
bot.

# State

Verified 2026-09-16. master at e00fcdd (2026-08-13, ignore editor backups)
plus today's hygiene commit; public repo pknull/rpg-dice. v0.4 security
hardening is in the tree: sympy.sympify on user input replaced by the
whitelist-based dice_roller/safe_compare.py. Suite green today. Memory
reduced to the v2 pair; v1 files, reasoning_bank DB, event logs, dead hook
backups and the spent AUDIT-REVIEW were retired.

# Next

- None scheduled.

# Blockers

- None.
