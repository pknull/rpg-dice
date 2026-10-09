from dice_roller import notation
from dice_roller.DiceException import DiceException
from dice_roller.Die import Die
from dice_roller.notation import bound


def methods_dict(dice, binding):
    """The per-term methods dict DiceRoller and DiceScorer consume.

    Same keys and string values as the e179458 parser produced, with subroll
    values taken from ``binding``.
    """
    methods = {}
    if dice.types == 'int':
        suffix = dice.suffix

        def text(value):
            return str(int(bound(value, binding)))

        if suffix.keep is not None:
            methods['k'] = {'val': text(suffix.keep.count), 'layer': suffix.keep.layer}
        if suffix.drop is not None:
            methods['d'] = {'val': text(suffix.drop.count), 'layer': suffix.drop.layer}
        if dice.explode is not None:
            methods['x'] = {'operator': dice.explode.operator, 'val': text(dice.explode.value),
                            'compound': dice.explode.compound, 'penetrate': dice.explode.penetrate}
        if dice.reroll is not None:
            methods['r'] = {'operator': dice.reroll.operator, 'val': text(dice.reroll.value),
                            'once': dice.reroll.once}
        for name, comparison in (('f', suffix.fail), ('ns', suffix.ns), ('nf', suffix.nf),
                                 ('t', suffix.check)):
            if comparison is not None:
                methods[name] = {'operator': comparison.operator, 'val': text(comparison.value)}
        methods['s'] = {'operator': suffix.success.operator, 'val': text(suffix.success.value)}
        if dice.per_die is not None:
            methods['b'] = {'operator': dice.per_die[0], 'val': str(dice.per_die[1])}
        else:
            methods['b'] = {'operator': '+', 'val': '0'}
        adjustment = sum(sign * bound(value, binding) for sign, value in suffix.total_mods)
        methods['l'] = {'operator': '+' if adjustment >= 0 else '-', 'val': str(abs(adjustment))}
    methods['number_of_dice'] = str(dice.count)
    methods['sides'] = list(dice.faces)
    methods['types'] = dice.types
    return methods


class DiceParser:
    counter_methods = ["s", "f", "ns", "nf"]
    roll_modifier_methods = ["x", "xx", "xp", "xxp", "r", "ro"]
    pool_modifier_methods = ["k", "kh", "kl", "d", "dh", "dl"]
    total_check_methods = ["t"]

    high_methods = list(notation.HIGH_DEFAULT)
    low_methods = list(notation.LOW_DEFAULT)

    def __init__(self):
        self.last_subrolls = []  # Subrolls rolled by the last roll_subrolls call

    def parse(self, expression, require_dice=True):
        """Parse an expression into a tree (dice_roller.notation); rolls nothing."""
        return notation.parse(expression, require_dice)

    def roll_subrolls(self, tree):
        """Roll every subroll once, as a throw does; returns the binding."""
        self.last_subrolls = []
        binding = {}
        for sub in notation.subrolls(tree):
            value = self._quick_roll(sub)
            binding[id(sub)] = value
            self.last_subrolls.append({'expression': sub.text, 'result': value})
        return binding

    def _quick_roll(self, sub):
        """Roll a simple NdS subroll and return its total as int."""
        die = Die(list(range(1, sub.sides + 1)))
        total = 0
        for _ in range(sub.count):
            die.roll()
            total += die.showing
        return total

    # this will parse one dice roll
    def parse_input(self, expression):
        """Methods dict for a single dice term, rolling any subrolls now."""
        tree = notation.parse(expression)
        if not isinstance(tree, notation.Dice):
            raise DiceException('Unable to parse expression',
                                'parse_input takes one dice term; use parse() for expressions')
        binding = self.roll_subrolls(tree)
        notation.check_die_pipeline(tree, binding)
        return methods_dict(tree, binding)

    # this will parse a full equation and return the dice
    # expressions with their position in the equation
    def parse_expression_from_equation(self, equation):
        tree = notation.parse(equation, require_dice=False)
        binding = self.roll_subrolls(tree)
        parsed_equation = {}
        for dice in notation.leaves(tree):
            notation.check_die_pipeline(dice, binding)
            parsed_equation[term_key(parsed_equation, dice)] = [methods_dict(dice, binding),
                                                                dice.start, dice.stop]
        return parsed_equation


def term_key(table, dice):
    """A term's text, suffixed with its position when the same text repeats."""
    return dice.text if dice.text not in table else f'{dice.text}@{dice.start}'
