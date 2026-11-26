"""Experiment E4, video coding, from revision.tsv (the equal-rate and
quality-coefficient tables).

  equal rate     GOPs 3-9 and 6-6 at T = 9 s and again at the mean packet rate
                 of GOP 9-3 (T = 9.65 and 9.32 s), against GOP 9-3 at T = 9 s
  coefficient    the four stacks at GOP 9-3 and T = 9 s with the quality
                 coefficient 0.1 (arms -q01, simulated for the 168 s of their
                 counterparts), against the coefficient 0.01 of the main study

The tests of the coefficient series were fixed before the results, and only
they are made: at 0.1, hybrid - rules and agents - rules (Holm over the two);
per stack, 0.1 - 0.01 (Holm over the four)."""
from ..common import data, paths, stats
from . import quality


def packets():
    """{split: packets the camera sends}: the lines of each set's
    encoding/st-priority.dat (the same in every simulation of a GOP), as
    compile/measures.py counts them into methode-mesures.tsv (kind packets,
    keyed by the GOP)."""
    rows = {r['key']: r['value'] for r in data.table('methode-mesures.tsv') if r['kind'] == 'packets'}
    return {s: int(rows[g].split()[0]) for s, g in data.GOP.items()}


PACKETS = packets()


def packets_q01():
    """The packets the camera sends with the video coded at the quality
    coefficient 0.1 (GOP 9-3), which methode-mesures.tsv does not count: the
    video packets sent of each simulation of the coefficient series as the
    article reads it (the -t168-s10 sets), in the oracle file of study 10
    (code/metrics/compile_runs.py); the same in every simulation, or it
    stops."""
    rows = data.read_tsv(paths.results(paths.STUDY_R1, 'oracle.tsv'))
    sent = {int(r['sent']) for r in rows if '_GC-QC-0p1_' in r['set'] and r['set'].endswith('-t168-s10')}
    if len(sent) != 1:
        raise SystemExit('oracle.tsv of study 10: the coefficient series sends %s packets, one count expected' % sorted(sent))
    return sent.pop()


PACKETS_Q01 = packets_q01()
PERIOD = {'p9': 9.0, 'p9r32': 9.32, 'p9r65': 9.65}
EQUAL_RATE = (('3M9D', 'p9r65'), ('6M6D', 'p9r32'))   # the period that gives a GOP the rate of GOP 9-3
FRAMES = 12
STACKS = (('pq', 'AOMDV'), ('rules', 'rules'), ('agents', 'agents'), ('hybrid', 'hybrid'))


def values(arm, metric, split='9M3D', period='p9'):
    return data.select(data.table('revision.tsv'), arm, metric, split=split, period=period)


def mean(arm, split, period, metric):
    """The mean over the 60 seeds, or None when the sets do not provide all 60."""
    return stats.complete_mean(values(arm, metric, split, period).values(), data.SEEDS)


def rate(packets, period):
    """The mean packet rate of the camera over the twelve capture periods."""
    return packets / (FRAMES * PERIOD[period])


def coefficient_tests():
    """The two families of the coefficient series, PSNR."""
    q = {s: values(s + '-q01', 'psnr') for s, _ in STACKS}
    ref = {s: values(s, 'psnr') for s, _ in STACKS}
    for v in list(q.values()) + list(ref.values()):
        if len(v) != data.SEEDS:
            raise SystemExit('the coefficient series needs the 60 seeds of every arm')
    test1 = stats.family({'hybrid - rules': stats.paired(q['hybrid'], q['rules']),
                          'agents - rules': stats.paired(q['agents'], q['rules'])})
    test2 = stats.family({'%s 0.1 - 0.01' % label: stats.paired(q[s], ref[s]) for s, label in STACKS})
    return test1, test2


def gop_gaps():
    """Hybrid - rules at T = 9 s per GOP over the 60 seeds, Holm over the
    three GOPs (the family of E0 that the GOPs form)."""
    return quality.gops('hybrid', 'rules', 'psnr')


def equal_rate_gaps():
    """Hybrid - rules at equal rate, GOP 3-9 at T = 9.65 s and GOP 6-6 at
    9.32 s, Holm over the two GOPs."""
    return stats.family({s: stats.paired(values('hybrid', 'psnr', s, p), values('rules', 'psnr', s, p))
                         for s, p in EQUAL_RATE})


def volume_shares():
    """{(stack, split): Estimate of the PSNR at equal rate minus the PSNR at
    T = 9 s}, the rule and hybrid stacks at GOPs 3-9 and 6-6, Holm over the
    four: the part of the effect of the GOP that the traffic volume carries."""
    return stats.family({(s, g): stats.paired(values(s, 'psnr', g, p), values(s, 'psnr', g))
                         for g, p in EQUAL_RATE for s in ('rules', 'hybrid')})


def report():
    print('Hybrid - rules, PSNR: per GOP at T = 9 s (Holm over 3), at equal rate (Holm over 2)')
    for title, fam in (('T = 9 s', gop_gaps()), ('equal rate', equal_rate_gaps())):
        for s, e in fam.items():
            print('  %-10s %s  %+.2f dB [%+.2f, %+.2f]  p=%.3g  Holm %.3g' % (title, data.GOP[s], e.mean, e.lo, e.hi, e.p, e.holm))
    print()
    test1, test2 = coefficient_tests()
    for title, fam in (('Test 1: at the coefficient 0.1, stack minus rules, PSNR (Holm over 2)', test1),
                       ('Test 2: per stack, PSNR at 0.1 minus PSNR at 0.01 (Holm over 4)', test2)):
        print(title)
        for label, e in fam.items():
            print('  %-26s n=%d  %+.2f dB [%+.2f, %+.2f]  p=%.3g  Holm %.3g' % (label, e.n, e.mean, e.lo, e.hi, e.p, e.holm))
        print()
    print('Without a test: means over the 60 seeds, GOP 9-3, T = 9 s')
    print('  %-7s %-5s %8s %9s %9s %8s %8s %13s' % ('stack', 'coef', 'PSNR', 'loss(%)', 'M1(%)', 'images', 'sent', 'rate(pkt/s)'))
    for s, label in STACKS:
        for coef, suffix, sent in (('0.01', '', PACKETS['9M3D']), ('0.1', '-q01', PACKETS_Q01)):
            row = [mean(s + suffix, '9M3D', 'p9', m) for m in ('psnr', 'loss', 'm1loss', 'usable')]
            print('  %-7s %-5s %8.2f %9.1f %9.1f %8.2f %8d %13.2f' % ((label, coef) + tuple(row) + (sent, rate(sent, 'p9'))))
    print('\nEqual rate: mean packet rate per GOP and period')
    for split, period in (('3M9D', 'p9'), ('3M9D', 'p9r65'), ('6M6D', 'p9'), ('6M6D', 'p9r32'), ('9M3D', 'p9')):
        print('  %s %-6s %.2f packets/s' % (data.GOP[split], period, rate(PACKETS[split], period)))
