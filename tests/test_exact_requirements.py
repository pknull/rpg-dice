"""Requirements from rpg-skills/docs/rpg-dice-requirements.md (approved 2026-10-09).

Every exact value is first checked against a brute-force oracle (tests/oracle.py)
and only then against the figure the requirements document states.  Rounded
figures in the document (``4d6dl1`` mean 12.24) are compared after rounding the
exact rational, never used as the reference.
"""
import pathlib
import re
import subprocess
import sys
from fractions import Fraction

import pytest

from dice_roller.DiceException import DiceException
from dice_roller.DiceParser import DiceParser
from dice_roller.DiceProbability import DiceProbability
from dice_roller.DiceThrower import DiceThrower
from dice_roller.exact import FIELDS
from tests.oracle import (faces_of, marginal, product_distribution,
                          replay_distribution)

ROOT = pathlib.Path(__file__).resolve().parents[1]
D6 = list(range(1, 7))
D20 = list(range(1, 21))


@pytest.fixture
def prob():
    return DiceProbability()


def exact(expression, **kwargs):
    return DiceProbability().exact(expression, **kwargs)


def assert_matches_replay(expression, max_draws=12, **kwargs):
    result = exact(expression, **kwargs)
    oracle, truncated = replay_distribution(expression, max_draws=max_draws)
    assert truncated == 0
    assert result.unresolved == 0
    assert result.joint == oracle
    return result


def run_isolated(code, timeout):
    """Run code in a fresh interpreter; a hang or crash fails the test."""
    return subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True,
                          text=True, timeout=timeout)


class TestRegressionFixtures:
    """The document's fixture table, each checked against brute force first."""

    def test_3d6_t_ge_10(self):
        result = exact('3d6t>=10')
        assert result.joint == product_distribution(3, D6, check=('>=', 10))
        assert result.marginal('pass')[1] == Fraction(5, 8)

    def test_2d20kh1_t_ge_11(self):
        result = exact('2d20kh1t>=11')
        assert result.joint == product_distribution(2, D20, keep=('high', 1), check=('>=', 11))
        assert result.marginal('pass')[1] == Fraction(3, 4)

    def test_advantage_plus_5(self):
        result = exact('2d20=+5kh1t>=15')
        assert result.joint == product_distribution(2, D20, keep=('high', 1), total_mod=5,
                                                    check=('>=', 15))
        assert result.marginal('pass')[1] == Fraction(319, 400)

    def test_4d6dl1_mean_rounded(self, prob):
        result = exact('4d6dl1')
        oracle = product_distribution(4, D6, keep=('high', 3))
        assert result.joint == oracle
        exact_mean = sum(k[0] * p for k, p in oracle.items())
        assert exact_mean == Fraction(15869, 1296)
        assert result.mean('total') == exact_mean
        assert round(float(exact_mean), 2) == 12.24
        assert prob.analyze('4d6dl1')['mean'] == 12.24

    def test_2d6_plus1_t_ge_10(self):
        result = exact('2d6=+1t>=10')
        assert result.joint == product_distribution(2, D6, total_mod=1, check=('>=', 10))
        assert result.marginal('pass')[1] == Fraction(5, 18)

    def test_5d6_at_least_one_success(self):
        result = exact('5d6>=6')
        assert result.joint == product_distribution(5, D6, success=('>=', 6))
        assert result.probability(lambda o: o['success'] >= 1) == Fraction(4651, 7776)

    def test_fate_mean(self):
        result = exact('4d{-1,0,1}')
        assert result.joint == product_distribution(4, [-1, 0, 1])
        assert result.mean('total') == 0

    def test_fate_plus_2_vs_good(self):
        result = exact('4d{-1,0,1}=+2t>=3')
        assert result.joint == product_distribution(4, [-1, 0, 1], total_mod=2, check=('>=', 3))
        assert result.marginal('pass')[1] == Fraction(31, 81)

    def test_brp_percentile(self):
        result = exact('1d100t<=45')
        assert result.joint == product_distribution(1, list(range(1, 101)), check=('<=', 45))
        assert result.marginal('pass')[1] == Fraction(9, 20)

    def test_zero_dice(self, prob):
        assert exact('0d6').joint == {(0, 0, None, None, None, None): Fraction(1)}
        assert prob.analyze('0d6')['mean'] == 0

    def test_subroll_total_modifier(self, prob):
        results = [exact('3d6=+1d4') for _ in range(6)]
        assert all(r.joint == results[0].joint for r in results)
        oracle, _ = replay_distribution('3d6=+1d4')
        assert results[0].joint == oracle
        assert results[0].mean('total') == 13
        assert {prob.analyze('3d6=+1d4')['mean'] for _ in range(6)} == {13.0}

    def test_pool_sum(self):
        result = exact('1d8+1d6')
        oracle, _ = replay_distribution('1d8+1d6')
        assert result.joint == oracle
        assert result.marginal('total') == {
            t: Fraction(sum(1 for a in range(1, 9) for b in D6 if a + b == t), 48)
            for t in range(2, 15)}
        assert result.mean('total') == 8


class TestPilotCoverage:

    def test_yze_pool_reports_success_and_fail(self):
        roll = DiceThrower().throw('5d6>=6f<=1')
        assert 'success' in roll and 'fail' in roll
        result = exact('5d6>=6f<=1')
        assert result.joint == product_distribution(5, D6, success=('>=', 6), fail=('<=', 1))
        assert result.marginal('success')[0] == Fraction(3125, 7776)

    @pytest.mark.parametrize('expression, expected', [('1d10>=6', Fraction(1, 2)),
                                                      ('1d10>=10', Fraction(1, 10))])
    def test_yze_step_die(self, expression, expected):
        assert exact(expression).marginal('success')[1] == expected

    def test_dnd_advantage_naturals(self):
        result = exact('2d20=+5kh1t>=15ns20nf1')
        assert result.joint == product_distribution(2, D20, keep=('high', 1), total_mod=5,
                                                    check=('>=', 15), ns=('==', 20), nf=('==', 1))
        assert result.marginal('pass')[1] == Fraction(319, 400)


class TestD1Subrolls:

    def test_threshold_subroll_is_a_mixture(self):
        results = [exact('3d6t>=1d6') for _ in range(6)]
        assert all(r.joint == results[0].joint for r in results)
        oracle, _ = replay_distribution('3d6t>=1d6')
        assert results[0].joint == oracle

    def test_analysis_never_rolls(self, prob, monkeypatch):
        import dice_roller.Die as die_module

        def refuse(*args, **kwargs):
            raise AssertionError('exact analysis rolled a die')

        monkeypatch.setattr(die_module.random, 'choice', refuse)
        monkeypatch.setattr(die_module.random, 'randint', refuse)
        exact('3d6=+1d4=-1d2t>=1d6')
        prob.analyze('10d6kh1d4')


class TestD2PoolSum:

    def test_throw_reads_pool_sum(self):
        roll = DiceThrower().throw('1d8+1d6')
        assert len(roll['natural']) == 2
        assert int(roll['total']) == sum(roll['modified'])

    def test_throw_string_pool_sum(self):
        dist, _ = replay_distribution('1d8+1d6', key=lambda r: r[0],
                                      call=lambda t, e: t.throw_string(e))
        assert sum(k * p for k, p in dist.items()) == 8
        assert dist == exact('1d8+1d6').marginal('total')

    def test_throw_string_grouped_product(self):
        dist, _ = replay_distribution('(1d8+1d6)*2', key=lambda r: r[0],
                                      call=lambda t, e: t.throw_string(e))
        assert sum(k * p for k, p in dist.items()) == 16

    def test_bare_and_grouped_forms_agree(self):
        assert exact('1d8+1d6').joint == exact('(1d8)+(1d6)').joint


MALFORMED = [
    '2d20kh1=+5t>=15', '2d6kh1>=', '2d6 4', '2d6+', '2d6++3', '2d6kh1kh2', '2d6xx>=5x>=6',
    '2d6r<2ro<3', '2d6kh2kl1', '2d6dh1dl1', '2d6>=5s>=4', '2d6t>=5>=7', '2d6f<2f<3', '2d6q',
    'abc', '2d', 'd6', '(1d6', '1d6)', '()', '1d6=+', '1d6b3', '1d6l2', '2d{a,b}x',
    '2d{a,b}>=1', '2d{a,b}kh1', '(1d6)x>=6', '(1d6)r<2', '(1d6)+3t>=5', '1d8+1d6t>=5',
    '(1d6t>=3)', '1d6*1d4', '(1d6)/0', '2d6/0', '1d6r<=6', '1d6x>=1', '201d6', '1d101',
    '1d0', '100d6+101d6', '(' * 40 + '1d6' + ')' * 40, '1d20**2', '2d6kh1+',
    '1d{5}', '', '1d6,', '2d6>=5 5', '1 d6', '1d 6', '1+' * 300 + '1', '1d{a\n,b}',
    '0d6+' * 250 + '1d6',
    '1d6+\u00b2', '\u00b2', '1d6>=' + '9' * 30, '9' * 5000 + 'd6', '4d{-1,0,1}>=-1', '3d6>=+5',
    '2d6>= -1', '1d\u0663', '2d{-2,-1}k', '2d{-2,-1}dh',
]


def _short(expression):
    return expression if len(expression) <= 30 else f'{expression[:24]}...({len(expression)})'


class TestD3Strictness:

    @pytest.mark.parametrize('expression', MALFORMED, ids=_short)
    def test_parser_raises(self, expression):
        with pytest.raises(DiceException):
            DiceParser().parse(expression)

    @pytest.mark.parametrize('expression', MALFORMED, ids=_short)
    def test_exact_raises(self, expression):
        with pytest.raises(DiceException):
            exact(expression)

    @pytest.mark.parametrize('expression', MALFORMED, ids=_short)
    def test_throw_reports_bad_roll(self, expression):
        result = DiceThrower().throw(expression)
        assert isinstance(result, str) and result.startswith('Bad roll expression')

    def test_out_of_order_example(self):
        with pytest.raises(DiceException):
            DiceParser().parse_input('2d20kh1=+5t>=15')
        assert exact('(2d20kh1)=+5t>=15').marginal('pass')[1] == Fraction(319, 400)


class TestD4ZeroDice:

    @pytest.mark.parametrize('expression', ['0d6', '0d6>=6', '0d6kh1', '0d6x6', '0d6r1'])
    def test_zero_dice_identity(self, expression):
        assert exact(expression).joint == {(0, 0, None, None, None, None): Fraction(1)}

    def test_zero_dice_in_a_sum(self):
        assert exact('(0d6)+(1d4)').joint == exact('1d4').joint


class TestS1Grouping:

    def test_mixed_sizes_add_counts(self):
        roll = DiceThrower().throw('(1d10>=6)+(1d8>=6)')
        assert len(roll['natural']) == 2 and len(roll['modified']) == 2
        assert int(roll['success']) == sum(1 for v in roll['modified'] if v >= 6)
        result = assert_matches_replay('(1d10>=6)+(1d8>=6)')
        assert result.marginal('success') == {0: Fraction(5, 16), 1: Fraction(8, 16),
                                              2: Fraction(3, 16)}

    def test_group_modifier_and_check(self):
        roll = DiceThrower().throw('(2d20kh1)=+5t>=15')
        assert int(roll['total']) == max(roll['natural']) + 5
        assert roll['pass'] == ('1' if int(roll['total']) >= 15 else '0')

    def test_previously_rejected_form(self):
        roll = DiceThrower().throw('(1d8)+(1d6)')
        assert isinstance(roll, dict)

    @pytest.mark.parametrize('expression', [
        '((1d4)+(1d6))>=4', '((1d4)+(1d6))kh1', '((1d4>=4)+(1d6>=6))kh1',
        '((1d4>=3)+(1d4>=4))kh1', '(1d6+1d4)*2', '1d6-1d4', '(2d4)=+1t>=6',
    ])
    def test_group_forms_match_replay(self, expression):
        assert_matches_replay(expression)


class TestS2KeepDropScaling:

    @pytest.mark.parametrize('expression', ['10d6kh3', '10d10kh3'])
    def test_under_one_second(self, expression):
        # First call in a fresh interpreter: no warm caches.
        code = ('import time\nfrom dice_roller.DiceProbability import DiceProbability\n'
                'start = time.perf_counter()\nDiceProbability().exact(%r)\n'
                'print(time.perf_counter() - start)' % expression)
        out = run_isolated(code, timeout=60)
        assert out.returncode == 0, out.stderr
        assert float(out.stdout) < 1.0


class TestS3ResultInterface:

    def test_fields_and_fraction_probabilities(self):
        result = exact('5d6>=6f<=1ns6nf1')
        assert FIELDS == ('total', 'success', 'fail', 'ns', 'nf', 'pass')
        assert result.fields == FIELDS
        assert all(isinstance(p, Fraction) for p in result.joint.values())
        assert sum(result.joint.values()) + result.unresolved == 1
        record = result.records()[0]
        assert set(record) == set(FIELDS) | {'probability'}

    @pytest.mark.parametrize('expression, keys', [
        ('10d6', {'roll', 'natural', 'modified', 'total', 'success'}),
        ('5d6>=6f<=1', {'roll', 'natural', 'modified', 'total', 'success', 'fail'}),
        ('1d20>15ns20nf1', {'roll', 'natural', 'modified', 'total', 'success', 'ns', 'nf'}),
        ('2d6t>=7', {'roll', 'natural', 'modified', 'total', 'success', 'pass'}),
        ('5d{a,b,c}', {'roll', 'natural', 'modified', 'total'}),
    ])
    def test_roll_result_keys_preserved(self, expression, keys):
        assert set(DiceThrower().throw(expression)) == keys

    @pytest.mark.parametrize('expression', ['3d6kh2', '2d6ro<3kh1ns1', '(1d4)+(1d6)', '3d{a,b}'])
    def test_faces_distribution_matches_replay(self, expression):
        result = exact(expression, faces=True)
        oracle, _ = replay_distribution(expression, key=lambda r: faces_of(r))
        got = {}
        for (kept, natural, _outcome), p in result.faces.items():
            got[(kept, natural)] = got.get((kept, natural), 0) + p
        assert got == oracle

    def test_faces_carry_outcomes(self):
        result = exact('3d6kh2t>=10', faces=True)
        for (kept, _natural, outcome), _p in result.faces.items():
            assert outcome[0] == sum(kept)
            assert outcome[5] == int(sum(kept) >= 10)

    def test_faces_bound_is_explicit(self):
        with pytest.raises(DiceException) as info:
            exact('60d10', faces=True)
        assert 'faces limit' in info.value.errors


class TestS4Hygiene:

    def test_no_sympy(self):
        assert 'sympy' not in (ROOT / 'requirements.txt').read_text()
        assert 'sympy' not in (ROOT / 'setup.py').read_text()
        for path in (ROOT / 'dice_roller').glob('*.py'):
            assert not re.search(r'^\s*(import|from)\s+sympy', path.read_text(), re.M), path

    def test_pycache_ignored(self):
        assert '__pycache__/' in (ROOT / '.gitignore').read_text().splitlines()

    def test_icepool_is_test_only(self):
        assert 'icepool' not in (ROOT / 'requirements.txt').read_text()
        assert 'icepool' not in (ROOT / 'setup.py').read_text()
        for path in (ROOT / 'dice_roller').glob('*.py'):
            assert 'icepool' not in path.read_text(), path


class TestFurtherDefects:
    """Defects found while reading e179458, beyond D1-D4."""

    def test_reroll_every_face_is_rejected_not_hung(self):
        with pytest.raises(DiceException):
            DiceParser().parse('1d6r<=6')
        out = run_isolated('from dice_roller.DiceThrower import DiceThrower\n'
                           'print(DiceThrower().throw("1d6r<=6"))', timeout=20)
        assert out.stdout.startswith('Bad roll expression')

    def test_certain_explosion_is_a_dice_exception(self):
        assert DiceThrower().throw('1d6x>=1').startswith('Bad roll expression')
        with pytest.raises(DiceException):
            exact('1d6x>=1')

    def test_subroll_that_rerolls_every_face(self):
        with pytest.raises(DiceException):
            exact('1d6r<=1d6')

    def test_throw_string_does_not_evaluate_python(self):
        with pytest.raises(DiceException):
            DiceThrower().throw_string('1d6+2**100')

    def test_safe_eval_arithmetic_has_no_eval(self):
        from dice_roller.safe_compare import safe_eval_arithmetic
        assert safe_eval_arithmetic('(7 + 15) * 2 - 4') == 40
        with pytest.raises(ValueError):
            safe_eval_arithmetic('2**100')


class TestDicelessExpressions:
    """e179458 rejected a throw without dice but evaluated plain arithmetic in throw_string."""

    @pytest.mark.parametrize('expression', ['5', '2+3', '(4)*2'])
    def test_throw_needs_dice(self, expression):
        assert DiceThrower().throw(expression).startswith('Bad roll expression')
        with pytest.raises(DiceException):
            exact(expression)

    def test_throw_string_keeps_plain_arithmetic(self):
        assert DiceThrower().throw_string('2+3') == (5, {})
        assert DiceThrower().throw_string('(4)*2/3')[0] == Fraction(8, 3)


@pytest.mark.parametrize('expression', ['10d6>=5', '((1d8xx)+(1d6xx))kh1t>=4', '3d6=+1d4kh1d3',
                                        '1d8+1d6-1d4', '6d6xp>=5dl2'])
def test_seed_reproduces_throws(expression):
    """The spec relies on random.seed(n) reproducing every throw."""
    import random
    state = random.getstate()
    try:
        runs = []
        for _ in range(2):
            random.seed(7)
            runs.append([DiceThrower().throw(expression) for _ in range(20)])
        assert runs[0] == runs[1]
    finally:
        random.setstate(state)


class TestReviewFindings:
    """Defects found by the independent review of this change (2026-10-09)."""

    def test_huge_sides_rejected_without_allocating(self):
        code = ('import resource\n'
                'resource.setrlimit(resource.RLIMIT_AS, (512 * 2 ** 20, 512 * 2 ** 20))\n'
                'from dice_roller.DiceThrower import DiceThrower\n'
                'print(DiceThrower().throw("1d99999999999"))')
        out = run_isolated(code, timeout=20)
        assert out.stdout.startswith('Bad roll expression'), out.stderr[-300:]

    @pytest.mark.parametrize('expression', ['0d6=+5', '2d4=+3dl2', '2d20=+5k0t>=5', '3d6=-2kh0'])
    def test_total_modifier_applies_to_an_empty_pool(self, expression):
        assert_matches_replay(expression)
        roll = DiceThrower().throw(expression)
        assert int(roll['total']) != 0

    @pytest.mark.parametrize('tight, spaced', [
        ('2d6+3', '2d6 + 3'), ('2d6+3', '2d6 +3'), ('2d6+3', '2d6+ 3'), ('4d6-1', '4d6 - 1'),
        ('2d6*2>=7', '2d6 * 2 >=7'), ('1d8+1d6', '1d8 + 1d6'), ('2d20kh1+5', '2d20kh1 + 5'),
        ('2d6=+3', '2d6 =+3'), ('(1d6+1)+2', '( 1d6 + 1 ) + 2'),
    ])
    def test_spaces_do_not_change_meaning(self, tight, spaced):
        """README: spaces are for readability only; +N after the sides is per die."""
        assert exact(spaced).joint == exact(tight).joint

        def roll_fields(roll):
            return tuple(sorted((k, str(v)) for k, v in roll.items() if k != 'roll'))

        for call, key in ((lambda t, e: t.throw(e), roll_fields),
                          (lambda t, e: t.throw_string(e)[0], lambda total: total)):
            assert (replay_distribution(spaced, call=call, key=key)[0]
                    == replay_distribution(tight, call=call, key=key)[0])

    def test_per_die_reading_is_the_documented_one(self):
        assert exact('2d6 + 3').mean('total') == 13
        assert exact('2d6=+3').mean('total') == 10

    def test_double_equals_is_equality(self):
        assert exact('1d6x==6').joint == exact('1d6x=6').joint
        assert exact('10d6==6').joint == exact('10d6=6').joint
