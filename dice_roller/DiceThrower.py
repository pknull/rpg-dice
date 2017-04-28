from __future__ import division

from dice_roller.DiceParser import DiceParser
from dice_roller.DiceRoller import DiceRoller
import sympy


class DiceThrower(object):
    parser = DiceParser()
    roller = DiceRoller()
    result = []

    def __init__(self):
        return

    def throw(self, dexp='1d1'):

        # apply template
        if ":" in dexp:
            template, value = dexp.split(":", 1)
            dexp = self.apply_template(template,value)

        # parse
        parsed_roll = self.parser.parse_input(dexp)

        # roll dice
        if parsed_roll == False:
            return 'No result, unable to parse'
        else :
            result = self.roller.roll(parsed_roll)
            self.result = result
            return self.get_result(dexp, result, parsed_roll)

    def throw_string(self, deq):

        parsed_equation = self.parser.parse_expression_from_equation(deq)
        mod_deq = deq
        for roll in parsed_equation:
            result = self.roller.roll(parsed_equation[roll][0])
            parsed_equation[roll].append(result)

            total = self.get_roll_total(result['modified'], parsed_equation[roll][0])
            mod_deq = mod_deq.replace(roll, str(total))
            print(mod_deq)

        full_result = sympy.sympify(mod_deq)
        return full_result, parsed_equation

    def get_roll_total(self, result, parsed_roll):
        core = sum(int(i) for i in result)
        if 'l' in parsed_roll:
            mod_core = sympy.sympify(str(core) + parsed_roll['l']['operator'] + parsed_roll['l']['val'])
        else:
            mod_core = core
        return mod_core

    def get_count(self, result, type, parsed_roll):
        counter = 0
        if type in parsed_roll:
            for i in result:
                if sympy.sympify(str(i) + parsed_roll[type]['operator'] + parsed_roll[type]['val']):
                    counter += 1
        return counter

    def get_result(self, dexp, result, parsed_roll):
        rep = ''
        rep += dexp + ' '
        rep += str(result) + ' '
        rep += 'total:' + str(self.get_roll_total(result['modified'], parsed_roll)) + ' '
        if parsed_roll['sides'] is not 'F':
            if 'f' in parsed_roll:
                rep += 'fail:' + str(self.get_count(result['modified'], 'f', parsed_roll)) + ' '
            rep += 'success:' + str(self.get_count(result['modified'], 's', parsed_roll)) + ' '
            if 'nf' in parsed_roll:
                rep += 'nf:' + str(self.get_count(result['natural'], 'nf', parsed_roll)) + ' '
            if 'ns' in parsed_roll:
                rep += 'ns:' + str(self.get_count(result['natural'], 'ns', parsed_roll))+ ' '
        return rep

    def apply_template(self, template, value=''):
        return {
            'SR': value + 'd6>=5',
            'F': '4d3-2'
        }.get(template, False)
