"""Tests for DiceProbability (AnyDice-style probability analyzer)."""
import pytest
from fractions import Fraction
from dice_roller.DiceProbability import DiceProbability


@pytest.fixture
def prob():
    return DiceProbability()


class TestBasicDistribution:
    """Basic distribution calculations."""

    def test_analyze_returns_dict(self, prob):
        result = prob.analyze('2d6')
        assert isinstance(result, dict)

    def test_analyze_has_required_keys(self, prob):
        result = prob.analyze('2d6')
        assert 'distribution' in result
        assert 'mean' in result
        assert 'std' in result
        assert 'min' in result
        assert 'max' in result
        assert 'mode' in result
        assert 'expression' in result

    def test_1d6_distribution(self, prob):
        result = prob.analyze('1d6')
        dist = result['distribution']
        # 1d6 should have 6 outcomes, each with 1/6 probability
        assert len(dist) == 6
        assert all(p == Fraction(1, 6) for p in dist.values())
        assert set(dist.keys()) == {1, 2, 3, 4, 5, 6}

    def test_2d6_distribution(self, prob):
        result = prob.analyze('2d6')
        dist = result['distribution']
        # 2d6 range is 2-12
        assert result['min'] == 2
        assert result['max'] == 12
        # 7 is most likely
        assert 7 in result['mode']
        # Sum of probabilities should be 1
        total = sum(dist.values())
        assert total == Fraction(1)

    def test_2d6_mean(self, prob):
        result = prob.analyze('2d6')
        assert result['mean'] == 7.0

    def test_2d6_mode_is_7(self, prob):
        result = prob.analyze('2d6')
        assert result['mode'] == [7]


class TestPerDieModifier:
    """Per-die modifier (+N) tests."""

    def test_perdie_positive(self, prob):
        result = prob.analyze('2d6+3')
        # Each die gets +3, so range shifts by 6 (2*3)
        assert result['min'] == 2 + 6
        assert result['max'] == 12 + 6
        # Mean shifts by 6
        assert result['mean'] == 13.0

    def test_perdie_negative(self, prob):
        result = prob.analyze('2d6-1')
        # Each die gets -1, so range shifts by -2
        assert result['min'] == 0
        assert result['max'] == 10
        assert result['mean'] == 5.0


class TestTotalModifier:
    """Total modifier (=+N) tests."""

    def test_total_positive(self, prob):
        result = prob.analyze('2d6=+5')
        # Only total shifts, not individual dice
        assert result['min'] == 7
        assert result['max'] == 17
        assert result['mean'] == 12.0

    def test_total_negative(self, prob):
        result = prob.analyze('2d6=-3')
        assert result['min'] == -1
        assert result['max'] == 9
        assert result['mean'] == 4.0

    def test_combined_perdie_and_total(self, prob):
        result = prob.analyze('2d6+2=+5')
        # Per-die: +2 each → +4 total shift
        # Total: +5 shift
        # Original 2d6: min=2, max=12, mean=7
        # After +2 per-die: min=6, max=16, mean=11
        # After +5 total: min=11, max=21, mean=16
        assert result['min'] == 11
        assert result['max'] == 21
        assert result['mean'] == 16.0


class TestKeepDrop:
    """Keep and drop mechanics."""

    def test_keep_high_reduces_count(self, prob):
        result = prob.analyze('4d6kh3')
        # 4d6kh3: keep 3 highest
        # Min is 3 (three 1s), max is 18 (three 6s)
        assert result['min'] == 3
        assert result['max'] == 18

    def test_keep_high_mean(self, prob):
        result = prob.analyze('4d6kh3')
        # Known value for 4d6 drop lowest
        assert 12.0 < result['mean'] < 13.0

    def test_drop_low_equals_keep_high(self, prob):
        kh = prob.analyze('4d6kh3')
        dl = prob.analyze('4d6dl1')
        # 4d6kh3 == 4d6dl1
        assert kh['mean'] == dl['mean']
        assert kh['distribution'] == dl['distribution']

    def test_keep_low(self, prob):
        result = prob.analyze('4d6kl2')
        # Keep 2 lowest
        assert result['min'] == 2  # Two 1s
        assert result['max'] == 12  # Two 6s

    def test_drop_high(self, prob):
        result = prob.analyze('4d6dh2')
        # Drop 2 highest = keep 2 lowest
        kl = prob.analyze('4d6kl2')
        assert result['mean'] == kl['mean']


class TestSuccessDistribution:
    """Success counting distribution."""

    def test_success_distribution_present(self, prob):
        result = prob.analyze('10d6>=5')
        assert 'success_distribution' in result

    def test_success_distribution_range(self, prob):
        result = prob.analyze('10d6>=5')
        dist = result['success_distribution']
        # 0 to 10 successes possible
        assert min(dist.keys()) == 0
        assert max(dist.keys()) == 10

    def test_success_probabilities_sum_to_one(self, prob):
        result = prob.analyze('10d6>=5')
        dist = result['success_distribution']
        total = sum(dist.values())
        assert total == Fraction(1)

    def test_success_with_perdie_modifier(self, prob):
        result = prob.analyze('5d6+2>=7')
        dist = result['success_distribution']
        # With +2, values are 3-8, so >=7 means natural 5,6 only
        # Still 2/6 chance per die
        assert 'success_distribution' in result


class TestTotalCheck:
    """Total check (t>=N) probability."""

    def test_pass_probability_present(self, prob):
        result = prob.analyze('2d6t>=7')
        assert 'pass_probability' in result

    def test_pass_probability_always_true(self, prob):
        result = prob.analyze('2d6t>=2')
        # 2d6 always >= 2
        assert result['pass_probability'] == Fraction(1)

    def test_pass_probability_always_false(self, prob):
        result = prob.analyze('2d6t>=13')
        # 2d6 max is 12, never >= 13
        assert result['pass_probability'] == Fraction(0)

    def test_pass_probability_2d6_gte_7(self, prob):
        result = prob.analyze('2d6t>=7')
        # P(2d6 >= 7) = 21/36 = 7/12
        assert result['pass_probability'] == Fraction(21, 36)

    def test_pass_with_total_modifier(self, prob):
        result = prob.analyze('2d6=+5t>=12')
        # Same as P(2d6 >= 7) since +5 shifts threshold
        assert result['pass_probability'] == Fraction(21, 36)


class TestCustomFaces:
    """Custom dice faces."""

    def test_fate_dice(self, prob):
        result = prob.analyze('4d{-1,0,1}')
        # 4dF: range -4 to +4, mean 0
        assert result['min'] == -4
        assert result['max'] == 4
        assert result['mean'] == 0.0

    def test_fate_dice_mode_is_zero(self, prob):
        result = prob.analyze('4d{-1,0,1}')
        assert result['mode'] == [0]

    def test_custom_integer_faces(self, prob):
        result = prob.analyze('2d{2,4,6}')
        # Faces are 2,4,6
        # Range: 4 to 12
        assert result['min'] == 4
        assert result['max'] == 12


class TestErrorHandling:
    """Error handling for unsupported features."""

    def test_exploding_raises_error(self, prob):
        with pytest.raises(ValueError, match="Exploding"):
            prob.analyze('5d6x=6')

    def test_reroll_raises_error(self, prob):
        with pytest.raises(ValueError, match="Exploding"):
            prob.analyze('5d6r<3')

    def test_string_faces_raises_error(self, prob):
        with pytest.raises(ValueError, match="numeric"):
            prob.analyze('4d{a,b,c}')


class TestMonteCarlo:
    """Monte Carlo fallback for complex expressions."""

    def test_monte_carlo_returns_dict(self, prob):
        result = prob.monte_carlo('5d6', samples=1000)
        assert isinstance(result, dict)

    def test_monte_carlo_has_samples_count(self, prob):
        result = prob.monte_carlo('5d6', samples=500)
        assert result['samples'] == 500

    def test_monte_carlo_has_method_marker(self, prob):
        result = prob.monte_carlo('5d6', samples=100)
        assert result['method'] == 'monte_carlo'

    def test_monte_carlo_works_with_exploding(self, prob):
        # Should not raise error
        result = prob.monte_carlo('5d6x=6', samples=100)
        assert 'mean' in result


class TestFormatDistribution:
    """Output formatting."""

    def test_format_returns_string(self, prob):
        stats = prob.analyze('2d6')
        output = prob.format_distribution(stats)
        assert isinstance(output, str)

    def test_format_contains_expression(self, prob):
        stats = prob.analyze('2d6')
        output = prob.format_distribution(stats)
        assert '2d6' in output

    def test_format_contains_mean(self, prob):
        stats = prob.analyze('2d6')
        output = prob.format_distribution(stats)
        assert '7.00' in output


class TestStatistics:
    """Statistical measures."""

    def test_percentiles_present(self, prob):
        result = prob.analyze('2d6')
        assert 'percentiles' in result
        assert 25 in result['percentiles']
        assert 50 in result['percentiles']
        assert 75 in result['percentiles']

    def test_median_equals_50th_percentile(self, prob):
        result = prob.analyze('2d6')
        assert result['median'] == result['percentiles'][50]

    def test_std_is_positive(self, prob):
        result = prob.analyze('2d6')
        assert result['std'] > 0
