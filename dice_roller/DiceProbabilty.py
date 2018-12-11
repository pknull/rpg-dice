from fractions import Fraction
from decimal import Decimal
from collections import Counter
import itertools as it
from dice_roller.DiceParser import DiceParser
import sympy

class DiceProbability(object):
    parser = DiceParser()

    def throw(self, dexp='1d1', target=4):
        # parse
        parsed_roll = self.parser.parse_input(dexp)
        numberOfDice = int(parsed_roll['number_of_dice'])
        numberOfSides = int(parsed_roll['sides'])

        s_op = parsed_roll['s']['operator']
        s_val = parsed_roll['s']['val']
        f_op = parsed_roll['f']['operator']
        f_val = parsed_roll['f']['val']

        dice = Counter(range(1, numberOfSides + 1))
        possibilities = list(it.product(dice, repeat=numberOfDice))
        total_possibilities = numberOfSides**numberOfDice

        success_set = self.calc(s_op, s_val, dice)
        fail_set = self.calc(f_op, f_val, dice)

        print(parsed_roll)

        targetAmount = target
        totalSuccess = 0
        totalFails = 0
        totalCritFails = 0

        for i in possibilities:
            successes = 0
            fails = 0
            totals = Counter(i)
            for j in success_set:
                successes += totals[j]
            for j in fail_set:
                fails += totals[j]

            if fails > (numberOfDice/2):
                totalCritFails += 1
            elif successes >= targetAmount:
                totalSuccess += 1
            else:
                totalFails += 1

        win = Fraction(totalSuccess, total_possibilities)
        fail = Fraction(totalFails, total_possibilities)
        crits = Fraction(totalCritFails, total_possibilities)

        finalCount = sum([totalSuccess,totalFails,totalCritFails])
        print('---- Counts')
        print(total_possibilities)
        print(finalCount)
        print('---- Win')
        print(success_set)
        print(totalSuccess)
        print('{0:.2f}'.format(win.numerator / Decimal(win.denominator) * 100))
        print('---- Fail')
        print(fail_set)
        print(totalFails)
        print('{0:.2f}'.format(fail.numerator / Decimal(fail.denominator) * 100))
        print('---- Die')
        print(totalCritFails)
        print('{0:.2f}'.format(crits.numerator / Decimal(crits.denominator) * 100))


    def calc(self, op, val, space):
        """Subset of sample space for which a condition is true."""
        return {element for element in space if sympy.sympify(str(element) + op + val)}

