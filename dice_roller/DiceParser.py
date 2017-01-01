import re
from pyparsing import Literal, Word, oneOf, Optional, Group, ZeroOrMore, delimitedList
import collections


class DiceParser(object):
    # methods (grouped by defaults)
    counter_methods = ["s", "f", "ns", "nf"]
    roll_modifier_methods = ["x", "xx", "xp", "xxp", "r", "ro"]
    pool_modifier_methods = ["k", "kh", "kl", "d", "dh", "dl"]
    hidden_modifier_methods = ["b", "l"]

    # collection of all methods
    all_methods = ' '.join(counter_methods + roll_modifier_methods + pool_modifier_methods + hidden_modifier_methods)

    # high and low face defaults
    high_methods = ["s", "x", "xx", "xp", "xxp", "k", "kh", "dh", "ns"]
    low_methods = ["f", "kl", "d", "dl", "r", "ro", "nf"]

    def __init__(self):
        return

    def parse_input(self, expression):

        # create the parsing expression based on our method list
        dice_expr = self.get_expression(self.all_methods)

        # parse the expression, using our  expression
        try:
            parsed_string = dice_expr.parseString(expression)
        except:
            return False

        # pull out a dictionary of the specific methods
        methods = self.clean_methods(parsed_string)

        return methods

    def get_expression(self, method_list):
        methods = method_list
        numbers = "0123456789"
        dice_numbers = numbers + 'F'
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
        sides = parsed.sides
        methods = {}

        for value in parsed_methods:
            method_name = value.method_name
            # default value is based on method
            if value.method_value:
                val = value.method_value
            else:
                if (value.method_name in self.high_methods):
                    val = sides
                elif (value.method_name in self.low_methods):
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
                methods['k'] = {'val': val, 'layer': layer}
            # drop
            elif method_name[0] == 'd':
                layer = 'low'
                if len(method_name) > 1:
                    if method_name[1] == 'h':
                        layer = 'high'
                methods['d'] = {'val': val, 'layer': layer}
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
                methods['x'] = {'operator': operator, 'val': val, 'compound': compound, 'penetrate': penetrate}
            # reroll flags
            elif method_name[0] == 'r':
                once = False
                if len(method_name) > 1:
                    if method_name[1] == 'o':
                        once = True
                methods['r'] = {'operator': operator, 'val': val, 'once': once}
            # default
            else:
                methods[method_name] = {'operator': operator, 'val': val}



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
            s_eval = '=='

        methods['s'] = {'operator': s_eval, 'val': s_thresh}

        if parsed.dice_modifier:
            b_mod = parsed.dice_modifier
        else:
            b_mod = '+'

        if parsed.dice_boost:
            b_boost = parsed.dice_boost
        else:
            b_boost = '0'

        methods['b'] = {'operator': b_mod, 'val': b_boost}

        if parsed.pool_modifier:
            l_mod = parsed.pool_modifier
        else:
            l_mod = '+'

        if parsed.pool_boost:
            l_boost = parsed.pool_boost
        else:
            l_boost = '0'

        methods['l'] = {'operator': l_mod, 'val': l_boost}

        # this is silly, but makes problems obvious in the parse debug.
        # NO METHODS FOR FUDGE DICE
        if parsed.sides == 'F':
            methods = {'l': methods['l']}
        # 0 or less sided dice are stupid.
        elif int(parsed.sides) <= 0:
            raise Exception('Impossible dice')

        # take the remaining parsed items and put them in methods
        methods['number_of_dice'] = parsed.number_of_dice
        methods['sides'] = parsed.sides

        return methods
