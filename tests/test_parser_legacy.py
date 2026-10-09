"""The rewritten parser against a snapshot of the e179458 parser.

tests/data/legacy_parse_e179458.json holds parse_input() output from e179458
for 152 subroll-free expressions, with a flag recording whether its grammar
consumed the whole string.  Expressions it consumed fully must produce the same
methods dict today, except for the deliberate changes listed in CHANGED.
"""
import json
import pathlib

import pytest

from dice_roller.DiceException import DiceException
from dice_roller.DiceParser import DiceParser

SNAPSHOT = json.loads((pathlib.Path(__file__).parent / 'data' / 'legacy_parse_e179458.json').read_text())

# expression -> reason the methods dict now differs.
CHANGED = {
    '5d6s>=5': 'D3: the s method was silently overwritten by the default success rule',
}

ACCEPTED = sorted(e for e, v in SNAPSHOT.items() if v['full'] and 'error' not in v and e not in CHANGED)


def _normalise(methods):
    return json.loads(json.dumps(methods, sort_keys=True, default=str))


@pytest.mark.parametrize('expression', ACCEPTED)
def test_methods_dict_unchanged(expression):
    assert _normalise(DiceParser().parse_input(expression)) == SNAPSHOT[expression]['methods']


def test_s_method_now_honoured():
    assert DiceParser().parse_input('5d6s>=5')['s'] == {'operator': '>=', 'val': '5'}


@pytest.mark.parametrize('expression', sorted(e for e, v in SNAPSHOT.items() if 'error' in v))
def test_previous_errors_still_raise(expression):
    with pytest.raises(DiceException):
        DiceParser().parse_input(expression)


@pytest.mark.parametrize('expression, legacy_tail', [('5d6+0+10', '+10'),
                                                     ('10d6+0>=5f<=2xxp>=5ro=1dl5+4', '+4')])
def test_trailing_integer_is_now_a_term(expression, legacy_tail):
    """The old grammar dropped the trailing integer; it is now added to the total."""
    tree = DiceParser().parse(expression)
    assert tree.op == '+' and tree.right.value == int(legacy_tail[1:])
