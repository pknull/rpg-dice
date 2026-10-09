from fractions import Fraction
from collections import Counter
from math import factorial, sqrt
from dice_roller import exact as exact_engine
from dice_roller.DiceParser import DiceParser
from dice_roller.DiceThrower import DiceThrower
from dice_roller.safe_compare import safe_compare


class DiceProbability:
    """
    AnyDice-style probability analyzer for dice expressions.

    exact() returns the joint distribution of every roll-result field with
    Fraction probabilities (see dice_roller.exact).  analyze() summarises it.
    """

    def __init__(self):
        self.parser = DiceParser()

    def exact(self, dexp, explode_depth=exact_engine.DEFAULT_EXPLODE_DEPTH, faces=False,
              faces_limit=exact_engine.DEFAULT_FACES_LIMIT):
        """Exact joint distribution over (total, success, fail, ns, nf, pass).

        Returns a dice_roller.exact.ExactResult.  Raises DiceException for a
        malformed expression.
        """
        return exact_engine.exact(dexp, explode_depth=explode_depth, faces=faces,
                                  faces_limit=faces_limit)

    def analyze(self, dexp, explode_depth=exact_engine.DEFAULT_EXPLODE_DEPTH):
        """
        Analyze a dice expression and return probability distribution + statistics.

        Returns dict with:
            - distribution: {value: probability} as Fractions
            - mean: expected value
            - std: standard deviation
            - min/max: range
            - percentiles: 25th, 50th (median), 75th
            - mode: most likely value(s)
            - expression: original expression
            - success_distribution (and fail/ns/nf_distribution when counted)
            - pass_probability when the expression has a total check
            - joint: the full exact joint distribution
            - unresolved: probability of explosion chains deeper than explode_depth;
              every other figure covers only the resolved outcomes
        """
        result = self.exact(dexp, explode_depth=explode_depth)
        if None in result.marginal('success'):
            raise ValueError("Probability analysis only supports numeric dice faces.")

        dist = result.marginal('total')
        stats = self._calculate_stats(dist)
        stats['expression'] = dexp
        stats['distribution'] = dist
        stats['joint'] = result.joint
        stats['unresolved'] = result.unresolved
        stats['success_distribution'] = result.marginal('success')
        for field in ('fail', 'ns', 'nf'):
            marginal = result.marginal(field)
            if None not in marginal:
                stats[field + '_distribution'] = marginal
        passes = result.marginal('pass')
        if None not in passes:
            stats['pass_probability'] = passes.get(1, Fraction(0))
        return stats

    def _calculate_stats(self, dist):
        """Calculate statistical measures from distribution."""
        if not dist:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'mode': [0]}

        # Mean
        mean = sum(v * float(p) for v, p in dist.items())

        # Variance and std
        variance = sum(((v - mean) ** 2) * float(p) for v, p in dist.items())
        std = sqrt(variance)

        # Min/Max
        min_val = min(dist.keys())
        max_val = max(dist.keys())

        # Mode (most likely values)
        max_prob = max(dist.values())
        mode = [v for v, p in dist.items() if p == max_prob]

        # Percentiles (25th, 50th, 75th)
        sorted_vals = sorted(dist.keys())
        cumulative = Fraction(0)
        percentiles = {}
        targets = [(25, None), (50, None), (75, None)]

        for v in sorted_vals:
            cumulative += dist[v]
            for i, (pct, val) in enumerate(targets):
                if val is None and cumulative >= Fraction(pct, 100):
                    targets[i] = (pct, v)

        percentiles = {t[0]: t[1] for t in targets}

        return {
            'mean': round(mean, 2),
            'std': round(std, 2),
            'min': min_val,
            'max': max_val,
            'mode': mode,
            'median': percentiles.get(50, min_val),
            'percentiles': percentiles
        }

    def format_distribution(self, stats, width=60):
        """Format distribution as AnyDice-style ASCII histogram."""
        dist = stats['distribution']
        if not dist:
            return "Empty distribution"

        lines = []
        lines.append(f"Expression: {stats['expression']}")
        lines.append(f"Mean: {stats['mean']:.2f}  Std: {stats['std']:.2f}")
        lines.append(f"Range: {stats['min']} to {stats['max']}  Mode: {stats['mode']}")
        lines.append("")

        max_prob = max(float(p) for p in dist.values())

        for val in sorted(dist.keys()):
            prob = dist[val]
            pct = float(prob) * 100
            bar_len = int((float(prob) / max_prob) * (width - 20))
            bar = '#' * bar_len
            lines.append(f"{str(val):>4}: {pct:5.2f}% {bar}")

        return '\n'.join(lines)

    def monte_carlo(self, dexp, samples=100000):
        """
        Monte Carlo analysis for complex expressions (exploding, reroll, etc).
        Returns same format as analyze() but with approximate probabilities.
        """
        dice = DiceThrower()
        results = Counter()

        for _ in range(samples):
            result = dice.throw(dexp)
            total = Fraction(result['total'])
            results[total.numerator if total.denominator == 1 else total] += 1

        # Convert to probability distribution
        dist = {v: Fraction(count, samples) for v, count in results.items()}

        stats = self._calculate_stats(dist)
        stats['expression'] = dexp
        stats['distribution'] = dist
        stats['samples'] = samples
        stats['method'] = 'monte_carlo'

        return stats

    # Legacy methods for backwards compatibility
    def calcThrow(self, dexp='1d1', target=2):
        """Legacy method - use analyze() instead."""
        stats = self.analyze(dexp)
        success_dist = stats.get('success_distribution', {})

        print('---- Distribution')
        print(self.format_distribution(stats))
        print(f'\n---- P(successes >= {target})')
        prob = sum(p for k, p in success_dist.items() if k >= target)
        print(f'{float(prob) * 100:.2f}%')

    def bruteThrow(self, dexp='1d1', target=2):
        """Legacy method - use analyze() instead."""
        self.calcThrow(dexp, target)

    def statThrow(self, dexp='1d1', target=2, pool=100000):
        """Legacy method - use monte_carlo() instead."""
        stats = self.monte_carlo(dexp, pool)
        print('---- Monte Carlo Distribution')
        print(self.format_distribution(stats))

    def calc(self, op, val, space):
        """Subset of sample space for which a condition is true."""
        return {element for element in space if safe_compare(element, op, val)}

    def binomial(self, x, y):
        try:
            binom = factorial(x) // factorial(y) // factorial(x - y)
        except ValueError:
            binom = 0
        return binom

    def exact_hit_chance(self, n, k, p):
        """Return the probability of exactly k hits from n dice"""
        return self.binomial(n, k) * (p) ** k * (1 - p) ** (n - k)

    def hit_chance(self, n, k, p):
        """Return the probability of at least k hits from n dice"""
        return sum([self.exact_hit_chance(n, x, p) for x in range(k, n + 1)])
