---
version: 1.0.0
lastUpdated: 2025-12-07
lifecycle: active
stakeholder: pknull
changeTrigger: session-completion
validatedBy: manual-review
dependencies: [projectbrief.md, techEnvironment.md]
---

# Active Context: rpg-dice

## Current Status

**Phase**: Feature Complete
**Date**: 2025-12-07
**Version**: v0.3

## Recent Changes (v0.3)

- **Subrolls**: Dice expressions now work anywhere a number value is expected
  - Total modifiers: `1d20=+1d4`
  - Comparators: `10d6>=1d3`
  - Method values: `10d6kh1d4`
- **Chained total modifiers**: `3d6=+10=-3` accumulates correctly
- **Removed legacy pool_modifier**: Use `=+`/`=-` syntax instead
- **Documentation updated**: README.md and dice_roller_cheat_sheet.md

## Previous Changes (v0.2)

- Total check syntax (`t>=N`)
- Total modifier syntax (`=+N`, `=-N`)
- AnyDice-style probability analyzer
- Asha framework integration

## Current Branch

`master`

## Known Issues

None currently identified.

## Session Notes

v0.3 release - Subrolls feature complete. All 93 tests pass.
