"""Experiment E5, the reach of the hybrid stack's lead, from revision.tsv at
GOP 9-3; every contrast pairs the 60 seeds of the main study.

  load      the alarm period T = 7, 9, 12, 18 and 30 s, the four stacks: the
            gap hybrid - rules per period, Holm over the five
  fire      seven variants of the fire scenario, each changing one element
            (AZ = 1 dB/m, PF = 0.5, failures uniform in the TF = 60 s before
            the front), rule and hybrid stacks:
              az015, az05, az165   heated-zone attenuation 0.15, 0.5, 1.65 dB/m
              pf0, pf025, pf075    early-failure probability 0, 0.25, 0.75
              fd1                  failure instant TF * u^2 before the front
            gain    hybrid-<v> - rules-<v>, Holm over the seven variants
            shift   <stack>-<v> - <stack>, Holm over the seven variants
            change  (hybrid-<v> - rules-<v>) - (hybrid - rules), Holm over the
                    seven variants
  scenario  five variants of the reference scenario, the four stacks:
            two other videos (forest, smoke, at the coefficient
            that gives them nine M frames), a 30 m grid with every node moved
            by at most 8 m (j8), camera and sink exchanged (swap), the head
            speed times 1.5 (v15)
            gap     <a>-<v> - <b>-<v>, Holm over the five variants
            change  (<a>-<v> - <b>-<v>) - (<a> - <b>), Holm over the five
                    variants
The load, fire and scenario tables (tables/robustness.py) give the gaps of
the three series; the reference of the fire and scenario series is a single
test."""
from ..common import data, stats

PERIODS = ('p7', 'p9', 'p12', 'p18', 'p30')
FIRE_VARIANTS = ('az015', 'az05', 'az165', 'pf0', 'pf025', 'pf075', 'fd1')
FIRE_METRICS = ('psnr', 'm1loss', 'loss', 'usable', 'declared', 'false_declared')
SCENARIO_VARIANTS = ('forest', 'smoke', 'j8', 'swap', 'v15')
SCENARIO_STACKS = ('pq', 'rules', 'hybrid', 'agents')
CONTRASTS = {'hybrid-rules': ('hybrid', 'rules'), 'agents-rules': ('agents', 'rules'),
             'rules-pq': ('rules', 'pq'), 'hybrid-pq': ('hybrid', 'pq'), 'hybrid-agents': ('hybrid', 'agents')}
SCENARIO_METRICS = ('psnr', 'ssim', 'loss', 'm1loss', 'usable', 'usable25', 'usable31',
                    'declared', 'false_declared', 'rreq_all')


def arm(stack, v):
    return stack if v is None else '%s-%s' % (stack, v)


def values(a, metric, period='p9', fire=None):
    # the 30 m grid is the only variant whose sets carry d30
    return data.select(data.table('revision.tsv'), a, metric, period=period, dist='30' if a.endswith('-j8') else '40', fire=fire)


def mean_of(a, metric, period='p9', fire=None):
    """The mean over the 60 seeds (20 for one fire), None when the sets do not
    provide them all."""
    return stats.complete_mean(values(a, metric, period, fire).values(),
                               data.SEEDS if fire is None else data.SEEDS // 3)


def _full(d):
    return stats.estimate(d.values()) if len(d) == data.SEEDS else None


# ---------------------------------------------------------------------- load

def period_family(a, b, metric):
    """{period: Estimate of a - b}, Holm over the five alarm periods (the
    family of one comparison and one metric of the load series); a period
    whose sets do not provide the 60 seeds leaves the family uncorrected."""
    fam = {p: _full(data.difference(values(a, metric, p), values(b, metric, p))) for p in PERIODS}
    if all(e is not None for e in fam.values()):
        stats.family(fam)
    return fam


def load():
    """Per period: the rule stack's loss, the mean PSNR of the four stacks,
    and the gaps hybrid - rules of the PSNR and of the images that reach the
    PSNR threshold, each Holm over the five periods (the family of one
    comparison and one metric)."""
    psnr = period_family('hybrid', 'rules', 'psnr')
    images = period_family('hybrid', 'rules', 'usable')
    loss = {p: mean_of('rules', 'loss', p) for p in PERIODS}
    means = {p: {s: mean_of(s, 'psnr', p) for s in data.STACKS} for p in PERIODS}
    return dict(psnr=psnr, images=images, loss=loss, means=means)


# ---------------------------------------------------------------------- fire

def fire_contrast(kind, v, metric):
    if kind == 'gain':
        return data.difference(values(arm('hybrid', v), metric), values(arm('rules', v), metric))
    if kind in ('shift-rules', 'shift-hybrid'):
        s = kind.split('-')[1]
        return data.difference(values(arm(s, v), metric), values(s, metric))
    if kind == 'change':
        return data.difference(fire_contrast('gain', v, metric), fire_contrast('gain', None, metric))
    raise ValueError(kind)


def fire_family(kind, metric):
    return stats.family({v: _full(fire_contrast(kind, v, metric)) for v in FIRE_VARIANTS})


def fire():
    means = {arm(s, v): {m: mean_of(arm(s, v), m) for m in FIRE_METRICS}
             for s in ('rules', 'hybrid') for v in (None,) + FIRE_VARIANTS}
    families = {kind: {m: fire_family(kind, m) for m in FIRE_METRICS}
                for kind in ('gain', 'shift-rules', 'shift-hybrid', 'change')}
    reference = {m: stats.estimate(fire_contrast('gain', None, m).values()) for m in FIRE_METRICS}
    return dict(means=means, families=families, reference=reference)


# ------------------------------------------------------------------ scenario

def scenario_gap(contrast, v, metric):
    a, b = CONTRASTS[contrast]
    return data.difference(values(arm(a, v), metric), values(arm(b, v), metric))


def scenario_change(contrast, v, metric):
    return data.difference(scenario_gap(contrast, v, metric), scenario_gap(contrast, None, metric))


def scenario_family(kind, contrast, metric):
    """{variant: Estimate} of the gap or of its change from the reference
    scenario, Holm over the five variants."""
    f = {'gap': scenario_gap, 'change': scenario_change}[kind]
    return stats.family({v: _full(f(contrast, v, metric)) for v in SCENARIO_VARIANTS})


def scenario():
    means = {arm(s, v): {m: mean_of(arm(s, v), m) for m in SCENARIO_METRICS}
             for v in (None,) + SCENARIO_VARIANTS for s in SCENARIO_STACKS}
    fire_means = {arm(s, v): {f: {m: mean_of(arm(s, v), m, fire=f) for m in ('psnr', 'loss', 'm1loss')} for f in data.FIRES}
                  for v in (None,) + SCENARIO_VARIANTS for s in SCENARIO_STACKS}
    ranks = {}
    for v in (None,) + SCENARIO_VARIANTS:
        key = 'reference' if v is None else v
        ranks[key] = {'all': sorted(SCENARIO_STACKS, key=lambda s: -means[arm(s, v)]['psnr'])}
        for f in data.FIRES:
            ranks[key][f] = sorted(SCENARIO_STACKS, key=lambda s: -fire_means[arm(s, v)][f]['psnr'])
    families = {kind: {c: {m: scenario_family(kind, c, m) for m in SCENARIO_METRICS} for c in CONTRASTS}
                for kind in ('gap', 'change')}
    reference = {c: {m: _full(scenario_gap(c, None, m)) for m in SCENARIO_METRICS} for c in CONTRASTS}
    return dict(means=means, fire_means=fire_means, ranks=ranks, families=families, reference=reference)


# -------------------------------------------------------------------- report

def _line(label, e):
    return '  %-6s n=%d %+7.2f [%+6.2f, %+6.2f] p=%-9.3g Holm %.3g' % (label, e.n, e.mean, e.lo, e.hi, e.p, e.holm)


def report():
    ld = load()
    print('Load: hybrid - rules per alarm period, GOP 9-3 (Holm over the five periods)')
    for p in PERIODS:
        e, i = ld['psnr'][p], ld['images'][p]
        print('  %-4s rules loss %5.1f %%  PSNR %+6.2f dB p=%.3g Holm %.3g  images %+5.2f'
              % (p, ld['loss'][p], e.mean, e.p, e.holm, i.mean))

    res = fire()
    print('\nFire variants: means over the 60 seeds, GOP 9-3')
    print('  %-14s' % 'arm' + ''.join('%10s' % m[:9] for m in FIRE_METRICS))
    for a, row in res['means'].items():
        print('  %-14s' % a + ''.join('%10s' % ('%.2f' % row[m] if row[m] is not None else '--') for m in FIRE_METRICS))
    g0 = res['reference']['psnr']
    print('\nReference gain hybrid - rules, PSNR: %+.2f [%+.2f, %+.2f] p=%.3g' % (g0.mean, g0.lo, g0.hi, g0.p))
    for kind in ('gain', 'shift-rules', 'shift-hybrid', 'change'):
        for m in ('psnr', 'm1loss', 'usable', 'declared'):
            print('\n%s, %s' % (kind, m))
            for v in FIRE_VARIANTS:
                print(_line(v, res['families'][kind][m][v]))

    res = scenario()
    show = ('psnr', 'loss', 'm1loss', 'usable', 'declared', 'false_declared')
    print('\nScenario variants: means over the 60 seeds, GOP 9-3, T = 9 s')
    print('  %-16s' % 'arm' + ''.join('%10s' % m[:9] for m in show))
    for a, row in res['means'].items():
        print('  %-16s' % a + ''.join('%10s' % ('%.2f' % row[m] if row[m] is not None else '--') for m in show))
    print('\nRules loss per fire (%)')
    for v in (None,) + SCENARIO_VARIANTS:
        print('  %-10s' % (v or 'reference') + ''.join('%8.1f' % res['fire_means'][arm('rules', v)][f]['loss'] for f in data.FIRES))
    print('\nRanking by mean PSNR (best first)')
    for k, r in res['ranks'].items():
        print('  %-10s all %-30s ' % (k, ' '.join(r['all'])) + '  '.join('%s %s' % (f, ' '.join(r[f])) for f in data.FIRES))
    for c in CONTRASTS:
        for m in ('psnr', 'm1loss', 'loss', 'usable', 'declared'):
            ref = res['reference'][c][m]
            if ref is None:
                continue
            print('\n%s, %s: reference %+.2f [%+.2f, %+.2f] p=%.3g' % (c, m, ref.mean, ref.lo, ref.hi, ref.p))
            for kind in ('gap', 'change'):
                for v in SCENARIO_VARIANTS:
                    e = res['families'][kind][c][m][v]
                    if e is not None:
                        print(_line('%s %s' % (kind, v), e))
