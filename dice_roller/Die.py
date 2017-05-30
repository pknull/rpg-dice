import random

class Die(object):
    sides = 0

    def __init__(self, sides):
        self.sides = sides

    def roll(self):
        if self.sides == 'f':
            roll = int(random.randint(-1, 1))
        elif int(self.sides) < 1:
            roll = 0
        else:
            roll = int(random.randint(1, int(self.sides)))
        return roll
