# rpg-dice
A simple RPG dice roller


## How do I use it?
The dice roller can perform several different types of rolls based on the roll tokens

Lets use this as the base of our examples

```
10d6
```

We will be running the following and pasting the result with the example.

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

##### Sides, or FATE dN (required)
The second segment is the number of sides, with the token of dN

```
d6
```

This would constitute a 6 sided dice. You can also replace the number with a **CAPITAL** F for FATE 
dice. Note any additional modifiers are ignored.

```
10dF [0, 0, 0, 0, -1, 1, -1, -1, -1, 0] t:-3 
```

---

### COUNTERS
The following two methods allow us to provide rules for counting successes and failures. Successes are
automatically assumed to be the highest face. You can adjust it by providing another number. Failures
can just be flagged with a default counter of the lowest face. You can also provide comparators for
advanced counters.

##### Successes N
To count successes instead of totals, add a comparator after the sides.

```
10d6>=5 [5, 6, 2, 1, 3, 3, 6, 2, 2, 6] t:36 s:4
```

##### Failures fN
To count failures, use the fN token with a comparator or just the side

```
10d6f<2 [6, 4, 4, 4, 4, 5, 1, 5, 4, 5] t:42 f:1 s:1
```

---

### ROLL MODIFIERS
Roll modifiers are complicated in that they stack. You must at least have exploding. Then you can 
optionally add compounding, exploding, or both. In the example above we've added both. Highest face
is assumed unless otherwise provided.  You may provide a comparator for advanced usage.

##### Exploding Dice xN
Exploding dice roll an additional die if the maximum, on that die, is rolled.

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

### Conclusion
Once you get the main dice roll down, such as

```
2d5
``` 

you can add on the tokens above for some very
expressive dice rolls.

```
10d6>=5f<=2xxp>=5ro=1dl5 [4, 4, 4, 7, 2] t:21 f:1 s:1
```
