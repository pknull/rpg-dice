from dice_roller.safe_compare import safe_compare, safe_arithmetic


class DiceScorer:

    def __init__(self):
        pass

    def get_roll_total(self, result, parsed_roll):

        if parsed_roll['types'] != "int":
            return 0

        # An empty pool still takes the total modifier: 0d6=+5 totals 5.
        if not result or isinstance(result[0], str):
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

    def score_expression(self, dexp, natural, modified, total, rules, check, binding):
        """Roll result for a whole expression (groups, sums, arithmetic).

        ``natural`` and ``modified`` are (face, leaf) entries; each die is
        counted with its own leaf's rule, after any group override.  Keys and
        their order match get_result for a single dice term.
        """
        rep = {'roll': dexp,
               'natural': [face for face, _leaf in natural],
               'modified': [value for value, _leaf in modified],
               'total': str(total)}

        def count(entries, field):
            hits = 0
            for value, leaf in entries:
                rule = rules.bound_rule(leaf, field, binding)
                if rule is not None and safe_compare(value, *rule):
                    hits += 1
            return str(hits)

        if rules.defined['success']:
            rep['success'] = count(modified, 'success')
        if rules.defined['fail']:
            rep['fail'] = count(modified, 'fail')
        if rules.defined['nf']:
            rep['nf'] = count(natural, 'nf')
        if rules.defined['ns']:
            rep['ns'] = count(natural, 'ns')
        if check is not None:
            passed = safe_compare(total, check[0], check[1])
            rep['pass'] = '1' if passed else '0'
        return rep
