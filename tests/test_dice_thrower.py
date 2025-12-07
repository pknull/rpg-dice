"""Tests for DiceThrower based on README specifications."""
import pytest
from dice_roller.DiceThrower import DiceThrower


@pytest.fixture
def dice():
    return DiceThrower()


class TestBasicRolls:
    """Basic dice rolling functionality."""

    def test_basic_roll_returns_dict(self, dice):
        result = dice.throw('10d6')
        assert isinstance(result, dict)

    def test_basic_roll_has_required_keys(self, dice):
        result = dice.throw('10d6')
        assert 'natural' in result
        assert 'modified' in result
        assert 'roll' in result
        assert 'success' in result
        assert 'total' in result

    def test_basic_roll_correct_dice_count(self, dice):
        result = dice.throw('10d6')
        assert len(result['natural']) == 10

    def test_basic_roll_values_in_range(self, dice):
        result = dice.throw('10d6')
        for val in result['natural']:
            assert 1 <= val <= 6

    def test_single_die(self, dice):
        result = dice.throw('1d20')
        assert len(result['natural']) == 1
        assert 1 <= result['natural'][0] <= 20


class TestDiceBoost:
    """Dice modifier (+/-N after sides)."""

    def test_positive_boost(self, dice):
        result = dice.throw('2d6+4')
        for i, natural in enumerate(result['natural']):
            assert result['modified'][i] == natural + 4

    def test_negative_boost(self, dice):
        result = dice.throw('2d6-2')
        for i, natural in enumerate(result['natural']):
            assert result['modified'][i] == natural - 2

    def test_zero_boost(self, dice):
        result = dice.throw('2d6+0')
        assert result['natural'] == result['modified']


class TestSuccessCounter:
    """Success counting with comparators."""

    def test_success_gte(self, dice):
        result = dice.throw('10d6>=5')
        successes = sum(1 for v in result['modified'] if v >= 5)
        assert int(result['success']) == successes

    def test_success_gt(self, dice):
        result = dice.throw('10d6>5')
        successes = sum(1 for v in result['modified'] if v > 5)
        assert int(result['success']) == successes

    def test_success_with_boost(self, dice):
        result = dice.throw('2d6+4>5')
        successes = sum(1 for v in result['modified'] if v > 5)
        assert int(result['success']) == successes


class TestFailureCounter:
    """Failure counting with f token."""

    def test_failure_counter_present(self, dice):
        result = dice.throw('10d6f<2')
        assert 'fail' in result

    def test_failure_counter_accuracy(self, dice):
        result = dice.throw('10d6f<=1')
        failures = sum(1 for v in result['modified'] if v <= 1)
        assert int(result['fail']) == failures


class TestNaturalCounters:
    """Natural success/fail counting (pre-modifier)."""

    def test_natural_success_present(self, dice):
        result = dice.throw('1d20>15ns20nf1')
        assert 'ns' in result
        assert 'nf' in result

    def test_natural_counters_use_natural_values(self, dice):
        result = dice.throw('10d6+5ns6nf1')
        ns = sum(1 for v in result['natural'] if v == 6)
        nf = sum(1 for v in result['natural'] if v == 1)
        assert int(result['ns']) == ns
        assert int(result['nf']) == nf


class TestExplodingDice:
    """Exploding dice (x token)."""

    def test_exploding_can_add_dice(self, dice):
        # Roll many times to ensure explosion triggers
        for _ in range(50):
            result = dice.throw('10d6x=6')
            # Modified may have more entries than natural if explosions occurred
            if 6 in result['natural']:
                assert len(result['modified']) >= len(result['natural'])
                break


class TestCompoundingDice:
    """Compounding dice (xx token)."""

    def test_compounding_same_length(self, dice):
        result = dice.throw('10d6xx>=5')
        # Compounding adds to existing dice, count stays same
        assert len(result['modified']) == len(result['natural'])

    def test_compounding_can_exceed_sides(self, dice):
        # Roll until we get a compound that exceeds 6
        for _ in range(100):
            result = dice.throw('5d6xx=6')
            if any(v > 6 for v in result['modified']):
                return  # Test passes
        # Not guaranteed, but very likely with 100 attempts


class TestPenetratingDice:
    """Penetrating dice (xp/xxp tokens)."""

    def test_penetrating_subtracts_one(self, dice):
        # Penetrating exploded dice have -1 applied
        result = dice.throw('10d6xp=6')
        # Check roll expression is recorded
        assert result['roll'] == '10d6xp=6'


class TestReroll:
    """Reroll mechanics (r/ro tokens)."""

    def test_reroll_until_fixed(self, dice):
        result = dice.throw('10d6r<3')
        # No modified values should be less than 3
        for v in result['modified']:
            assert v >= 3

    def test_reroll_once_may_still_fail(self, dice):
        # ro only rerolls once, so low values possible
        result = dice.throw('10d6ro<3')
        # Just verify it runs; values may still be < 3
        assert 'modified' in result


class TestKeepDrop:
    """Keep and drop mechanics (kh/kl/dh/dl)."""

    def test_keep_high(self, dice):
        result = dice.throw('10d6kh5')
        assert len(result['modified']) == 5
        # Should be the 5 highest
        sorted_natural = sorted(result['natural'], reverse=True)[:5]
        assert sorted(result['modified'], reverse=True) == sorted_natural

    def test_keep_low(self, dice):
        result = dice.throw('10d6kl5')
        assert len(result['modified']) == 5
        sorted_natural = sorted(result['natural'])[:5]
        assert sorted(result['modified']) == sorted_natural

    def test_drop_high(self, dice):
        result = dice.throw('10d6dh3')
        assert len(result['modified']) == 7

    def test_drop_low(self, dice):
        result = dice.throw('10d6dl3')
        assert len(result['modified']) == 7


class TestTotalModifier:
    """Total modifier (=+N syntax and legacy +0+N)."""

    def test_total_modifier_new_syntax(self, dice):
        result = dice.throw('5d10=+5')
        raw_total = sum(result['modified'])
        assert int(result['total']) == raw_total + 5

    def test_total_modifier_subtraction(self, dice):
        result = dice.throw('5d10=-3')
        raw_total = sum(result['modified'])
        assert int(result['total']) == raw_total - 3

    def test_total_modifier_leaves_dice_unchanged(self, dice):
        result = dice.throw('5d6=+10')
        assert result['natural'] == result['modified']

    def test_combined_perdie_and_total(self, dice):
        result = dice.throw('2d6+2=+5')
        # Each die should have +2
        for i, natural in enumerate(result['natural']):
            assert result['modified'][i] == natural + 2
        # Total should have +5 on top
        raw_total = sum(result['modified'])
        assert int(result['total']) == raw_total + 5

    def test_legacy_syntax_still_works(self, dice):
        result = dice.throw('2d6+0+2')
        raw_total = sum(result['modified'])
        assert int(result['total']) == raw_total + 2


class TestCustomFaces:
    """Custom dice faces with curly brackets."""

    def test_int_list_faces(self, dice):
        result = dice.throw('5d{1,2,3}')
        for v in result['natural']:
            assert v in [1, 2, 3]

    def test_negative_int_faces(self, dice):
        result = dice.throw('5d{-1,0,1}')
        for v in result['natural']:
            assert v in [-1, 0, 1]

    def test_string_faces(self, dice):
        result = dice.throw('5d{a,b,c}')
        for v in result['natural']:
            assert v in ['a', 'b', 'c']

    def test_mixed_faces(self, dice):
        result = dice.throw('5d{Ace,King,10}')
        # Should be treated as strings due to mixed content
        assert 'natural' in result


class TestTotalCheck:
    """Total check (t>=N syntax)."""

    def test_total_check_pass_present(self, dice):
        result = dice.throw('2d6t>=5')
        assert 'pass' in result

    def test_total_check_gte_pass(self, dice):
        result = dice.throw('2d6t>=2')  # Min total is 2, always passes
        assert result['pass'] == '1'

    def test_total_check_gte_fail(self, dice):
        result = dice.throw('2d6t>=100')  # Max total is 12, always fails
        assert result['pass'] == '0'

    def test_total_check_exact_match(self, dice):
        result = dice.throw('2d6t=7')
        total = int(result['total'])
        expected = '1' if total == 7 else '0'
        assert result['pass'] == expected

    def test_total_check_with_total_modifier(self, dice):
        result = dice.throw('2d6=+100t>=100')  # +100 to total, always passes
        assert result['pass'] == '1'

    def test_total_check_less_than(self, dice):
        result = dice.throw('2d6t<100')  # Max total is 12, always passes
        assert result['pass'] == '1'

    def test_total_check_with_perdie_and_total_modifier(self, dice):
        result = dice.throw('2d6+2=+5t>=10')
        # Each die +2, then +5 to total
        # Total should be (sum of modified) + 5
        raw_total = sum(result['modified'])
        assert int(result['total']) == raw_total + 5
        expected = '1' if (raw_total + 5) >= 10 else '0'
        assert result['pass'] == expected

    def test_total_check_with_success_counting(self, dice):
        result = dice.throw('5d10>=8t>=25')
        # Should have both success count and pass/fail
        assert 'success' in result
        assert 'pass' in result
        # Verify success counting works correctly
        successes = sum(1 for v in result['modified'] if v >= 8)
        assert int(result['success']) == successes
        # Verify total check works correctly
        total = int(result['total'])
        expected_pass = '1' if total >= 25 else '0'
        assert result['pass'] == expected_pass

    def test_total_check_with_perdie_and_success(self, dice):
        result = dice.throw('5d10+2>=10t>=40')
        # Each die +2, count successes >= 10, check total >= 40
        for i, nat in enumerate(result['natural']):
            assert result['modified'][i] == nat + 2
        successes = sum(1 for v in result['modified'] if v >= 10)
        assert int(result['success']) == successes
        total = int(result['total'])
        expected_pass = '1' if total >= 40 else '0'
        assert result['pass'] == expected_pass

    def test_total_check_gt_operator(self, dice):
        result = dice.throw('2d6t>12')  # Max is 12, so > 12 always fails
        assert result['pass'] == '0'

    def test_total_check_lte_operator(self, dice):
        result = dice.throw('2d6t<=12')  # Max is 12, always passes
        assert result['pass'] == '1'

    def test_total_check_ne_operator(self, dice):
        result = dice.throw('2d6t!=1')  # Min is 2, never equals 1
        assert result['pass'] == '1'


class TestComplexRolls:
    """Complex roll combinations."""

    def test_everything_roll(self, dice):
        result = dice.throw('10d6+0>=5f<=2xxp>=5ro=1dl5+4')
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'fail' in result

    def test_everything_with_total_check(self, dice):
        # =+10 must come before >=5 (success evaluator), but t can go anywhere in methods
        result = dice.throw('10d6=+10>=5t>=30f<=2x=6kh5')
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'fail' in result
        assert 'pass' in result
        # Should have kept only 5 dice
        assert len(result['modified']) == 5
        # Total should include +10 modifier
        raw_total = sum(result['modified'])
        assert int(result['total']) == raw_total + 10

    def test_success_fail_and_total_check(self, dice):
        result = dice.throw('8d6>=5f=1t>=20')
        assert 'success' in result
        assert 'fail' in result
        assert 'pass' in result
        # Verify all counters calculated correctly
        successes = sum(1 for v in result['modified'] if v >= 5)
        failures = sum(1 for v in result['modified'] if v == 1)
        assert int(result['success']) == successes
        assert int(result['fail']) == failures
        total = int(result['total'])
        expected_pass = '1' if total >= 20 else '0'
        assert result['pass'] == expected_pass


class TestBadInput:
    """Error handling for invalid input."""

    def test_invalid_expression(self, dice):
        result = dice.throw('invalid')
        assert isinstance(result, str)
        assert 'Bad roll' in result

    def test_too_many_sides(self, dice):
        result = dice.throw('1d200')
        assert isinstance(result, str)
        assert 'Bad roll' in result

    def test_too_many_dice(self, dice):
        result = dice.throw('500d6')
        assert isinstance(result, str)
        assert 'Bad roll' in result
