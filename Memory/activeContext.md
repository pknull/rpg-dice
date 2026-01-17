---
version: 1.1.0
lastUpdated: 2026-01-16
lifecycle: active
stakeholder: pknull
changeTrigger: session-completion
validatedBy: manual-review
dependencies: [projectbrief.md, techEnvironment.md]
---

# Active Context: rpg-dice

## Current Status

**Phase**: Security Hardening Complete
**Date**: 2026-01-16
**Version**: v0.4 (security)

## Recent Changes (v0.4 - Security)

### Critical: Removed sympy.sympify() Code Injection Risk

**Problem**: `sympy.sympify()` was called with user-controlled input in multiple files, creating potential code injection vulnerabilities.

**Solution**: Created `dice_roller/safe_compare.py` with:
- `safe_compare(left, op, right)` - Whitelist-based comparison operators
- `safe_arithmetic(left, op, right)` - Whitelist-based arithmetic operators
- `safe_eval_arithmetic(expr)` - Safe math expression evaluator

**Files Updated**:
- `DiceRoller.py` - 3 sympify calls replaced
- `DiceScorer.py` - 3 sympify calls replaced
- `DiceProbability.py` - 4 sympify calls replaced
- `DiceThrower.py` - 1 sympify call replaced

**Testing**: Added `tests/test_operator_coverage.py` with 57 exhaustive operator tests. All 150 tests pass.

**Performance Bonus**: Test suite runs 4x faster (36.98s → 8.44s) without sympy overhead.

## Previous Changes (v0.3)

- **Subrolls**: Dice expressions work anywhere a number value is expected
- **Chained total modifiers**: `3d6=+10=-3` accumulates correctly
- **Documentation updated**: README.md and dice_roller_cheat_sheet.md

## Previous Changes (v0.2)

- Total check syntax (`t>=N`)
- Total modifier syntax (`=+N`, `=-N`)
- AnyDice-style probability analyzer

## Current Branch

`master`

## Known Issues

None currently identified.

## Next Steps

From AUDIT-REVIEW.md remaining items:
- **[Medium]** Refactor DiceParser.py `clean_methods()` (160+ lines, high complexity)
- **[Medium]** Fix redundant `del rolls[:]` followed by `rolls = []` in DiceRoller.py:62-63
- **[Low]** Fix setup.py version (float → string)
- **[Low]** Convert DiceParser class lists to frozensets
- **[Low]** Add type hints throughout codebase
- **[Low]** Mark legacy DiceProbability methods as deprecated

## Session Notes

### 2026-01-16: Security Hardening

**Goal**: Address critical security findings from code audit regarding `sympy.sympify()` usage.

**Approach**: Test-first refactoring
1. Analyzed existing test coverage (93 tests)
2. Created exhaustive operator coverage tests (57 new tests) before changes
3. Discovered and documented actual grammar behavior (order matters!)
4. Implemented safe operator functions with strict whitelists
5. Replaced all sympify calls, verified all 150 tests pass

**Key Learning**: Expression order in dice syntax is critical:
- Correct: `NdS+N=+N>=N methods t>=N`
- The success evaluator must come BEFORE method tokens
- Using `>=5` after methods gets parsed as total check instead
