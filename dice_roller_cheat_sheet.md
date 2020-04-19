# Dice Roller Cheat Sheet

Layout of this cheat sheet:

```
<Syntax>
<example>
n = dice count
y = dice size
```

## Basic Roll

```
ndy
10d6
```

## Boost Dice Roll Values

```
ndy+c
10d6+4
```

## Boost Dice Roll Ending Total

```
ndy+0+c
2d6+0+2
```

## Exploding Dice

```
ndyx[>,<,>=,<=,==]c
10d6x>=5
```

## Count Successes

```
ndy[>,<,>=,<=,==]c
10d6>=5
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

## Compounding Dice

Similar to the exploding dice

```
ndyxx[>,<,>=,<=,==]c
10d6xx>=5
```

## Penetrating Dice

Any exploded dice are recorded as one less (after exploding if applicable)

```
ndyxp[>,<,>=,<=,==]c
10d6xp>=5
```

## Syntax Structure

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

