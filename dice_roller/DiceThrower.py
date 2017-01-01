from dice_roller.DiceParser import DiceParser
from dice_roller.DiceRoller import DiceRoller
from dice_roller.NumericStringParser import NumericStringParser
import sympy


class DiceThrower(object):
    result = []

    def __init__(self):
        return

    def throw(self, dexp='1d1'):
        parser = DiceParser()
        roller = DiceRoller()
        # parse
        parsed_roll = parser.parse_input(dexp)
        # roll dice
        result = roller.roll(parsed_roll)
        self.result = result
        return self.get_result(dexp, result, parsed_roll)

    def throw_string(self, deq):
        mathp = NumericStringParser()
        evaluated = mathp.eval(deq)
        return evaluated

    def throw_parsed(self, parsed):
        roller = DiceRoller()
        return roller.roll_die(parsed)

    def get_roll_total(self, result, parsed_roll):
        if not result:
            return False
        else:
            core = sum(int(i) for i in result)
            if 'l' in parsed_roll:
                mod_core = sympy.sympify(str(core) + parsed_roll['l']['operator'] + parsed_roll['l']['val'])
            else:
                mod_core = core
            return mod_core

    def get_count(self, result, type, parsed_roll):
        if not result:
            return False
        else:
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

if __name__ == '__main__':
    print('make this a standalone tool')
