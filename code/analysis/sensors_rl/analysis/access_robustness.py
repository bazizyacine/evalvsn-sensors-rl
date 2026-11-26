"""Tranche T7 of study 11, the robustness of the access-only
stack: the rule stack with the channel-access agent alone, measured in the
series of E4 and E5. Its protocol, its sets, its comparisons and their Holm
families were fixed before its results, in
data/sensors-rl/2-round2/README.md, "Robustness of the access-only stack
(T7, 23 November 2026)", which rules this module.

  series   load      the five alarm periods at GOP 9-3 (E5)
           fire      the seven variants of the fire parameters (E5)
           scenario  the five variants of the scenario (E5)
           rate      the two GOPs at equal rate (E4)
           coding    the quality coefficient 0.1 at GOP 9-3 (E4)
  arms     the access-only stack from round2.tsv (study 11), but at the
           period of 9 s of the load series, rules-onlyA-s10 of study 10
           (revision.tsv); the rule and hybrid stacks of studies 09 and 10
           at the same level, from revision.tsv
  tests    access - rules, the access-only stack minus the rule stack, and
           hybrid - access, the hybrid stack minus the access-only stack,
           paired on the 60 seeds: the PSNR corrected by Holm within its
           series and its comparison (families of 5, 7, 5 and 2 tests, the
           coefficient a single test); the secondary measures are single
           tests, uncorrected. No variation of a gap with the variant and no
           other comparison: what the README does not list is not tested

Every function that tests gives None while an arm it needs lacks some of the
60 seeds, as round2.learned_csma does; complete() says whether every arm of
every series holds them, and the report of this module (report --only
access-robustness) lists what is missing otherwise. The article takes these
results since 24 November 2026 (IN_ARTICLE; sections 3.7 and 3.8): the equal-rate and
coefficient tables (tables/coding.py), the load, fire and scenario tables
(tables/robustness.py), the plan and families tables (tables/plan.py) and the
tests of the assumptions (analysis/assumptions.py) hold them, and
claims/access_robustness.py reads the text."""
import sys
from collections import namedtuple

from ..common import data, paths, stats
from . import ablation, coding, quality, robustness

# The one switch of the article: True since the campaign is over and the text
# gives these results (sections 3.7 and 3.8). It puts the 57 sets of T7 in the plan
# (tables/plan.py), their families in the families table and their tests in
# the checks of the assumptions (analysis/assumptions.py). It does not stand
# on partial data: active() stops.
IN_ARTICLE = True

# A level of a series: its key, its variant (the suffix of its arms, None for
# the reference scenario's), its GOP, its alarm period and its grid spacing.
Level = namedtuple('Level', 'key variant split period dist')
# The period of 9 s of the load series, the reference scenario: its
# access-only arm is study 10's.
REFERENCE = Level('p9', None, '9M3D', 'p9', '40')


def _variants(names):
    # the 30 m grid is the only variant whose sets carry d30
    return tuple(Level(v, v, '9M3D', 'p9', '30' if v == 'j8' else '40') for v in names)


SERIES = {
    'load': tuple(Level(p, None, '9M3D', p, '40') for p in robustness.PERIODS),
    'fire': _variants(robustness.FIRE_VARIANTS),
    'scenario': _variants(robustness.SCENARIO_VARIANTS),
    'rate': tuple(Level(s, None, s, p, '40') for s, p in coding.EQUAL_RATE),
    'coding': _variants(('q01',)),
}
# The experiment of each series and the size of its Holm family per
# comparison, as the README fixes them (None: a single test).
EXPERIMENT = {'load': 'E5', 'fire': 'E5', 'scenario': 'E5', 'rate': 'E4', 'coding': 'E4'}
FAMILY = {'load': 5, 'fire': 7, 'scenario': 5, 'rate': 2, 'coding': None}
assert all(len(levels) == (FAMILY[s] or 1) for s, levels in SERIES.items()) and REFERENCE in SERIES['load']

STACKS = ('rules', 'access', 'hybrid')
# The two comparisons, a - b, in the words of round2.ACCESS_COMPARISONS.
COMPARISONS = {'access - rules': ('access', 'rules'), 'hybrid - access': ('hybrid', 'access')}


def arm(stack, level):
    """The arm of a stack at a level, as its table names it."""
    if stack != 'access':
        return robustness.arm(stack, level.variant)
    a = robustness.arm(ablation.ACCESS_ONLY, level.variant)
    return a if level == REFERENCE else a + '-s11'


def values(stack, level, metric='psnr'):
    """{seed: value} of a stack at a level; the delays in ms, as
    quality.values gives them."""
    a = arm(stack, level)
    scale = dict((m, s) for m, _, s in quality.METRICS).get(metric, 1.0)
    found = data.select(data.table(data.holding(a)) or (), a, metric, split=level.split, period=level.period, dist=level.dist)
    return {k: scale * v for k, v in found.items()}


def mean(stack, level, metric='psnr'):
    """The mean over the 60 seeds, None when the sets do not provide them all."""
    return stats.complete_mean(values(stack, level, metric).values(), data.SEEDS)


def missing():
    """[(series, level key, stack, seeds present)] of every arm the
    comparisons need that does not hold the 60 seeds of the PSNR."""
    out = []
    for series, levels in SERIES.items():
        for level in levels:
            for s in STACKS:
                n = len(values(s, level))
                if n != data.SEEDS:
                    out.append((series, level.key, s, n))
    return out


def complete():
    """Every arm of every series holds its 60 seeds: the campaign is over
    and stored."""
    return not missing()


def active():
    """The article takes T7: IN_ARTICLE, which stands only on complete data."""
    if IN_ARTICLE and not complete():
        sys.exit('analysis/access_robustness.py: IN_ARTICLE is set while arms of T7 lack seeds: %s'
                 % ', '.join('%s %s %s (%d of %d)' % (m + (data.SEEDS,)) for m in missing()))
    return IN_ARTICLE


# --------------------------------------------------------------------- tests

def gap(comparison, level, metric='psnr'):
    """Estimate of one comparison at one level over the 60 seeds; None when
    an arm lacks some of them."""
    a, b = (values(s, level, metric) for s in COMPARISONS[comparison])
    if len(a) != data.SEEDS or set(a) != set(b):
        return None
    return stats.paired(a, b)


def tests(series, comparison, metric='psnr'):
    """{level key: Estimate} of one comparison over the levels of a series:
    the PSNR corrected by Holm over its levels (the coefficient, one level,
    stays a single test), another measure as single tests. None while an arm
    of the series lacks some of the 60 seeds; a secondary measure a
    simulation leaves empty gives None at its level."""
    if any(gap(comparison, level) is None for level in SERIES[series]):
        return None
    out = {level.key: gap(comparison, level, metric) for level in SERIES[series]}
    return stats.family(out) if metric == 'psnr' and FAMILY[series] else out


def families():
    """{(series, comparison): {level key: Estimate}} of the PSNR, every
    family and the two single tests; None until every arm is complete."""
    if not complete():
        return None
    return {(s, c): tests(s, c) for s in SERIES for c in COMPARISONS}


# ------------------------------------------------------------------ pairing

def pairing():
    """(simulations of T7 in study 11's runs.tsv, those whose seed is not the
    one of the hybrid stack's simulation of study 10 they pair with): two
    simulations pair when the fire, the realisation and the level are the
    same. None without the results of the studies."""
    def seeds(study):
        return {(r['arm'], r['fire'], r['split'], r['period'], r['dist'], r['realisation']): r['seed']
                for r in data.read_tsv(paths.results(study, 'runs.tsv')) or ()}
    own, paired = seeds(paths.STUDY_R2), seeds(paths.STUDY_R1)
    if not own or not paired:
        return None
    n, wrong = 0, []
    for levels in SERIES.values():
        for level in levels:
            a, h = arm('access', level), arm('hybrid', level)
            for key, seed in own.items():
                if key[0] == a and key[2:5] == level[2:]:
                    n += 1
                    if paired.get((h,) + key[1:]) != seed:
                        wrong.append(key)
    return n, wrong


def lost_without_path(series=tuple(SERIES)):
    """(simulations, packets lost, those that left the camera while no path
    of live nodes joined it to the sink) over the sets of T7, or of some of
    its series, from study 11's oracle.tsv; None without it."""
    import sets     # code/metrics, on sys.path by paths
    arms = {(arm('access', v), v.split, v.period, v.dist) for s in series for v in SERIES[s]}
    rows = data.read_tsv(paths.results(paths.STUDY_R2, 'oracle.tsv'))
    if rows is None:
        return None
    n = lost = cut = 0
    for r in rows:
        a, _, split, period, dist = sets.keys(r['set'])
        if (a, split, period, dist) in arms:
            n, lost, cut = n + 1, lost + int(r['lost']), cut + int(r['unreachable'])
    return n, lost, cut


# -------------------------------------------------------------------- report

TITLES = {'load': 'Load (E5), alarm period, GOP 9-3', 'fire': 'Fire (E5), seven variants, GOP 9-3, T = 9 s',
          'scenario': 'Scenario (E5), five variants, GOP 9-3, T = 9 s', 'rate': 'Equal rate (E4), two GOPs',
          'coding': 'Quality coefficient 0.1 (E4), GOP 9-3, T = 9 s'}


def report():
    """The means, the two comparisons with their families and the secondary
    measures of each complete series; what is missing otherwise."""
    from . import round2    # here: round2 reads tables/plan.py, which reads this module
    print('Robustness of the access-only stack (study 11, T7)')
    gone = missing()
    if gone:
        print('  the campaign is not complete: %d arms lack some of the %d seeds (seeds present)' % (len(gone), data.SEEDS))
        for series, key, stack, n in gone:
            print('    %-9s %-6s %-7s %d' % (series, key, stack, n))
    check, oracle = pairing(), lost_without_path()
    if check:
        n, wrong = check
        print('  seeds: %d of %d simulations of T7 in runs.tsv, %d with another seed than the hybrid stack\'s simulation of study 10%s'
              % (n, data.SEEDS * (sum(len(v) for v in SERIES.values()) - 1), len(wrong), ': ' + ', '.join(wrong[0]) if wrong else ''))
    if oracle:
        print('  oracle: %d simulations of T7, %d packets lost, %d of them without a path of live nodes' % oracle)
    metrics = round2.METRICS
    for series, levels in SERIES.items():
        print('\n%s' % TITLES[series])
        if tests(series, 'access - rules') is None or tests(series, 'hybrid - access') is None:
            print('  not all its arms are in round2.tsv')
            continue
        print('  means over the 60 seeds (delay in ms)')
        print('    %-14s' % 'level, stack' + ''.join('%11s' % m for m, _ in metrics))
        for level in levels:
            for s in STACKS:
                row = [mean(s, level, m) for m, _ in metrics]
                print('    %-6s %-7s' % (level.key, s) + ''.join('%11.2f' % x if x is not None else '%11s' % '--' for x in row))
        size = FAMILY[series]
        for c in COMPARISONS:
            print('  %s, PSNR (dB), %s' % (c, 'Holm over the %d levels' % size if size else 'single test'))
            for k, e in tests(series, c).items():
                print(round2._line(k, e))
            print('  %s, secondary measures, single tests, uncorrected' % c)
            for m, name in metrics[1:]:
                print('   %s' % name)
                for k, e in tests(series, c, m).items():
                    print(round2._line(k, e) if e is not None else '    %-48s a simulation leaves it empty' % k)
