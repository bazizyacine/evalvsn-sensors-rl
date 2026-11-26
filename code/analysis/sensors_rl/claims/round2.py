"""S07 to S10: the numbers of study 11 (the controls of the second review
round, analysis/round2.py) in the French text, each recomputed by the
package's functions:

  S07  control 1, the crossing of learning and exploration in the hybrid
       stack at GOP 9-3 (round2.crossing, Holm over its four contrasts)
  S08  control 2, the four configurations learned in
       development runs, frozen, on each stack (round2.learned_csma, Holm over
       the four configurations of each stack and reference); the four fixed
       (BE, NB) of before the learned configurations left the text, and report --only round2 prints
       them apart
  S09  control 3, the access-only stack at the three GOPs (round2.access_gops,
       Holm over the three GOPs of each comparison), the stack the rule of
       choice keeps, and its M1 loss, its images that reach the PSNR
       threshold and its mean delay against the rule stack (section 3.6),
       single tests
  S10  control 5, the link-break agent without exploration or with its
       exploration decaying alone (round2.link_break, Holm over the three
       GOPs of each level and reference), and the decay alone against all
       seven agents decaying (round2.outside, a single test)

The PSNR carries Holm's p within its family, the secondary measures their
single test. A range the text gives ('−0,23 à +0,02 dB, intervalles de −0,66
à +0,69 dB, p ≥ 0,84') is checked by both ends, by the lowest and the highest
bound of the intervals and by the bound on p over the comparisons it covers
(checks.range_checks). The other secondary measures are in the controls table;
report --only round2 prints them all."""
from ..analysis import ablation, round2
from ..common import data, stats
from .checks import gap_checks, pv, range_checks

GOP = data.GOP
MEASURE = {'psnr': 'PSNR', 'm1loss': 'perte du niveau M1', 'usable': 'images ≥ 28 dB', 'delay_mean': 'délai moyen (ms)'}


def claims(C):
    """Adds the rows of S07 to S10 to the Claims C."""
    claim = C.claim

    def gap(block, ident, label, text, e, sign=1):
        claim(block, '%s ; %s' % (label, ident), text, gap_checks(e, text, sign))

    # S07, control 1: the hybrid stack at GOP 9-3, learning crossed with exploration
    crossing = {m: round2.crossing(m) for m in ('psnr',)}
    name = {'learning alone': 'apprentissage seul − politique figée', 'exploration alone': 'exploration seule − politique figée',
            'exploration under learning': 'pile hybride − apprentissage seul',
            'learning under exploration': 'pile hybride − exploration seule'}
    code = {'learning alone': 'L-F', 'exploration alone': 'E-F', 'exploration under learning': 'H-L', 'learning under exploration': 'H-E'}
    for m, contrast, text in (
            ('psnr', 'learning alone', '+1,61 dB [1,11 ; 2,10], p < 0,001'),
            ('psnr', 'exploration under learning', '+0,33 dB [−0,15 ; 0,82], p = 0,35'),
            ('psnr', 'exploration alone', '+0,32 dB [−0,27 ; 0,92], p = 0,35'),
            ('psnr', 'learning under exploration', '+1,62 dB [1,18 ; 2,06], p < 0,001')):
        gap('S07', 'C1-%s-%s' % (code[contrast], m), '%s, %s, GOP 9-3%s'
            % (MEASURE[m], name[contrast], ', Holm sur quatre' if m == 'psnr' else ', test unique'), text, crossing[m][contrast])
    gap('S07', 'C1-E-L', 'PSNR, exploration seule − apprentissage seul, GOP 9-3, test unique',
        'Cette pile passe sous celle de l\'apprentissage seul (−1,28 dB [−1,82 ; −0,74], p < 0,001, test unique',
        round2.outside('psnr')[('exploration only - learning only', '9M3D')])
    claim('S07', 'PSNR, croisement au GOP 9-3 : les deux écarts de l\'apprentissage au-dessus avec Holm < 0,05, les deux de '
          'l\'exploration avec Holm ≥ 0,05',
          'Un gain statistiquement significatif est donc détecté avec l\'apprentissage, et aucun avec l\'exploration',
          [(sorted(k for k, e in crossing['psnr'].items() if e.mean > 0 and e.holm < 0.05)
            == ['learning alone', 'learning under exploration'], '=', True, 0)])

    # S08, control 2: the learned configurations frozen, GOP 9-3
    lc = {(st, ref): round2.learned_csma(st, ref) for st in ('rules', 'hybrid') for ref in ('agent', 'standard')}
    stack_name = {'rules': 'pile à accès seul', 'hybrid': 'pile hybride'}
    ref_name = {'agent': 'l\'agent qui apprend', 'standard': 'les paramètres de la norme'}

    def lspan(st, ref, ks, text):
        claim('S08', 'PSNR, configurations %s figées sur la %s − %s, GOP 9-3 : min., max. ; bornes min. et max. ; Holm sur quatre'
              % (', '.join('k%d' % k for k in ks), stack_name[st], ref_name[ref]), text, range_checks([lc[st, ref][k] for k in ks], text))

    all4, first3 = round2.CONFIGURATIONS, round2.CONFIGURATIONS[:3]
    claim('S08', 'configurations apprises, puis figées, par pile', 'relevées en développement, puis figées, quatre par pile',
          [(all(len(es) == 4 for es in lc.values()), '=', True, 0)])
    lspan('rules', 'agent', all4, '+0,02 à +0,34 dB, intervalles de −0,45 à +0,77 dB, p ≥ 0,46')
    lspan('rules', 'standard', all4, '+2,02 à +2,33 dB, intervalles de 1,53 à 2,88 dB, p < 0,001')
    lspan('hybrid', 'standard', first3, '+2,23 à +2,61 dB, intervalles de 1,72 à 3,10 dB, p < 0,001')
    above = {st: sorted(k for k, e in lc[st, 'standard'].items() if e.mean > 0 and e.holm < 0.05) for st in ('rules', 'hybrid')}
    claim('S08', 'PSNR, configurations figées − les paramètres de la norme : celles au-dessus avec Holm < 0,05, les quatre de la pile à '
          'accès seul et trois de la pile hybride',
          'Sur la pile à accès seul, toutes dépassent la pile à règles … Sur la pile hybride, trois dépassent la même pile sans l\'agent',
          [(above == {'rules': list(all4), 'hybrid': list(first3)}, '=', True, 0)])
    seven = [lc['rules', 'agent'][k] for k in all4] + [lc['hybrid', 'agent'][k] for k in first3]
    text = '+0,02 à +0,48 dB, intervalles de −0,45 à +0,89 dB, p ≥ 0,070'
    claim('S08', 'PSNR, configurations figées − l\'agent qui apprend, les sept sans la k4 de la pile hybride, GOP 9-3 : min., max. ; '
          'bornes min. et max. ; Holm sur quatre, min. ; aucun Holm < 0,05',
          'Entre ces sept configurations et l\'agent qui apprend, aucune différence statistiquement significative n\'a été détectée ('
          + text, range_checks(seven, text) + [(len(seven) == 7 and all(e.holm >= 0.05 for e in seven), '=', True, 0)])
    out = [(st, k) for st in ('rules', 'hybrid') for k, e in lc[st, 'agent'].items() if round2.flagged(e)]
    claim('S08', 'PSNR, configurations figées − l\'agent qui apprend : les intervalles sans zéro avec Holm ≥ 0,05, k2 et k3 de la pile '
          'hybride, leurs écarts positifs',
          'Deux intervalles, sur la pile hybride, excluent toutefois zéro en faveur de la configuration figée',
          [(out == [('hybrid', 2), ('hybrid', 3)] and all(lc[p[0], 'agent'][p[1]].mean > 0 for p in out), '=', True, 0)])
    es = lc['hybrid', 'agent']
    claim('S08', 'PSNR, configurations figées sur la pile hybride − l\'agent qui apprend : la k4, seule sous l\'agent avec Holm < 0,05',
          'La quatrième configuration de cette pile passe sous l\'agent qui apprend (−2,06 dB [−2,45 ; −1,66], p < 0,001',
          [(sorted(k for k, e in es.items() if e.mean < 0 and e.holm < 0.05) == [4], '=', True, 0)])
    # the four fixed and uniform CSMA/CA settings of before the learned configurations, against the
    # agent that learns, on each stack: single tests (sections 2.7, 3.3, 4.1, 5)
    fixed = {st: [stats.paired(round2.values('%s-%s-s11' % (st, s), 'psnr'), round2.values(round2.REFERENCES[st]['agent'], 'psnr'))
                  for s, *_ in round2.SETTINGS] for st in ('rules', 'hybrid')}
    for st, name, text, where in (
            ('rules', 'pile à accès seul', '−2,43 à −1,28 dB, intervalles de −2,95 à −0,76 dB, p < 0,001',
             'Dans la pile à accès seul, chacun passe sous l\'agent qui apprend (%s, tests uniques … Les écarts vont de −2,43 à −1,28 dB '
             '(intervalles de −2,95 à −0,76 dB, p < 0,001, tests uniques … Sur la pile à accès seul, l\'écart va de −1,28 à −2,43 dB (intervalles de −2,95 à −0,76 dB, p < 0,001, tests uniques'),
            ('hybrid', 'pile hybride', '−2,48 à −1,26 dB, intervalles de −2,96 à −0,88 dB, p < 0,001',
             'Il en va de même dans la pile hybride (%s … Dans la pile hybride, ils passent aussi sous l\'agent (%s, tests uniques … '
             'Sur la pile hybride, il va de −1,26 à −2,48 dB (intervalles de −2,96 à −0,88 dB, p < 0,001')):
        claim('S08', 'PSNR, quatre réglages CSMA/CA fixes − l\'agent qui apprend, %s, GOP 9-3, tests uniques : min., max. ; p max. ; bornes '
              'min. et max. ; réglages, simulations' % name, where.replace('%s', text),
              range_checks(fixed[st], text) + [(len(fixed[st]) == 4 and all(e.mean < 0 for e in fixed[st]), '=', True, 0)])
    both = fixed['rules'] + fixed['hybrid']
    text = '−2,48 à −1,26 dB, intervalles de −2,96 à −0,76 dB, p < 0,001'
    claim('S08', 'PSNR, réglages CSMA/CA fixes − l\'agent qui apprend, les deux piles, tests uniques : min., max. ; p max. ; bornes ; '
          'simulations de la série', 'font moins bien que lui dans les piles à accès seul et hybride (%s … quatre réglages CSMA/CA fixes et '
          'uniformes, pris parmi ses actions (480 simulations … de ses quatre actions les plus fréquentes après celle de la norme (480 '
          'simulations' % text,
          range_checks(both, text) + [(sum(e.n for e in both), '=', 480, 0)])
    gap('S08', 'C2-learned-hybrid-k4-agent', 'PSNR, configuration k4 figée sur la pile hybride − l\'agent qui apprend, Holm sur quatre',
        '−2,06 dB [−2,45 ; −1,66], p < 0,001', es[4])
    gap('S08', 'C2-learned-hybrid-k4-standard', 'PSNR, configuration k4 figée sur la pile hybride − les paramètres de la norme, '
        'Holm sur quatre', '+0,08 dB [−0,42 ; 0,57], p = 0,76', lc['hybrid', 'standard'][4])

    # S09, control 3: the access-only stack at the three GOPs
    # the comparison the results lead with (section 3.3): the PSNR, Holm
    # over the three GOPs of each comparison
    ar, ha = round2.access_gops('access - rules'), round2.access_gops('hybrid - access')
    es = list(ar.values())
    text = '+1,06 à +2,00 dB, intervalles de 0,37 à 2,62 dB, p ≤ 0,004'
    claim('S09', 'PSNR, pile à accès seul − pile à règles, trois GOP : min., max. (dB) ; Holm max. ; bornes min. et max.', text,
          range_checks(es, text))
    gap('S09', 'C3-AR-psnr-3-9', 'PSNR, pile à accès seul − pile à règles, GOP 3-9, Holm sur trois GOP',
        'L\'écart est de +1,06 dB [0,37 ; 1,75] au GOP 3-9 (p = 0,003', ar['3M9D'])
    claim('S09', 'PSNR, pile à accès seul − pile à règles, GOP 6-6 et 9-3, Holm sur trois GOP ; C3-AR-psnr-6-6, C3-AR-psnr-9-3',
          'Il est de +1,70 dB [1,24 ; 2,16] au GOP 6-6 et de +2,00 dB [1,38 ; 2,62] au GOP 9-3 (p < 0,001 pour les deux',
          gap_checks(ar['6M6D'], '+1,70 dB [1,24 ; 2,16], p < 0,001') + gap_checks(ar['9M3D'], '+2,00 dB [1,38 ; 2,62], p < 0,001'))
    claim('S09', 'PSNR, pile à accès seul − pile à règles : au-dessus avec Holm < 0,05 à chacun des trois GOP',
          'Elle dépasse la pile à règles à chacun des trois GOP … '
          'La pile à accès seul, retenue à la sous-section \\ref{sec:fr-results-ablation}, dépasse la pile à règles aux trois GOP',
          [(len(es) == 3 and all(e.mean > 0 and e.holm < 0.05 for e in es), '=', True, 0)])
    es = list(ha.values())
    text = '−0,23 à +0,02 dB, intervalles de −0,66 à +0,69 dB, p ≥ 0,84'
    claim('S09', 'PSNR, pile hybride − pile à accès seul, trois GOP : min., max. (dB) ; Holm min. ; bornes min. et max.', text,
          range_checks(es, text))
    three = ('+0,02 [−0,66 ; 0,69]', '−0,23 [−0,66 ; 0,19]', '+0,02 dB [−0,49 ; 0,54]')
    claim('S09', 'PSNR, pile hybride − pile à accès seul, GOP 3-9, 6-6 et 9-3, Holm sur trois GOP ; Holm min. ; C3-HA-psnr',
          'n\'a été détectée, à aucun GOP (%s, %s et %s, p ≥ 0,84' % three,
          [c for s, x in zip(data.SPLITS, three) for c in gap_checks(ha[s], x)] + [pv(min(e.holm for e in es), '≥ 0,84')])
    claim('S09', 'PSNR, pile hybride − pile à accès seul : aucun Holm < 0,05 aux trois GOP, la pile la plus simple retenue ; les agents '
          'que la pile hybride ajoute',
          'La pile hybride lui ajoute cinq agents. Entre ces deux piles, aucune différence statistiquement significative n\'a été '
          'détectée, à aucun GOP … La pile à accès seul, la plus simple, est donc retenue',
          [(len(es) == 3 and all(e.holm >= 0.05 for e in es), '=', True, 0), (len(ablation.HYBRID) - 1 == 5, '=', True, 0)])

    # its M1 loss against the rule stack, single tests (section 3.6)
    es = round2.access_gops('access - rules', 'm1loss')
    two = [es['6M6D'], es['9M3D']]
    text = '−3,5 et −5,1 points (intervalles de −7,7 à −1,4 point, p ≤ 0,002'
    claim('S09', 'perte du niveau M1, pile à accès seul − pile à règles, GOP 6-6 et 9-3, tests uniques : écarts ; p max. ; bornes min. '
          'et max.', 'moins de paquets M1 que la pile à règles aux GOP 6-6 et 9-3. Les écarts sont de %s, tests uniques … Les écarts '
          'sont de %s, tests uniques' % (text, text),
          range_checks(two, text, ordered=True) + [(all(e.holm is None for e in two), '=', True, 0)])
    gap('S09', 'C3-AR-m1loss-3-9', '%s, pile à accès seul − pile à règles, GOP 3-9, test unique' % MEASURE['m1loss'],
        '−3,0 points [−6,8 ; 0,9], p = 0,13, test unique … (−3,0 points [−6,8 ; 0,9], p = 0,13', es['3M9D'])

    # its images that reach the threshold and its mean delay, single tests (section 3.6)
    for m, start, text in (
            ('usable', 'Face à la pile à règles, la pile à accès seul restitue par simulation plus d\'images qui atteignent le seuil de PSNR, à '
             'chaque GOP (', '+0,62 à +2,05 images, intervalles de 0,29 à 2,62 images, p < 0,001'),
            ('delay_mean', 'Son délai moyen est aussi plus court (', '−89,6 à −26,8 ms, intervalles de −97,9 à −18,6 ms, p < 0,001')):
        es = list(round2.access_gops('access - rules', m).values())
        claim('S09', '%s, pile à accès seul − pile à règles, trois GOP, tests uniques : min., max. ; p max. ; bornes min. et max.' % MEASURE[m],
              start + text + ', tests uniques', range_checks(es, text) + [(len(es) == 3 and all(e.holm is None for e in es), '=', True, 0)])

    # S10, control 5: the link-break agent without exploration, or with its
    # exploration decaying alone, the six other agents keeping 0.1
    level = {'agents-bgreedy': 'sans exploration', 'agents-bdec-s11': 'à exploration décroissante seule'}
    br = {(lv, ref): round2.link_break(lv, ref) for lv in level for ref in round2.BREAK_REFERENCES}

    def bspan(lv, ref, splits, text, context, extra=()):
        """A range over the GOPs given: text, the numbers, within context, the
        sentence that names the comparison ('%s' where text goes)."""
        es = br[lv, ref]
        claim('S10', 'PSNR, agent de détection de rupture %s − pile %s, GOP %s : min., max. ; Holm sur trois GOP ; bornes min. et max.'
              % (level[lv], 'à agents' if ref == 'agents' else 'hybride', ', '.join(GOP[s] for s in splits)), context % text,
              range_checks([es[s] for s in splits], text) + list(extra))

    every = list(data.SPLITS)
    detected = lambda es, up: all((e.mean > 0) == up and e.holm < 0.05 for e in es)  # noqa: E731
    bspan('agents-bgreedy', 'agents', every, '+1,39 à +2,21 dB, intervalles de 0,71 à 2,62 dB, p < 0,001',
          'Sans cette exploration (\\varepsilon = 0), la pile à agents gagne en PSNR à chaque GOP (%s',
          [(detected(br['agents-bgreedy', 'agents'].values(), True), '=', True, 0)])
    es = br['agents-bgreedy', 'hybrid']
    bspan('agents-bgreedy', 'hybrid', every, '+0,14 à +0,51 dB, intervalles de −0,24 à +1,09 dB, p ≥ 0,071', '%s',
          [(all(e.holm >= 0.05 for e in es.values()), '=', True, 0)])
    claim('S10', 'PSNR, agent de détection de rupture sans exploration − pile hybride : seul le GOP 6-6 a l\'intervalle sans zéro, '
          'Holm ≥ 0,05', 'n\'a été détectée, à aucun GOP (+0,14 … L\'intervalle du GOP 6-6 exclut toutefois zéro',
          [(sorted(s for s, e in es.items() if round2.flagged(e)) == ['6M6D'], '=', True, 0)])
    bspan('agents-bdec-s11', 'agents', every, '1,18 à 1,72 dB (intervalles de 0,63 à 2,16 dB, p < 0,001',
          'Quand cette exploration décroît, les six autres agents gardant \\varepsilon = 0,1, le gain va de %s',
          [(detected(br['agents-bdec-s11', 'agents'].values(), True), '=', True, 0)])
    es = br['agents-bdec-s11', 'hybrid']
    bspan('agents-bdec-s11', 'hybrid', ['3M9D', '6M6D'], '+0,11 à +0,26 dB, intervalles de −0,33 à +0,86 dB, p = 0,76',
          'Aux GOP 3-9 et 6-6, aucune différence statistiquement significative n\'a été détectée avec la pile hybride (%s pour les deux')
    gap('S10', 'C5-bdec-hybrid-psnr-9-3', 'PSNR, agent de détection de rupture à exploration décroissante seule − pile hybride, GOP 9-3, '
        'Holm sur trois GOP', 'Au GOP 9-3, cette pile à agents passe sous la pile hybride (−0,62 dB [−1,04 ; −0,19], p = 0,015', es['9M3D'])
    gap('S10', 'C5-bdec-edec-psnr-9-3', 'PSNR, exploration décroissante du seul agent de détection de rupture − des sept agents, '
        'GOP 9-3, test unique', '−0,09 dB [−0,50 ; 0,32], p = 0,66',
        round2.outside('psnr')[('break decay alone - all agents decaying', '9M3D')])
    claim('S10', 'même écart : les agents dont l\'exploration décroît avec le sien, sept dans la pile à agents, six autres que lui',
          'entre cette décroissance et celle des sept agents … les six autres agents gardant \\varepsilon = 0,1',
          [(len(ablation.SOLO) == 7 and len(ablation.HYBRID) == 6, '=', True, 0)])
