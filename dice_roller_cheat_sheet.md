# Dice Roller Cheat Sheet

Layout of this cheat sheet:

```
<Syntax>
<example>
n = dice count
y = dice size
c = constant OR dice expression (subroll)
```

**Subrolls:** Anywhere you see `c`, you can use a dice expression like `1d4` instead of a number.

## Basic Roll

```
ndy
10d6
```

## Boost Dice Roll Values (Per-Die)

```
ndy+c
10d6+4
```

## Boost Dice Roll Total

```
ndy=+c
ndy=-c
ndy=+c=-c      (chainable)
2d6=+5
3d6=+10=-3
1d20=+1d4      (with subroll)
3d6=+1d4=-1d2  (chained subrolls)
```

## Exploding Dice

```
ndyx[>,<,>=,<=,==]c
10d6x>=5
10d6x>=1d3     (subroll threshold)
```

## Count Successes

```
ndy[>,<,>=,<=,==]c
10d6>=5
10d6>=1d4      (subroll threshold)
```

## Count Unmodified Successes

This will count the amount of times number `c` shows up in a roll and consider it a natural success.

```
ndynsc
10d6ns3
```

## Count Failures

```
ndyf[>,<,>=,<=,==]c
10d6f<3
10d6f<=1d2     (subroll threshold)
```

## Count Unmodified Failures

This will count the amount of times number `c` shows up in a roll and consider it a natural failures.

```
ndynfc
10d6nf3
```

## Keep and Drop

Keep High

```
ndykhc
10d6kh5
10d6kh1d4      (subroll count)
```

Keep Low

```
ndyklc
10d6kl5
```

Drop High

```
ndydhc
10d6dh5
```

Drop low

```
ndydlc
10d6dl5
```

## Reroll

```
ndyr[>,<,>=,<=,==]c
10d6r<=2
10d6r<=1d2     (subroll threshold)
10d6ro<=2      (reroll once)
```

## Compounding Dice

Similar to the exploding dice

```
ndyxx[>,<,>=,<=,==]c
10d6xx>=5
10d6xx>=1d3    (subroll threshold)
```

## Penetrating Dice

Any exploded dice are recorded as one less (after exploding if applicable)

```
ndyxp[>,<,>=,<=,==]c
10d6xp>=5
```

## Total Check

Check if total meets a target (returns pass: '1' or '0')

```
ndyt[>,<,>=,<=,==]c
2d6t>=7
1d20=+1d4t>=15   (with subroll modifier)
```

## Syntax Structure

```
          N   d   N   (+|-)N   (=+|=-)N...   cmpN   McmpN   t cmpN
         ─┬─ ─┬─ ─┬─ ─┬────── ─┬──────────── ─┬──── ─┬───── ─┬─────
# of Dice ┘   │   │   │        │              │      │       │
Place Holder ─┘   │   │        │              │      │       │
Number of Sides ──┘   │        │              │      │       │
Per-Die Modifier ─────┘        │              │      │       │
Total Modifier (chainable) ────┘              │      │       │
Success Handler ──────────────────────────────┘      │       │
Method Modifiers (x, kh, r, f, etc.) ────────────────┘       │
Total Check ─────────────────────────────────────────────────┘
```

Any `N` value in modifiers can be a dice expression (subroll) like `1d4`.

