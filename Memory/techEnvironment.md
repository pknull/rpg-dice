---
version: 1.0.0
lastUpdated: 2025-12-06
lifecycle: active
stakeholder: pknull
changeTrigger: tool-addition
validatedBy: manual-testing
dependencies: [projectbrief.md]
---

# Technical Environment: rpg-dice

## Project Structure

```
/home/pknull/Code/rpg-dice/
├── dice_roller/              # Main package module
│   ├── __init__.py
│   ├── DiceThrower.py       # Main API entry point
│   ├── DiceParser.py        # Notation parsing
│   ├── DiceRoller.py        # Roll execution
│   ├── DiceScorer.py        # Success/failure counting
│   ├── DiceProbability.py   # Probability calculations
│   ├── Die.py               # Single die representation
│   └── DiceException.py     # Custom exceptions
├── build/                    # Build artifacts
├── dist/                     # Distribution files
├── dice_roller.egg-info/    # Package metadata
├── asha/                     # Asha framework submodule
├── Memory/                   # Memory Bank (this location)
├── venv/                     # Python virtual environment
├── setup.py                  # Package configuration
├── requirements.txt          # Dependencies
├── test.py                   # Test script
├── README.md                 # Usage documentation
├── dice_roller_cheat_sheet.md # Quick reference
└── LICENSE                   # MIT license
```

## Python Environment

**Python Version**: 3.x
**Virtual Environment**: `/home/pknull/Code/rpg-dice/venv`

**Activation**:
```bash
source /home/pknull/Code/rpg-dice/venv/bin/activate
```

**Dependencies**:
- sympy - Symbolic mathematics
- pyparsing - Grammar-based parsing

## Package Installation

**Development Mode**:
```bash
cd /home/pknull/Code/rpg-dice
pip install -e .
```

**Build Package**:
```bash
python setup.py sdist bdist_wheel
```

**Install from Git** (pk.shado usage):
```bash
pip install git+https://github.com/pknull/rpg-dice.git@master
```

## Testing

**Basic Import Test**:
```bash
python test.py
```

**Manual Testing**:
```python
from dice_roller.DiceThrower import DiceThrower
dice = DiceThrower()
dice.throw('2d6+3')
```

## API Usage

**Import**:
```python
from dice_roller.DiceThrower import DiceThrower
```

**Initialize**:
```python
dice = DiceThrower()
```

**Roll Dice**:
```python
result = dice.throw('10d6>=5')
```

**Result Structure**:
```python
{
    'natural': [6, 1, 3, ...],      # Original roll results
    'roll': '10d6>=5',              # Original roll string
    'modified': [6, 1, 3, ...],     # After modifiers applied
    'success': '3',                 # Success count (if applicable)
    'fail': '0',                    # Failure count (if applicable)
    'total': '42'                   # Sum of modified values
}
```

## Dice Notation Format

**Core Format**:
```
NdN(+|-)N  cmpN  McmpN  (+|-)N
```

**Components** (in order):
1. Number of dice (required)
2. `d` + sides (required)
3. Dice modifier (optional)
4. Success handler (optional)
5. Roll modifiers (optional)
6. Total modifier (optional)

**Examples**:
- `2d6` - Roll 2 six-sided dice
- `2d6+3` - Roll 2d6, add 3 to each die
- `10d6>=5` - Roll 10d6, count successes >=5
- `10d6x>=5` - Roll 10d6, explode on >=5
- `4d6kh3` - Roll 4d6, keep highest 3

## Development Conventions

**Code Style**:
- Python standard library conventions
- Minimal comments (self-documenting code preferred)
- Exception handling via DiceException

**Module Structure**:
- Single responsibility per module
- Clear separation: parsing → rolling → scoring
- Stateless operations where possible

## Git Workflow

**Current Branch**: `master`
**Remote**: `origin` (git@github.com:pknull/rpg-dice.git)

**Common Commands**:
```bash
git status
git add <files>
git commit -m "message"
git push origin master
```

## Integration Points

**pk.shado Discord Bot**:
- Imported in Games.py cog
- Used for `!dice` command
- Installed via git reference in requirements.txt

## Platform

**OS**: Linux 6.8.0-88-generic
**Architecture**: x86_64
**Working Directory**: /home/pknull/Code/rpg-dice

## Asha Framework

**Location**: `/home/pknull/Code/rpg-dice/asha/` (git submodule)
**CLAUDE.md**: References `@asha/CORE.md`
**Memory Bank**: `/home/pknull/Code/rpg-dice/Memory/`

## Tools and Integrations

**No MCP integrations currently configured**
**No external agents currently configured**

## Future Considerations

- Unit test suite (pytest)
- Type hints for Python 3.5+
- Performance profiling for complex rolls
- Documentation generation (Sphinx)
- PyPI publication
