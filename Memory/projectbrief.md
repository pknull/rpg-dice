---
version: 1.0.0
lastUpdated: 2025-12-06
lifecycle: stable
stakeholder: pknull
changeTrigger: major-feature-addition
validatedBy: architecture-review
dependencies: []
---

# Project Brief: rpg-dice

## Overview

rpg-dice is a Python package providing flexible RPG-style dice rolling functionality. It supports complex dice notation including modifiers, exploding dice, success counting, and pool manipulation. Used as a dependency by the pk.shado Discord bot.

## Core Purpose

Provide programmable dice rolling with:
- D&D-style dice notation parsing (e.g., 2d6+3, 10d10>=5)
- Advanced roll modifiers (exploding, compounding, penetrating, rerolls)
- Success/failure counting systems
- Result pool manipulation (keep/drop highest/lowest)
- Custom dice faces via list notation

## Technical Foundation

**Language**: Python 3.x
**Distribution**: Python package via setup.py
**Key Dependencies**:
- sympy - Symbolic mathematics
- pyparsing - Grammar-based parsing

## Architecture

**Entry Point**: `dice_roller.DiceThrower.DiceThrower` class
**Core Modules**:
- `DiceThrower.py` - Main API entry point
- `DiceParser.py` - Notation parsing engine
- `DiceRoller.py` - Roll execution logic
- `DiceScorer.py` - Success/failure counting
- `DiceProbability.py` - Probability calculations
- `Die.py` - Single die representation
- `DiceException.py` - Custom exceptions

## Key Features

1. **Dice Notation Parsing**
   - Standard format: `NdN` (e.g., 2d6, 3d10)
   - Custom faces: `Nd{a,b,c}` for custom values
   - Modifiers stack in specific order

2. **Roll Modifiers**
   - Dice boost: `+N` or `-N` applied to each die
   - Roll boost: `+N` or `-N` applied to total
   - Success counters: `>=N`, `>N`, `<=N`, `<N`, `=N`
   - Failure counters: `f<N` or similar
   - Natural counters: `nsN`, `nfN` (pre-modifier)

3. **Exploding Mechanics**
   - Exploding: `xN` or `x>=N`
   - Compounding: `xxN` or `xx>=N`
   - Penetrating: `xpN` or `xxpN`

4. **Reroll Systems**
   - Infinite reroll: `r<N`
   - Single reroll: `ro<N`

5. **Pool Manipulation**
   - Keep high/low: `khN`, `klN`
   - Drop high/low: `dhN`, `dlN`

## API Usage

```python
from dice_roller.DiceThrower import DiceThrower
dice = DiceThrower()
result = dice.throw('10d6>=5')
# Returns: {'natural': [...], 'roll': '10d6>=5', 'modified': [...], 'success': '3', 'total': '42'}
```

## Constraints

- Python 3.x required
- Deterministic parsing via pyparsing
- No external service dependencies
- Pure Python implementation

## Distribution

- **Repository**: git@github.com:pknull/rpg-dice.git
- **Installation**: Via git reference in requirements.txt
- **Build Artifacts**: build/, dist/, dice_roller.egg-info/
- **Testing**: test.py for validation

## Integration

Used by:
- pk.shado Discord bot (Games.py cog)
- Installed via: `git+https://github.com/pknull/rpg-dice.git@master`

## Documentation

- README.md - Usage guide with examples
- dice_roller_cheat_sheet.md - Quick reference
- Inline docstrings in modules

## Success Criteria

- Parse all valid dice notations correctly
- Return consistent result structure
- Handle edge cases (0 dice, invalid notation)
- Maintain backward compatibility for pk.shado
