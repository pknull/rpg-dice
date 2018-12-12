from fractions import Fraction
from decimal import Decimal
from collections import Counter
import itertools as it
from math import factorial
from dice_roller.DiceParser import DiceParser
import sympy


class DiceProbability(object):
    parser = DiceParser()

    def calcThrow(self, dexp='1d1', target=2):
        parsed_roll = self.parser.parse_input(dexp)
        numberOfDice = int(parsed_roll['number_of_dice'])
        numberOfSides = int(parsed_roll['sides'])
        total_possibilities = numberOfSides ** numberOfDice

        s_op = parsed_roll['s']['operator']
        s_val = parsed_roll['s']['val']
        f_op = parsed_roll['f']['operator']
        f_val = parsed_roll['f']['val']

        dice = Counter(range(1, numberOfSides + 1))

        success_set = self.calc(s_op, s_val, dice)
        fail_set = self.calc(f_op, f_val, dice)

        success_probability = Fraction(len(success_set), numberOfSides)
        die_probability = Fraction(len(fail_set), numberOfSides)

        print('---- Counts')
        print(total_possibilities)

        print('---- Win')
        chance = self.hit_chance(numberOfDice, target, success_probability)
        print('{0:.2f}'.format(chance.numerator / Decimal(chance.denominator) * 100))

        print('---- Fail')
        chance = 1 - chance
        print('{0:.2f}'.format(chance.numerator / Decimal(chance.denominator) * 100))

        print('---- Die')
        fail_target = round((numberOfDice / 2) + 1)
        chance = self.hit_chance(numberOfDice, fail_target, die_probability)
        print('{0:.2f}'.format(chance.numerator / Decimal(chance.denominator) * 100))

    def bruteThrow(self, dexp='1d1', target=2):
        # parse
        parsed_roll = self.parser.parse_input(dexp)
        numberOfDice = int(parsed_roll['number_of_dice'])
        numberOfSides = int(parsed_roll['sides'])

        s_op = parsed_roll['s']['operator']
        s_val = parsed_roll['s']['val']
        f_op = parsed_roll['f']['operator']
        f_val = parsed_roll['f']['val']

        dice = Counter(range(1, numberOfSides + 1))
        total_possibilities = numberOfSides ** numberOfDice

        success_set = self.calc(s_op, s_val, dice)
        fail_set = self.calc(f_op, f_val, dice)

        targetAmount = target
        totalSuccess = 0
        totalFails = 0
        totalCritFails = 0
        fail_target = round((numberOfDice / 2) + 1)

        for i in it.product(dice, repeat=numberOfDice):
            successes = 0
            fails = 0
            totals = Counter(i)
            for j in success_set:
                successes += totals[j]
            for j in fail_set:
                fails += totals[j]

            if fails >= fail_target:
                totalFails += 1
                totalCritFails += 1
            elif successes >= targetAmount:
                totalSuccess += 1
            else:
                totalFails += 1

        win = Fraction(totalSuccess, total_possibilities)
        fail = Fraction(totalFails, total_possibilities)
        crits = Fraction(totalCritFails, total_possibilities)

        print('---- Counts')
        print(total_possibilities)
        print('---- Win')
        print('{0:.2f}'.format(win.numerator / Decimal(win.denominator) * 100))
        print('---- Fail')
        print('{0:.2f}'.format(fail.numerator / Decimal(fail.denominator) * 100))
        print('---- Die')
        print('{0:.2f}'.format(crits.numerator / Decimal(crits.denominator) * 100))

    def calc(self, op, val, space):
        """Subset of sample space for which a condition is true."""
        return {element for element in space if sympy.sympify(str(element) + op + val)}

    def binomial(self, x, y):
        try:
            binom = factorial(x) // factorial(y) // factorial(x - y)
        except ValueError:
            binom = 0
        return binom

    def exact_hit_chance(self, n, k, p):
        """Return the probability of exactly k hits from n dice"""
        # a hit is a 5 or 6, so 1/3 chance.
        return self.binomial(n, k) * (p) ** k * (1 - p) ** (n - k)

    def hit_chance(self, n, k, p):
        """Return the probability of at least k hits from n dice"""
        return sum([self.exact_hit_chance(n, x, p) for x in range(k, n + 1)])
