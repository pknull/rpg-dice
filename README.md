# rpg-dice

A simple RPG dice roller

> This project is partially managed by [Asha](https://github.com/pknull/asha), a Claude Code framework.

## Quick start

1. Install the package (it has no runtime dependencies):

   ```bash
   pip install -e .
   ```

   To run the tests: `pip install -r requirements-test.txt && python -m pytest`.
   icepool appears there only to cross-check the exact engine; rpg-dice never imports it.

2. Use the `DiceThrower` class to roll dice:

   ```python
   from dice_roller.DiceThrower import DiceThrower
   dice = DiceThrower()
   result = dice.throw('2d6')
   print(result)
   ```

## Classes

| Class | Purpose |
|-------|---------|
| `DiceThrower` | Main entry point - parses and executes dice expressions |
| `DiceParser` | Parses dice notation strings into executable components |
| `DiceRoller` | Handles the actual dice rolling logic |
| `DiceScorer` | Calculates successes, failures, and totals |
| `DiceProbability` | Exact probabilities (`exact`, `analyze`) and sampling (`monte_carlo`) |
| `Die` | Represents a single die with customizable sides |
| `DiceException` | Custom exception for dice-related errors |

## Explain the roll format

The dice roller can perform several different types of rolls based on the roll tokens. A quick summary
is as follows (spaces for readablity only).

This is our core roll.

```
          N   d   N   (+|-)N   =(+|-)N   cmpN   McmpN
         ─┬─ ─┬─ ─┬─ ─┬────── ─┬─────── ─┬──── ─┬─────
# of Dice ┘   │   │   │        │         │      │
Place Holder ─┘   │   │        │         │      │
Number of Sides ──┘   │        │         │      │
Per-Die Modifier ─────┘        │         │      │
Total Modifier ────────────────┘         │      │
Success Handler ─────────────────────────┘      │
Modifiers (x, kh, f, t, etc.) ─────────────────┘
```

The above order is specific and important. Not following the above format can lead to failure
executing your roll. The core structure (dice, per-die modifier, total modifier, success handler)
must follow this order. However, the method modifiers (M) such as `f`, `x`, `xx`, `kh`, `r`, `t`,
etc. may be placed in any order relative to each other.

### Quick Reference: The Three Modifiers

These look similar but do very different things:

| Syntax | Name | What it does | Example |
|--------|------|--------------|---------|
| `+N` | Per-Die Modifier | Adds N to each die | `2d6+5` → [3,4] becomes [8,9] |
| `=+N` | Total Modifier | Adds N to final total | `2d6=+5` → [3,4] total 7+5=12 |
| `>=N` | Success Threshold | Counts dice meeting condition | `2d6>=5` → [3,6] = 1 success |

**Combined example:** `5d10+5=+5>=10`

- Roll 5d10: [4, 8, 7, 9, 6]
- `+5` each die: [9, 13, 12, 14, 11]
- `>=10` count successes: 4 (the 13, 12, 14, 11)
- `=+5` add to total: 59 + 5 = 64

Result: `{success: '4', total: '64', ...}`

### Subrolls (Dice as Values)

Anywhere you see `N` (a number) in the table below, you can use a dice expression `NdS` instead. The dice is
rolled once per throw and its result replaces the value; exact analysis treats it as a random variable.
The per-die modifier takes only a number: `1d8+1d6` is a sum of two dice (see Pools, groups and arithmetic).

| Position | Static | With Subroll |
|----------|--------|--------------|
| Total Modifier | `=+5` | `=+1d4` |
| Total Modifier Chain | `=+10=-3` | `=+1d6=-1d4` |
| Success Threshold | `>=5` | `>=1d6` |
| Method Value | `kh3` | `kh1d4` |
| Explode Threshold | `x>=5` | `x=1d6` |
| Reroll Threshold | `r<=2` | `r<=1d2` |

**Example:** `1d20=+1d4t>=15`

- Roll 1d20: 12
- Roll subroll 1d4: 3
- Add to total: 12 + 3 = 15
- Check t>=15: pass!

**Chained subrolls:** `3d6=+1d4=-1d2`

- Roll 3d6: [4, 3, 5] = 12
- Roll 1d4: 3, Roll 1d2: 1
- Total: 12 + 3 - 1 = 14

### Pools, groups and arithmetic

`+` and `-` between dice terms add or subtract their totals: `1d8+1d6` is one d8 plus one d6, exactly as
`(1d8)+(1d6)`. Each term keeps its own tokens. A `+N` directly after the sides is still the per-die modifier
(`2d6+3` adds 3 to each die; spaces change nothing, so `2d6 + 3` is the same); a `+N` after any other token
adds N to the total (`2d20kh1+5`), and `=+N` always does.

Parentheses make a group. Groups combine with `+`; across them `natural` and `modified` concatenate, while
`total`, `success`, `fail`, `ns` and `nf` add:

```
dice.throw('(1d10>=6)+(1d8>=6)')     # one success count over a d10 and a d8
dice.throw('(2d20kh1)=+5t>=15')      # advantage, +5, against DC 15
```

Tokens after a closing parenthesis apply to the group's combined result: total modifiers (`=+N`), a success
comparator, `s`/`f`/`ns`/`nf` (these replace the members' own rules for the whole group), keep/drop and the total
check. Group tokens need explicit values. Keep/drop on a group needs members that are plain sums of dice terms;
tied values are kept in left-to-right order. `*` and `/` take a constant (`(1d8+1d6)*2`, `(1d6)/2`); division
gives an exact fraction.

A total check (`t`, or a comparator after the methods) tests the total of the whole expression, so it may only
follow the last token of a single term or group: `1d20+1d4t>=10` is rejected, `(1d20+1d4)t>=10` works.

### Strict parsing

Every character must be placed. A misplaced or unknown token, a repeated method (`kh1kh2`), a total modifier
after the methods, a reroll that matches every face, an explosion every face triggers, a keep/drop count
below zero (a bare `k` on dice like `{-2,-1}`), more than 200 dice in
one expression (subrolls included), more than 100 sides, more than 200 terms or groups nested deeper than 32
raise `DiceException`; `throw()` returns `'Bad roll expression - ...'`. The token order is the one shown at the
top: dice, per-die modifier, total modifiers, success comparator, methods, total check. Comparison
values are unsigned numbers (`f<0` counts the -1 face of a Fate die); `=` and `==` both mean equal.

### Exact probabilities

```python
from dice_roller.DiceProbability import DiceProbability
result = DiceProbability().exact('2d20=+5kh1t>=15ns20nf1')
result.fields                  # ('total', 'success', 'fail', 'ns', 'nf', 'pass')
result.joint                   # {(total, success, fail, ns, nf, pass): Fraction, ...}
result.marginal('pass')[1]     # Fraction(319, 400)
result.records()               # [{'total': 6, ..., 'probability': Fraction(1, 400)}, ...]
```

`exact()` returns the joint distribution of every roll-result field with `Fraction` probabilities, computed
without rolling. A field the expression does not define is `None` (`fail` without `f`, `pass` without a total
check). Explosions are followed to `explode_depth` extra dice per die (default 10); the probability of deeper
chains is reported as `result.unresolved`, never folded into an outcome. `faces=True` adds `result.faces`, the
distribution of (sorted kept `modified`, sorted `natural`, outcome), for pools within `faces_limit` multisets
(default 250,000: about 28d6, 11d10 or 6d20 without rerolls); beyond it a `DiceException` names the limit.
`analyze()` summarises the same result (`distribution`, `mean`, `std`, percentiles, `success_distribution`,
`pass_probability`, `joint`, `unresolved`). 10d10kh3 takes a few milliseconds; `tools/bench_exact.py` times
any expression in a fresh interpreter.

### Quick Reference: Success vs Pass

| Field | Syntax | Question Answered |
|-------|--------|-------------------|
| `success` | `>=N` | How many dice meet the threshold? |
| `pass` | `t>=N` | Does the total meet the target? |

**Example:** `5d10>=8t>=30` answers both "how many hits?" and "did I beat the DC?"

---

Code wise, you'll just need to import the dice roller module, create an instance of the class
and wham-o, you can start rolling dice!

 ```
from dice_roller.DiceThrower import DiceThrower
dice = DiceThrower()
dice.throw('10d6')
{'natural': [5, 4, 5, 1, 3, 1, 2, 6, 4, 6], 'roll': '10d6', 'modified': [5, 4, 5, 1, 3, 1, 2, 6, 4, 6], 'success': '2', 'total': '37'}
```

### I need examples and more explanation please

This is a base example roll

```
10d6
```

This is how it would be executed.

```
from dice_roller.DiceThrower import DiceThrower
dice = DiceThrower()
dice.throw('10d6')
{'natural': [5, 4, 5, 1, 3, 1, 2, 6, 4, 6], 'roll': '10d6', 'modified': [5, 4, 5, 1, 3, 1, 2, 6, 4, 6], 'success': '2', 'total': '37'}

```

Breaking the roll up into it's components it works like this

#### The first integer is the number of dice to roll (required)

```
10
```

#### Sides, or the set dN (required)

The second segment is the number of sides, with the token of dN

```
d6
```

This would constitute a 6 sided dice. You can also replace the number with a list in curly brackets dice. A list
containing any text face takes no modifiers: the roll is rejected rather than the modifiers ignored.

```
10d{a,b,c}
```

---

### PER-DIE MODIFIER

Add a bonus to each individual die result. Place the modifier directly after the sides.

```
dice.throw('2d6+4')
{'natural': [4, 2], 'roll': '2d6+4', 'modified': [8, 6], 'success': '1', 'total': '14'}
```

Each die gets +4: natural 4 becomes 8, natural 2 becomes 6.

---

### COUNTERS

The following two methods allow us to provide rules for counting successes and failures. Successes are
automatically assumed to be the highest face. You can adjust it by providing another number. Failures
can just be flagged with a default counter of the lowest face. You can also provide comparators for
advanced counters.

#### Successes N

To count successes instead of totals, add a comparator after the sides and any boost modifiers.

```
dice.throw('10d6>=5')
{'natural': [6, 1, 3, 1, 2, 4, 2, 6, 5, 2], 'roll': '10d6>=5', 'modified': [6, 1, 3, 1, 2, 4, 2, 6, 5, 2], 'success': '3', 'total': '32'}

dice.throw('2d6+4>5')
{'natural': [3, 6], 'roll': '2d6+4>5', 'modified': [7, 10], 'success': '2', 'total': '17'}
```

#### Failures fN

To count failures, use the fN token with a comparator or just the side

```
dice.throw('10d6f<2')
{'natural': [5, 5, 4, 3, 2, 3, 4, 6, 6, 4], 'success': '2', 'fail': '0', 'total': '42', 'roll': '10d6f<2', 'modified': [5, 5, 4, 3, 2, 3, 4, 6, 6, 4]}
```

#### Naturals nsN/nsF

If you'd like to count success and fails before modifiers, you can add ns and nf to your roll. A
typical DnD roll might look like. Do note that successes are automatically tallied for the highest
and lowest values for the dice.

```
dice.throw('1d20>15ns20nf1')
{'natural': [8], 'success': '0', 'ns': '0', 'nf': '0', 'total': '8', 'roll': '1d20>15ns20nf1', 'modified': [8]}
```

So technically you could do this (the f token is to count fails)

```
 dice.throw('1d20f')
{'natural': [20], 'success': '1', 'fail': '0', 'total': '20', 'roll': '1d20f', 'modified': [20]}

dice.throw('1d20f')
{'natural': [1], 'success': '0', 'fail': '1', 'total': '1', 'roll': '1d20f', 'modified': [1]}
```

---

### ROLL MODIFIERS

Roll modifiers are complicated in that they stack. You must at least have exploding. Then you can
optionally add compounding, penetrating, or both. Highest face
is assumed unless otherwise provided. You may provide a comparator for advanced usage. Note that
dice boost modifiers are applied BEFORE additional modifiers.

#### Exploding Dice xN

Exploding dice roll an additional die when the comparator, on that die, is rolled.

```
 dice.throw('10d6x>=5')
{'natural': [1, 1, 1, 2, 5, 5, 1, 6, 4, 3], 'roll': '10d6x>=5', 'modified': [1, 1, 1, 2, 5, 4, 5, 1, 1, 6, 6, 2, 4, 3], 'success': '2', 'total': '42'}
```

This would explode any dice equal or greater than 5 in our roll.

With subroll threshold:

```
dice.throw('10d6x=1d6')
# 1d6 rolls 4, so explode on 4
```

A subroll that can make every face explode (`x>=1d3` when it rolls 1) or match every reroll
(`r<=1d6` when it rolls 6) is rejected for that throw, and `exact()` rejects the expression.

#### Compounding Dice xxN

Sometimes, you may want the exploded dice rolls to be added together under the same, original roll.
This can lead to large singular dice rolls.

```
dice.throw('10d6xx>=5')
{'natural': [5, 2, 2, 4, 5, 4, 5, 2, 4, 2], 'roll': '10d6xx>=5', 'modified': [7, 2, 2, 4, 7, 4, 8, 2, 4, 2], 'success': '0', 'total': '42'}
```

#### Penetrating Dice xpN/xxpN

Simply put, any exploded dice are recorded as one less (after exploding if applicable)

```
dice.throw('10d6xp>=5')
{'natural': [2, 5, 2, 1, 4, 4, 6, 2, 4, 6], 'roll': '10d6xp>=5', 'modified': [2, 5, 5, 1, 2, 1, 4, 4, 6, 2, 2, 4, 6, 5, 4, 5, 1], 'success': '2', 'total': '59'}
```

Note you can occasionally get dice with a value of 0 here.

---

### ADDITIONAL ROLL MODIFIERS

Some systems may let you reroll those failures. Same as before, defaults to lowest with no input, can
use comparators and numbers for more advanced usage.

#### Reroll rN

If the dice matches, reroll. Defaults to lowest. Rerolls until it no longer matches.

```
dice.throw('10d6r<3')
{'natural': [1, 1, 4, 2, 4, 5, 2, 1, 5, 2], 'roll': '10d6r<3', 'modified': [3, 5, 4, 5, 4, 5, 6, 3, 5, 6], 'success': '2', 'total': '46'}
```

With subroll threshold:

```
dice.throw('10d6r<=1d2')
# 1d2 rolls 2, so reroll any dice <= 2
```

#### Reroll Once roN

If the dice matches, reroll. Defaults to lowest. Reroll only once.

```
dice.throw('10d6ro<3')
{'natural': [6, 2, 5, 1, 1, 6, 3, 1, 2, 5], 'roll': '10d6ro<3', 'modified': [6, 3, 5, 1, 3, 6, 3, 6, 6, 5], 'success': '4', 'total': '44'}
```

Note the 1, bad luck there...

---

### RESULT POOL MODIFIERS

You didn't want all those results anyways. Keep or drop dice of any amount specified. Note the
system will keep dice first, then drop (if you do both for some reason)

#### Keep and Drop khN/klN/dhN/dlN

Simple, keep high, keep low, drop high, drop low, of the specified number. Easy.

```
dice.throw('10d6kh5')
{'natural': [2, 5, 3, 1, 6, 3, 4, 2, 5, 3], 'roll': '10d6kh5', 'modified': [6, 5, 5, 4, 3], 'success': '1', 'total': '23'}
```

Can't believe a 3 made it there...

```
dice.throw('10d6kl5')
{'natural': [5, 3, 6, 5, 1, 4, 5, 2, 6, 2], 'roll': '10d6kl5', 'modified': [1, 2, 2, 3, 4], 'success': '0', 'total': '12'}
```

With subroll count (keep a random number of dice):

```
dice.throw('10d6kh1d4')
# 1d4 rolls 3, so keep highest 3
```

---

### TOTAL MODIFIER

Add a bonus to the final total (not individual dice). Use `=+N` or `=-N` syntax.

```
dice.throw('5d10=+5')
{'natural': [3, 7, 2, 8, 4], 'roll': '5d10=+5', 'modified': [3, 7, 2, 8, 4], 'total': '29', 'success': '1'}
```

The dice stay unchanged; only the total is modified (24 + 5 = 29).

#### Combining Per-Die and Total Modifiers

You can use both in the same roll:

```
dice.throw('2d6+2=+5')
{'natural': [3, 4], 'roll': '2d6+2=+5', 'modified': [5, 6], 'total': '16', 'success': '0'}
```

Each die gets +2 (modified: 5, 6), then +5 to total (11 + 5 = 16).

#### Chained Total Modifiers

You can chain multiple total modifiers:

```
dice.throw('3d6=+10=-3')
{'natural': [4, 3, 5], 'roll': '3d6=+10=-3', 'modified': [4, 3, 5], 'total': '19', 'success': '0'}
```

The modifiers accumulate: +10 - 3 = +7, so 12 + 7 = 19.

#### Subrolls in Total Modifiers

Use dice expressions instead of static numbers:

```
dice.throw('3d6=+1d4=-1d2')
# 1d4 rolls 3, 1d2 rolls 1
{'natural': [4, 3, 5], 'roll': '3d6=+1d4=-1d2', 'modified': [4, 3, 5], 'total': '14', 'success': '0'}
```

---

### TOTAL CHECK

Check if the final total meets a condition. Use `t` followed by a comparator and target value.
Returns `pass: '1'` if the condition is met, `pass: '0'` otherwise.

```
dice.throw('2d10t>=15')
{'natural': [8, 9], 'roll': '2d10t>=15', 'modified': [8, 9], 'total': '17', 'success': '0', 'pass': '1'}
```

The total (17) is >= 15, so pass is '1'.

#### Combining with Total Modifier

Total check evaluates after total modifiers are applied:

```
dice.throw('2d6=+5t>=15')
{'natural': [4, 5], 'roll': '2d6=+5t>=15', 'modified': [4, 5], 'total': '14', 'success': '0', 'pass': '0'}
```

Each die stays natural, +5 to total (9 + 5 = 14), then check if 14 >= 15 (fails).

#### Other Comparators

```
dice.throw('2d6t=7')    # Exact match - pass if total equals 7
dice.throw('2d6t>10')   # Greater than - pass if total > 10
dice.throw('2d6t<=5')   # Less than or equal - pass if total <= 5
```

#### Combining with Success Counting

Use success counting and total check together to answer "how many hits?" and "did I beat the DC?" in one roll:

```
dice.throw('5d10>=8t>=25')
{'natural': [6, 4, 10, 8, 8], 'roll': '5d10>=8t>=25', 'modified': [6, 4, 10, 8, 8], 'total': '36', 'success': '3', 'pass': '1'}
```

- `>=8` counts successes (3 dice rolled 8 or higher)
- `t>=25` checks if total meets target (36 >= 25, passes)

#### Full Combined Example

All modifiers can work together:

```
dice.throw('5d10+2>=10t>=40')
{'natural': [7, 9, 3, 8, 6], 'roll': '5d10+2>=10t>=40', 'modified': [9, 11, 5, 10, 8], 'total': '43', 'success': '2', 'pass': '1'}
```

- `+2` adds 2 to each die
- `>=10` counts modified dice >= 10 (2 successes)
- `t>=40` checks if total >= 40 (43 >= 40, passes)

---

### Conclusion

Once you get the main dice roll down ```2d5``` you can add on the tokens above for some very
expressive (and meaningless) dice rolls. The trailing `+4` below is a term of its own and adds 4 to the total.

```
dice.throw('10d6+0>=5f<=2xxp>=5ro=1dl5+4')
{'natural': [1, 3, 1, 2, 3, 4, 5, 5, 3, 1], 'success': '3', 'fail': '0', 'total': '51', 'roll': '10d6+0>=5f<=2xxp>=5ro=1dl5+4', 'modified': [20, 11, 8, 4, 4]}
```
