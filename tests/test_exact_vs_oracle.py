"""The exact engine against the replay oracle and against seeded sampling.

Replay (tests/oracle.py) walks every face sequence through the real roller, so
agreement here means the engine reproduces the roller's semantics.  Where
explosions or reroll-until loops make sequences unbounded, both sides are
truncated: the engine per die (``explode_depth``), the replay per throw
(``max_draws``).  Each reported probability is then a lower bound on the true
one, so the two may differ by at most the other side's unresolved mass.
"""
import math
import random
from fractions import Fraction

import pytest

from dice_roller.DiceProbability import DiceProbability
from dice_roller.DiceThrower import DiceThrower
from tests.oracle import faces_of, outcome_of, replay_distribution

EXACT_CASES = [
    # plain pools, per-die arithmetic, custom faces
    '3d6', '2d6+3', '2d6-1', '3d4*2', '3d4/2', '2d{1,1,2}', '3d{-1,0,1}', '2d{2,4,6}+1',
    '2d6>=5f<=2ns6nf1', '3d6<3', '3d6!=1', '3d6=6', '2d6+2>=6kh1t>=5', '2d6>=5>=7',
    '2d6kh1>=5', '3d6=+10=-3t>=15', '2d6t!=7', '3d4s>=3', '2d4ns', '2d4nf<=2', '2d4f',
    # keep and drop, including both and out-of-range counts
    '3d6kh2', '3d6kl2', '4d4dh1', '4d4dl2', '4d4kh3dl1', '4d4kl3dh1', '4d4kh3dh1',
    '4d4kl3dl1', '3d6kh5', '3d6dl5', '3d6kh0', '3d4k', '3d4d', '3d4+1>=4kh2f<=2ns4nf1',
    '3d{-1,0,1}kh2', '3d4/2kh2>=1', '2d{-2,-1}/2=+1d2>1d2kh1', '3d{-1,0,1}k',
    # rerolls
    '2d6ro<3', '2d6ro>=5nf1', '2d6>=5ro=1ns1kh1', '3d4ro1kh2', '2d4ro!=4',
    # subrolls
    '2d6>=1d6', '3d4kh1d3', '2d6=+1d4=-1d2', '2d4t>=1d8', '2d4f<=1d2ns>=1d4',
    # groups and arithmetic
    '(1d4>=3)+(1d6>=5)', '(1d4)+(1d6)', '1d4+1d6', '1d6-1d4', '(1d6+1d4)*2', '2*(1d4)',
    '(1d6)/2', '(2d4)=+1t>=6', '((1d4)+(1d6))kh1', '((1d4)+(1d6))>=4',
    '((1d4>=4)+(1d6>=6))kh1', '((1d4>=3)+(1d4>=4))kh1', '((1d4>=3)+(1d4>=4))kl1',
    '((2d4kh1)+(1d6))kl1', '(1d6)+3', '1d6+1d4+2', '(1d4ns4)+(1d4nf1)',
    '((1d4)+(1d4))ns>=3', '(1d4f<=1)+(1d6)', '(2d{a,b})+(1d4)', '((1d4)+(1d4))dl1',
    '((1d4)+(2d4))kh2dl1', '(1d4)=+1+(1d4)=-1', '((1d4)+(1d4))=+2t>=6', '5+1d4',
    '((1d4)+((1d4)+(1d4)))kh1>=4', '(1d4>=2)*3', '1d4-(1d4)',
    # string faces and zero dice
    '2d{a,b,c}', '2d{Ace,10}', '0d6', '0d6>=6', '0d6kh1', '(0d6)+(1d4)', '0d6t>=0',
]

TRUNCATED_CASES = [
    # (expression, engine explode_depth, replay max_draws)
    ('2d6r<3', 8, 9), ('2d6>=5r=1ns1', 8, 9), ('2d4r>=3', 8, 11), ('3d4r1kh2', 8, 10),
    ('2d4x4', 6, 10), ('2d4xx4', 6, 10), ('2d4xp4', 6, 10), ('2d4xxp4', 6, 10),
    ('1d6x>=5', 8, 9), ('2d4x=4ns4nf1', 6, 10), ('2d4r1x4', 6, 10), ('1d4x<2', 8, 9),
    ('2d4+1x>=5', 6, 10), ('2d4>=4x4f1', 6, 10), ('2d4x=1d4', 6, 10),
    ('((1d4xx)+(1d4xx))kh1', 6, 10), ('1d4xx4kh1', 8, 9), ('(1d4x4)+(1d4)', 6, 10),
    ('2d4xp>=3t>=6', 6, 10), ('1d4xxp>=3>=5', 8, 9), ('2d4x4kh1', 6, 10),
    ('3d4x4kh2>=4', 4, 10), ('2d4x4dl1ns4', 6, 10), ('2d4xp4kl1', 6, 10),
]


def exact(expression, **kwargs):
    return DiceProbability().exact(expression, **kwargs)


@pytest.mark.parametrize('expression', EXACT_CASES)
def test_engine_equals_replay(expression):
    oracle, truncated = replay_distribution(expression, max_draws=12)
    assert truncated == 0
    result = exact(expression)
    assert result.unresolved == 0
    assert result.joint == oracle


@pytest.mark.parametrize('expression, depth, draws', TRUNCATED_CASES)
def test_engine_within_truncation_of_replay(expression, depth, draws):
    oracle, truncated = replay_distribution(expression, max_draws=draws)
    result = exact(expression, explode_depth=depth)
    assert result.unresolved < Fraction(1, 50)
    assert truncated < Fraction(1, 50)
    for key in set(oracle) | set(result.joint):
        mine = result.joint.get(key, Fraction(0))
        theirs = oracle.get(key, Fraction(0))
        assert mine - theirs <= truncated, key
        assert theirs - mine <= result.unresolved, key
    # Every probability both sides resolve fully must agree exactly.
    assert sum(result.joint.values()) + result.unresolved == 1
    assert sum(oracle.values()) + truncated == 1


@pytest.mark.parametrize('expression', ['3d4kh2>=3', '2d4ro1ns1', '((1d4)+(1d6))kh1',
                                        '(2d{a,b})+(1d4)', '0d6', '3d4=+2dl1t>=7'])
def test_faces_equal_replay(expression):
    oracle, _ = replay_distribution(expression, key=lambda r: (faces_of(r), outcome_of(r)))
    result = exact(expression, faces=True)
    assert result.unresolved == 0
    assert {((kept, natural), outcome): p for (kept, natural, outcome), p in result.faces.items()} == oracle
    joint = {}
    for (_kept, _natural, outcome), p in result.faces.items():
        joint[outcome] = joint.get(outcome, 0) + p
    assert joint == result.joint


def test_faces_with_explosions_report_truncation():
    result = exact('2d4x4kh1', faces=True, explode_depth=5)
    oracle, truncated = replay_distribution('2d4x4kh1', key=lambda r: (faces_of(r), outcome_of(r)),
                                            max_draws=10)
    for (kept, natural, outcome), p in result.faces.items():
        theirs = oracle.get(((kept, natural), outcome), Fraction(0))
        assert p - theirs <= truncated
        assert theirs - p <= result.unresolved
    assert sum(result.faces.values()) + result.unresolved == 1


SAMPLED = ['10d10>=8x>=10', '5d6>=6f<=1', '4d6r1kh3', '((1d8xx)+(1d6xx))kh1t>=4',
           '2d20=+5kh1t>=15ns20nf1', '6d6xp>=5dl2', '1d8+1d6-1d4']


@pytest.mark.parametrize('expression', SAMPLED)
def test_seeded_sampling_agrees(expression):
    """Seeded DiceThrower sample against the exact law, within 4 standard errors.

    The seed makes the check deterministic.  Under the exact law a 4-SE
    deviation of the sample mean has probability about 6e-5 per statistic.
    """
    samples = 20000
    result = exact(expression, explode_depth=30)
    assert result.unresolved < Fraction(1, 10 ** 9)
    rng_state = random.getstate()
    random.seed(20261009)
    try:
        thrower = DiceThrower()
        rolls = [thrower.throw(expression) for _ in range(samples)]
    finally:
        random.setstate(rng_state)
    for field in ('total', 'success'):
        mean = float(result.mean(field))
        se = math.sqrt(float(result.variance(field)) / samples)
        observed = sum(int(r[field]) for r in rolls) / samples
        assert abs(observed - mean) <= 4 * se, field
    if None not in result.marginal('pass'):
        p = float(result.marginal('pass').get(1, 0))
        observed = sum(int(r['pass']) for r in rolls) / samples
        assert abs(observed - p) <= 4 * math.sqrt(p * (1 - p) / samples) + 1e-12


@pytest.mark.parametrize('merged, split', [('4d6x>=5kh2', '4d6x>=5kh2ns1'),
                                           ('5d6>=5x6dl2', '5d6>=5x6dl2nf1'),
                                           ('6d10x>=10kh3', '6d10x>=10kh3ns10')])
def test_exploding_keep_routes_agree(merged, split):
    """Without natural counters the engine merges first and later draws; with
    them it keeps four groups.  The counter cannot change the other fields."""
    a, b = exact(merged), exact(split)
    assert a.unresolved == b.unresolved
    for field in ('total', 'success', 'fail', 'pass'):
        assert a.marginal(field) == b.marginal(field)


def test_exploding_keep_medium_pool_against_replay():
    oracle, truncated = replay_distribution('3d4x4kh2', max_draws=11)
    result = exact('3d4x4kh2', explode_depth=8)
    for key in set(oracle) | set(result.joint):
        mine, theirs = result.joint.get(key, Fraction(0)), oracle.get(key, Fraction(0))
        assert mine - theirs <= truncated and theirs - mine <= result.unresolved


def test_group_keep_over_exploding_members_is_bounded():
    """Group keep/drop over non-plain members enumerates multisets: exact within
    faces_limit, an explicit DiceException beyond it, never a silent result."""
    from dice_roller.DiceException import DiceException
    small = exact('((1d4x4)+(1d4))kh1', explode_depth=4)
    oracle, truncated = replay_distribution('((1d4x4)+(1d4))kh1', max_draws=7)
    for key in set(oracle) | set(small.joint):
        mine, theirs = small.joint.get(key, Fraction(0)), oracle.get(key, Fraction(0))
        assert mine - theirs <= truncated and theirs - mine <= small.unresolved
    with pytest.raises(DiceException) as info:
        exact('((8d10x>=9)+(1d8))kh2')
    assert 'faces limit' in info.value.errors


@pytest.mark.parametrize('expression', ['12d6', '12d6>=5', '9d6>=5f<=1', '7d{-1,0,1}>=1f<0',
                                        '6d6>=5f<=2ns6', '8d4+1>=4', '5d10>=8x>=10', '0d6', '3d6'])
def test_pool_power_equals_plain_power(expression):
    """The class decomposition must reproduce plain repeated convolution."""
    import dice_roller.exact as engine
    fast = exact(expression).joint
    original = engine._pool_power
    engine._pool_power = engine._power
    try:
        assert exact(expression).joint == fast
    finally:
        engine._pool_power = original
