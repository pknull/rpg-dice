from __future__ import division
from pyparsing import Literal, Word, oneOf, Optional, Group, ZeroOrMore, Combine
from dice_roller.DiceException import DiceException


class DiceParser(object):
    # methods (grouped by defaults)
    counter_methods = ["s", "f", "ns", "nf"]
    roll_modifier_methods = ["x", "xx", "xp", "xxp", "r", "ro"]
    pool_modifier_methods = ["k", "kh", "kl", "d", "dh", "dl"]
    hidden_modifier_methods = ["b", "l"]
    non_int_die = ['F', 'P']

    # collection of all methods
    all_methods = ' '.join(counter_methods + roll_modifier_methods + pool_modifier_methods + hidden_modifier_methods)

    # high and low face defaults
    high_methods = ["s", "x", "xx", "xp", "xxp", "k", "kh", "dh", "ns"]
    low_methods = ["f", "kl", "d", "dl", "r", "ro", "nf"]

    def __init__(self):
        return

    # this will parse one dice roll
    def parse_input(self, expression):
        # create the parsing expression based on our method list
        dice_expr = self.get_expression(self.all_methods)

        # parse the expression, using our  expression
        try:
            parsed_string = dice_expr.parseString(expression)
        except Exception:
            raise DiceException('Unable to parse expression', 'Bad Expression')
        # pull out a dictionary of the specific methods
        methods = self.clean_methods(parsed_string)
        return methods

    # this will parse a full equation and return the dice
    # expressions with their position in the equation
    def parse_expression_from_equation(self, equation):
        # create the parsing expression based on our method list
        dice_expr = Combine(self.get_expression(self.all_methods)).setResultsName('expression')
        parsed_equation = {}

        for result, start, stop in dice_expr.scanString(equation):
            methods = self.clean_methods(result.expression)
            parsed_equation[str(result[0][0])] = [methods, start, stop]

        return parsed_equation

    def get_expression(self, method_list):
        methods = method_list

        numbers = "0123456789"

        dice_numbers = numbers + "".join(self.non_int_die)
        dice = Literal("d")

        operators = '+ -'
        comparators = '< <= > >= = !='
        digits = Word(numbers)
        dice_digits = Word(dice_numbers)

        dice_expr = digits.setResultsName("number_of_dice") \
                    + dice \
                    + dice_digits.setResultsName("sides") \
                    + Optional(oneOf(operators).setResultsName("dice_modifier")) \
                    + Optional(digits.setResultsName("dice_boost")) \
                    + Optional(oneOf(comparators).setResultsName("success_evaluator")) \
                    + Optional(digits.setResultsName("success_threshhold")) \
                    + ZeroOrMore(Group(oneOf(methods).setResultsName('method_name') \
                                       + Optional(oneOf(comparators).setResultsName("method_operator")) \
                                       + Optional(digits.setResultsName("method_value"))).setResultsName('methods',
                                                                                                         True)) \
                    + Optional(oneOf(operators).setResultsName("pool_modifier")) \
                    + Optional(digits.setResultsName("pool_boost"))

        return dice_expr

    def clean_methods(self, parsed):
        parsed_methods = parsed.methods
        sides = self.clean_values(parsed.sides)
        methods = {}

        # 0 or less sided dice are stupid.
        if parsed.sides in self.non_int_die:
            sides = parsed.sides
        elif sides is None:
            raise DiceException('Unable to parse expression', 'Unknown dice sides')
        elif int(sides) <= 0:
            raise DiceException('Unable to parse expression', 'Impossible dice faces')
        elif int(sides) > 100:
            raise DiceException('Unable to perform roll', 'Too many dice faces')
        elif int(parsed.number_of_dice) > 200:
            raise DiceException('Unable to perform roll', 'Too many dice requested')

        for value in parsed_methods:
            method_name = value.method_name
            # default value is based on method
            if value.method_value:
                val = value.method_value
            else:
                if value.method_name in self.high_methods:
                    val = sides
                elif value.method_name in self.low_methods:
                    val = '1'
                else:
                    val = '0'

            # pool modifiers don't need methods (yet)
            if value.method_name not in list(self.pool_modifier_methods):
                if value.method_operator:
                    if value.method_operator == '=':
                        operator = '=='
                    else:
                        operator = value.method_operator
                else:
                    operator = '=='

            # keep
            if method_name[0] == 'k':
                layer = 'high'
                if len(method_name) > 1:
                    if method_name[1] == 'l':
                        layer = 'low'
                methods['k'] = {'val': self.clean_values(val), 'layer': layer}
            # drop
            elif method_name[0] == 'd':
                layer = 'low'
                if len(method_name) > 1:
                    if method_name[1] == 'h':
                        layer = 'high'
                methods['d'] = {'val': self.clean_values(val), 'layer': layer}
            # exploding flags
            elif method_name[0] == 'x':
                compound = False
                penetrate = False
                if len(method_name) > 1:
                    if method_name[1] == 'x':
                        compound = True
                    elif method_name[1] == 'p':
                        penetrate = True
                    if len(method_name) > 2:
                        if method_name[2] == 'p':
                            penetrate = True
                methods['x'] = {'operator': operator, 'val': self.clean_values(val), 'compound': compound,
                                'penetrate': penetrate}
            # reroll flags
            elif method_name[0] == 'r':
                once = False
                if len(method_name) > 1:
                    if method_name[1] == 'o':
                        once = True
                methods['r'] = {'operator': operator, 'val': self.clean_values(val), 'once': once}
            # default
            else:
                methods[method_name] = {'operator': operator, 'val': self.clean_values(val)}

        # success
        if parsed.success_threshhold:
            s_thresh = parsed.success_threshhold
        else:
            s_thresh = sides

        if parsed.success_evaluator:
            if parsed.success_evaluator == '=':
                s_eval = '=='
            else:
                s_eval = parsed.success_evaluator
        else:
            s_eval = '>='

        methods['s'] = {'operator': s_eval, 'val': self.clean_values(s_thresh)}

        # boost
        if parsed.dice_modifier:
            b_mod = parsed.dice_modifier
        else:
            b_mod = '+'

        if parsed.dice_boost:
            b_boost = parsed.dice_boost
        else:
            b_boost = '0'

        methods['b'] = {'operator': b_mod, 'val': self.clean_values(b_boost)}

        # Pool boost
        if parsed.pool_modifier:
            l_mod = parsed.pool_modifier
        else:
            l_mod = '+'

        if parsed.pool_boost:
            l_boost = parsed.pool_boost
        else:
            l_boost = '0'

        methods['l'] = {'operator': l_mod, 'val': self.clean_values(l_boost)}

        # this is silly, but makes problems obvious in the parse debug.
        # NO METHODS FOR NON INT DICE
        if sides in self.non_int_die:
            methods = {'l': methods['l']}

        # take the remaining parsed items and put them in methods
        methods['number_of_dice'] = self.clean_values(parsed.number_of_dice)
        methods['sides'] = sides

        return methods

    def clean_values(self, value):
        int_val = int(value) if value and value.isdecimal() else None
        if isinstance(int_val, int):
            return str(int_val)
        else:
            return int_val
