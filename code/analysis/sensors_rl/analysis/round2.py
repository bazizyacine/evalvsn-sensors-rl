"""Study 11, the controls of the second review round
(data/sensors-rl/2-round2/README.md), from round2.tsv paired, realisation by
realisation on the same seeds, with the arms of studies 09 and 10 in
revision.tsv:

  crossing     control 1, the hybrid stack at GOP 9-3, learning (its rates
               or 0) crossed with exploration (0.1 or 0): the hybrid stack
               minus exploration only, the gain of learning under
               exploration; minus learning only, the gain of exploration
               under learning; exploration only and learning only against
               the frozen policy, each alone
  learned CSMA control 2, the configuration the
               channel-access agent learned in each of four development
               runs, frozen at GOP 9-3: on the access-only stack, against
               the access-only stack (the agent learning) and the rule stack
               (the standard's setting); in the hybrid stack, against the
               hybrid stack and the hybrid stack without the agent
  fixed CSMA   control 2 before the learned configurations, the agent kept on one action (BE, NB),
               against the same references: run, outside the plan and its
               families, printed apart
  access only  control 3, the access-only stack at the three GOPs (GOP 9-3
               from study 10): against the rule stack, and the hybrid stack
               against it
  link break   control 5, the link-break agent of the agents stack without
               exploration or with its exploration decaying alone, the six
               other agents keeping 0.1, at the three GOPs: against the
               agents stack (its constant rate) and the hybrid stack (the
               three-failure rule)

The PSNR of each comparison is corrected by Holm within its family of the
families table (tables/plan.py, FAMILIES), fixed before the results; the
secondary measures are single tests, uncorrected, as the families table sets
those of E2 and E3. The comparisons the README names that fit no family of
the families table are printed apart, with their raw p only (OUTSIDE)."""
from ..common import data, stats
from ..tables.plan import FAMILIES
from . import ablation, quality

SPLITS = data.SPLITS
SECONDARY = (('m1loss', 'M1 loss (points)'), ('loss', 'loss (points)'), ('usable', 'images >= 28 dB'),
             ('declared', 'neighbours declared dead'), ('delay_mean', 'mean delay (ms)'))
METRICS = (('psnr', 'PSNR (dB)'),) + SECONDARY


def values(arm, metric, split='9M3D'):
    """{seed: value} of an arm of any study at one GOP (quality.values)."""
    return quality.values(arm, metric, split)


def family_name(experiment, series, size):
    """The English name of a family of the families table."""
    names = [f.en for f in FAMILIES if f.experiment == experiment and series in f.series.split() and f.size == size]
    assert len(names) == 1, (experiment, series, size)
    return names[0]


def _tests(pairs, metric):
    """{label: Estimate of a - b} for pairs (label, a, b, split): the PSNR
    corrected by Holm over the pairs, a secondary measure a single test."""
    tests = {label: stats.paired(values(a, metric, s), values(b, metric, s)) for label, a, b, s in pairs}
    return stats.family(tests) if metric == 'psnr' else tests


# ------------------------------------------------------------ control 1

EXPLORE, LEARN, FROZEN = 'hybrid-explore-s11', 'hybrid-learn-s11', 'hybrid-frozen'
CROSSING = (('learning under exploration', 'hybrid', EXPLORE), ('exploration under learning', 'hybrid', LEARN),
            ('exploration alone', EXPLORE, FROZEN), ('learning alone', LEARN, FROZEN))


def crossing(metric='psnr'):
    """{contrast: Estimate}, the four contrasts of the crossing at GOP 9-3,
    Holm over the four (E3)."""
    return _tests([(k, a, b, '9M3D') for k, a, b in CROSSING], metric)


# ------------------------------------------------------------ control 2

# The four fixed settings, ranked before the campaign: the suffix of their
# arms, the agent's action, (BE, NB).
SETTINGS = (('be4nb5', 8, 4, 5), ('be4nb4', 7, 4, 4), ('be2nb5', 2, 2, 5), ('be3nb5', 5, 3, 5))
# Per stack, the arm where the agent learns and the arm at the standard's setting.
REFERENCES = {'rules': {'agent': ablation.ACCESS_ONLY, 'standard': 'rules'},
              'hybrid': {'agent': 'hybrid', 'standard': 'hybrid-noA'}}


def fixed_csma(stack, reference, metric='psnr'):
    """{setting: Estimate of the stack at the fixed setting minus the
    reference ('agent' or 'standard')}, GOP 9-3, Holm over the four
    settings: one family per stack and reference (E2)."""
    ref = REFERENCES[stack][reference]
    return _tests([(s, '%s-%s-s11' % (stack, s), ref, '9M3D') for s, *_ in SETTINGS], metric)


# The configurations each stack's channel-access agent learned in its four
# development runs, replayed frozen (control 2 with learned configurations,
# data/sensors-rl/2-round2/README.md): k, and the prefix of the
# replays' arms per stack.
CONFIGURATIONS = (1, 2, 3, 4)
LEARNED_ARM = {'rules': ablation.ACCESS_ONLY, 'hybrid': 'hybrid'}


def learned_csma(stack, reference, metric='psnr'):
    """{k: Estimate of configuration k frozen on its stack minus the
    reference ('agent' or 'standard')}, GOP 9-3, Holm over the four
    configurations: one family per stack and reference, as the README fixes
    it; None while a replay lacks some of the 60 seeds in round2.tsv."""
    arms = {k: '%s-cfg%d-s11' % (LEARNED_ARM[stack], k) for k in CONFIGURATIONS}
    if any(len(values(a, metric)) < data.SEEDS for a in arms.values()):
        return None
    return _tests([(k, a, REFERENCES[stack][reference], '9M3D') for k, a in arms.items()], metric)


# The agent's action (BE, NB) = (3, 4), the standard's setting, its initial choice.
STANDARD_ACTION = 4


# ------------------------------------------------------------ control 3

ACCESS_COMPARISONS = ('access - rules', 'hybrid - access')


def access_only(split):
    """The arm of the access-only stack at a GOP: study 10's at GOP 9-3,
    study 11's at the two others."""
    return ablation.ACCESS_ONLY if split == '9M3D' else ablation.ACCESS_ONLY + '-s11'


def access_gops(comparison, metric='psnr'):
    """{split: Estimate} of the access-only stack minus the rule stack, or
    of the hybrid stack minus the access-only stack, per GOP over the 60
    seeds, Holm over the three GOPs of each comparison (E2)."""
    def arms(s):
        return (access_only(s), 'rules') if comparison == 'access - rules' else ('hybrid', access_only(s))
    return _tests([(s,) + arms(s) + (s,) for s in SPLITS], metric)


def access_cells(comparison, metric='psnr'):
    """{(fire, split): Estimate} of the same comparisons in each cell of the
    main study, twenty seeds: the gap and its interval only, no test. The
    README fixes these comparisons at the three GOPs (access_gops), not per
    cell."""
    out = {}
    for s in SPLITS:
        a, b = (access_only(s), 'rules') if comparison == 'access - rules' else ('hybrid', access_only(s))
        a, b = values(a, metric, s), values(b, metric, s)
        for f in data.FIRES:
            out[(f, s)] = stats.paired({k: v for k, v in a.items() if k[0] == f}, {k: v for k, v in b.items() if k[0] == f})
    return {(f, s): out[(f, s)] for f in data.FIRES for s in SPLITS}


# ------------------------------------------------------------ control 5

LEVELS = (('agents-bgreedy', 'without exploration'), ('agents-bdec-s11', 'with its exploration decaying alone'))
BREAK_REFERENCES = ('agents', 'hybrid')


def link_break(level, reference, metric='psnr'):
    """{split: Estimate of the level minus the reference stack}, Holm over
    the three GOPs: one family per level and reference (E3)."""
    return _tests([(s, level, reference, s) for s in SPLITS], metric)


# ------------------------------------------------------------ outside

# The comparisons the README names that fit no family of the families table:
# exploration only against learning only (its table of the controls; the family of the
# crossing holds its four contrasts); the link-break decay alone against no
# exploration ("the decay below"; section 2.7 does not compare the two
# levels); at GOP 9-3 only, the decay alone against all seven agents decaying
# (section 2.7 names it; the family of the link-break series holds three GOPs).
OUTSIDE = (('exploration only - learning only', EXPLORE, LEARN, ('9M3D',)),
           ('break decay alone - no exploration', 'agents-bdec-s11', 'agents-bgreedy', SPLITS),
           ('break decay alone - all agents decaying', 'agents-bdec-s11', 'agents-edec', ('9M3D',)))


def outside(metric='psnr'):
    """{(label, split): Estimate}, each a single test, raw p only."""
    return {(label, s): stats.paired(values(a, metric, s), values(b, metric, s))
            for label, a, b, splits in OUTSIDE for s in splits}


# ------------------------------------------------------------ report

def flagged(e):
    """The interval, uncorrected, excludes 0 while Holm's p exceeds 0.05:
    the case section 2.7 has the text point out."""
    return e.holm is not None and (e.lo > 0 or e.hi < 0) and e.holm >= 0.05


def _line(label, e):
    s = '    %-48s n=%d  %+8.2f [%+7.2f, %+7.2f]  p=%-9.3g' % (label, e.n, e.mean, e.lo, e.hi, e.p)
    if e.holm is not None:
        s += '  Holm %-9.3g' % e.holm + ('  flagged: the interval excludes 0, Holm > 0.05' if flagged(e) else '')
    return s.rstrip()


def _block(title, family, get, label=str):
    """get(metric) -> {key: Estimate}: the PSNR in its family of the families
    table, then each secondary measure, single tests."""
    print('\n' + title)
    print('  PSNR (dB), Holm within "%s" (%s, %d tests)' % family)
    for k, e in get('psnr').items():
        print(_line(label(k), e))
    print('  secondary measures, single tests, uncorrected')
    for m, name in SECONDARY:
        print('   %s' % name)
        for k, e in get(m).items():
            print(_line(label(k), e))


def _family(experiment, series, size):
    return family_name(experiment, series, size), experiment, size


def _means(split, arms):
    print('  GOP %s' % data.GOP[split])
    for a in arms:
        row = [stats.complete_mean(values(a, m, split).values(), data.SEEDS) for m, _ in METRICS]
        print('    %-20s' % a + ''.join('%11.2f' % x if x is not None else '%11s' % '--' for x in row))


def report():
    print('Means over the 60 seeds (delay in ms)')
    print('    %-20s' % 'arm' + ''.join('%11s' % m for m, _ in METRICS))
    fixed = ['%s-%s-s11' % (st, s) for st in ('rules', 'hybrid') for s, *_ in SETTINGS]
    _means('9M3D', ['rules', ablation.ACCESS_ONLY, 'hybrid', 'hybrid-noA', EXPLORE, LEARN, FROZEN] + fixed
           + ['agents', 'agents-bgreedy', 'agents-bdec-s11', 'agents-edec'])
    for s in ('6M6D', '3M9D'):
        _means(s, ['rules', access_only(s), 'hybrid', 'agents', 'agents-bgreedy', 'agents-bdec-s11'])

    arms = {c: '%s - %s' % (a, b) for c, a, b in CROSSING}
    _block('Control 1 (E3): the crossing of learning and exploration, hybrid stack, GOP 9-3; '
           + '; '.join('%s = %s' % (c, arms[c]) for c, _, _ in CROSSING), _family('E3', 'split', 4), crossing, label=arms.get)

    for stack in ('rules', 'hybrid'):
        for ref in ('agent', 'standard'):
            what = (stack, REFERENCES[stack][ref], 'agent learning' if ref == 'agent' else "standard's setting")
            if learned_csma(stack, ref) is None:
                print('\nControl 2 (E2): learned configurations frozen on the %s stack, minus %s (the %s), GOP 9-3: '
                      'replays not all in round2.tsv' % what)
                continue
            _block('Control 2 (E2): learned configurations frozen on the %s stack, minus %s (the %s), GOP 9-3' % what,
                   _family('E2', 'learned', 4), lambda m, st=stack, r=ref: learned_csma(st, r, m), label='configuration k%d'.__mod__)
    setting = {s: 'a%d (BE %d, NB %d)' % (a, be, nb) for s, a, be, nb in SETTINGS}
    for stack in ('rules', 'hybrid'):
        for ref in ('agent', 'standard'):
            _block('Control 2 before the learned configurations, outside the plan: fixed CSMA/CA on the %s stack, minus %s (the %s), GOP 9-3'
                   % (stack, REFERENCES[stack][ref], 'agent learning' if ref == 'agent' else "standard's setting"),
                   ('the four fixed settings, in no family', 'E2', 4),
                   lambda m, st=stack, r=ref: fixed_csma(st, r, m), label=setting.get)

    for c in ACCESS_COMPARISONS:
        _block('Control 3 (E2): %s per GOP, the access-only stack of study 10 at 9-3, of study 11 at 6-6 and 3-9' % c,
               _family('E2', 'onlyA', 3), lambda m, c=c: access_gops(c, m), label=data.GOP.get)
    print('\nControl 3 at GOP 9-3, studies 09 and 10 only (in the text, claims S06): the two learning stacks minus the '
          'access-only stack, Holm within "%s" (E2, 2 tests), at each exploration rate' % family_name('E2', 'E2', 2))
    for arms in (('hybrid', 'agents'), ('hybrid-edec', 'agents-edec')):
        for k, e in ablation.against_access(arms).items():
            print(_line('%s - %s' % (k, ablation.ACCESS_ONLY), e))

    for level, name in LEVELS:
        for ref in BREAK_REFERENCES:
            _block('Control 5 (E3): the link-break agent %s (%s) minus the %s stack, per GOP' % (name, level, ref),
                   _family('E3', 'break', 3), lambda m, lv=level, r=ref: link_break(lv, r, m), label=data.GOP.get)

    print('\nNamed by the README, in no family of the families table: single tests, raw p only, to settle before the text')
    for m, name in METRICS:
        print('   %s' % name)
        for (label, s), e in outside(m).items():
            print(_line('%s, %s' % (label, data.GOP[s]), e))
