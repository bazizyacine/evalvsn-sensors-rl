"""The quality of the images, the delay of the packets and the share of the
packets sent that arrive in time, for the four stacks of the main study
(the quality table), from revision.tsv (values() also reads the arms of study 11 in
round2.tsv, for analysis/round2.py): means over the 60
simulations of a stack and a GOP (three fires, twenty seeds each), and the
paired tests the text cites. Two stacks pair on (fire, realisation) within a
GOP; Holm's correction runs per comparison and metric over the three GOPs,
and, for the per-seed differences averaged over the three GOPs, per
comparison over the metrics."""
from ..common import data, stats

ARMS = (('pq', 'AOMDV'), ('rules', 'Règles'), ('agents', 'Agents'), ('hybrid', 'Hybride'))
# metric, decimals, scale applied to the stored value (the delays in ms); the
# share received in time is derived per simulation (on_time)
METRICS = (('psnr', 2, 1.0), ('usable', 1, 1.0), ('delay_mean', 0, 1000.0), ('late', 2, 1.0), ('on_time', 1, 1.0))
PAIRS = (('hybrid', 'rules'), ('agents', 'rules'), ('hybrid', 'agents'), ('rules', 'pq'), ('hybrid', 'pq'))


def on_time(arm, split):
    """{seed: share of the video packets sent that reach the sink before their
    deadline (%)}: (100 - loss) x (100 - late) / 100, the loss counting the
    packets sent that never arrive and the late share the packets received
    after the next image's first packet left the camera. A simulation that
    delivered nothing has no late share and counts 0 % (two of AOMDV's)."""
    rows = data.table(data.holding(arm))
    loss = data.select(rows, arm, 'loss', split=split)
    late = data.select(rows, arm, 'late', split=split)
    out = {}
    for k, lost in loss.items():
        if k in late:
            out[k] = (100.0 - lost) * (100.0 - late[k]) / 100.0
        elif lost >= 100.0:
            out[k] = 0.0
    return out


def values(arm, metric, split):
    """{seed: value} of one stack or arm at one GOP, T = 9 s, 40 m grid, from
    revision.tsv or, for an arm of study 11, round2.tsv; the delays in ms."""
    if metric == 'on_time':
        return on_time(arm, split)
    scale = dict((m, s) for m, _, s in METRICS).get(metric, 1.0)
    return {k: scale * v for k, v in data.select(data.table(data.holding(arm)), arm, metric, split=split).items()}


def mean(arm, metric, split):
    return stats.mean(values(arm, metric, split).values())


def gops(a, b, metric):
    """{split: Estimate of a - b over the 60 seeds}, T = 9 s, Holm over the
    three GOPs: the family the GOPs of one comparison and one metric form
    (experiments E0, E1 and E3, families table)."""
    return stats.family({s: stats.paired(values(a, metric, s), values(b, metric, s)) for s in data.SPLITS})


def _print_family(title, tests):
    """tests: (label, Estimate); Holm within the list."""
    print(title)
    stats.family(dict(tests))
    for label, e in tests:
        print('  %-28s n=%2d  %+9.4f [%+9.4f, %+9.4f]  p=%.3g  Holm %.3g' % (label, e.n, e.mean, e.lo, e.hi, e.p, e.holm))


def over_gops(a, b, metric):
    """Each seed's difference averaged over the three GOPs, as one-sample data."""
    per = [data.difference(values(a, metric, s), values(b, metric, s)) for s in data.SPLITS]
    return stats.estimate(data.pooled_over_gops(per).values())


def report():
    print('Means per stack and GOP: n, mean, sd, 95 % half-width, min, max (delays in ms)')
    for split in data.SPLITS:
        for arm, fr in ARMS:
            parts = []
            for m, _, _ in METRICS:
                v = list(values(arm, m, split).values())
                n, mu, s, h = stats.spread(v)
                parts.append('%s n=%d %.4f sd %.4f +-%.4f [%.3f, %.3f]' % (m, n, mu, s, h, min(v), max(v)))
            print('  %s %-7s ' % (data.GOP[split], fr) + ' | '.join(parts))

    print('\nUsable images: share of the 12 frames, and simulations with no usable frame')
    for split in data.SPLITS:
        for arm, fr in ARMS:
            v = list(values(arm, 'usable', split).values())
            print('  %s %-7s %.1f %% of frames, %d of %d simulations with none'
                  % (data.GOP[split], fr, 100 * stats.mean(v) / 12, sum(1 for x in v if x == 0), len(v)))

    print('\nLargest per-simulation 95th percentile of the delay (ms), over the three GOPs')
    for arm, fr in ARMS:
        v = [x for split in data.SPLITS for x in values(arm, 'delay_p95', split).values()]
        w = [x for split in data.SPLITS for x in values(arm, 'late', split).values()]
        print('  %-7s max P95 %.0f ms over %d simulations; max missed deadlines %.2f %%' % (fr, max(v), len(v), max(w)))

    for metric, _, _ in METRICS:
        print('\n== %s' % metric)
        for a, b in PAIRS:
            _print_family('  %s - %s, per GOP (Holm over the three GOPs)' % (a, b),
                          [(data.GOP[s], e) for s, e in gops(a, b, metric).items()])

    print('\n== usable images at the bounds of the fair class, 25 and 31 dB: means, then per GOP (Holm over the three GOPs)')
    for m in ('usable25', 'usable31'):
        for split in data.SPLITS:
            print('  %s %s: ' % (m, data.GOP[split]) + ', '.join('%s %.2f' % (fr, mean(arm, m, split)) for arm, fr in ARMS))
        for a, b in (('hybrid', 'rules'), ('hybrid', 'agents')):
            _print_family('  %s %s - %s' % (m, a, b), [(data.GOP[s], e) for s, e in gops(a, b, m).items()])

    print('\n== pooled: each seed averaged over the three GOPs (Holm over the metrics of a comparison)')
    for a, b in PAIRS:
        _print_family('  %s - %s' % (a, b), [(m, over_gops(a, b, m)) for m, _, _ in METRICS])
