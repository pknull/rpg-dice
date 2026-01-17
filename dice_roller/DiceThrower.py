from dice_roller.DiceParser import DiceParser
from dice_roller.DiceRoller import DiceRoller
from dice_roller.DiceScorer import DiceScorer
from dice_roller.DiceException import DiceException
from dice_roller.safe_compare import safe_eval_arithmetic


class DiceThrower:

    def __init__(self):
        self.parser = DiceParser()
        self.roller = DiceRoller()
        self.scorer = DiceScorer()
        self.result = []

    def throw(self, dexp='1d1'):

        # parse
        try:
            parsed_roll = self.parser.parse_input(dexp)
        except DiceException:
            return 'Bad roll expression - ' + dexp

        # roll dice
        result = self.roller.roll(parsed_roll)
        self.result = result

        # score
        score = self.scorer.get_result(dexp, result, parsed_roll)

        return score

    def throw_string(self, deq):

        parsed_equation = self.parser.parse_expression_from_equation(deq)
        mod_deq = deq
        for roll in parsed_equation:
            result = self.roller.roll(parsed_equation[roll][0])
            parsed_equation[roll].append(result)

            total = self.scorer.get_roll_total(
                result['modified'], parsed_equation[roll][0]
            )
            mod_deq = mod_deq.replace(roll, str(total))

        full_result = safe_eval_arithmetic(mod_deq)
        return full_result, parsed_equation
