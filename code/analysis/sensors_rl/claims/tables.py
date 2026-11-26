"""S03: the tables of the results that hold the second round's rows and
columns (the first round's, completed), one line of checks per
group of rows: every cell of the French table, as the table prints it, is
recomputed from data/sensors-rl/article by the functions of the analyses, not
by the module that writes the table.

A row is written here as the reader reads it; its place in the table (the
label its \\multirow writes once over the rows of a group, the box of a p or
of a mean and its half-width) is put back by the type of the values the row
is checked against, so that the whole group is found in the table as one run
of text: two rows exchanged, or a row moved to another group, break it."""
from collections import namedtuple

from ..analysis import ablation, coding, comparative, controls, overhead, quality, robustness, round2
from ..analysis import access_robustness as access
from ..common import data, stats
from ..compile import measures
from .checks import gap_checks, table, written

SPLITS, FIRES, GOP = data.SPLITS, data.FIRES, data.GOP
# What a cell is checked against, beside a number and an Estimate (a gap, its
# interval and, where the cell gives one, its p): the p of a p column, a mean
# and the half-width of its interval, a gap set over its interval.
P = namedtuple('P', 'p')
Mean = namedtuple('Mean', 'mean half')
Over = namedtuple('Over', 'estimate')
ABSENT = ('--', 'non tracé')


def cell(text, x):
    """(the cell as plain reads it in the table, its checks) of a cell the
    reader reads as text, against x; a dash or 'non tracé' is a value the data
    do not give."""
    if text in ABSENT or x is None:
        return text, [(x is None, '=', True, 0) if text in ABSENT else (None, '=', 0, 0)]
    if isinstance(x, P):
        if text.startswith('< '):
            return '\\mbox{<\\;%s}' % text[2:], [(x.p, '<', written(text[2:])[0], 3)]
        return '\\mbox{\\phantom{<\\;}%s}' % text, [(x.p, '=') + written(text)]
    if isinstance(x, Mean):
        m, h = text.split(' ± ')
        return '\\mbox{%s \\pm %s}' % (m, h), [(x.mean, '=') + written(m), (x.half, '=') + written(h)]
    if isinstance(x, Over):
        gap, interval = text.split(' ', 1)
        return '\\begin{tabular}[c]{@{}c@{}}%s\\\\ %s\\end{tabular}' % (gap, interval), gap_checks(x.estimate, text)
    if isinstance(x, stats.Estimate):
        return text, gap_checks(x, text)
    return text, [(x, '=') + written(text)]


def claims(C):
    """Adds the rows of S03 to the Claims C."""

    def rows(name, label, group):
        """One line for contiguous rows of fr_NAME.tex: group holds, per row,
        its label as plain reads it, its cells joined by ' & ' and the values
        they are checked against."""
        lines, checks = [], []
        for head, text, xs in group:
            texts = text.split(' & ')
            assert len(texts) == len(xs), (name, head, len(texts), len(xs))
            got = [cell(t, x) for t, x in zip(texts, xs)]
            lines.append(' & '.join([head] + [form for form, _ in got]).strip())
            checks += [c for _, cs in got for c in cs]
        C.claim('S03', label, ' \\\\ '.join(lines), checks, source=table(name))

    def several(head, i, n):
        """The label of row i of a group of n: the group's, written once."""
        return '\\multirow[m]{%d}{*}{%s} &' % (n, head) if i == 0 else '&'

    rs = comparative.rows()
    psnr = comparative.cells(rs, 'psnr')

    # ------------------------------------------- the PSNR per fire and GOP
    def seeds(stack, fire, split):
        """{realisation: PSNR} of a stack in a cell: the main study's, or the
        arm of AOMDV with cross-layer timers and of the access-only stack."""
        if stack not in ('tuned', 'access'):
            return psnr[(fire, split, stack)]
        arm = 'pq-tuned' if stack == 'tuned' else round2.access_only(split)
        return {k[1]: v for k, v in quality.values(arm, 'psnr', split).items() if k[0] == fire}

    def mean(stack, fire, split):
        n, m, _, h = stats.spread(seeds(stack, fire, split).values())
        return Mean(m, h) if n == data.SEEDS // 3 else None

    cells = {
        'F1': ('17,99 ± 0,67 & 19,59 ± 0,45 & 22,10 ± 0,88 & 22,27 ± 1,05 & 21,67 ± 0,82 & 22,40 ± 0,79',
               '18,47 ± 0,69 & 20,98 ± 0,36 & 25,66 ± 0,75 & 27,25 ± 0,53 & 25,07 ± 0,57 & 26,97 ± 0,55',
               '18,72 ± 0,83 & 21,44 ± 0,23 & 27,60 ± 0,72 & 29,20 ± 0,77 & 27,27 ± 0,66 & 29,52 ± 0,49'),
        'F2': ('18,07 ± 0,58 & 19,59 ± 0,48 & 21,32 ± 0,76 & 22,21 ± 1,03 & 21,68 ± 1,00 & 22,45 ± 0,83',
               '18,93 ± 0,86 & 20,73 ± 0,32 & 25,48 ± 0,72 & 26,69 ± 0,66 & 25,28 ± 0,79 & 26,64 ± 0,61',
               '18,62 ± 0,79 & 20,98 ± 0,32 & 27,08 ± 0,94 & 29,66 ± 0,46 & 26,67 ± 0,87 & 29,26 ± 0,57'),
        'F3': ('18,08 ± 0,62 & 20,01 ± 0,25 & 21,29 ± 0,81 & 23,42 ± 0,67 & 21,85 ± 0,81 & 23,10 ± 0,87',
               '18,62 ± 0,73 & 21,00 ± 0,18 & 24,99 ± 0,67 & 27,30 ± 0,43 & 25,35 ± 0,99 & 26,93 ± 0,51',
               '19,09 ± 0,78 & 21,27 ± 0,27 & 27,20 ± 0,92 & 29,01 ± 0,57 & 27,77 ± 0,70 & 29,15 ± 0,66')}
    stacks = ('aomdv', 'tuned', 'rules', 'access', 'agents', 'hybrid')
    for f in FIRES:
        rows('comparatif-psnr', 'tableau du PSNR, %s : moyenne ± demi-largeur de l\'intervalle à 95 %%, six piles, trois GOP' % f,
             [('%s %s' % (several(f, i, 3), GOP[s]), text, [mean(st, f, s) for st in stacks])
              for i, (s, text) in enumerate(zip(SPLITS, cells[f]))])

    # ------------------------------ the gaps per cell, Holm over nine cells
    # (the access-only stack's two comparisons without a test there)
    pairs = [round2.access_cells('access - rules'), round2.access_cells('hybrid - access')]
    pairs += [comparative.paired_cells(psnr, a, b) for a, b in (('hybrid', 'rules'), ('agents', 'rules'), ('hybrid', 'agents'))]
    gaps = {
        'F1': ('+0,16 [−0,89 ; 1,22] & +0,13 [−1,24 ; 1,50] & +0,30 [−1,09 ; 1,69] p = 0,66 & −0,43 [−1,55 ; 0,69] p = 1,00 & '
               '+0,73 [−0,07 ; 1,53] p = 0,14',
               '+1,59 [0,67 ; 2,50] & −0,27 [−0,96 ; 0,41] & +1,31 [0,39 ; 2,23] p = 0,038 & −0,59 [−1,46 ; 0,28] p = 1,00 & '
               '+1,90 [1,01 ; 2,79] p = 0,002',
               '+1,60 [0,46 ; 2,74] & +0,32 [−0,75 ; 1,39] & +1,92 [1,02 ; 2,83] p = 0,002 & −0,33 [−1,39 ; 0,74] p = 1,00 & '
               '+2,25 [1,35 ; 3,14] p < 0,001'),
        'F2': ('+0,89 [−0,45 ; 2,23] & +0,24 [−1,07 ; 1,54] & +1,13 [0,07 ; 2,18] p = 0,11 & +0,36 [−0,78 ; 1,49] p = 1,00 & '
               '+0,77 [−0,48 ; 2,01] p = 0,21',
               '+1,21 [0,39 ; 2,02] & −0,05 [−1,02 ; 0,92] & +1,16 [0,07 ; 2,24] p = 0,11 & −0,20 [−1,51 ; 1,10] p = 1,00 & '
               '+1,36 [0,51 ; 2,21] p = 0,021',
               '+2,58 [1,48 ; 3,69] & −0,40 [−1,20 ; 0,41] & +2,18 [1,22 ; 3,15] p = 0,001 & −0,41 [−1,82 ; 1,00] p = 1,00 & '
               '+2,60 [1,57 ; 3,62] p < 0,001'),
        'F3': ('+2,13 [0,92 ; 3,34] & −0,32 [−1,31 ; 0,67] & +1,81 [0,33 ; 3,29] p = 0,077 & +0,56 [−0,74 ; 1,86] p = 1,00 & '
               '+1,25 [0,08 ; 2,42] p = 0,11',
               '+2,31 [1,59 ; 3,03] & −0,37 [−1,03 ; 0,29] & +1,94 [0,96 ; 2,92] p = 0,004 & +0,36 [−0,58 ; 1,30] p = 1,00 & '
               '+1,58 [0,55 ; 2,61] p = 0,023',
               '+1,81 [0,67 ; 2,94] & +0,14 [−0,79 ; 1,07] & +1,95 [0,96 ; 2,93] p = 0,004 & +0,57 [−0,41 ; 1,55] p = 1,00 & '
               '+1,38 [0,42 ; 2,33] p = 0,028')}
    for f in FIRES:
        rows('comparatif-tests', 'tableau des écarts de PSNR, %s : accès seul − règles, hybride − accès seul (sans test), hybride − '
             'règles, agents − règles, hybride − agents, Holm sur neuf cellules, trois GOP' % f,
             [('%s%s %s' % ('\\addlinespace[2pt] ' if i else '', several(f, i, 6), GOP[s]), text, [p[(f, s)] for p in pairs])
              for i, (s, text) in enumerate(zip(SPLITS, gaps[f]))])

    # -------------------------------------------------------- the ablations
    e, m1, decl = (ablation.effects(m) for m in ('psnr', 'm1loss', 'declared'))
    rows('revision-ablation', 'tableau des ablations, sept agents, seuls sur la pile à règles (Holm sur sept) et dans la pile hybride '
         '(Holm sur six ; la rupture, sa famille de E0) : PSNR, p, perte du niveau M1, déclarations',
         [(head, text, [x for k in (0, 1) for x in (e[k][a], P(e[k][a].holm), m1[k][a].mean, decl[k][a].mean)]) for a, head, text in (
             ('P', 'Chemin', '+0,29 [−0,21 ; 0,79] & 1,000 & −1,7 & −0,2 & +0,02 [−0,29 ; 0,33] & 1,000 & +0,1 & −0,3'),
             ('C', '\\midrule Congestion', '0,00 [−0,37 ; 0,37] & 1,000 & −0,1 & +0,4 & +0,04 [−0,17 ; 0,25] & 1,000 & −0,4 & −0,2'),
             ('A', '\\midrule Accès au canal', '+2,00 [1,38 ; 2,62] & < 0,001 & −5,1 & −14,6 & +2,13 [1,64 ; 2,62] & < 0,001 & −4,5 & −14,8'),
             ('E', '\\midrule Rejet anticipé', '+0,19 [−0,33 ; 0,71] & 1,000 & −0,8 & +0,9 & +0,52 [0,06 ; 0,97] & 0,136 & −1,1 & −0,7'),
             ('D', '\\midrule Découverte', '−0,10 [−0,63 ; 0,43] & 1,000 & −0,9 & −0,1 & +0,09 [−0,32 ; 0,50] & 1,000 & +0,2 & 0,0'),
             ('T', '\\midrule Puissance', '0,00 [0,00 ; 0,00] & 1,000 & 0,0 & 0,0 & 0,00 [0,00 ; 0,00] & 1,000 & 0,0 & 0,0'),
             ('B', '\\midrule Détection de rupture', '−1,42 [−2,08 ; −0,75] & < 0,001 & +5,7 & +6,1 & −2,07 [−2,61 ; −1,54] & < 0,001 & +5,8 & +12,6'))])

    # --------------------------------------------------------- the controls
    def control(arm, traced):
        """An arm's means over the 60 seeds; for None, the mean of the four
        configurations learned on the access-only stack, frozen."""
        if arm is None:
            return [round2.learned_mean(m) for m in ('psnr', 'm1loss', 'loss', 'usable', 'declared', 'rreq_all', 'rerr')]
        return ([controls.mean(arm, m) for m in ('psnr', 'm1loss', 'loss', 'usable', 'declared')]
                + [controls.mean(traced or arm, m) for m in ('rreq_all', 'rerr')])

    rows('revision-controles', 'tableau des contrôles, GOP 9-3 : PSNR, perte M1, perte, images ≥ 28 dB, déclarations, RREQ, RERR ; '
         'sans agent, figée, croisement, ε constant (accès seul compris), configurations apprises puis figées (moyenne des '
         'quatre, 240 simulations), ε décroissant, rupture seule',
         [(head, text, control(arm, traced)) for head, arm, traced, text in (
             ('sans agent & Règles', 'rules', None, '27,29 & 14,6 & 56,2 & 5,9 & 22,0 & 2 334 & 67'),
             ('\\midrule \\multirow[m]{2}{*}{figée} & Agents', 'agents-frozen', None, '27,52 & 12,6 & 56,1 & 5,9 & 21,2 & 2 306 & 67'),
             ('& Hybride', 'hybrid-frozen', None, '27,37 & 14,4 & 55,9 & 5,9 & 22,4 & 2 387 & 82'),
             ('\\midrule exploration seule (\\nu = 0) & Hybride', round2.EXPLORE, None, '27,70 & 12,6 & 56,3 & 6,1 & 22,2 & 2 322 & 80'),
             ('\\midrule apprentissage seul (\\varepsilon = 0) & Hybride', round2.LEARN, None, '28,98 & 10,5 & 49,4 & 7,2 & 8,5 & 1 136 & 55'),
             ('\\midrule \\multirow[m]{3}{*}{\\varepsilon constant} & Accès seul', ablation.ACCESS_ONLY, None,
              '29,29 & 9,5 & 44,9 & 8,0 & 7,4 & 1 024 & 61'),
             ('& Agents', 'agents', 'agents-tr', '27,24 & 15,5 & 51,1 & 6,0 & 19,9 & 2 195 & 174'),
             ('& Hybride', 'hybrid', 'hybrid-tr', '29,31 & 9,7 & 46,0 & 7,8 & 7,3 & 1 034 & 61'),
             ('\\midrule \\begin{tabular}[c]{@{}l@{}}apprises, puis figées\\\\ (4 configurations)\\end{tabular} & Accès seul', None, None,
              '29,50 & 9,4 & 42,6 & 8,1 & 4,5 & 732 & 64'),
             ('\\midrule \\multirow[m]{2}{*}{\\varepsilon décroissant} & Agents', 'agents-edec', None, '28,78 & 11,0 & 49,8 & 7,3 & 9,3 & 1 172 & 95'),
             ('& Hybride', 'hybrid-edec', None, '28,98 & 10,0 & 49,1 & 7,4 & 8,3 & 1 115 & 58'),
             ('\\midrule \\varepsilon = 0, rupture seule & Agents', 'agents-bgreedy', None, '29,45 & 9,3 & 43,4 & 7,9 & 4,3 & 783 & 63'),
             ('\\midrule \\varepsilon décroissant, rupture seule & Agents', 'agents-bdec-s11', None, '28,70 & 11,9 & 46,1 & 7,3 & 8,5 & 1 163 & 99'))])

    # -------------------------------------------------------- the decisions
    trace = {(r['arm'], r['agent']): r for r in data.table('agent-trace.tsv') if r['t'] == '999'}

    def decided(arm, agent):
        r = trace[arm, agent]
        decisions = float(r['decisions'])
        return [float(r['nodes']), decisions, float(r['median']), 100 * max(float(r['a%d' % a]) for a in range(9)) / decisions,
                float(r['changed']) if r['changed'] else None]

    rows('revision-agents', 'tableau des décisions, sept agents : nœuds, décisions, médiane par nœud, action la plus choisie (%), hors du '
         'choix initial (%)',
         [('%s%s' % ('\\midrule ' if i else '', head), text, decided(arm, agent)) for i, (head, arm, agent, text) in enumerate((
             ('Chemin & Hybride', 'hybrid', 'path', '69 & 52 225 & 541 & 67,0 & 19,9'),
             ('Congestion & Hybride', 'hybrid', 'congestion', '69 & 52 225 & 541 & 79,7 & 19,8'),
             ('Accès au canal & Hybride', 'hybrid', 'access', '70 & 50 680 & 529 & 85,5 & 8,0'),
             ('Rejet anticipé & Hybride', 'hybrid', 'discard', '99 & 3 098 & 32 & 88,9 & 8,5'),
             ('Découverte & Hybride', 'hybrid', 'discovery', '1 & 11 & 11 & 60,2 & 38,6'),
             ('Puissance & Hybride', 'hybrid', 'power', '70 & 50 680 & 529 & 100,0 & non tracé'),
             ('Détection de rupture & Agents', 'agents', 'break', '38 & 550 & 2 & 60,7 & 11,1')))])

    # ---------------------------------------------------------- the quality
    metrics = ('psnr', 'usable', 'delay_mean', 'late', 'on_time')
    arms = (('AOMDV\\textsuperscript{1}', lambda s: 'pq'), ('AOMDV aux temporisations inter-couches', lambda s: 'pq-tuned'),
            ('Règles', lambda s: 'rules'), ('Accès seul', round2.access_only), ('Agents', lambda s: 'agents'), ('Hybride', lambda s: 'hybrid'))
    for s, texts in (
            ('3M9D', ('18,05 & 0,0 & 456 & 0,09 & 24,7', '19,73 & 0,0 & 424 & 0,02 & 55,8', '21,57 & 1,2 & 348 & 0,04 & 37,7',
                      '22,63 & 1,8 & 322 & 0,02 & 44,9', '21,73 & 1,4 & 361 & 0,13 & 40,7', '22,65 & 1,7 & 341 & 0,06 & 44,9')),
            ('6M6D', ('18,67 & 0,0 & 456 & 0,06 & 23,9', '20,90 & 0,0 & 420 & 0,02 & 56,4', '25,38 & 3,6 & 418 & 0,13 & 40,7',
                      '27,08 & 5,2 & 358 & 0,01 & 50,1', '25,23 & 3,8 & 397 & 0,14 & 44,5', '26,85 & 5,5 & 375 & 0,06 & 50,1')),
            ('9M3D', ('18,81 & 0,0 & 453 & 0,09 & 22,9', '21,23 & 0,0 & 418 & 0,01 & 55,7', '27,29 & 5,9 & 476 & 0,03 & 43,8',
                      '29,29 & 8,0 & 386 & 0,00 & 55,1', '27,24 & 6,0 & 426 & 0,04 & 48,8', '29,31 & 7,8 & 410 & 0,03 & 54,0'))):
        rows('revision-qualite', 'tableau de la qualité, GOP %s : PSNR, images ≥ 28 dB, délai moyen (ms), échéances manquées, reçus à '
             'temps (%% des envoyés), six piles' % GOP[s],
             [('%s %s' % (several(GOP[s], i, 6), head), text, [quality.mean(arm(s), m, s) for m in metrics])
              for i, ((head, arm), text) in enumerate(zip(arms, texts))])

    # ------------------------------------------------------------ the ANOVA
    terms = {t[0]: t for t in comparative.anova(rs)}
    eta = comparative.effect_sizes(rs)

    def anova(term):
        t = terms[term]
        gg = [None, None] if t[6] is None else [t[6], P(t[7])]
        return [(t[1], t[2]), t[3], P(t[4])] + gg + [eta[term]]

    def anova_row(head, term, df, text):
        """The degrees of freedom stay a pair: checked apart from the cells."""
        xs = anova(term)
        dfs = [int(x) for x in df.split(', ')]
        return '%s & %s' % (head, df), text, xs[1:], [(xs[0] == tuple(dfs), '=', True, 0)]

    group = [anova_row(*r) for r in (
        ('Pile', 'stack', '2, 114', '52,3 & < 0,001 & 0,89 & < 0,001 & 0,48 [0,34 ; 0,57]'),
        ('\\midrule Feu', 'fire', '2, 57', '1,1 & 0,331 & -- & -- & 0,04 [0,00 ; 0,15]'),
        ('\\midrule GOP', 'split', '2, 114', '681,3 & < 0,001 & 0,98 & < 0,001 & 0,92 [0,90 ; 0,94]'),
        ('\\midrule Pile \\times Feu', 'stack x fire', '4, 114', '1,4 & 0,241 & 0,89 & 0,246 & 0,05 [0,00 ; 0,11]'),
        ('\\midrule Pile \\times GOP', 'stack x split', '4, 228', '2,2 & 0,068 & 0,85 & 0,079 & 0,04 [0,00 ; 0,08]'),
        ('\\midrule Feu \\times GOP', 'fire x split', '4, 114', '0,4 & 0,839 & 0,98 & 0,834 & 0,01 [0,00 ; 0,04]'),
        ('\\midrule Pile \\times Feu \\times GOP', 'stack x fire x split', '8, 228', '0,6 & 0,756 & 0,85 & 0,731 & 0,02 [0,00 ; 0,03]'))]
    rows('comparatif-anova', 'tableau de l\'ANOVA, sept termes : F, p, facteur de Greenhouse-Geisser, p corrigé, η² partiel et son '
         'intervalle à 95 % (loi F décentrée)', [g[:3] for g in group])
    C.claim('S03', 'tableau de l\'ANOVA, sept termes : degrés de liberté du terme et de son erreur',
            ' … '.join('%s &' % g[0].replace('\\midrule ', '') for g in group), [c for g in group for c in g[3]],
            source=table('comparatif-anova'))

    # -------------------------------------- the equal rate, the coefficient
    def coded(stack, split, period, m, suffix=None):
        """The mean of a stack in the series of E4, the access-only stack's
        from its arm (access_robustness)."""
        if stack == 'access':
            return access.mean(stack, access.Level(period, suffix, split, period, '40'), m)
        return coding.mean(stack if suffix is None else '%s-%s' % (stack, suffix), split, period, m)

    four = ('m1loss', 'loss', 'usable')
    for group in ((('3M9D', 'p9', '\\multirow[m]{2}{*}{3-9}', '9 & 53,1 & 21,57 & 22,63 & 22,65 & 29,8 & 24,5 & 62,2 & 55,1 & 1,2 & 1,7'),
                   ('3M9D', 'p9r65', '', '9,65 & 49,6 & 22,18 & 23,14 & 23,69 & 27,0 & 21,2 & 61,6 & 51,6 & 1,4 & 2,7')),
                  (('6M6D', 'p9', '\\multirow[m]{2}{*}{6-6}', '9 & 51,3 & 25,38 & 27,08 & 26,85 & 17,1 & 14,0 & 59,2 & 49,8 & 3,6 & 5,5'),
                   ('6M6D', 'p9r32', '', '9,32 & 49,6 & 25,47 & 27,48 & 27,31 & 18,6 & 13,8 & 57,8 & 47,8 & 3,8 & 6,1')),
                  (('9M3D', 'p9', '9-3', '9 & 49,6 & 27,29 & 29,29 & 29,31 & 14,6 & 9,7 & 56,2 & 46,0 & 5,9 & 7,8'),)):
        rows('revision-volume', 'tableau du débit égal, GOP %s : T (s), débit moyen (paquets/s), PSNR des piles à règles, à accès seul et '
             'hybride, puis perte M1, perte et images ≥ 28 dB des piles à règles et hybride' % GOP[group[0][0]],
             [(head, text, [coding.PERIOD[p], coding.rate(coding.PACKETS[s], p)]
               + [coded(st, s, p, 'psnr') for st in ('rules', 'access', 'hybrid')]
               + [coded(st, s, p, m) for m in four for st in ('rules', 'hybrid')]) for s, p, head, text in group])
    rows('revision-qualite-coef', 'tableau du coefficient de qualité, GOP 9-3, à 0,01 puis à 0,1 : débit moyen (paquets/s), PSNR, perte '
         'M1, perte, images ≥ 28 dB, cinq piles',
         [('%s%s' % ('\\midrule ' if i else '', head), text,
           [coding.rate(n, 'p9') for n in (coding.PACKETS['9M3D'], coding.PACKETS_Q01)]
           + [coded(st, '9M3D', 'p9', m, suffix) for m in ('psnr',) + four for suffix in (None, 'q01')])
          for i, (st, head, text) in enumerate((
              ('pq', 'AOMDV', '49,6 & 24,7 & 18,81 & 20,26 & 66,6 & 48,7 & 77,1 & 55,8 & 0,0 & 0,0'),
              ('rules', 'Règles', '49,6 & 24,7 & 27,29 & 28,57 & 14,6 & 12,8 & 56,2 & 49,1 & 5,9 & 7,5'),
              ('access', 'Accès seul', '49,6 & 24,7 & 29,29 & 29,88 & 9,5 & 10,9 & 44,9 & 43,0 & 8,0 & 9,1'),
              ('agents', 'Agents', '49,6 & 24,7 & 27,24 & 28,49 & 15,5 & 13,0 & 51,1 & 49,2 & 6,0 & 7,6'),
              ('hybrid', 'Hybride', '49,6 & 24,7 & 29,31 & 30,27 & 9,7 & 9,6 & 46,0 & 41,6 & 7,8 & 9,4')))])

    # ---------------------------------- the load, the fire and the scenario
    def alone(series, key):
        """The mean PSNR of the access-only stack at a level of a series (None: the reference scenario)."""
        return access.mean('access', access.REFERENCE if key is None else next(v for v in access.SERIES[series] if v.key == key))

    # the access-only stack minus the rule stack, Holm within each series; the
    # reference scenario's, the period of 9 s, within the load series
    lead = {s: access.tests(s, 'access - rules') for s in ('load', 'fire', 'scenario')}

    def ahead(series, key):
        """[the gap, its p] of the access-only stack over the rule stack at a level of a series (None: the reference scenario)."""
        e = lead['load'][access.REFERENCE.key] if key is None else lead[series][key]
        return [Over(e) if series == 'scenario' else e, P(e.holm)]

    ld, fi, sc = robustness.load(), robustness.fire(), robustness.scenario()
    rows('revision-charge', 'tableau de la charge, cinq périodes : perte des règles (%), PSNR des cinq piles, pile à accès seul − règles et '
         'pile hybride − règles : PSNR et p, Holm sur cinq périodes, images ≥ 28 dB',
         [('%s%s' % ('\\midrule ' if i else '', t), text,
           [ld['loss'][p]] + [alone('load', p) if st == 'access' else ld['means'][p][st] for st in ('pq', 'rules', 'access', 'agents', 'hybrid')]
           + ahead('load', p) + [ld['psnr'][p], P(ld['psnr'][p].holm), ld['images'][p].mean])
          for i, (p, t, text) in enumerate((
              ('p7', '7', '63,5 & 18,64 & 24,36 & 23,64 & 22,60 & 23,44 & −0,73 [−1,07 ; −0,38] & < 0,001 & −0,92 [−1,27 ; −0,57] & < 0,001 '
               '& −2,0'),
              ('p9', '9', '56,2 & 18,81 & 27,29 & 29,29 & 27,24 & 29,31 & +2,00 [1,38 ; 2,62] & < 0,001 & +2,02 [1,50 ; 2,53] & < 0,001 & +1,9'),
              ('p12', '12', '35,6 & 20,08 & 31,27 & 33,60 & 31,68 & 33,69 & +2,34 [1,72 ; 2,96] & < 0,001 & +2,42 [1,82 ; 3,02] & < 0,001 '
               '& +0,8'),
              ('p18', '18', '1,5 & 35,88 & 59,00 & 58,88 & 59,41 & 59,89 & −0,12 [−1,15 ; 0,91] & 1,000 & +0,89 [−0,18 ; 1,97] & 0,205 & +0,1'),
              ('p30', '30', '0,5 & 45,32 & 62,74 & 62,73 & 62,21 & 62,21 & −0,01 [−0,50 ; 0,49] & 1,000 & −0,53 [−1,44 ; 0,38] & 0,247 & −0,1')))])

    def gain(v, m):
        return fi['reference'][m] if v is None else fi['families']['gain'][m][v]

    rows('revision-sensibilite', 'tableau des paramètres du feu, référence et sept variantes : perte des règles (%), PSNR des trois piles, '
         'pile à accès seul − règles (Holm sur sept, la référence sur cinq périodes) et pile hybride − règles (Holm sur sept, la référence '
         'test unique) : PSNR et p ; perte M1, images ≥ 28 dB, déclarations',
         [('%s%s' % ('\\midrule ' if i else '', head), text,
           [fi['means'][robustness.arm('rules', v)]['loss'], fi['means'][robustness.arm('rules', v)]['psnr'], alone('fire', v),
            fi['means'][robustness.arm('hybrid', v)]['psnr']] + ahead('fire', v)
           + [gain(v, 'psnr'), P(gain(v, 'psnr').p if v is None else gain(v, 'psnr').holm)]
           + [gain(v, m).mean for m in ('m1loss', 'usable', 'declared')])
          for i, (v, head, text) in enumerate((
              (None, '\\begin{tabular}[c]{@{}l@{}}Référence\\\\ (\\mathrm{AZ} = 1 dB/m,\\\\ \\mathrm{PF} = 0,5)\\end{tabular}',
               '56,2 & 27,29 & 29,29 & 29,31 & +2,00 [1,38 ; 2,62] & < 0,001 & +2,02 [1,50 ; 2,53] & < 0,001 & −4,9 & +1,9 & −14,7'),
              ('az015', '\\mathrm{AZ} = 0,15 dB/m',
               '56,0 & 27,11 & 28,76 & 28,79 & +1,65 [1,10 ; 2,20] & < 0,001 & +1,68 [1,15 ; 2,21] & < 0,001 & −3,1 & +1,7 & −15,4'),
              ('az05', '\\mathrm{AZ} = 0,5 dB/m',
               '55,5 & 27,28 & 29,30 & 28,96 & +2,03 [1,59 ; 2,46] & < 0,001 & +1,69 [1,17 ; 2,21] & < 0,001 & −3,0 & +1,7 & −14,7'),
              ('az165', '\\mathrm{AZ} = 1,65 dB/m',
               '55,9 & 27,50 & 29,14 & 29,04 & +1,65 [1,10 ; 2,19] & < 0,001 & +1,55 [1,05 ; 2,04] & < 0,001 & −3,5 & +1,9 & −14,3'),
              ('pf0', '\\mathrm{PF} = 0',
               '56,1 & 27,36 & 29,33 & 29,18 & +1,97 [1,37 ; 2,56] & < 0,001 & +1,82 [1,26 ; 2,38] & < 0,001 & −4,0 & +1,8 & −14,1'),
              ('pf025', '\\mathrm{PF} = 0,25',
               '56,5 & 27,28 & 29,30 & 29,31 & +2,02 [1,42 ; 2,62] & < 0,001 & +2,03 [1,46 ; 2,59] & < 0,001 & −4,6 & +2,0 & −14,7'),
              ('pf075', '\\mathrm{PF} = 0,75',
               '56,1 & 27,41 & 29,28 & 29,33 & +1,87 [1,24 ; 2,49] & < 0,001 & +1,91 [1,40 ; 2,43] & < 0,001 & −4,5 & +1,8 & −14,4'),
              ('fd1', '\\begin{tabular}[c]{@{}l@{}}Pannes près\\\\ du front\\textsuperscript{1}\\end{tabular}',
               '56,2 & 27,34 & 29,30 & 29,20 & +1,96 [1,37 ; 2,55] & < 0,001 & +1,86 [1,34 ; 2,38] & < 0,001 & −4,0 & +1,8 & −14,5')))])

    def contrast(c, v, m):
        return sc['reference'][c][m] if v is None else sc['families']['gap'][c][m][v]

    def contrasts(v):
        out = []
        for c in ('hybrid-rules', 'agents-rules'):
            e_ = contrast(c, v, 'psnr')
            out += [Over(e_), P(e_.p if v is None else e_.holm), contrast(c, v, 'usable').mean]
        return out

    rows('revision-generalisation', 'tableau des variantes du scénario, référence et cinq variantes : perte des règles (%), PSNR des cinq '
         'piles, pile à accès seul − règles (Holm sur cinq variantes, la référence sur cinq périodes), pile hybride − règles et pile à '
         'agents − règles (Holm sur cinq, la référence test unique) : PSNR et p, images ≥ 28 dB',
         [('%s%s' % ('\\midrule ' if i else '', head), text,
           [sc['means'][robustness.arm('rules', v)]['loss']]
           + [alone('scenario', v) if st == 'access' else sc['means'][robustness.arm(st, v)]['psnr']
              for st in ('pq', 'rules', 'access', 'agents', 'hybrid')] + ahead('scenario', v) + contrasts(v))
          for i, (v, head, text) in enumerate((
              (None, 'Référence', '56,2 & 18,81 & 27,29 & 29,29 & 27,24 & 29,31 & +2,00 [1,38 ; 2,62] & < 0,001 & '
               '+2,02 [1,50 ; 2,53] & < 0,001 & +1,9 & −0,06 [−0,70 ; 0,59] & 0,863 & +0,1'),
              ('forest', 'Vidéo forêt', '56,3 & 14,86 & 22,85 & 24,23 & 22,54 & 24,02 & +1,38 [0,82 ; 1,95] & < 0,001 & '
               '+1,18 [0,65 ; 1,70] & < 0,001 & +0,5 & −0,31 [−0,84 ; 0,23] & 0,506 & −0,6'),
              ('smoke', 'Vidéo fumée', '52,9 & 21,25 & 32,12 & 34,06 & 31,53 & 33,77 & +1,94 [1,25 ; 2,62] & < 0,001 & '
               '+1,64 [0,97 ; 2,31] & < 0,001 & +1,0 & −0,59 [−1,32 ; 0,14] & 0,330 & −0,7'),
              ('j8', 'Grille de 30 m', '44,7 & 18,56 & 28,47 & 28,87 & 26,53 & 28,86 & +0,41 [−0,11 ; 0,93] & 0,124 & '
               '+0,40 [−0,11 ; 0,91] & 0,124 & +0,6 & −1,93 [−2,41 ; −1,45] & < 0,001 & −1,9'),
              ('swap', '\\begin{tabular}[c]{@{}l@{}}Caméra et puits\\\\ échangés\\end{tabular}',
               '57,0 & 19,02 & 27,45 & 29,09 & 26,65 & 28,69 & +1,65 [1,13 ; 2,16] & < 0,001 & '
               '+1,25 [0,72 ; 1,77] & < 0,001 & +1,4 & −0,80 [−1,41 ; −0,19] & 0,046 & −0,4'),
              ('v15', '\\begin{tabular}[c]{@{}l@{}}Vitesse de tête\\\\ \\times 1,5\\end{tabular}',
               '58,3 & 19,04 & 27,13 & 28,89 & 27,05 & 29,03 & +1,75 [1,13 ; 2,38] & < 0,001 & '
               '+1,90 [1,33 ; 2,46] & < 0,001 & +1,9 & −0,09 [−0,65 ; 0,48] & 0,763 & +0,2')))])

    # ------------------------------------------------------------ the costs
    over, rev, routing = overhead.inputs()
    _, mem = overhead.memory()
    traced = {stack: arm for stack, _, arm in measures.ENERGY_STACKS}

    def costs(stack):
        en, msg = overhead.energy(over, stack) or {}, overhead.control(stack, traced[stack], rev, routing)
        return [en.get('e_total'), en.get('e_node')] + [msg[m] for m in ('hello', 'rreq_all', 'rerr')] + [
            mem[stack]['node'] if stack in mem else 0.0]

    rows('revision-couts', 'tableau des coûts, GOP 9-3 : énergie du réseau et par nœud (J), HELLO, RREQ, RERR, mémoire des agents '
         '(octets), six piles',
         [('%s%s' % ('\\midrule ' if i else '', head), text, costs(stack)) for i, (stack, head, text) in enumerate((
             ('pq', 'AOMDV', '600,0 & 6,08 & 16 153 & 1 193 & 123 & 0'),
             ('pq-ctl', 'AOMDV de contrôle', '600,0 & 6,08 & 16 155 & 1 290 & 131 & 0'),
             ('rules', 'Règles', '601,7 & 6,10 & 3 212 & 2 334 & 67 & 0'),
             ('access', 'Accès seul', '601,5 & 6,10 & 3 214 & 1 024 & 61 & 338'),
             ('agents', 'Agents', '601,6 & 6,10 & 3 214 & 2 195 & 174 & 927'),
             ('hybrid', 'Hybride', '601,5 & 6,10 & 3 214 & 1 034 & 61 & 863')))])
