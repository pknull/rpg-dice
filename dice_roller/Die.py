import random

class Die(object):
    sides = 0
    showing = 0

    def __init__(self, sides):
        self.sides = sides
        self.roll()

    def roll(self):
        if self.sides == 'F':
            roll = random.choice([-1, -1, 0, 0, 1, 1])
        elif int(self.sides) < 1:
            roll = 0
        else:
            roll = int(random.randint(1, int(self.sides)))
        self.showing = roll
