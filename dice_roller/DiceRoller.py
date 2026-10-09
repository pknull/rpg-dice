from dice_roller.Die import Die
from dice_roller.DiceException import DiceException
from dice_roller.safe_compare import safe_compare, safe_arithmetic


class DiceRoller:

    def __init__(self):
        pass

    def roll(self, methods):
        sides = methods['sides']
        number_of_dice = methods['number_of_dice']

        roll = self.roll_die(number_of_dice, sides, methods)
        roll_mod = self.dropper_keeper(roll, methods)
        return roll_mod

    def roll_die(self, number, sides, methods=None):
        if methods is None:
            methods = {}
        dice = {'natural': [], 'modified': []}
        full_roll = []
        die = Die(sides)

        for i in range(0, int(number)):
            die.roll()
            roll = nroll = die.showing

            # reroll
            if 'r' in methods:
                if safe_compare(roll, methods['r']['operator'], methods['r']['val']):
                    while safe_compare(roll, methods['r']['operator'], methods['r']['val']):
                        die.roll()
                        roll = die.showing
                        if methods['r']['once']:
                            break

            # boost
            if 'b' in methods:
                roll = safe_arithmetic(roll, methods['b']['operator'], methods['b']['val'])

            # explode
            if 'x' in methods:
                if safe_compare(roll, methods['x']['operator'], methods['x']['val']):
                    try:
                        explode = self.roll_die(1, sides, methods)
                    except RuntimeError:
                        raise DiceException('Unable to perform roll',
                                            'The dice have exploded out of control ruining everything')
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
        keep = drop = None
        if 'k' in methods:
            keep = (methods['k']['layer'], int(methods['k']['val']))
        if 'd' in methods:
            drop = (methods['d']['layer'], int(methods['d']['val']))
        roll_result['modified'] = self.keep_drop(rolls, keep, drop)
        return roll_result

    @staticmethod
    def keep_drop(rolls, keep, drop, key=None):
        """Keep first, then drop, as (layer, count) pairs.

        Sorting is stable, so tied values keep their list order; ``key`` maps
        an entry to its value when entries carry more than the value.
        """
        # first we keep
        if keep is not None:
            layer, count = keep
            rolls = sorted(rolls, key=key, reverse=(layer != 'low'))[:count]

        if drop is not None:
            layer, count = drop
            size = len(rolls) - count
            if size <= 0:
                rolls = []
            else:
                rolls = sorted(rolls, key=key, reverse=(layer != 'high'))[:size]

        return list(rolls)
