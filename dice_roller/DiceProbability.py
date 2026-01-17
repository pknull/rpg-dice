from fractions import Fraction
from decimal import Decimal
from collections import Counter
import itertools as it
from math import factorial, sqrt
from dice_roller.DiceParser import DiceParser
from dice_roller.DiceThrower import DiceThrower
from dice_roller.safe_compare import safe_compare


class DiceProbability:
    """
    AnyDice-style probability analyzer for dice expressions.

    Supports: NdX, +N (per-die), =+N (total), >=N (success), kh/kl/dh/dl, t>=N
    Excludes: exploding (x), reroll (r/ro) - use Monte Carlo for these
    """

    def __init__(self):
        self.parser = DiceParser()

    def analyze(self, dexp):
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
        """
        parsed = self.parser.parse_input(dexp)

        # Check for unsupported modifiers
        if 'x' in parsed or 'r' in parsed:
            raise ValueError("Exploding/reroll not supported in exact analysis. Use monte_carlo() instead.")

        if parsed['types'] != 'int':
            raise ValueError("Probability analysis only supports numeric dice faces.")

        # Get base distribution
        dist = self._base_distribution(parsed)

        # Apply keep/drop if present
        if 'k' in parsed or 'd' in parsed:
            dist = self._apply_keep_drop(parsed, dist)

        # Apply per-die modifier (+N) - already in modified values for keep/drop
        # For basic rolls without keep/drop, apply here
        if 'k' not in parsed and 'd' not in parsed:
            if 'b' in parsed and parsed['b']['val'] != '0':
                dist = self._apply_per_die_modifier(parsed, dist)

        # Apply total modifier (=+N)
        if 'l' in parsed and parsed['l']['val'] != '0':
            dist = self._apply_total_modifier(parsed['l'], dist)

        # Calculate statistics
        stats = self._calculate_stats(dist)
        stats['expression'] = dexp
        stats['distribution'] = dist

        # Add success probability if threshold specified
        if 's' in parsed and parsed['s']['val'] is not None:
            stats['success_distribution'] = self._success_distribution(parsed, dist)

        # Add pass/fail for total check
        if 't' in parsed:
            stats['pass_probability'] = self._total_check_probability(parsed['t'], dist)

        return stats

    def _base_distribution(self, parsed):
        """Calculate base distribution for NdX (uniform dice)."""
        n = int(parsed['number_of_dice'])
        sides = parsed['sides']  # Already a list like [1,2,3,4,5,6]

        # Start with single die distribution (uniform)
        single_die = {face: Fraction(1, len(sides)) for face in sides}

        # Convolve n times for n dice sum
        dist = single_die
        for _ in range(n - 1):
            dist = self._convolve(dist, single_die)

        return dist

    def _convolve(self, dist1, dist2):
        """Convolve two distributions (sum of independent random variables)."""
        result = {}
        for v1, p1 in dist1.items():
            for v2, p2 in dist2.items():
                total = v1 + v2
                result[total] = result.get(total, Fraction(0)) + p1 * p2
        return result

    def _apply_per_die_modifier(self, parsed, dist):
        """Apply per-die modifier to shift distribution."""
        n = int(parsed['number_of_dice'])
        mod = int(parsed['b']['val'])
        if parsed['b']['operator'] == '-':
            mod = -mod

        # Total shift is n * mod
        total_shift = n * mod
        return {v + total_shift: p for v, p in dist.items()}

    def _apply_total_modifier(self, modifier, dist):
        """Apply total modifier (=+N or =-N)."""
        mod = int(modifier['val'])
        if modifier['operator'] == '-':
            mod = -mod
        return {v + mod: p for v, p in dist.items()}

    def _apply_keep_drop(self, parsed, base_dist):
        """
        Apply keep/drop using order statistics.
        This requires enumerating combinations for exact calculation.
        """
        n = int(parsed['number_of_dice'])
        sides = parsed['sides']

        # Per-die modifier
        per_die_mod = 0
        if 'b' in parsed and parsed['b']['val'] != '0':
            per_die_mod = int(parsed['b']['val'])
            if parsed['b']['operator'] == '-':
                per_die_mod = -per_die_mod

        # Determine how many to keep
        if 'k' in parsed:
            keep_n = int(parsed['k']['val'])
            keep_high = parsed['k']['layer'] == 'high'
        elif 'd' in parsed:
            drop_n = int(parsed['d']['val'])
            keep_n = n - drop_n
            keep_high = parsed['d']['layer'] == 'low'  # drop high = keep low
        else:
            return base_dist

        if keep_n <= 0:
            return {0: Fraction(1)}
        if keep_n >= n:
            # No filtering, but apply per-die mod
            if per_die_mod != 0:
                return self._apply_per_die_modifier(parsed, base_dist)
            return base_dist

        # Enumerate all combinations
        dist = {}
        total_outcomes = len(sides) ** n

        for roll in it.product(sides, repeat=n):
            sorted_roll = sorted(roll, reverse=keep_high)
            kept = sorted_roll[:keep_n]
            # Apply per-die modifier
            total = sum(v + per_die_mod for v in kept)
            dist[total] = dist.get(total, Fraction(0)) + Fraction(1, total_outcomes)

        return dist

    def _success_distribution(self, parsed, total_dist):
        """
        Calculate distribution of success counts.
        Returns {num_successes: probability}
        """
        n = int(parsed['number_of_dice'])
        sides = parsed['sides']

        # Per-die modifier
        per_die_mod = 0
        if 'b' in parsed and parsed['b']['val'] != '0':
            per_die_mod = int(parsed['b']['val'])
            if parsed['b']['operator'] == '-':
                per_die_mod = -per_die_mod

        # Success threshold
        s_op = parsed['s']['operator']
        s_val = int(parsed['s']['val'])

        # Count successes per die face (after per-die mod)
        success_faces = sum(1 for face in sides
                          if safe_compare(face + per_die_mod, s_op, s_val))

        # If keep/drop, enumerate
        if 'k' in parsed or 'd' in parsed:
            return self._success_with_keep_drop(parsed)

        # Binomial distribution for success count
        p = Fraction(success_faces, len(sides))
        dist = {}
        for k in range(n + 1):
            prob = self._binomial_prob(n, k, p)
            if prob > 0:
                dist[k] = prob
        return dist

    def _success_with_keep_drop(self, parsed):
        """Calculate success distribution with keep/drop (enumeration)."""
        n = int(parsed['number_of_dice'])
        sides = parsed['sides']

        per_die_mod = 0
        if 'b' in parsed and parsed['b']['val'] != '0':
            per_die_mod = int(parsed['b']['val'])
            if parsed['b']['operator'] == '-':
                per_die_mod = -per_die_mod

        s_op = parsed['s']['operator']
        s_val = int(parsed['s']['val'])

        if 'k' in parsed:
            keep_n = int(parsed['k']['val'])
            keep_high = parsed['k']['layer'] == 'high'
        else:
            drop_n = int(parsed['d']['val'])
            keep_n = n - drop_n
            keep_high = parsed['d']['layer'] == 'low'

        dist = {}
        total_outcomes = len(sides) ** n

        for roll in it.product(sides, repeat=n):
            sorted_roll = sorted(roll, reverse=keep_high)
            kept = sorted_roll[:keep_n]
            successes = sum(1 for v in kept
                          if safe_compare(v + per_die_mod, s_op, s_val))
            dist[successes] = dist.get(successes, Fraction(0)) + Fraction(1, total_outcomes)

        return dist

    def _total_check_probability(self, t_parsed, dist):
        """Calculate probability of passing total check."""
        t_op = t_parsed['operator']
        t_val = int(t_parsed['val'])

        pass_prob = Fraction(0)
        for total, prob in dist.items():
            if safe_compare(total, t_op, t_val):
                pass_prob += prob

        return pass_prob

    def _binomial_prob(self, n, k, p):
        """Binomial probability: P(X=k) for n trials with probability p."""
        if k < 0 or k > n:
            return Fraction(0)
        coeff = self._binomial_coeff(n, k)
        return coeff * (p ** k) * ((1 - p) ** (n - k))

    def _binomial_coeff(self, n, k):
        """Calculate binomial coefficient (n choose k)."""
        if k < 0 or k > n:
            return 0
        return factorial(n) // (factorial(k) * factorial(n - k))

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
            lines.append(f"{val:4d}: {pct:5.2f}% {bar}")

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
            total = int(result['total'])
            results[total] += 1

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
