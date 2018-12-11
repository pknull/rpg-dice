# rpg-dice
A simple RPG dice roller

## More about our classes
TBCL

## Explain the roll format
The dice roller can perform several different types of rolls based on the roll tokens. A quick summary
is as follows (spaces for readablity only).

This is our core roll.
```
          N   d   N   (+|-)N   cmpN   McmpN   (+|-)N
         ─┬─ ─┬─ ─┬─ ─┬────── ─┬──── ─┬───── ─┬──────
# of Dice ┘   │   │   │        │      │       │
Place Holder ─┘   │   │        │      │       │
Number of Sides ──┘   │        │      │       │
Dice Modifier ────────┘        │      │       │
Success Handler ───────────────┘      │       │
Modifier(s) Such as exploding. ───────┘       │
Roll Modifier ────────────────────────────────┘
```

The above order is specific, and important. Not following the above format can lead to failure
 executing your roll and no one likes failures. That said, modifier may be placed in any order 
 as they are parsed seperately from the rest of the roll.
 
 Code wise, you'll just need to import the dice roller module, create an instance of the class
 and wham-o, you can start rolling dice!
 
 ```
from dice_roller.DiceThrower import DiceThrower
dice = DiceThrower()
dice.throw('10d6')
{'natural': [5, 4, 5, 1, 3, 1, 2, 6, 4, 6], 'roll': '10d6', 'modified': [5, 4, 5, 1, 3, 1, 2, 6, 4, 6], 'success': '2', 'total': '37'}
```

### I need examples and more explanation please.
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

##### The first integer is the number of dice to roll (required)

```
10
```

##### Sides, or fudge dN (required)
The second segment is the number of sides, with the token of dN

```
d6
```

This would constitute a 6 sided dice. You can also replace the number with a **UPPERCASE** F for fudge 
dice. Note any additional modifiers are ignored.

```
10dF
```

---

### BOOST
Sometimes you may want to modify the DICE value. You can do this by adding a modifier and value
after the sides.

```
dice.throw('2d6+4')
{'natural': [4, 2], 'roll': '2d6+4', 'modified': [8, 6], 'success': '1', 'total': '14'}
```

---

### COUNTERS
The following two methods allow us to provide rules for counting successes and failures. Successes are
automatically assumed to be the highest face. You can adjust it by providing another number. Failures
can just be flagged with a default counter of the lowest face. You can also provide comparators for
advanced counters.

##### Successes N
To count successes instead of totals, add a comparator after the sides and any boost modifiers.

```
dice.throw('10d6>=5')
{'natural': [6, 1, 3, 1, 2, 4, 2, 6, 5, 2], 'roll': '10d6>=5', 'modified': [6, 1, 3, 1, 2, 4, 2, 6, 5, 2], 'success': '3', 'total': '32'}

dice.throw('2d6+4>5')
{'natural': [3, 6], 'roll': '2d6+4>5', 'modified': [7, 10], 'success': '2', 'total': '17'}
```

##### Failures fN
To count failures, use the fN token with a comparator or just the side

```
dice.throw('10d6f<2')
{'natural': [5, 5, 4, 3, 2, 3, 4, 6, 6, 4], 'success': '2', 'fail': '0', 'total': '42', 'roll': '10d6f<2', 'modified': [5, 5, 4, 3, 2, 3, 4, 6, 6, 4]}
```


##### Naturals nsN/nsF
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
is assumed unless otherwise provided.  You may provide a comparator for advanced usage. Note that 
dice boost modifiers are applied BEFORE additional modifiers.

##### Exploding Dice xN
Exploding dice roll an additional die when the comparator, on that die, is rolled.

```
 dice.throw('10d6x>=5')
{'natural': [1, 1, 1, 2, 5, 5, 1, 6, 4, 3], 'roll': '10d6x>=5', 'modified': [1, 1, 1, 2, 5, 4, 5, 1, 1, 6, 6, 2, 4, 3], 'success': '2', 'total': '42'}
```

This would explode any dice equal or greater than 5 in our roll.

##### Compounding Dice xxN
Sometimes, you may want the exploded dice rolls to be added together under the same, original roll. 
This can lead to large singular dice rolls.

```
dice.throw('10d6xx>=5')
{'natural': [5, 2, 2, 4, 5, 4, 5, 2, 4, 2], 'roll': '10d6xx>=5', 'modified': [7, 2, 2, 4, 7, 4, 8, 2, 4, 2], 'success': '0', 'total': '42'}
```

##### Penetrating Dice xpN/xxpN
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

##### Reroll rN
If the dice matches, reroll. Defaults to lowest. Rerolls until it no longer matches.

```
dice.throw('10d6r<3')
{'natural': [1, 1, 4, 2, 4, 5, 2, 1, 5, 2], 'roll': '10d6r<3', 'modified': [3, 5, 4, 5, 4, 5, 6, 3, 5, 6], 'success': '2', 'total': '46'}
```

##### Reroll Once roN
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

##### Keep and Drop khN/klN/dhN/dlN
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

---

### Result Pool Boost (aka the laziest thing ever)
You may want to adjust the total based on bonuses. This can be achieved by using the same format 
as the dice boost at the end (again) as a total boost. This doesn't effect the roll itself, just
the total. Note you'll need to add a place holder for the dice modifier though as punishment for 
your (and mine) laziness. As an apology you can also use this with fudge sides.

```
 dice.throw('2d6+0+2')
{'natural': [1, 2], 'roll': '2d6+0+2', 'modified': [1, 2], 'success': '0', 'total': '5'}

dice.throw('2dF+0+2')
{'natural': [1, 0], 'roll': '2dF+0+2', 'modified': [1, 0], 'total': '3'}
```

---
### Conclusion
Once you get the main dice roll down ```2d5``` you can add on the tokens above for some very
expressive (and meaningless) dice rolls.

```
dice.throw('10d6+0>=5f<=2xxp>=5ro=1dl5+4')
{'natural': [1, 3, 1, 2, 3, 4, 5, 5, 3, 1], 'success': '3', 'fail': '0', 'total': '51', 'roll': '10d6+0>=5f<=2xxp>=5ro=1dl5+4', 'modified': [20, 11, 8, 4, 4]}
```
