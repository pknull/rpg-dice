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
dice.get_result()
'10d6 [6, 2, 6, 4, 6, 4, 6, 6, 5, 4] t:49 s:5 '
```

### I need examples and more explanation please.
This is a base example roll

```
10d6
```

This is how it would be executed.

```
from dice_roller.DiceRoller import DiceRoller
dice = DiceRoller()
dice.throw('10d6')
dice.get_result()
'10d6 [6, 2, 6, 4, 6, 4, 6, 6, 5, 4] t:49 s:5 '

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

This would constitute a 6 sided dice. You can also replace the number with a **CAPITAL** F for fudge 
dice. Note any additional modifiers are ignored.

```
10dF
```

---

### BOOST
Sometimes you may want to modify the DICE value. You can do this by adding a modifier and value
after the sides.

```
2d6+4 [10, 5] t:15 s:0
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
10d6>=5 [5, 6, 2, 1, 3, 3, 6, 2, 2, 6] t:36 s:4
2d6+4>5 [9, 9] t:18 s:2
```

##### Failures fN
To count failures, use the fN token with a comparator or just the side

```
10d6f<2 [6, 4, 4, 4, 4, 5, 1, 5, 4, 5] t:42 f:1 s:1
```


##### Naturals nsN/nsF
If you'd like to count success and fails before modifiers, you can add ns and nf to your roll. A
typical DnD roll might look like. Do note that successes are automatically tallied for the highest
and lowest values for the dice.

```
1d20>15ns20nf1 ['20'] t:20 s:1 nf:0 ns:1
```


So technically you could do this (the f token is to count fails)

```
1d20f ['20'] t:20 f:0 s:1
1d20f ['1'] t:1 f:1 s:0
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
10d6x>=5 [1, 6, 4, 5, 5, 2, 5, 5, 1, 5, 3, 3, 2, 5, 2, 5, 2, 5, 2] t:68 s:1
```

This would explode any dice equal or greater than 5 in our roll.

##### Compounding Dice xxN
Sometimes, you may want the exploded dice rolls to be added together under the same, original roll. 
This can lead to large singular dice rolls.

```
10d6xx>=5 [1, 1, 1, 4, 2, 26, 8, 1, 1, 4] t:49 s:0 
```

##### Penetrating Dice xpN/xxpN
Simply put, any exploded dice are recorded as one less (after exploding if applicable)

```
10d6xp>=5 [1, 4, 4, 3, 6, 3, 1, 5, 0, 5, 1, 1, 5, 3] t:42 s:1
```

Note you can occasionally get dice with a value of 0 here.

---

### ADDITIONAL ROLL MODIFIERS
Some systems may let you reroll those failures. Same as before, defaults to lowest with no input, can
use comparators and numbers for more advanced usage.

##### Reroll rN
If the dice matches, reroll. Defaults to lowest. Rerolls until it no longer matches.

```
10d6r<3 [4, 5, 3, 5, 3, 6, 4, 4, 3, 5] t:42 s:1 
```

##### Reroll Once roN
If the dice matches, reroll. Defaults to lowest. Reroll only once.

```
10d6ro<3 [5, 3, 6, 4, 4, 2, 3, 4, 5, 6] t:42 s:2
```

Note the 2, bad luck there...

---

### RESULT POOL MODIFIERS
You didn't want all those results anyways. Keep or drop dice of any amount specified. Note the 
system will keep dice first, then drop (if you do both for some reason)

##### Keep and Drop khN/klN/dhN/dlN
Simple, keep high, keep low, drop high, drop low, of the specified number. Easy.

```
10d6kh5 [5, 4, 4, 4, 2] t:19 s:0 
```
Can't believe a 2 made it there...

```
10d6kl5 [1, 2, 2, 3, 3] t:11 s:0
```

---

### Result Pool Boost (aka the laziest thing ever)
You may want to adjust the total based on bonuses. This can be achieved by using the same format 
as the dice boost at the end (again) as a total boost. This doesn't effect the roll itself, just
the total. Note you'll need to add a place holder for the dice modifier though as punishment for 
your (and mine) laziness. As an apology you can also use this with fudge sides.

```
2d6+0+2 [4, 6] t:12 s:1 
2dF+0+2 [0, 1] t:3 
```

---
### Conclusion
Once you get the main dice roll down ```2d5``` you can add on the tokens above for some very
expressive (and meaningless) dice rolls.

```
10d6+0>=5f<=2xxp>=5ro=1dl5+4 [6, 3, 4, 2, 4] t:23 f:1 s:1
```
