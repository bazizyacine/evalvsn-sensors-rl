"""Experiments E1 and E3, the controls of the implementation of AOMDV and of
the adaptation of the agents, from revision.tsv, break-agent.tsv and
break-cases.tsv (the decisions and controls tables): AOMDV on the EvalVSN PHY and MAC
(pq-ctl), the frozen policy, the decaying exploration (edec), the traced arms
(-tr, identical runs to the agents and hybrid stacks), what the traces say
about the link-break agent, and what each declaration of a dead neighbour
hits. Two arms share their seeds, so every test pairs the same seeds; Holm's
correction runs within each family of comparisons."""
from ..common import data, stats

COUNTS = (1, 2, 3, 5)
BINS = (60, 78, 96, 114, 132, 150)


def values(arm, metric, split='9M3D', period='p9'):
    return data.select(data.table(data.holding(arm)), arm, metric, split=split, period=period, dist=None)


def mean(arm, metric):
    """The mean over the 60 seeds at GOP 9-3, or None when the sets do not provide all 60."""
    return stats.complete_mean(values(arm, metric).values(), data.SEEDS)


def cell(arm, metric):
    return stats.mean(values(arm, metric).values())


def brk(arm, col):
    v = [float(r[col]) for r in data.table('break-agent.tsv') if r['arm'] == arm and r[col] != '']
    return stats.mean(v) if v else float('nan')


def images(arm, first, last):
    """{seed: mean PSNR of images first to last} of a traced arm; image 7 is
    captured at 114 s, when the decaying exploration reaches 0."""
    return {(r['fire'], r['realisation']): stats.mean(float(r['img%d' % i]) for i in range(first, last + 1))
            for r in data.table('break-agent.tsv') if r['arm'] == arm}


def decay(metric='psnr'):
    """{stack: Estimate of the decaying exploration minus the constant rate},
    the two learning stacks, Holm over the two."""
    return stats.family({s: stats.paired(values(s + '-edec', metric), values(s, metric)) for s in ('agents', 'hybrid')})


def decay_difference(metric='psnr'):
    """The effect of the decay on the agents stack minus its effect on the
    hybrid stack, seed by seed: a single test."""
    return stats.paired(data.difference(values('agents-edec', metric), values('agents', metric)),
                        data.difference(values('hybrid-edec', metric), values('hybrid', metric)))


def decayed_agents():
    """The agents stack under decaying exploration placed among the others,
    PSNR, Holm over the three: against the rules, against the hybrid stack
    under the same exploration, and the hybrid stack at the constant rate
    minus it."""
    ae = values('agents-edec', 'psnr')
    return stats.family({'rules': stats.paired(ae, values('rules', 'psnr')),
                         'hybrid-edec': stats.paired(ae, values('hybrid-edec', 'psnr')),
                         'hybrid': stats.paired(values('hybrid', 'psnr'), ae)})


def cases(arm, col):
    """{seed: value} of a column of break-cases.tsv (data.CASES and their
    attribution to the failure counts); None without the file."""
    rows = data.table('break-cases.tsv')
    if rows is None:
        return None
    return {(r['fire'], r['realisation']): float(r[col]) for r in rows if r['arm'] == arm and r[col] != ''}


def case_share(arm, cols):
    """{seed: share (%) of its declarations in the cases cols}, over the
    simulations with at least one declaration; None without the file."""
    n = cases(arm, 'n')
    if n is None:
        return None
    per = [cases(arm, c) for c in cols]
    return {k: 100.0 * sum(v[k] for v in per) / n[k] for k in n if n[k] > 0}


def _family(title, tests):
    """tests: (label, a, b); prints each raw p and its Holm correction in the family."""
    print(title)
    fam = stats.family({label: stats.paired(a, b) for label, a, b in tests})
    for label, e in fam.items():
        print('  %-34s n=%d  %+.2f [%+.2f, %+.2f]  p=%.3g  Holm %.3g' % (label, e.n, e.mean, e.lo, e.hi, e.p, e.holm))


def _over_gops(a, b):
    per = [data.difference(values(a, 'psnr', s), values(b, 'psnr', s)) for s in data.SPLITS]
    e = stats.estimate(data.pooled_over_gops(per).values())
    return e.n, e.mean, e.lo, e.hi, e.p


def report():
    print('Arms at GOP 9-3, means over the 60 seeds')
    arms = ('pq', 'pq-ctl', 'rules', 'agents-frozen', 'hybrid-frozen', 'agents', 'hybrid', 'agents-edec', 'hybrid-edec')
    print('  %-14s %6s %6s %6s %6s %7s %7s %6s %6s' % ('arm', 'psnr', 'm1loss', 'loss', 'usable', 'declared', 'false', 'rreq', 'rerr'))
    for a in arms:
        ctl = {'agents': 'agents-tr', 'hybrid': 'hybrid-tr'}.get(a, a)
        row = [cell(a, 'psnr'), cell(a, 'm1loss'), cell(a, 'loss'), cell(a, 'usable')]
        row += [cell(a, m) if values(a, m) else float('nan') for m in ('declared', 'false_declared')]
        row += [cell(ctl, m) if values(ctl, m) else float('nan') for m in ('rreq_all', 'rerr')]
        print('  %-14s %6.2f %6.2f %6.2f %6.2f %7.2f %7.2f %6.0f %6.0f' % ((a,) + tuple(row)))

    print('\nTraced arms against study 09 (identical runs give 0)')
    for a, b in (('agents-tr', 'agents'), ('hybrid-tr', 'hybrid')):
        for m in ('psnr', 'm1loss', 'usable'):
            x, y = values(a, m), values(b, m)
            print('  %s - %s %s: largest difference %.4f' % (a, b, m, max(abs(x[k] - y[k]) for k in x)))

    print('\nLink-break agent, agents stack, per simulation (traced runs)')
    total = sum(brk('agents', 'pick%d' % k) for k in COUNTS)
    declared = sum(brk('agents', 'decl%d' % k) for k in COUNTS)
    print('  decisions %.1f, share a uniform draw gives one count %.1f %%' % (total, 100 * 0.1 / 4))
    for k in COUNTS:
        print('  count %d: picked %6.1f (%4.1f %%), declared %5.2f (%4.1f %%), best value on %4.1f node-states'
              % (k, brk('agents', 'pick%d' % k), 100 * brk('agents', 'pick%d' % k) / total, brk('agents', 'decl%d' % k),
                 100 * brk('agents', 'decl%d' % k) / declared, brk('agents', 'best%d' % k)))
    print('  declared %.2f, proved alive within 15 s %.2f, silent %.2f' % (declared, brk('agents', 'alive'), brk('agents', 'silent')))
    other = declared - brk('agents', 'decl1')
    print('  one failure: at least %.0f %% of its %.2f declarations proved alive (the other counts declare %.2f)'
          % (100 * (brk('agents', 'alive') - other) / brk('agents', 'decl1'), brk('agents', 'decl1'), other))

    print('\nDeclarations per 18 s of the alarm, per simulation')
    print('  %-14s' % 'arm' + ''.join('%7d' % t for t in BINS) + '   sum')
    for a in ('rules', 'agents-frozen', 'hybrid', 'agents', 'hybrid-edec', 'agents-edec'):
        v = [brk(a, 't%d' % t) for t in BINS]
        print('  %-14s' % a + ''.join('%7.2f' % x for x in v) + '%7.2f' % sum(v))

    print('\nPSNR of the twelve images, mean over the seeds (dB)')
    for a in ('hybrid', 'agents', 'hybrid-edec', 'agents-edec'):
        print('  %-14s' % a + ''.join('%6.1f' % brk(a, 'img%d' % i) for i in range(1, 13)))

    print()
    _family('E1: AOMDV control against AOMDV, per GOP', [
        (s, values('pq-ctl', 'psnr', s), values('pq', 'psnr', s)) for s in data.SPLITS])
    _family('E1: rules against the AOMDV control, per GOP', [
        (s, values('rules', 'psnr', s), values('pq-ctl', 'psnr', s)) for s in data.SPLITS])
    print('  rules - control, per seed over the three GOPs: n=%d %+.2f [%+.2f, %+.2f] p=%.3g' % _over_gops('rules', 'pq-ctl'))
    print('  control - AOMDV, per seed over the three GOPs: n=%d %+.2f [%+.2f, %+.2f] p=%.3g' % _over_gops('pq-ctl', 'pq'))

    print()
    _family('E3: exploration decay against constant exploration, PSNR', [
        ('agents', values('agents-edec', 'psnr'), values('agents', 'psnr')),
        ('hybrid', values('hybrid-edec', 'psnr'), values('hybrid', 'psnr'))])
    _family('E3: stacks under decay and under constant exploration, PSNR', [
        ('hybrid - agents, constant', values('hybrid', 'psnr'), values('agents', 'psnr')),
        ('hybrid - agents, decay', values('hybrid-edec', 'psnr'), values('agents-edec', 'psnr')),
        ('agents decay - rules', values('agents-edec', 'psnr'), values('rules', 'psnr')),
        ('hybrid decay - rules', values('hybrid-edec', 'psnr'), values('rules', 'psnr'))])
    e = decay_difference()
    print('  effect of the decay, agents minus hybrid: n=%d %+.2f [%+.2f, %+.2f] p=%.3g' % (e.n, e.mean, e.lo, e.hi, e.p))
    for m in ('m1loss', 'loss', 'usable', 'declared'):
        _family('E3: decay against constant, %s' % m, [
            ('agents', values('agents-edec', m), values('agents', m)),
            ('hybrid', values('hybrid-edec', m), values('hybrid', m))])

    print()
    for x, y, title in (('hybrid', 'hybrid-frozen', 'Hybrid and the frozen hybrid'), ('hybrid-frozen', 'rules', 'Frozen hybrid and the rules'),
                        ('agents', 'agents-frozen', 'Agents and the frozen agents'), ('agents-frozen', 'rules', 'Frozen agents and the rules')):
        _family('%s, per GOP' % title, [(s, values(x, 'psnr', s), values(y, 'psnr', s)) for s in data.SPLITS])
    print('  hybrid - frozen, per seed over the three GOPs: n=%d %+.2f [%+.2f, %+.2f] p=%.3g' % _over_gops('hybrid', 'hybrid-frozen'))
    print('  frozen hybrid - rules, per seed over the three GOPs: n=%d %+.2f [%+.2f, %+.2f] p=%.3g' % _over_gops('hybrid-frozen', 'rules'))
    _family('Hybrid against the agents under decay', [
        ('hybrid - agents decay', values('hybrid', 'psnr'), values('agents-edec', 'psnr')),
        ('hybrid - hybrid decay', values('hybrid', 'psnr'), values('hybrid-edec', 'psnr'))])

    late = {a: {(r['fire'], r['realisation']): sum(float(r['t%d' % t]) for t in BINS[3:]) for r in data.table('break-agent.tsv') if r['arm'] == a}
            for a in ('agents', 'hybrid', 'agents-edec', 'hybrid-edec')}
    print('\nDeclarations after 114 s: ' + ', '.join('%s %.2f' % (a, stats.mean(v.values())) for a, v in late.items()))
    for x, y in (('agents-edec', 'hybrid'), ('agents-edec', 'hybrid-edec')):
        e = stats.paired(late[x], late[y])
        print('  %s - %s: n=%d %+.2f [%+.2f, %+.2f] p=%.3g' % (x, y, e.n, e.mean, e.lo, e.hi, e.p))

    for first, last in ((1, 6), (7, 12)):
        print('Images %d to %d: ' % (first, last) + ', '.join(
            '%s %.2f' % (a, stats.mean(images(a, first, last).values())) for a in ('agents', 'hybrid', 'agents-edec', 'hybrid-edec')))
        _family('  paired, images %d to %d' % (first, last), [
            ('agents decay - hybrid', images('agents-edec', first, last), images('hybrid', first, last)),
            ('agents decay - agents', images('agents-edec', first, last), images('agents', first, last))])
