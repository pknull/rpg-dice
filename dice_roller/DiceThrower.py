from fractions import Fraction

from dice_roller import notation
from dice_roller.DiceException import DiceException
from dice_roller.DiceParser import DiceParser, methods_dict, term_key
from dice_roller.DiceRoller import DiceRoller
from dice_roller.DiceScorer import DiceScorer


class DiceThrower:

    def __init__(self):
        self.parser = DiceParser()
        self.roller = DiceRoller()
        self.scorer = DiceScorer()
        self.result = []

    def throw(self, dexp='1d1'):

        # parse, then roll any subrolls once for this throw
        try:
            tree, binding = self._prepare(dexp)
        except DiceException:
            return 'Bad roll expression - ' + dexp

        # roll dice
        terms = {}
        natural, modified, total = self._evaluate(tree, binding, terms)
        self.result = {'natural': [face for face, _leaf in natural],
                       'modified': [value for value, _leaf in modified]}

        # score
        check = None
        if isinstance(tree, (notation.Dice, notation.Group)) and tree.suffix.check is not None:
            check = (tree.suffix.check.operator, notation.bound(tree.suffix.check.value, binding))
        return self.scorer.score_expression(dexp, natural, modified, total,
                                            notation.CountingRules(tree), check, binding)

    def throw_string(self, deq):
        """Total of an equation such as '(1d8+1d6)*2', and its dice terms.

        Returns (total, terms) where terms maps each dice term's text to
        [methods, start, stop, {'natural', 'modified'}].  A division that does
        not come out even gives a Fraction.
        """
        tree, binding = self._prepare(deq, require_dice=False)
        terms = {}
        _natural, _modified, total = self._evaluate(tree, binding, terms)
        return total, terms

    def _prepare(self, dexp, require_dice=True):
        tree = self.parser.parse(dexp, require_dice)
        binding = self.parser.roll_subrolls(tree)
        for dice in notation.leaves(tree):
            notation.check_die_pipeline(dice, binding)
        return tree, binding

    def _evaluate(self, node, binding, terms):
        """(natural entries, modified entries, total); entries are (face, leaf)."""
        if isinstance(node, notation.Const):
            return [], [], node.value
        if isinstance(node, notation.Dice):
            methods = methods_dict(node, binding)
            result = self.roller.roll(methods)
            terms[term_key(terms, node)] = [methods, node.start, node.stop, result]
            total = self.scorer.get_roll_total(result['modified'], methods)
            return ([(face, node) for face in result['natural']],
                    [(value, node) for value in result['modified']], total)
        if isinstance(node, notation.Group):
            natural, modified, total = self._evaluate(node.child, binding, terms)
            suffix = node.suffix
            if suffix.keep is not None or suffix.drop is not None:
                keep = drop = None
                if suffix.keep is not None:
                    keep = (suffix.keep.layer, notation.bound(suffix.keep.count, binding))
                if suffix.drop is not None:
                    drop = (suffix.drop.layer, notation.bound(suffix.drop.count, binding))
                modified = self.roller.keep_drop(modified, keep, drop, key=lambda entry: entry[0])
                total = sum(int(value) for value, _leaf in modified)
            return natural, modified, total + self._total_mods(suffix, binding)
        left_nat, left_mod, left = self._evaluate(node.left, binding, terms)
        right_nat, right_mod, right = self._evaluate(node.right, binding, terms)
        if node.op == '+':
            total = left + right
        elif node.op == '-':
            total = left - right
        elif node.op == '*':
            total = left * right
        else:
            total = Fraction(left, right)
            if total.denominator == 1:
                total = total.numerator
        return left_nat + right_nat, left_mod + right_mod, total

    @staticmethod
    def _total_mods(suffix, binding):
        return sum(sign * notation.bound(value, binding) for sign, value in suffix.total_mods)
