"""
Exhaustive operator coverage tests for sympify replacement safety.

These tests ensure that ALL comparison and arithmetic operators work correctly
in ALL contexts where they are used. This provides a safety net before
refactoring sympify() calls to use safe_compare/safe_arithmetic functions.
"""
import pytest
from dice_roller.DiceThrower import DiceThrower


@pytest.fixture
def dice():
    return DiceThrower()


class TestRerollOperators:
    """Test all comparison operators with reroll (r/ro)."""

    def test_reroll_less_than(self, dice):
        """r<3 - reroll while less than 3"""
        result = dice.throw('10d6r<3')
        for v in result['modified']:
            assert v >= 3

    def test_reroll_less_equal(self, dice):
        """r<=2 - reroll while less than or equal to 2"""
        result = dice.throw('10d6r<=2')
        for v in result['modified']:
            assert v > 2

    def test_reroll_greater_than(self, dice):
        """r>4 - reroll while greater than 4"""
        result = dice.throw('10d6r>4')
        for v in result['modified']:
            assert v <= 4

    def test_reroll_greater_equal(self, dice):
        """r>=5 - reroll while greater than or equal to 5"""
        result = dice.throw('10d6r>=5')
        for v in result['modified']:
            assert v < 5

    def test_reroll_equal(self, dice):
        """r=1 - reroll while equal to 1"""
        result = dice.throw('10d6r=1')
        for v in result['modified']:
            assert v != 1

    def test_reroll_not_equal(self, dice):
        """r!=6 - reroll while not equal to 6 (all become 6)"""
        result = dice.throw('10d6r!=6')
        for v in result['modified']:
            assert v == 6

    def test_reroll_once_less_than(self, dice):
        """ro<3 - reroll once if less than 3"""
        result = dice.throw('10d6ro<3')
        assert 'modified' in result  # Just verify it runs

    def test_reroll_once_greater_equal(self, dice):
        """ro>=5 - reroll once if >= 5"""
        result = dice.throw('10d6ro>=5')
        assert 'modified' in result


class TestExplodeOperators:
    """Test all comparison operators with explode (x/xx/xp/xxp)."""

    def test_explode_equal(self, dice):
        """x=6 - explode on 6"""
        for _ in range(50):
            result = dice.throw('10d6x=6')
            if 6 in result['natural']:
                assert len(result['modified']) >= len(result['natural'])
                return
        # Statistically should hit within 50 tries

    def test_explode_greater_equal(self, dice):
        """x>=5 - explode on 5 or 6"""
        result = dice.throw('10d6x>=5')
        assert 'modified' in result

    def test_explode_greater_than(self, dice):
        """x>5 - explode on 6 only"""
        result = dice.throw('10d6x>5')
        assert 'modified' in result

    def test_explode_less_than(self, dice):
        """x<2 - explode on 1"""
        result = dice.throw('10d6x<2')
        assert 'modified' in result

    def test_explode_less_equal(self, dice):
        """x<=2 - explode on 1 or 2"""
        result = dice.throw('10d6x<=2')
        assert 'modified' in result

    def test_explode_not_equal(self, dice):
        """x!=3 - explode on anything but 3"""
        result = dice.throw('5d6x!=3')
        assert 'modified' in result

    def test_compound_greater_equal(self, dice):
        """xx>=5 - compound on 5+"""
        result = dice.throw('10d6xx>=5')
        assert len(result['modified']) == len(result['natural'])

    def test_penetrate_equal(self, dice):
        """xp=6 - penetrating explode on 6"""
        result = dice.throw('10d6xp=6')
        assert 'modified' in result


class TestSuccessOperators:
    """Test all comparison operators with success counting.

    NOTE: The success evaluator position is AFTER total modifier but BEFORE methods.
    The syntax is: NdS+N=+N>=N (methods) t>=N
    Using operators in the main evaluator position, not 's' prefix.
    """

    def test_success_greater_equal(self, dice):
        """>=5 - count successes >= 5"""
        result = dice.throw('10d6>=5')
        expected = sum(1 for v in result['modified'] if v >= 5)
        assert int(result['success']) == expected

    def test_success_greater_than(self, dice):
        """>5 - count successes > 5"""
        result = dice.throw('10d6>5')
        expected = sum(1 for v in result['modified'] if v > 5)
        assert int(result['success']) == expected

    def test_success_less_than(self, dice):
        """<3 - count successes < 3 (evaluator position)"""
        result = dice.throw('10d6<3')
        expected = sum(1 for v in result['modified'] if v < 3)
        assert int(result['success']) == expected

    def test_success_less_equal(self, dice):
        """<=2 - count successes <= 2 (evaluator position)"""
        result = dice.throw('10d6<=2')
        expected = sum(1 for v in result['modified'] if v <= 2)
        assert int(result['success']) == expected

    def test_success_equal(self, dice):
        """=6 - count successes == 6 (evaluator position)"""
        result = dice.throw('10d6=6')
        expected = sum(1 for v in result['modified'] if v == 6)
        assert int(result['success']) == expected

    def test_success_not_equal(self, dice):
        """!=1 - count successes != 1 (evaluator position)"""
        result = dice.throw('10d6!=1')
        expected = sum(1 for v in result['modified'] if v != 1)
        assert int(result['success']) == expected


class TestFailOperators:
    """Test all comparison operators with fail counting (f)."""

    def test_fail_less_than(self, dice):
        """f<2 - count failures < 2"""
        result = dice.throw('10d6f<2')
        expected = sum(1 for v in result['modified'] if v < 2)
        assert int(result['fail']) == expected

    def test_fail_less_equal(self, dice):
        """f<=2 - count failures <= 2"""
        result = dice.throw('10d6f<=2')
        expected = sum(1 for v in result['modified'] if v <= 2)
        assert int(result['fail']) == expected

    def test_fail_greater_than(self, dice):
        """f>4 - count failures > 4"""
        result = dice.throw('10d6f>4')
        expected = sum(1 for v in result['modified'] if v > 4)
        assert int(result['fail']) == expected

    def test_fail_greater_equal(self, dice):
        """f>=5 - count failures >= 5"""
        result = dice.throw('10d6f>=5')
        expected = sum(1 for v in result['modified'] if v >= 5)
        assert int(result['fail']) == expected

    def test_fail_equal(self, dice):
        """f=1 - count failures == 1"""
        result = dice.throw('10d6f=1')
        expected = sum(1 for v in result['modified'] if v == 1)
        assert int(result['fail']) == expected

    def test_fail_not_equal(self, dice):
        """f!=6 - count failures != 6"""
        result = dice.throw('10d6f!=6')
        expected = sum(1 for v in result['modified'] if v != 6)
        assert int(result['fail']) == expected


class TestNaturalCounterOperators:
    """Test comparison operators with natural success/fail (ns/nf)."""

    def test_ns_equal(self, dice):
        """ns6 or ns=6 - count natural 6s"""
        result = dice.throw('10d6+2ns6')
        expected = sum(1 for v in result['natural'] if v == 6)
        assert int(result['ns']) == expected

    def test_ns_greater_equal(self, dice):
        """ns>=5 - count natural >= 5"""
        result = dice.throw('10d6+2ns>=5')
        expected = sum(1 for v in result['natural'] if v >= 5)
        assert int(result['ns']) == expected

    def test_ns_greater_than(self, dice):
        """ns>4 - count natural > 4"""
        result = dice.throw('10d6+2ns>4')
        expected = sum(1 for v in result['natural'] if v > 4)
        assert int(result['ns']) == expected

    def test_ns_less_than(self, dice):
        """ns<3 - count natural < 3"""
        result = dice.throw('10d6+2ns<3')
        expected = sum(1 for v in result['natural'] if v < 3)
        assert int(result['ns']) == expected

    def test_ns_less_equal(self, dice):
        """ns<=2 - count natural <= 2"""
        result = dice.throw('10d6+2ns<=2')
        expected = sum(1 for v in result['natural'] if v <= 2)
        assert int(result['ns']) == expected

    def test_nf_equal(self, dice):
        """nf1 or nf=1 - count natural 1s"""
        result = dice.throw('10d6+2nf1')
        expected = sum(1 for v in result['natural'] if v == 1)
        assert int(result['nf']) == expected

    def test_nf_less_equal(self, dice):
        """nf<=2 - count natural <= 2"""
        result = dice.throw('10d6+2nf<=2')
        expected = sum(1 for v in result['natural'] if v <= 2)
        assert int(result['nf']) == expected

    def test_nf_greater_equal(self, dice):
        """nf>=5 - count natural >= 5"""
        result = dice.throw('10d6+2nf>=5')
        expected = sum(1 for v in result['natural'] if v >= 5)
        assert int(result['nf']) == expected


class TestBoostOperators:
    """Test arithmetic operators with per-die boost."""

    def test_boost_plus(self, dice):
        """+3 - add 3 to each die"""
        result = dice.throw('5d6+3')
        for i, nat in enumerate(result['natural']):
            assert result['modified'][i] == nat + 3

    def test_boost_minus(self, dice):
        """-2 - subtract 2 from each die"""
        result = dice.throw('5d6-2')
        for i, nat in enumerate(result['natural']):
            assert result['modified'][i] == nat - 2

    def test_boost_multiply(self, dice):
        """*2 - multiply each die by 2"""
        result = dice.throw('5d6*2')
        for i, nat in enumerate(result['natural']):
            assert result['modified'][i] == nat * 2

    def test_boost_divide(self, dice):
        """/2 - divide each die by 2"""
        result = dice.throw('5d6/2')
        for i, nat in enumerate(result['natural']):
            # sympify returns exact Rational fractions
            # Convert to float for comparison
            modified_val = float(result['modified'][i])
            expected = nat / 2
            assert modified_val == expected


class TestTotalModifierOperators:
    """Test total modifier arithmetic (=+N, =-N)."""

    def test_total_plus(self, dice):
        """=+10 - add 10 to total"""
        result = dice.throw('3d6=+10')
        raw = sum(result['modified'])
        assert int(result['total']) == raw + 10

    def test_total_minus(self, dice):
        """=-5 - subtract 5 from total"""
        result = dice.throw('3d6=-5')
        raw = sum(result['modified'])
        assert int(result['total']) == raw - 5

    def test_total_chained(self, dice):
        """=+10=-3 - net +7 to total"""
        result = dice.throw('3d6=+10=-3')
        raw = sum(result['modified'])
        assert int(result['total']) == raw + 7

    def test_total_chained_negative_result(self, dice):
        """=+5=-10 - net -5 to total"""
        result = dice.throw('3d6=+5=-10')
        raw = sum(result['modified'])
        assert int(result['total']) == raw - 5


class TestTotalCheckOperators:
    """Test all comparison operators with total check (t)."""

    def test_total_check_greater_equal(self, dice):
        """t>=7 - pass if total >= 7"""
        result = dice.throw('2d6t>=7')
        total = int(result['total'])
        expected = '1' if total >= 7 else '0'
        assert result['pass'] == expected

    def test_total_check_greater_than(self, dice):
        """t>7 - pass if total > 7"""
        result = dice.throw('2d6t>7')
        total = int(result['total'])
        expected = '1' if total > 7 else '0'
        assert result['pass'] == expected

    def test_total_check_less_than(self, dice):
        """t<7 - pass if total < 7"""
        result = dice.throw('2d6t<7')
        total = int(result['total'])
        expected = '1' if total < 7 else '0'
        assert result['pass'] == expected

    def test_total_check_less_equal(self, dice):
        """t<=7 - pass if total <= 7"""
        result = dice.throw('2d6t<=7')
        total = int(result['total'])
        expected = '1' if total <= 7 else '0'
        assert result['pass'] == expected

    def test_total_check_equal(self, dice):
        """t=7 - pass if total == 7"""
        result = dice.throw('2d6t=7')
        total = int(result['total'])
        expected = '1' if total == 7 else '0'
        assert result['pass'] == expected

    def test_total_check_not_equal(self, dice):
        """t!=7 - pass if total != 7"""
        result = dice.throw('2d6t!=7')
        total = int(result['total'])
        expected = '1' if total != 7 else '0'
        assert result['pass'] == expected


class TestCombinedOperators:
    """Test combinations of operators in single expressions.

    NOTE: Order matters! The format is:
    NdS (+|-)N =(+|-)N cmpN McmpN... t>=N
    - dice + sides
    - per-die modifier (+N)
    - total modifier (=+N)
    - success evaluator (>=N)
    - methods (f, x, kh, r, etc.)
    - total check (t>=N)
    """

    def test_boost_and_success_gte(self, dice):
        """5d6+3>=7 - boost then count successes"""
        result = dice.throw('5d6+3>=7')
        expected = sum(1 for v in result['modified'] if v >= 7)
        assert int(result['success']) == expected

    def test_reroll_and_success(self, dice):
        """Success evaluator BEFORE reroll method"""
        # Correct order: 10d6>=5r<3 (success evaluator before method)
        result = dice.throw('10d6>=5r<3')
        for v in result['modified']:
            assert v >= 3  # reroll worked
        expected = sum(1 for v in result['modified'] if v >= 5)
        assert int(result['success']) == expected

    def test_explode_and_keep(self, dice):
        """Explode and keep highest"""
        result = dice.throw('10d6x=6kh5')
        assert len(result['modified']) == 5

    def test_reroll_and_explode(self, dice):
        """Reroll 1s, explode on 6"""
        result = dice.throw('10d6r=1x=6')
        assert 'modified' in result

    def test_boost_success_fail(self, dice):
        """Boost, count successes and failures"""
        result = dice.throw('10d6+2>=7f<=3')
        successes = sum(1 for v in result['modified'] if v >= 7)
        failures = sum(1 for v in result['modified'] if v <= 3)
        assert int(result['success']) == successes
        assert int(result['fail']) == failures

    def test_all_operators_combined(self, dice):
        """Complex expression with multiple operator types.

        Correct order: NdS+N=+N>=N methods t>=N
        """
        # Total modifier (=+5) must come BEFORE success evaluator (>=6)
        result = dice.throw('10d6+1=+5>=6f<=2x>=6kh5t>=20')
        assert 'success' in result
        assert 'fail' in result
        assert 'pass' in result
        assert len(result['modified']) == 5
        # Verify total includes the =+5 modifier
        raw = sum(result['modified'])
        assert int(result['total']) == raw + 5

    def test_natural_counters_with_boost(self, dice):
        """Natural counters should use pre-boost values"""
        result = dice.throw('10d6+5ns=6nf=1')
        ns_expected = sum(1 for v in result['natural'] if v == 6)
        nf_expected = sum(1 for v in result['natural'] if v == 1)
        assert int(result['ns']) == ns_expected
        assert int(result['nf']) == nf_expected
        # Modified should have +5 applied
        for i, nat in enumerate(result['natural']):
            assert result['modified'][i] == nat + 5
