
import sympy

class DiceScorer(object):

    def __init__(self):
        return

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
        rep = {}
        rep.update({'roll':dexp})
        rep.update(result)
        rep.update({'total': str(self.get_roll_total(result['modified'], parsed_roll))})

        if parsed_roll['sides'] is not 'F':
            if 'f' in parsed_roll:
                rep.update({'fail': str(self.get_count(result['modified'], 'f', parsed_roll))})
            rep.update({'success': str(self.get_count(result['modified'], 's', parsed_roll))})
            if 'nf' in parsed_roll:
                rep.update({'nf': str(self.get_count(result['natural'], 'nf', parsed_roll))})
            if 'ns' in parsed_roll:
                rep.update({'ns': str(self.get_count(result['natural'], 'ns', parsed_roll))})
        return rep
