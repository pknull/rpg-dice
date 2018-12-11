from dice_roller.Die import Die
import sympy


class DiceRoller(object):

    def __init__(self):
        return

    def roll(self, methods):
        sides = methods['sides']
        number_of_dice = methods['number_of_dice']

        roll = self.roll_die(number_of_dice, sides, methods)
        roll_mod = self.dropper_keeper(roll, methods)
        return roll_mod

    def roll_die(self, number, sides, methods={}):
        dice = {'natural': [], 'modified': []}
        full_roll = []
        die = Die(sides)

        for i in range(0, int(number)):
            die.roll()
            roll = nroll = die.showing

            # reroll
            if 'r' in methods:
                if sympy.sympify(str(roll) + methods['r']['operator'] + methods['r']['val']):
                    while sympy.sympify(str(roll) + methods['r']['operator'] + methods['r']['val']):
                        die.roll()
                        roll = die.showing
                        if methods['r']['once']:
                            break

            # boost
            if 'b' in methods:
                roll = sympy.sympify(
                    str(roll) + methods['b']['operator'] + methods['b']['val'])

            # explode
            if 'x' in methods:
                if sympy.sympify(str(roll) + methods['x']['operator'] + methods['x']['val']):
                    try:
                        explode = self.roll_die(1, sides, methods)
                    except RuntimeError:
                        raise Exception('The dice have exploded out of control ruining everything')
                    if methods['x']['penetrate']:
                        explode['modified'][0] -= 1

                    if methods['x']['compound']:
                        roll += explode['modified'][0]
                    else:
                        full_roll.append(roll)
                        full_roll.extend(explode['modified'])

            if full_roll:
                dice['modified'].extend(full_roll)
                del full_roll[:]
                full_roll = []
            else:
                dice['modified'].append(roll)
                roll = None

            dice['natural'].append(nroll)

        return dice

    def dropper_keeper(self, roll_result, methods):
        rolls = roll_result['modified']

        # first we keep
        if 'k' in methods:
            if methods['k']['layer'] == 'low':
                reverse = False
            else:
                reverse = True
            top_rolls = sorted(rolls, reverse=reverse)[:int(methods['k']['val'])]
            del rolls[:]
            rolls = top_rolls

        if 'd' in methods:
            if methods['d']['layer'] == 'high':
                reverse = False
            else:
                reverse = True
            keep = len(rolls) - int(methods['d']['val'])
            if keep <= 0:
                rolls = []
            else:
                top_rolls = sorted(rolls, reverse=reverse)[:keep]
                del rolls[:]
                rolls = top_rolls

        del roll_result['modified']
        roll_result['modified'] = rolls
        return roll_result
