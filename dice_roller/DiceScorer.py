from dice_roller.safe_compare import safe_compare, safe_arithmetic


class DiceScorer:

    def __init__(self):
        pass

    def get_roll_total(self, result, parsed_roll):

        if parsed_roll['types'] != "int" or len(result) == 0:
            return 0

        if isinstance(result[0], str):
            core = 0
        else:
            core = sum(int(i) for i in result)

        if 'l' in parsed_roll:
            mod_core = safe_arithmetic(core, parsed_roll['l']['operator'], parsed_roll['l']['val'])
        else:
            mod_core = core

        return mod_core

    def get_count(self, result, type, parsed_roll):
        counter = 0
        if type in parsed_roll:
            for i in result:
                if safe_compare(i, parsed_roll[type]['operator'], parsed_roll[type]['val']):
                    counter += 1
        return counter

    def get_result(self, dexp, result, parsed_roll):

        rep = {}
        rep.update({'roll': dexp})
        rep.update(result)
        total = self.get_roll_total(result['modified'], parsed_roll)
        rep.update({'total': str(total)})

        if parsed_roll['types'] == "int":
            rep.update({'success': str(self.get_count(result['modified'], 's', parsed_roll))})
            if 'f' in parsed_roll:
                rep.update({'fail': str(self.get_count(result['modified'], 'f', parsed_roll))})
            if 'nf' in parsed_roll:
                rep.update({'nf': str(self.get_count(result['natural'], 'nf', parsed_roll))})
            if 'ns' in parsed_roll:
                rep.update({'ns': str(self.get_count(result['natural'], 'ns', parsed_roll))})
            if 't' in parsed_roll:
                passed = safe_compare(total, parsed_roll['t']['operator'], parsed_roll['t']['val'])
                rep.update({'pass': '1' if passed else '0'})
        return rep
