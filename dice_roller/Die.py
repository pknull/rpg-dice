import random


class Die:

    def __init__(self, sides):
        self.sides = sides
        self.showing = 0
        self.roll()

    def roll(self):
        if isinstance(self.sides, list):
            roll = random.choice(self.sides)
        elif isinstance(self.sides, int):
            roll = int(random.randint(1, int(self.sides)))
        else:
            roll = 0
        self.showing = roll
