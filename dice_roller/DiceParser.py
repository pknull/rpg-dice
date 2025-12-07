import re
from pyparsing import Literal, Word, oneOf, Optional, Group, ZeroOrMore, Combine, Or, Suppress, Regex, nums, alphanums
from dice_roller.DiceException import DiceException
from dice_roller.Die import Die


def clean_value(value):
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return None


def clean_sides(values):
    list_type = "mixed"

    for index, sub in enumerate(values):
        try:
            values[index] = int(sub)
        except ValueError:
            values[index] = str(sub)

    if all(isinstance(sub, type(values[0])) for sub in values[1:]):
        list_type = values[0].__class__.__name__

    return values, list_type


class DiceParser:
    counter_methods = ["s", "f", "ns", "nf"]
    roll_modifier_methods = ["x", "xx", "xp", "xxp", "r", "ro"]
    pool_modifier_methods = ["k", "kh", "kl", "d", "dh", "dl"]
    total_check_methods = ["t"]
    hidden_modifier_methods = ["b", "l"]

    all_methods = ' '.join(counter_methods + roll_modifier_methods + pool_modifier_methods + total_check_methods + hidden_modifier_methods)

    high_methods = ["s", "x", "xx", "xp", "xxp", "k", "kh", "dh", "ns"]
    low_methods = ["f", "kl", "d", "dl", "r", "ro", "nf"]

    def __init__(self):
        self.last_subrolls = []  # Track subrolls from last parse

    def resolve_subrolls(self, expression):
        """
        Pre-process expression to resolve dice in modifier positions.
        E.g., '1d20=+1d3>=17' becomes '1d20=+2>=17' (where 2 is the 1d3 result)

        Subrolls are dice expressions after arithmetic operators (+, -, *, /)
        or total modifiers (=+, =-). They get rolled and replaced with their total.
        """
        self.last_subrolls = []

        # Match: operator, comparator, or method prefix followed by dice expression
        # Operators: =+, =-, +, -, *, /
        # Comparators: >=, <=, >, <, =, !=
        # Methods: kh, kl, dh, dl, k, d, x, xx, xp, xxp, r, ro, s, f, ns, nf, t
        # \d+d\d+ matches dice like 1d6, 2d10
        # (?![xrkd]) negative lookahead prevents matching when followed by die-modifying methods
        subroll_pattern = r'(=?[+\-*/]|>=|<=|!=|>|<|=|kh|kl|dh|dl|xxp|xx|xp|x|ro|r|ns|nf|s|f|t|k|d)(\d+d\d+)(?![xrkd])'

        def roll_and_replace(match):
            operator = match.group(1)
            dice_expr = match.group(2)
            result = self._quick_roll(dice_expr)
            self.last_subrolls.append({
                'expression': dice_expr,
                'result': result,
                'operator': operator
            })
            return f"{operator}{result}"

        return re.sub(subroll_pattern, roll_and_replace, expression)

    def _quick_roll(self, dice_expr):
        """Roll a simple NdS expression and return total as int"""
        match = re.match(r'(\d+)d(\d+)', dice_expr)
        if not match:
            return 0
        num_dice = int(match.group(1))
        sides = int(match.group(2))

        die = Die(list(range(1, sides + 1)))
        total = 0
        for _ in range(num_dice):
            die.roll()
            total += die.showing
        return total

    # this will parse one dice roll
    def parse_input(self, expression):
        # Resolve any subrolls (dice in modifier positions) first
        expression = self.resolve_subrolls(expression)

        # create the parsing expression based on our method list
        dice_expr = self.get_expression(self.all_methods)

        # parse the expression, using our  expression
        try:
            parsed_string = dice_expr.parseString(expression)
        except Exception as e:
            raise DiceException('Unable to parse expression', 'Bad Expression - ' + str(e))
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

        dice_numbers = nums
        dice = Literal("d")

        operators = '+ - / *'
        # Use regex for = to prevent matching =+ or =- (total_modifier syntax)
        eq_not_total_mod = Regex(r'=(?![+-])')
        other_comparators = oneOf('< <= > >= !=')
        comparators_expr = eq_not_total_mod | other_comparators
        digits = Word(nums)
        dice_digits = Word(dice_numbers)
        dice_faces = Word(alphanums + "," + "-")

        list_value = (Suppress("{") + dice_faces + Suppress("}"))

        # Total modifier: =+N or =-N syntax, can be chained (e.g., =+10=-3)
        total_modifier = Group(
            Combine(Literal("=") + oneOf('+ -')).setResultsName("mod_op")
            + digits.setResultsName("mod_val")
        )

        # Total check: >=N or similar at end of expression, checks if total meets threshold
        total_check = comparators_expr.copy().setResultsName("total_check_op") \
                      + digits.setResultsName("total_check_val")

        dice_expr = digits.setResultsName("number_of_dice") \
                    + dice \
                    + Or((dice_digits.setResultsName("sides"), list_value.setResultsName("sides"))) \
                    + Optional(oneOf(operators).setResultsName("dice_modifier")) \
                    + Optional(digits.setResultsName("dice_boost")) \
                    + ZeroOrMore(total_modifier).setResultsName("total_modifiers") \
                    + Optional(comparators_expr.setResultsName("success_evaluator")) \
                    + Optional(digits.setResultsName("success_threshhold")) \
                    + ZeroOrMore(Group(oneOf(methods).setResultsName('method_name') \
                                       + Optional(comparators_expr.copy().setResultsName("method_operator")) \
                                       + Optional(digits.setResultsName("method_value"))).setResultsName('methods',
                                                                                                         True)) \
                    + Optional(total_check)

        return dice_expr

    def clean_methods(self, parsed):
        parsed_methods = parsed.methods
        methods = {}

        dirty_sides = parsed.sides[0].split(',')

        if len(dirty_sides) > 1:
            sides, list_type = clean_sides(dirty_sides)
        elif len(dirty_sides) == 1:
            sides_int = clean_value(parsed.sides)
            if sides_int is None:
                raise DiceException('Unable to parse expression', 'Unknown dice sides')
            elif int(sides_int) <= 0:
                raise DiceException('Unable to parse expression', 'Impossible dice faces')
            elif int(sides_int) > 100:
                raise DiceException('Unable to perform roll', 'Too many dice faces')
            elif int(parsed.number_of_dice) > 200:
                raise DiceException('Unable to perform roll', 'Too many dice requested')

            sides = list(range(1, int(sides_int) + 1))
            list_type = "int"

        else:
            raise DiceException('Unable to parse expression', 'Unknown dice sides')

        # methods for ints

        if list_type == "int":

            for value in parsed_methods:
                method_name = value.method_name
                # default value is based on method
                if value.method_value:
                    val = value.method_value
                else:
                    if value.method_name in self.high_methods:
                        val = max(sides)
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
                    methods['k'] = {'val': clean_value(val), 'layer': layer}
                # drop
                elif method_name[0] == 'd':
                    layer = 'low'
                    if len(method_name) > 1:
                        if method_name[1] == 'h':
                            layer = 'high'
                    methods['d'] = {'val': clean_value(val), 'layer': layer}
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
                    methods['x'] = {'operator': operator, 'val': clean_value(val), 'compound': compound,
                                    'penetrate': penetrate}
                # reroll flags
                elif method_name[0] == 'r':
                    once = False
                    if len(method_name) > 1:
                        if method_name[1] == 'o':
                            once = True
                    methods['r'] = {'operator': operator, 'val': clean_value(val), 'once': once}
                # default
                else:
                    methods[method_name] = {'operator': operator, 'val': clean_value(val)}

            # success
            if parsed.success_threshhold:
                s_thresh = parsed.success_threshhold
            else:
                if list_type == "int":
                    s_thresh = max(sides)
                else:
                    s_thresh = 0

            if parsed.success_evaluator:
                if parsed.success_evaluator == '=':
                    s_eval = '=='
                else:
                    s_eval = parsed.success_evaluator
            else:
                s_eval = '>='

            methods['s'] = {'operator': s_eval, 'val': clean_value(s_thresh)}

            # boost
            if parsed.dice_modifier:
                b_mod = parsed.dice_modifier
            else:
                b_mod = '+'

            if parsed.dice_boost:
                b_boost = parsed.dice_boost
            else:
                b_boost = '0'

            methods['b'] = {'operator': b_mod, 'val': clean_value(b_boost)}

            # Total boost - =+N=-M syntax accumulates
            if parsed.total_modifiers:
                # Accumulate all total modifiers: =+10=-3 becomes +7
                total_adjustment = 0
                for mod in parsed.total_modifiers:
                    op = mod.mod_op[1]  # '+' or '-' (skip the '=')
                    val = int(mod.mod_val)
                    if op == '+':
                        total_adjustment += val
                    else:
                        total_adjustment -= val
                if total_adjustment >= 0:
                    l_mod = '+'
                    l_boost = str(total_adjustment)
                else:
                    l_mod = '-'
                    l_boost = str(abs(total_adjustment))
            else:
                l_mod = '+'
                l_boost = '0'

            methods['l'] = {'operator': l_mod, 'val': clean_value(l_boost)}

            # Total check: >=N at end of expression checks if total meets threshold
            if parsed.total_check_op:
                t_op = parsed.total_check_op
                if t_op == '=':
                    t_op = '=='
                t_val = parsed.total_check_val if parsed.total_check_val else '0'
                methods['t'] = {'operator': t_op, 'val': clean_value(t_val)}

        # take the remaining parsed items and put them in methods
        methods['number_of_dice'] = clean_value(parsed.number_of_dice)
        methods['sides'] = sides
        methods['types'] = list_type

        return methods
