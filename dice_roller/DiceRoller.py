import random
import sympy


class DiceRoller(object):
    # an array of results
    result = []

    def __init__(self):
        return

    def roll(self, methods):
        print(methods)

        sides = methods['sides']
        number_of_dice = methods['number_of_dice']

        roll = self.roll_die(number_of_dice, sides, methods)
        roll_mod = self.dropper_keeper(roll, methods)
        return roll_mod

    def roll_die(self, number, sides, methods={}):
        dice = {'natural': [], 'modified': []}
        full_roll = []

        for i in range(0, int(number)):
            nroll = self.core_roller(sides)
            if 'b' in methods:
                roll = sympy.sympify(str(nroll) + methods['b']['operator'] + methods['b']['val'])
            else:
                roll = nroll

            # reroll
            if 'r' in methods:
                if sympy.sympify(str(roll) + methods['r']['operator'] + methods['r']['val']):
                    while sympy.sympify(str(roll) + methods['r']['operator'] + methods['r']['val']):
                        if 'b' in methods:
                            roll = sympy.sympify(
                                str(self.core_roller(sides)) + methods['b']['operator'] + methods['b']['val'])
                        else:
                            roll = self.core_roller(sides)
                        if methods['r']['once']:
                            break

            # explode
            if 'x' in methods:
                if sympy.sympify(str(roll) + methods['x']['operator'] + methods['x']['val']):
                    try:
                        explode = self.roll_die(1, sides, methods)
                    except RuntimeError:
                        raise Exception('The dice have exploded out of control ruining everything')
                    if methods['x']['penetrate']:
                        explode[0] -= 1

                    if methods['x']['compound']:
                        roll += explode[0]
                    else:
                        full_roll.append(roll)
                        full_roll.extend(explode['modified'])

            if full_roll:
                dice['modified'].extend(full_roll)
                del full_roll[:]
                full_roll = []
            else:
                dice['modified'].extend([roll])

            dice['natural'].append(nroll)

        return dice

    def core_roller(self, sides):
        if sides == 'F':
            roll = int(random.randint(-1, 1))
        elif int(sides) < 1:
            roll = 0
        else:
            roll = int(random.randint(1, int(sides)))
        return roll

    def dropper_keeper(self, roll_result, methods):
        rolls = roll_result
        # first we keep
        if 'k' in methods:
            if methods['k']['layer'] == 'low':
                reverse = False
            else:
                reverse = True
            top_rolls = sorted(rolls, reverse=reverse)[:int(methods['k']['val'])]
            del rolls[:]
            rolls = top_rolls

        # then we drop
        if 'd' in methods:
            for i in range(0, int(methods['d']['val'])):
                if methods['d']['layer'] == 'high':
                    rolls.remove(min(rolls))
                else:
                    rolls.remove(max(rolls))
        return rolls
