"""The assumptions of the article's tests,
checked on the
tests themselves:

  1 normality   the differences, seed by seed, of every paired comparison
                the text, its tables or its figures give with a gap, an
                interval and a p (blocks(): the families of the families
                table, each whole, and the single tests): the sample
                skewness and excess kurtosis, and the Shapiro-Wilk test; a
                comparison two families share, the same differences, is
                tested once; a comparison whose seeds all give the same
                value has no test of its shape
  2 wilcoxon    every test of 1 again by Wilcoxon's signed-rank test,
                corrected by Holm in the same family: the tests whose
                conclusion at 0.05 differs from that of Student's test
  3 anova       the repeated-measures ANOVA of the PSNR of the three
                cross-layer stacks (analysis/comparative.py): the normality
                of the residuals of each stratum, the seed means between the
                seeds and the orthonormal contrasts of each within-seed
                term, each centered on its fire (Shapiro-Wilk per contrast,
                Mardia's multivariate skewness and kurtosis per stratum);
                the equality across the three fires of the covariance of the
                nine within-seed conditions (stack x GOP), and of each
                stratum's contrasts, which Mauchly's test pools (Box's M)

The coverage check closes section 1: every interval the French text writes
('+1,52 dB [1,12 ; 1,92]', or an interval alone) is the interval of one of
the tests, at the decimals written."""
import re
from decimal import Decimal

import numpy as np

from ..common import data, stats
from ..common.notation import half_up
from . import ablation, access_robustness, coding, comparative, controls, quality, robustness, round2

ALPHA = 0.05
GOP = data.GOP
AGENT = {'P': 'path', 'C': 'congestion', 'B': 'link-break detection', 'D': 'discovery', 'A': 'channel access',
         'T': 'power', 'E': 'early discard'}
SOURCE = {'psnr': 'PSNR (dB)', 'm1loss': 'M1 loss (points)', 'loss': 'loss (points)', 'usable': 'images >= 28 dB',
          'usable25': 'images >= 25 dB', 'usable31': 'images >= 31 dB', 'delay_mean': 'mean delay (ms)',
          'late': 'missed deadlines (points)', 'on_time': 'received in time (points)', 'declared': 'declarations'}


class Block:
    """A family of the families table (family: its name; every test of the
    family, Holm within it) or a group of single tests (family None)."""

    def __init__(self, experiment, family, title, tests):
        self.experiment, self.family, self.title = experiment, family, title
        self.tests = [(str(label), e) for label, e in tests if e is not None]


def _family(experiment, series, size, title, tests, label=str):
    """A family of the families table from an analysis function's dict of
    Estimates, their holm set; checks it is whole: the holm of each is
    Holm's correction of the p of the tests given."""
    b = Block(experiment, round2.family_name(experiment, series, size), title,
              [(label(k), e) for k, e in tests.items()])
    assert len(b.tests) == size, (title, len(b.tests), size)
    for (_, e), h in zip(b.tests, stats.holm([e.p for _, e in b.tests])):
        assert e.holm is not None and abs(e.holm - h) < 1e-12, title
    return b


def _single(experiment, title, tests):
    return Block(experiment, None, title, tests)


def _main_frames(arm, period='p7'):
    """{seed: main frames 2 to 12 whose level M1 loses at most 5 % of its
    packets} at the alarm period, from frames.tsv (claims P29)."""
    out = {}
    for r in data.table('frames.tsv') or ():
        if r['arm'] == arm and r['period'] == period:
            k = (r['fire'], r['realisation'])
            out[k] = out.get(k, 0) + (int(r['image']) in (2, 3, 4, 5, 6, 8, 10, 12) and float(r['l1loss']) <= 5)
    return out


def blocks():
    """Every test the text cites with a gap, an interval and a p, in the
    order of the results: the families of the families table, each whole
    (its PSNR, and the other measures it covers), and the single tests."""
    rs = comparative.rows()
    psnr, m1 = comparative.cells(rs, 'psnr'), comparative.cells(rs, 'm1loss')
    out = []
    add = out.append

    # E0, the main study
    for a, b in comparative.PAIRS:
        add(_family('E0', 'E0', 9, 'PSNR (dB), %s - %s, per cell (20 seeds)' % (a, b), comparative.paired_cells(psnr, a, b),
                    lambda k: '%s, GOP %s' % (k[0], GOP[k[1]])))
    for a, b in (('hybrid', 'rules'), ('agents', 'rules'), ('hybrid', 'agents')):
        add(_family('E0', 'E0', 3, 'PSNR (dB), %s - %s, per GOP' % (a, b), comparative.paired_gops(psnr, a, b), GOP.get))
    add(_family('E0', 'E0', 3, 'M1 loss (points), hybrid - rules, per GOP', comparative.paired_gops(m1, 'hybrid', 'rules'), GOP.get))
    for m, pairs in (('usable', (('hybrid', 'rules'), ('agents', 'rules'))), ('usable25', (('hybrid', 'rules'),)),
                     ('usable31', (('hybrid', 'rules'),)), ('delay_mean', (('hybrid', 'rules'),)),
                     ('late', (('hybrid', 'rules'),))):
        for a, b in pairs:
            add(_family('E0', 'E0', 3, '%s, %s - %s, per GOP' % (SOURCE[m], a, b), quality.gops(a, b, m), GOP.get))
    add(_single('E0', 'each seed averaged over the three GOPs', [
        ('PSNR, hybrid - rules', comparative.per_seed(psnr, 'hybrid', 'rules')[0]),
        ('PSNR, agents - rules', comparative.per_seed(psnr, 'agents', 'rules')[0]),
        ('PSNR, hybrid - agents', comparative.per_seed(psnr, 'hybrid', 'agents')[0]),
        ('PSNR, rules - AOMDV', comparative.per_seed(psnr, 'rules', 'aomdv')[0]),
        ('M1 loss, hybrid - rules', comparative.per_seed(m1, 'hybrid', 'rules')[0]),
        ('M1 loss, hybrid - agents', comparative.per_seed(m1, 'hybrid', 'agents')[0]),
        ('loss, hybrid - rules', comparative.per_seed(comparative.cells(rs, 'loss'), 'hybrid', 'rules')[0]),
        ('images >= 28 dB, hybrid - rules', quality.over_gops('hybrid', 'rules', 'usable'))]))

    # E1, AOMDV, its control and its tuned timers
    for a, b in (('pq-ctl', 'pq'), ('pq-tuned', 'pq-ctl'), ('rules', 'pq-tuned')):
        add(_family('E1', 'ctl', 3, 'PSNR (dB), %s - %s, per GOP' % (a, b), quality.gops(a, b, 'psnr'), GOP.get))
    for m in ('loss', 'm1loss'):
        add(_family('E1', 'ctl', 3, '%s, rules - pq-tuned, per GOP' % SOURCE[m], quality.gops('rules', 'pq-tuned', m), GOP.get))
    add(_single('E1', 'each seed averaged over the three GOPs',
                [('PSNR, %s - %s' % (a, b), quality.over_gops(a, b, 'psnr')) for a, b in
                 (('pq-ctl', 'pq'), ('pq-tuned', 'pq-ctl'), ('rules', 'pq-tuned'))]))

    # E2, the contribution of each agent, GOP 9-3
    alone, inside = ablation.effects('psnr')
    add(_family('E2', 'E2', 7, 'PSNR (dB), the agent alone on the rule stack: rules-onlyX - rules', alone, AGENT.get))
    add(_family('E2', 'E2', 6, 'PSNR (dB), the agent in the hybrid stack: hybrid - hybrid-noX',
                {x: inside[x] for x in ablation.HYBRID}, AGENT.get))
    add(_family('E2', 'E2', 6, 'PSNR (dB), effect in the hybrid stack - effect alone', ablation.interactions('psnr'), AGENT.get))
    add(_family('E2', 'E2', 2, 'PSNR (dB), the learning stacks - the access-only stack, constant exploration',
                ablation.against_access(('hybrid', 'agents'))))
    add(_family('E2', 'E2', 2, 'PSNR (dB), the learning stacks - the access-only stack, decaying exploration',
                ablation.against_access(('hybrid-edec', 'agents-edec'))))
    for c in round2.ACCESS_COMPARISONS:
        add(_family('E2', 'onlyA', 3, 'PSNR (dB), %s, per GOP' % c, round2.access_gops(c), GOP.get))
    # control 2: the four learned configurations frozen, one
    # family per stack and reference, once their replays are all in round2.tsv;
    # the four fixed CSMA/CA settings it replaced left the text, and the set
    for st in ('rules', 'hybrid'):
        for ref in ('agent', 'standard'):
            learned = round2.learned_csma(st, ref)
            if learned is not None:
                add(_family('E2', 'learned', 4, 'PSNR (dB), learned configuration frozen on the %s stack - %s'
                            % (st, round2.REFERENCES[st][ref]), learned, 'configuration k%d'.__mod__))
    # the M1 loss and the declarations of the ablations: the ablations table
    # gives their means; the text gives the channel-access agent's, alone on
    # the rule stack, with its interval and its p
    m1e, decl = ablation.effects('m1loss'), ablation.effects('declared')
    # the link-break agent in the hybrid stack, agents - hybrid, is a test of
    # E0 (hybrid - agents per GOP, above); the access-only stack's other
    # measures, against the rule stack, are the single tests of section 3.6,
    # its M1 loss at GOP 9-3 the one of the ablations
    access = [('%s, access - rules, GOP %s' % (SOURCE[m].partition(' (')[0], GOP[s]), e)
              for m in ('m1loss', 'usable', 'delay_mean') for s, e in round2.access_gops('access - rules', m).items()
              if (m, s) != ('m1loss', '9M3D')]
    singles = [('PSNR, hybrid-noA - rules', stats.paired(ablation.values('hybrid-noA', 'psnr'), ablation.values('rules', 'psnr'))),
               ('PSNR, hybrid - rules - the six effects alone (interaction)', ablation.additivity('psnr')),
               ('M1 loss, %s alone: rules-onlyA - rules' % AGENT['A'], m1e[0]['A']),
               ('declarations, %s alone: rules-onlyA - rules' % AGENT['A'], decl[0]['A'])] + access
    # the four fixed and uniform CSMA/CA settings of the first version of the
    # learned-configuration series, against the agent that learns on each
    # stack: single tests, outside the plan since the second round (sections 2.7 and 3.3)
    singles += [('PSNR, fixed CSMA/CA %s on the %s stack - %s' % (setting, st, round2.REFERENCES[st]['agent']),
                 stats.paired(round2.values('%s-%s-s11' % (st, setting), 'psnr'), round2.values(round2.REFERENCES[st]['agent'], 'psnr')))
                for st in ('rules', 'hybrid') for setting, *_ in round2.SETTINGS]
    add(_single('E2', 'the single tests of E2: PSNR outside the families, the other measures', singles))

    # E3, the adaptation of the agents
    add(_family('E3', 'frozen', 3, 'PSNR (dB), hybrid - hybrid-frozen, per GOP', quality.gops('hybrid', 'hybrid-frozen', 'psnr'), GOP.get))
    add(_family('E3', 'frozen', 3, 'PSNR (dB), hybrid-frozen - rules, per GOP', quality.gops('hybrid-frozen', 'rules', 'psnr'), GOP.get))
    add(_family('E3', 'split', 4, 'PSNR (dB), the crossing of learning and exploration, hybrid stack, GOP 9-3',
                round2.crossing('psnr'), lambda c: '%s (%s - %s)' % next((c, a, b) for k, a, b in round2.CROSSING if k == c)))
    add(_family('E3', 'edec', 2, 'PSNR (dB), decaying - constant exploration', controls.decay('psnr')))
    add(_family('E3', 'edec', 3, 'PSNR (dB), the agents stack under decaying exploration among the others', controls.decayed_agents(),
                {'rules': 'agents-edec - rules', 'hybrid-edec': 'agents-edec - hybrid-edec', 'hybrid': 'hybrid - agents-edec'}.get))
    for level, _ in round2.LEVELS:
        for ref in round2.BREAK_REFERENCES:
            add(_family('E3', 'break', 3, 'PSNR (dB), %s - %s, per GOP' % (level, ref), round2.link_break(level, ref), GOP.get))
    singles = [('PSNR, hybrid - hybrid-frozen, each seed over the three GOPs', quality.over_gops('hybrid', 'hybrid-frozen', 'psnr')),
               ('PSNR, hybrid-frozen - rules, each seed over the three GOPs', quality.over_gops('hybrid-frozen', 'rules', 'psnr')),
               ('PSNR, effect of the decay, agents - hybrid', controls.decay_difference()),
               ('PSNR, agents-frozen - hybrid-frozen, GOP 9-3',
                stats.paired(quality.values('agents-frozen', 'psnr', '9M3D'), quality.values('hybrid-frozen', 'psnr', '9M3D'))),
               ('PSNR, images 1 to 6, hybrid - agents-edec', stats.paired(controls.images('hybrid', 1, 6), controls.images('agents-edec', 1, 6))),
               ('PSNR, images 7 to 12, hybrid - agents-edec', stats.paired(controls.images('hybrid', 7, 12), controls.images('agents-edec', 7, 12))),
               ('PSNR, agents-bdec-s11 - agents-edec, GOP 9-3', round2.outside('psnr')[(round2.OUTSIDE[2][0], '9M3D')]),
               ('PSNR, exploration only - learning only, hybrid stack, GOP 9-3', round2.outside('psnr')[(round2.OUTSIDE[0][0], '9M3D')]),
               ('declarations, hybrid-frozen - rules, GOP 9-3', stats.paired(quality.values('hybrid-frozen', 'declared', '9M3D'),
                                                                        quality.values('rules', 'declared', '9M3D'))),
               ]
    singles += [('RREQ, agents-tr - hybrid-tr', stats.paired(controls.values('agents-tr', 'rreq_all'), controls.values('hybrid-tr', 'rreq_all'))),
                ('RERR, agents-tr - hybrid-tr', stats.paired(controls.values('agents-tr', 'rerr'), controls.values('hybrid-tr', 'rerr')))]
    if controls.cases('rules', 'n') is not None:
        singles += [('share of the declarations of a living neighbour over a link in the budget (points), agents-tr - rules, simulations '
                     'that declare', stats.paired(controls.case_share('agents-tr', ['budget']), controls.case_share('rules', ['budget'])))]
    add(_single('E3', 'the single tests of E3: PSNR over the GOPs and outside the families, the other measures', singles))

    # E4, video coding
    add(_family('E4', 'rate', 4, 'PSNR (dB), equal rate - T = 9 s, per stack and GOP', coding.volume_shares(),
                lambda k: '%s, GOP %s' % (k[0], GOP[k[1]])))
    add(_family('E4', 'rate', 2, 'PSNR (dB), hybrid - rules at equal rate, per GOP', coding.equal_rate_gaps(), GOP.get))
    test1, test2 = coding.coefficient_tests()
    add(_family('E4', 'coding', 4, 'PSNR (dB), coefficient 0.1 - 0.01, per stack', test2))
    add(_family('E4', 'coding', 2, 'PSNR (dB), at the coefficient 0.1', test1))
    singles = []
    for s in ('rules', 'hybrid'):
        nine = coding.values(s, 'psnr', '9M3D')
        singles += [('PSNR, %s, GOP 9-3 - GOP 3-9 at T = 9 s' % s, stats.paired(nine, coding.values(s, 'psnr', '3M9D'))),
                    ('PSNR, %s, GOP 9-3 - GOP 3-9 at equal rate' % s, stats.paired(nine, coding.values(s, 'psnr', '3M9D', 'p9r65'))),
                    ('PSNR, %s, GOP 9-3 - GOP 6-6 at equal rate' % s, stats.paired(nine, coding.values(s, 'psnr', '6M6D', 'p9r32')))]
    add(_single('E4', 'the effect of the GOP, single tests', singles))

    # E5, the reach of the lead
    # the load, fire and scenario tables give the PSNR gaps with their
    # interval and their p; the other measures keep the families whose gaps
    # the text gives: the loss and the M1 loss at 7 and 12 s, the M1 loss with
    # the camera and the sink exchanged
    for a, b, m in (('hybrid', 'rules', 'psnr'), ('hybrid', 'rules', 'loss'), ('hybrid', 'rules', 'm1loss'),
                    ('agents', 'rules', 'psnr')):
        add(_family('E5', 'load', 5, '%s, %s - %s, per alarm period' % (SOURCE[m], a, b), robustness.period_family(a, b, m),
                    lambda p: 'T = %s s' % p[1:]))
    for kind in ('gain', 'change'):
        add(_family('E5', 'fire', 7, '%s, fire variants, %s' % (SOURCE['psnr'], kind), robustness.fire_family(kind, 'psnr')))
    for kind, c, m in (('gap', 'hybrid-rules', 'psnr'), ('gap', 'hybrid-rules', 'm1loss'),
                       ('change', 'hybrid-rules', 'psnr'), ('gap', 'agents-rules', 'psnr'), ('gap', 'hybrid-agents', 'psnr')):
        add(_family('E5', 'scenario', 5, '%s, scenario variants, %s %s' % (SOURCE[m], kind, c), robustness.scenario_family(kind, c, m)))
    # E4 and E5, the access-only stack (tranche T7): the PSNR of its two
    # comparisons over each series, and its two single tests at the
    # coefficient 0.1; the text gives none of its secondary measures there
    if access_robustness.active():
        single = []
        for (series, c), fam in access_robustness.families().items():
            title = 'PSNR (dB), %s, %s' % (c, access_robustness.TITLES[series])
            if access_robustness.FAMILY[series]:
                add(_family(access_robustness.EXPERIMENT[series], series, access_robustness.FAMILY[series], title, fam))
            else:
                single += [(title, e) for e in fam.values()]
        add(_single('E4', 'the access-only stack at the coefficient 0.1', single))
    frames = stats.paired(_main_frames('hybrid'), _main_frames('rules')) if data.table('frames.tsv') else None
    add(_single('E5', 'the reference rows and the mechanism at T = 7 s', [
        ('PSNR, hybrid - rules, the reference of the fire series', stats.estimate(robustness.fire_contrast('gain', None, 'psnr').values())),
        ('PSNR, hybrid - rules, the reference of the scenario series',
         stats.estimate(robustness.scenario_gap('hybrid-rules', None, 'psnr').values())),
        ('PSNR, agents - rules, the reference of the scenario series',
         stats.estimate(robustness.scenario_gap('agents-rules', None, 'psnr').values())),
        ('main frames with at most 5 % of their M1 lost, hybrid - rules, T = 7 s', frames)]))
    return out


# ---------------------------------------------------------------- tests

def checks(bs=None):
    """Per block, its tests with their checks: (block, [(label, e, shape,
    sw, wx, wx_holm)]); shape (g1, g2), sw (W, p), both (None, None) for a
    comparison whose seeds all give the same value; wx Wilcoxon's dict,
    wx_holm its p corrected in the block when it is a family."""
    out = []
    for b in bs or blocks():
        rows = []
        wx = [stats.wilcoxon(e.values) for _, e in b.tests]
        adj = stats.holm([w['p'] for w in wx]) if b.family else [w['p'] for w in wx]
        for (label, e), w, h in zip(b.tests, wx, adj):
            flat = constant(e)
            rows.append((label, e, (None, None) if flat else stats.shape(e.values),
                         (None, None) if flat else stats.shapiro_wilk(e.values), w, h))
        out.append((b, rows))
    return out


def is_psnr(block, label):
    """A test of the PSNR: the measure opens the title of a family and the
    label of a single test."""
    return (block.title if block.family else label).startswith('PSNR')


def constant(e):
    """Every seed gives the same difference: no shape to test."""
    return max(e.values) == min(e.values)


def same_comparison(e, f):
    """The same differences, up to their order and their sign, within the
    rounding of the tables (comparative.tsv keeps four decimals, revision.tsv
    six digits): the same comparison in two blocks."""
    if e.n != f.n:
        return False
    a, b = np.sort(e.values), np.sort(f.values)
    return bool(np.allclose(a, b, rtol=0, atol=1e-3) or np.allclose(a, np.sort(-b), rtol=0, atol=1e-3))


# ------------------------------------------------------------- coverage

def coverage(bs):
    """(intervals, unmatched, written): every interval '[lo ; hi]' of the
    French text, with the gap written before it if any; those no test of the
    blocks, and no partial eta squared of the ANOVA, gives at the decimals
    written (either sign); and the ids of the Estimates whose interval the
    text writes. None without the text."""
    from ..claims import checks as written_form
    text = written_form.source_text('text')
    if text is None:
        return None
    estimates = [e for b in bs for _, e in b.tests] + list(comparative.effect_sizes(comparative.rows()).values())
    interval = re.compile(r'\[(%s) ; (%s)\]' % (written_form.NUMBER, written_form.NUMBER))
    gaps = {m.start('lo') - 1: m for m in written_form.WRITTEN_GAP.finditer(text)}

    def same(x, s):
        v, nd = written_form.written(s)
        return half_up(x, nd) == Decimal(repr(v)).quantize(Decimal(1).scaleb(-nd))

    total, missed, cited = 0, [], set()
    for m in interval.finditer(text):
        total += 1
        g = gaps.get(m.start())
        if g is not None and text[g.start('d') - 1:g.start('d')] == '-':
            g = None   # the second half of a GOP, '6-6 exclut zéro ([0,07 ; 0,95]', is no gap
        hits = [e for e in estimates for sign, lo, hi in ((1, e.lo, e.hi), (-1, -e.hi, -e.lo))
                if same(lo, m[1]) and same(hi, m[2]) and (g is None or same(sign * e.mean, g['d']))]
        cited.update(id(e) for e in hits)
        if not hits:
            missed.append(text[max(0, m.start() - 70):m.end()])
    return total, missed, cited


# ------------------------------------------------------------ the ANOVA

def anova_checks(rs=None, metric='psnr'):
    """The assumptions of the repeated-measures ANOVA of the three
    cross-layer stacks: dict(normal=[(stratum, contrast, W, p, g1, g2)],
    mardia={stratum: Mardia's dict}, box={stratum or 'conditions': Box's
    dict}); 'seed means' is the between-seed stratum, of the fire's test."""
    rs = rs or comparative.rows()
    y, fire, stacks, splits = stats.within_design([r for r in rs if r['stack'] != 'aomdv'], metric)
    scores = stats.contrast_scores(y)
    names = {'stack': _contrast_names(stacks), 'split': _contrast_names([GOP[s] for s in splits])}
    names['stack x split'] = ['(%s) x (%s)' % (a, b) for a in names['stack'] for b in names['split']]
    normal = []
    seed = stats.within_fires(y.mean(axis=(1, 2))[:, None], fire)[:, 0]
    normal.append(('seed means', 'between the seeds') + stats.shapiro_wilk(seed) + stats.shape(seed))
    for name, z in scores.items():
        r = stats.within_fires(z, fire)
        for j in range(r.shape[1]):
            normal.append((name, names[name][j]) + stats.shapiro_wilk(r[:, j]) + stats.shape(r[:, j]))
    mardia = {name: stats.mardia(stats.within_fires(z, fire)) for name, z in scores.items()}
    fires = sorted(set(fire))
    box = {'conditions': stats.box_m([y[fire == f].reshape((fire == f).sum(), -1) for f in fires])}
    box.update({name: stats.box_m([z[fire == f] for f in fires]) for name, z in scores.items()})
    return dict(normal=normal, mardia=mardia, box=box, n=len(fire), conditions=len(stacks) * len(splits))


def _contrast_names(levels):
    """The Helmert contrasts of stats.helmert, named by their levels: the
    j-th sets the first j levels against level j + 1."""
    return ['%s - %s' % (' + '.join(levels[:j]), levels[j] if j == 1 else '%d %s' % (j, levels[j])) for j in range(1, len(levels))]


# --------------------------------------------------------------- report

def _p(p):
    return '%.3g' % p if p >= 0.001 else '%.1e' % p


def _verdict(sig):
    return 'significant' if sig else 'not significant'


def _head(b):
    return '\n  %s  %s%s' % (b.experiment, b.title, ', Holm within "%s"' % b.family if b.family else ', single tests')


def _where(b, label, e, cited):
    """Where the text has the test: its interval written, or only its family
    (a range, a bound on p or a table)."""
    if cited is None:
        return ''
    return 'interval in the text' if id(e) in cited else 'in its family or a table, interval not written'


def summary():
    """Everything the report prints, computed once, for the report and for
    the checks of the text (claims): blocks and rows (checks()); tests, the
    (block, row) pairs; families, the family blocks, and family_tests, their
    tests; coverage (coverage(), None without the text) and cited, the ids
    of the Estimates whose interval the text writes; distinct, the
    comparisons with a shape, each once, (block, label, e, shape, sw); flat,
    those whose seeds all give the same difference, (block, label, e);
    rejected, the distinct ones whose normality Shapiro-Wilk rejects at
    0.05; psnr, the distinct ones of the PSNR; differ, the tests whose
    conclusion at 0.05 Wilcoxon changes, (block, label, e, Student's p,
    Wilcoxon's p, Student significant, Wilcoxon significant), each p Holm's
    in a family; anova (anova_checks())."""
    bs = blocks()
    rows = checks(bs)
    tests = [(b, r) for b, rs_ in rows for r in rs_]
    families = [b for b in bs if b.family]
    cov = coverage(bs)
    distinct, flat = [], []
    for b, (label, e, shape, sw, w, h) in tests:
        if constant(e):
            flat.append((b, label, e))
        elif not any(same_comparison(e, x[2]) for x in distinct):
            distinct.append((b, label, e, shape, sw))
    differ = []
    for b, (label, e, shape, sw, w, h) in tests:
        pt = e.holm if b.family else e.p
        if (pt < ALPHA) != (h < ALPHA):
            differ.append((b, label, e, pt, h, pt < ALPHA, h < ALPHA))
    return dict(blocks=bs, rows=rows, tests=tests, families=families, family_tests=sum(len(b.tests) for b in families),
                coverage=cov, cited=cov[2] if cov else None, distinct=distinct, flat=flat,
                rejected=[x for x in distinct if x[4][1] < ALPHA], psnr=[x for x in distinct if is_psnr(x[0], x[1])],
                differ=differ, anova=anova_checks())


def report():
    S = summary()
    rows, tests, fams, n_fam = S['rows'], S['tests'], S['families'], S['family_tests']
    cov, cited, distinct, flat, rejected, psnr, differ = (S[k] for k in ('coverage', 'cited', 'distinct', 'flat', 'rejected',
                                                                         'psnr', 'differ'))

    print('1. Normality of the paired differences, seed by seed')
    print('   %d tests: %d families (the families of the families table, one per comparison, metric or level they '
          'name; %d tests, Holm within each) and %d single tests' % (len(tests), len(fams), n_fam, len(tests) - n_fam))
    if cov is None:
        print('   the French text is not here: its intervals are not checked against the tests')
    else:
        print('   the French text: %d of its %d intervals are those of these tests, at the decimals written; %d of the '
              'tests have their interval written there' % (cov[0] - len(cov[1]), cov[0], len({id(e) for _, (_, e, *_) in tests} & cited)))
        for ctx in cov[1]:
            print('     not a test of the set: ...%s' % ctx)
    print('   %d distinct comparisons (a comparison several blocks share is tested once, where it first comes), %d of them '
          'with every seed at the same difference, which leaves %d with a shape to test, %d of them of the PSNR'
          % (len(distinct) + len(flat), len(flat), len(distinct), len(psnr)))
    print('   Shapiro-Wilk (Royston AS R94) at 0.05: %d of the %d reject normality, %.1f expected under normality; '
          '%d of the %d of the PSNR, %d of the %d other measures; g1 and g2: the skewness and the excess kurtosis'
          % (len(rejected), len(distinct), ALPHA * len(distinct), sum(is_psnr(x[0], x[1]) for x in rejected), len(psnr),
             sum(not is_psnr(x[0], x[1]) for x in rejected), len(distinct) - len(psnr)))
    current = None
    for b, label, e, (g1, g2), (w, p) in distinct:
        if b is not current:
            print(_head(b))
            current = b
        print('    %-62s n=%2d  %+8.2f  g1 %+5.2f  g2 %+6.2f  W %.4f  p %-8s%s'
              % (label, e.n, e.mean, g1, g2, w, _p(p), '  rejects normality' if p < ALPHA else ''))
    print('\n  Every seed at the same difference, %d (no shape; Student p = 1, Wilcoxon p = 1):' % len(flat))
    for b, label, e in flat:
        print('    %s  %s: %s' % (b.experiment, b.title, label))
    print('\n  The comparisons whose normality is rejected at 0.05, %d, smallest p first:' % len(rejected))
    for b, label, e, (g1, g2), (w, p) in sorted(rejected, key=lambda x: x[4][1]):
        print('    %s  %s: %s  n=%d  g1 %+.2f  g2 %+.2f  W %.4f  p %s  (%s)'
              % (b.experiment, b.title, label, e.n, g1, g2, w, _p(p), _where(b, label, e, cited) or '-'))

    print('\n2. Wilcoxon signed-rank test, normal approximation (zeros dropped, ties at their midrank), Holm in the same '
          'families; t p: Student\'s, Holm\'s in a family')
    for b, rs_ in rows:
        print(_head(b))
        for label, e, shape, sw, w, h in rs_:
            pt = e.holm if b.family else e.p
            t_sig, w_sig = pt < ALPHA, h < ALPHA
            print('    %-62s t p %-8s  Wilcoxon n=%2d z %+6.2f p %-8s%s  %s / %s%s'
                  % (label, _p(pt), w['n'], w['z'], _p(w['p']), ' Holm %-8s' % _p(h) if b.family else '',
                     _verdict(t_sig), _verdict(w_sig), '  DIFFERS' if t_sig != w_sig else ''))
    print('\n  %d tests (%d in families, %d single): the conclusion at 0.05 differs for %d'
          % (len(tests), n_fam, len(tests) - n_fam, len(differ)))
    for b, label, e, pt, h, t_sig, w_sig in differ:
        print('    %s  %s: %s  %+.2f [%+.2f, %+.2f]  t p %s (%s), Wilcoxon p %s (%s); %s'
              % (b.experiment, b.title, label, e.mean, e.lo, e.hi, _p(pt), _verdict(t_sig), _p(h), _verdict(w_sig),
                 _where(b, label, e, cited) or '-'))

    a = S['anova']
    print('\n3. The assumptions of the repeated-measures ANOVA of the PSNR, the three cross-layer stacks, %d seeds' % a['n'])
    print('  normality of the residuals of each stratum, centered on their fire: Shapiro-Wilk, skewness g1, excess kurtosis g2')
    for stratum, contrast, w, p, g1, g2 in a['normal']:
        print('    %-14s %-44s W %.4f  p %-8s g1 %+5.2f  g2 %+6.2f%s'
              % (stratum, contrast, w, _p(p), g1, g2, '  rejects normality' if p < ALPHA else ''))
    print('  multivariate normality of the contrasts of each within-seed stratum, centered on their fire: Mardia '
          '(covariance with divisor n)')
    for name, m in a['mardia'].items():
        print('    %-14s q %d  skewness b1 %.3f, chi2(%d) %.2f, p %-8s  kurtosis b2 %.3f, z %+.2f, p %s'
              % (name, m['p'], m['b1'], m['df'], m['chi2'], _p(m['p_skew']), m['b2'], m['z'], _p(m['p_kurt'])))
    print('  equal covariance across the three fires (20 seeds each): Box\'s M, chi-square approximation')
    for name, x in a['box'].items():
        what = 'the %d within-seed conditions (stack x GOP)' % a['conditions'] if name == 'conditions' else 'the contrasts of %s' % name
        print('    %-46s p %d  M %7.2f  chi2(%d) %6.2f  p %s' % (what, x['p'], x['M'], x['df'], x['chi2'], _p(x['p_value'])))

    within = [x for x in a['normal'] if x[0] != 'seed means']
    between = next(x for x in a['normal'] if x[0] == 'seed means')
    mardia = [p for m in a['mardia'].values() for p in (m['p_skew'], m['p_kurt'])]
    box = a['box']['conditions']
    strata = [a['box'][k]['p_value'] for k in a['mardia']]
    print('\nSummary. The text, its tables and its figures give %d paired tests with a gap, an interval and a p: %d in %d '
          'families of the families table, %d single. They cover %d distinct comparisons, %d of them with every seed at the '
          'same difference. Of the other %d, Shapiro-Wilk rejects the normality of the differences at 0.05 for %d (%.1f '
          'expected under normality): %d of the %d of the PSNR, %d of the %d other measures. Wilcoxon\'s signed-rank test, '
          'corrected by Holm in the same families, changes the conclusion at 0.05 of %d of the %d tests%s. In the ANOVA of '
          'the PSNR, Shapiro-Wilk rejects the normality of %d of the %d within-seed contrasts (smallest p = %s) and of the '
          'seed means, the stratum of the fire (p = %s); Mardia\'s skewness and kurtosis of the contrasts of the three '
          'within-seed strata give p from %s to %s; Box\'s M test of an equal covariance of the %d conditions across the '
          'three fires gives chi2(%d) = %.1f, p = %s, and p from %s to %s for the contrasts of the three strata.'
          % (len(tests), n_fam, len(fams), len(tests) - n_fam, len(distinct) + len(flat), len(flat), len(distinct),
             len(rejected), ALPHA * len(distinct), sum(is_psnr(x[0], x[1]) for x in rejected), len(psnr),
             sum(not is_psnr(x[0], x[1]) for x in rejected), len(distinct) - len(psnr), len(differ), len(tests),
             ' (%s)' % '; '.join('%s, %s: %s, Student %s, Wilcoxon %s' % (b.experiment, b.title, label, _p(pt), _p(h))
                                 for b, label, e, pt, h, *_ in differ) if differ else '',
             sum(x[3] < ALPHA for x in within), len(within), _p(min(x[3] for x in within)), _p(between[3]),
             _p(min(mardia)), _p(max(mardia)), a['conditions'], box['df'], box['chi2'], _p(box['p_value']),
             _p(min(strata)), _p(max(strata))))
