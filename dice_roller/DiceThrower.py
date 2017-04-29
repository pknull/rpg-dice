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

        # apply template
        if ":" in dexp:
            template, value = dexp.split(":", 1)
            dexp = self.apply_template(template,value)

        # get output format
        if "|" in dexp:
            dexp, result_template = dexp.split("|", 1)

        # parse
        parsed_roll = self.parser.parse_input(dexp)

        # roll dice
        if parsed_roll == False:
            return 'No result, unable to parse'
        else :
            result = self.roller.roll(parsed_roll)

        score = self.scorer.get_result(dexp, result, parsed_roll)

        print(str(score))

        if(len(result_template) > 0):
            final_result = result_template.format(s=score)
        else :
            final_result = score

        return final_result

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

    def apply_template(self, template, value=''):
        return {
            'SR': value + 'd6>=5f=1|{s[modified]} {s[success]} successes {s[fail]} fail',
            'F': '4d3-2' + value + '|{s[total]}',
            'W': '2d6+0' + value + '|{s[total]}'
        }.get(template, False)


