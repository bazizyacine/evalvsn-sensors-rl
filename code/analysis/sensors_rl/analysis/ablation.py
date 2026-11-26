"""Experiment E2, the contribution of each decision, from revision.tsv at
GOP 9-3, T = 9 s, 40 m grid. Each arm changes one decision of a stack of the
main study and keeps its seeds, so every test pairs the 60 seeds:

  alone      rules-only<X> - rules: agent X in place of its rule on the rule
             stack, for the seven agents (P path, C congestion, B link-break
             detection, D discovery, A channel access, T power, E early discard)
  in hybrid  hybrid - hybrid-no<X>: the stack with agent X minus the same stack
             with its rule, for the six agents of the hybrid stack; the
             link-break agent, absent from it, takes agents - hybrid, the one
             switch between the two stacks, a comparison of E0

Holm's correction runs within each family: the seven effects alone, and the
six removals from the hybrid stack; agents - hybrid keeps its family of E0,
its three GOPs. Additivity compares the joint effect
hybrid - rules with the sum of the six effects alone and of the six removals,
seed by seed."""
from ..common import data, stats
from . import quality

SOLO = 'PCBDATE'           # the seven agents, alone on the rule stack
HYBRID = 'PCDATE'          # the six agents of the hybrid stack
METRICS = (('psnr', 'PSNR (dB)'), ('m1loss', 'M1 loss (points)'), ('declared', 'declarations'),
           ('false_declared', 'declarations of a living neighbour'), ('loss', 'loss (points)'))


def values(arm, metric):
    return data.select(data.table('revision.tsv'), arm, metric)


def with_without(agent, metric, context):
    """Per-seed effect of an agent: the arm with it minus the arm with its rule."""
    if context == 'alone':
        return data.difference(values('rules-only' + agent, metric), values('rules', metric))
    if agent == 'B':
        return data.difference(values('agents', metric), values('hybrid', metric))
    return data.difference(values('hybrid', metric), values('hybrid-no' + agent, metric))


def family(effects):
    """{label: Estimate} Holm-corrected; a contrast the 60 seeds do not all
    back is left out of the family."""
    return {k: e for k, e in stats.family({k: stats.estimate(v.values()) if len(v) == data.SEEDS else None
                                           for k, v in effects.items()}).items() if e is not None}


def effects(metric):
    """The two families of a metric: the seven effects alone, and the effects in
    the hybrid stack, Holm over its six removals; the link-break agent's effect
    there, agents - hybrid, takes its family of E0, Holm over the three GOPs of
    that comparison (families table), the p the text gives it (3.5)."""
    alone = family({x: with_without(x, metric, 'alone') for x in SOLO})
    inside = family({x: with_without(x, metric, 'hybrid') for x in HYBRID})
    if len(with_without('B', metric, 'hybrid')) == data.SEEDS:
        inside['B'] = quality.gops('agents', 'hybrid', metric)['9M3D']
    return alone, inside


def interactions(metric='psnr'):
    """Each agent of the hybrid stack: its effect there minus its effect
    alone on the rule stack, seed by seed, Holm over the six (the family of
    the six agents of the hybrid stack, families table)."""
    return family({x: data.difference(with_without(x, metric, 'hybrid'), with_without(x, metric, 'alone')) for x in HYBRID})


# The access-only stack: the rule stack with the channel-access agent alone.
ACCESS_ONLY = 'rules-onlyA'


def against_access(arms, metric='psnr'):
    """{arm: Estimate of arm - the access-only stack} over the 60 seeds, Holm
    over the arms given: the two learning stacks at one exploration rate
    form a family (families table)."""
    return family({a: data.difference(values(a, metric), values(ACCESS_ONLY, metric)) for a in arms})


def sum_of(agents, metric, context):
    out = None
    for x in agents:
        e = with_without(x, metric, context)
        out = e if out is None else {k: out[k] + e[k] for k in out if k in e}
    return out


def additivity(metric='psnr'):
    """The joint effect hybrid - rules minus the sum of the six effects
    alone, seed by seed (the interaction of the agents): a single test."""
    joint = data.difference(values('hybrid', metric), values('rules', metric))
    solos = sum_of(HYBRID, metric, 'alone')
    return stats.estimate(joint[k] - solos[k] for k in joint)


def _fmt(e):
    s = 'n=%d  %+7.2f [%+6.2f, %+6.2f]  p=%-9.3g' % (e.n, e.mean, e.lo, e.hi, e.p)
    return s + ('  Holm %.3g' % e.holm if e.holm is not None else '')


def report():
    print('Means over the 60 seeds, GOP 9-3')
    arms = ['rules', 'hybrid', 'agents'] + ['rules-only' + x for x in SOLO] + ['hybrid-no' + x for x in HYBRID]
    print('  %-14s' % 'arm' + ''.join('%10s' % m for m, _ in METRICS))
    for a in arms:
        row = []
        for m, _ in METRICS:
            v = values(a, m)
            row.append('%10.2f' % (sum(v.values()) / len(v)) if len(v) == data.SEEDS else '%10s' % '--')
        print('  %-14s' % a + ''.join(row))

    print('\nIdentical simulations (every column of the 60 seeds equal)')
    cols = ('psnr', 'ssim', 'loss', 'm1loss', 'usable', 'delay_mean', 'declared', 'false_declared')
    for a, b in (('rules-onlyT', 'rules'), ('hybrid-noT', 'hybrid')):
        same = sum(all(values(a, c)[k] == values(b, c)[k] for c in cols) for k in values(a, 'psnr'))
        print('  %s and %s: %d of %d seeds' % (a, b, same, data.SEEDS))

    for metric, label in METRICS[:4]:
        alone, inside = effects(metric)
        seven = family({x: with_without(x, metric, 'hybrid') for x in SOLO})
        print('\n%s: effect alone on the rule stack, onlyX - rules, Holm over 7' % label)
        for x in SOLO:
            print('  %s  %s' % (x, _fmt(alone[x])))
        print('%s: effect in the hybrid stack, hybrid - noX, Holm over 6 (B: agents - hybrid, Holm over the three GOPs, E0)' % label)
        for x in SOLO:
            print('  %s  %s  (Holm over 7 with B: %.3g)' % (x, _fmt(inside[x]), seven[x].holm))

    print('\nAdditivity, PSNR, per seed')
    joint = data.difference(values('hybrid', 'psnr'), values('rules', 'psnr'))
    solos = sum_of(HYBRID, 'psnr', 'alone')
    removals = sum_of(HYBRID, 'psnr', 'hybrid')
    print('  joint, hybrid - rules          %s' % _fmt(stats.estimate(joint.values())))
    print('  sum of the six effects alone   %s' % _fmt(stats.estimate(solos.values())))
    print('  sum of the six removals        %s' % _fmt(stats.estimate(removals.values())))
    print('  joint - sum alone (interaction) %s' % _fmt(additivity('psnr')))
    print('  joint - sum of removals         %s' % _fmt(stats.estimate(joint[k] - removals[k] for k in joint)))
    print('  without A: sum alone of P, C, D, T, E %s' % _fmt(stats.estimate(sum_of('PCDTE', 'psnr', 'alone').values())))
    print('  without A: sum of removals of P, C, D, T, E %s' % _fmt(stats.estimate(sum_of('PCDTE', 'psnr', 'hybrid').values())))

    print('\nThe channel-access agent and the five others, PSNR (Holm over the 3)')
    tests = {'hybrid - onlyA (the five others with A)': data.difference(values('hybrid', 'psnr'), values('rules-onlyA', 'psnr')),
             'noA - rules (the five others without A)': data.difference(values('hybrid-noA', 'psnr'), values('rules', 'psnr')),
             'noE - onlyA (P, C, D, T with A, rule discard)': data.difference(values('hybrid-noE', 'psnr'), values('rules-onlyA', 'psnr'))}
    for k, e in family(tests).items():
        print('  %-46s %s' % (k, _fmt(e)))

    print('\nInteraction of each agent: effect in the hybrid minus effect alone, PSNR (Holm over 7)')
    inter = family({x: data.difference(with_without(x, 'psnr', 'hybrid'), with_without(x, 'psnr', 'alone')) for x in SOLO})
    for x in SOLO:
        print('  %s  %s' % (x, _fmt(inter[x])))
