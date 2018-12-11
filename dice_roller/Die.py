import random

class Die(object):
    sides = 0
    showing = 0

    def __init__(self, sides):
        self.sides = sides
        self.roll()

    def roll(self):
        if self.sides == 'F':
            possibilities = [-1, -1, 0, 0, 1, 1]
            roll = random.choice(possibilities)
        elif self.sides == 'P':
            possibilities = ['Pink'] * 35 + ['Dot'] * 30 + ['Razorback'] * 20 + ['Trotter'] * 10 + ['Snouter'] * 4 + ['Leaning Jowler']
            roll = random.choice(possibilities)
        elif int(self.sides) < 1:
            roll = 0
        else:
            roll = int(random.randint(1, int(self.sides)))
        self.showing = roll
