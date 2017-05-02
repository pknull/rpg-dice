from __future__ import division

from dice_roller.DiceParser import DiceParser
from dice_roller.DiceRoller import DiceRoller
from dice_roller.DiceScorer import DiceScorer

import sympy


class DiceThrower(object):
    parser = DiceParser()
    roller = DiceRoller()
    scorer = DiceScorer()
    result = []

    def __init__(self):
        return

    def throw(self, dexp='1d1'):

        # parse
        parsed_roll = self.parser.parse_input(dexp)

        # roll dice
        if parsed_roll == False:
            return 'No result, unable to parse'
        else :
            result = self.roller.roll(parsed_roll)

        score = self.scorer.get_result(dexp, result, parsed_roll)

        return score

    def throw_string(self, deq):

        parsed_equation = self.parser.parse_expression_from_equation(deq)
        mod_deq = deq
        for roll in parsed_equation:
            result = self.roller.roll(parsed_equation[roll][0])
            parsed_equation[roll].append(result)

            total = self.scorer.get_roll_total(result['modified'], parsed_equation[roll][0])
            mod_deq = mod_deq.replace(roll, str(total))
            print(mod_deq)

        full_result = sympy.sympify(mod_deq)
        return full_result, parsed_equation



