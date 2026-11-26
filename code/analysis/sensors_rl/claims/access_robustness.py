"""S14: the access-only stack in the series of E4 and E5 (tranche T7 of study
11) as the text gives it, in sections 3.7 and 3.8, in the
limits (4.4), in the introduction and in the conclusions, each number
recomputed by analysis/access_robustness.py:

  access - rules    the levels where the lead is significant (Holm within its
                    series and comparison, the coefficient 0.1 a single
                    test), with the hybrid stack's lead over the periods and
                    the scenario variants, the same conclusions at each level,
                    the gaps and their ranges, the levels where no difference
                    is detected, and 7 s, where the access-only stack falls
                    under the rule stack
  hybrid - access   no difference detected at any level of the load, the fire,
                    the scenario and the equal rate, the range of the gaps and
                    of their intervals; the single test of the coefficient
                    0.1, where the hybrid stack is above

The counts of simulations the oracle reads, the access-only stack's sets
included, are P29, P32 (claims/results.py) and G04 (claims/scenario.py); the
families and the tests S11 (claims/review.py)."""
from ..analysis import access_robustness as ar
from ..analysis import robustness
from .checks import gap_checks, span_checks

SCENARIO = ['forest', 'smoke', 'swap', 'v15']   # the scenario variants where the lead is significant


def _p(e):
    """Holm's p within the family, or the single test's."""
    return e.p if e.holm is None else e.holm


def _verdict(e):
    """The conclusion of a test: 0 no difference detected, 1 above, -1 below."""
    return 0 if _p(e) >= 0.05 else 1 if e.mean > 0 else -1


def claims(C):
    """Adds the rows of S14 to the Claims C."""
    claim = C.claim
    fam = ar.families()
    if fam is None:
        claim('S14', 'round2.tsv, pile à accès seul dans les séries de E4 et E5', '', [(None, '=', 0, 0)])
        return

    def span(label, text, es, gaps, bounds, ordered=False, also=()):
        """A range of gaps with the p the text gives them (gaps), and the
        range of their intervals (bounds), both as text, the fragments of the
        sources, writes them."""
        claim('S14', label, text, span_checks([e.mean for e in es], gaps, [_p(e) for e in es], ordered=ordered)
              + span_checks([e.lo for e in es] + [e.hi for e in es], bounds) + list(also))

    def gap(label, text, e, written=None):
        """written: the gap as text writes it, where text holds other numbers before it."""
        claim('S14', label, text, gap_checks(e, written or text))

    # ------------------------------------------- access-only minus rule stack
    a = {s: fam[s, 'access - rules'] for s in ar.SERIES}
    above = {s: [k for k, e in es.items() if e.mean > 0 and _p(e) < 0.05] for s, es in a.items()}
    below = [(s, k) for s, es in a.items() for k, e in es.items() if e.mean < 0 and _p(e) < 0.05]
    levels = {'load': ['p9', 'p12'], 'fire': list(a['fire']), 'scenario': SCENARIO, 'rate': ['3M9D', '6M6D'], 'coding': ['q01']}
    name = 'PSNR, pile à accès seul − pile à règles'
    claim('S14', name + ' : les niveaux où l\'avance est significative (Holm dans sa série, test unique au coefficient 0,1), ceux où aucune '
          'différence n\'a été détectée, 18 et 30 s et la grille de 30 m, et celui où elle s\'inverse, 7 s (limites)',
          'l\'avance de la pile à accès seul est significative, sauf à 7, 18 et 30 s et sur la grille de 30 m. Elle s\'inverse à 7 s',
          [(above == levels, '=', True, 0), (below == [('load', 'p7')], '=', True, 0),
           (sorted((s, k) for s, es in a.items() for k in es if k not in above[s] and (s, k) not in below)
            == [('load', 'p18'), ('load', 'p30'), ('scenario', 'j8')], '=', True, 0)])
    hybrid = {'load': robustness.period_family('hybrid', 'rules', 'psnr'),
              'scenario': robustness.scenario_family('gap', 'hybrid-rules', 'psnr')}
    verdicts = {'load': {'p7': -1, 'p9': 1, 'p12': 1, 'p18': 0, 'p30': 0},
                'scenario': {v: int(v in SCENARIO) for v in robustness.SCENARIO_VARIANTS}}
    claim('S14', 'PSNR, piles hybride et à accès seul − pile à règles : avances significatives à 9 et 12 s seules, inversées à 7 s, et sous '
          'quatre variantes du scénario, toutes sauf la grille de 30 m (introduction, conclusions)',
          'parmi cinq périodes d\'alarme, les avances des piles à accès seul et hybride ne sont significatives qu\'à 9 et 12 s. Elles '
          's\'inversent à 7 s … À 9 s, elles restent significatives sous quatre des cinq variantes du scénario. À 18 et 30 s et sous la '
          'cinquième, une grille de 30 m, aucune différence statistiquement significative avec la pile à règles n\'a été détectée … les '
          'avances des piles à accès seul et hybride sur la pile à règles ne sont significatives qu\'à 9 et 12 s. Elles s\'inversent à 7 s',
          [(all({k: _verdict(e) for k, e in es[s].items()} == verdicts[s] for s in verdicts), '=', True, 0) for es in (hybrid, a)])
    span(name + ' à 9 et 12 s, Holm sur cinq périodes : écarts ; Holm max. ; bornes min. et max. (dB)',
         'Au GOP 9-3, à T = 9 et 12 s, elle dépasse la pile à règles (+2,00 et +2,34 dB, intervalles de 1,38 à 2,96 dB, p < 0,001',
         [a['load']['p9'], a['load']['p12']], '+2,00 et +2,34 dB, p < 0,001', '1,38 à 2,96 dB', ordered=True)
    both = list(a['fire'].values()) + [a['scenario'][v] for v in SCENARIO]
    span(name + ', sept variantes du feu (Holm sur sept) et quatre variantes du scénario (Holm sur cinq) : écarts min., max. ; Holm max. ; '
         'bornes min. et max. (dB)',
         'Sous les sept variantes du feu et quatre des cinq variantes du scénario, son avance va de 1,38 à 2,03 dB (intervalles de 0,82 à '
         '2,62 dB, p < 0,001', both, '1,38 à 2,03 dB, p < 0,001', '0,82 à 2,62 dB',
         also=[((len(a['fire']), len(a['scenario']), len(SCENARIO)) == (7, 5, 4), '=', True, 0)])
    claim('S14', name + ' à débit égal, Holm sur deux : GOP 6-6, GOP 3-9',
          'À débit égal, la pile à accès seul dépasse la pile à règles de 2,00 dB [1,47 ; 2,54] au GOP 6-6 (p < 0,001) et de 0,97 dB '
          '[0,30 ; 1,63] au GOP 3-9 (p = 0,005',
          gap_checks(a['rate']['6M6D'], '2,00 dB [1,47 ; 2,54] au GOP 6-6 (p < 0,001')
          + gap_checks(a['rate']['3M9D'], '0,97 dB [0,30 ; 1,63] au GOP 3-9 (p = 0,005'))
    gap(name + ' au coefficient 0,1, GOP 9-3, test unique',
        'À ce coefficient, la pile à accès seul dépasse la pile à règles de 1,31 dB [0,84 ; 1,77] (p < 0,001, test unique',
        a['coding']['q01'], '1,31 dB [0,84 ; 1,77] (p < 0,001')
    span(name + ' à 18 et 30 s, Holm sur cinq périodes : écarts ; p de chacun ; bornes min. et max. (dB)',
         'À 18 et 30 s, aucune différence statistiquement significative n\'a été détectée entre ces deux piles (−0,12 et −0,01 dB, '
         'intervalles de −1,15 à +0,91 dB, p = 1,00 pour chacun',
         [a['load']['p18'], a['load']['p30']], '−0,12 et −0,01 dB, p = 1,00', '−1,15 à +0,91 dB', ordered=True)
    gap(name + ', grille de 30 m, Holm sur cinq variantes', 'n\'a été détectée non plus (+0,41 dB [−0,11 ; 0,93], p = 0,12',
        a['scenario']['j8'])
    none = [a['load']['p18'], a['load']['p30'], a['scenario']['j8']]
    text = '−0,12 à +0,41 dB, intervalles de −1,15 à +0,93 dB, p ≥ 0,12'
    span(name + ' à 18 et 30 s et sur la grille de 30 m, Holm dans chaque série : aucun p < 0,05 ; écarts min., max. ; Holm min. ; bornes '
         'min. et max. (limites, conclusions)',
         'À 18 et 30 s et sur cette grille, aucune différence statistiquement significative n\'a été détectée avec la pile à règles (%s … '
         'À 18 et 30 s et sous la cinquième, une grille de 30 m, aucune différence statistiquement significative n\'a été détectée entre la '
         'pile à accès seul et la pile à règles (%s' % (text, text),
         none, '−0,12 à +0,41 dB, p ≥ 0,12', '−1,15 à +0,93 dB', also=[(all(_verdict(e) == 0 for e in none), '=', True, 0)])
    claim('S14', 'PSNR, piles à accès seul et hybride − pile à règles à 7 s, Holm sur cinq périodes (introduction, conclusions)',
          'Elles s\'inversent à 7 s (−0,73 dB [−1,07 ; −0,38] et −0,92 dB [−1,27 ; −0,57], p < 0,001',
          gap_checks(a['load']['p7'], '−0,73 dB [−1,07 ; −0,38], p < 0,001') + gap_checks(hybrid['load']['p7'], '−0,92 dB [−1,27 ; −0,57], p < 0,001'))
    six = none + [hybrid['load']['p18'], hybrid['load']['p30'], hybrid['scenario']['j8']]
    span('PSNR, piles à accès seul et hybride − pile à règles à 18 et 30 s et sur la grille de 30 m : écarts min., max. ; Holm min. ; bornes '
         'min. et max. ; aucun p < 0,05 (introduction)',
         'aucune différence statistiquement significative avec la pile à règles n\'a été détectée (−0,53 à +0,89 dB, intervalles de −1,44 à '
         '+1,97 dB, p ≥ 0,12', six, '−0,53 à +0,89 dB, p ≥ 0,12', '−1,44 à +1,97 dB', also=[(all(_verdict(e) == 0 for e in six), '=', True, 0)])
    pair = [a['scenario']['j8'], hybrid['scenario']['j8']]
    span('PSNR, piles à accès seul et hybride − pile à règles, grille de 30 m : écarts ; p de chacun ; bornes min. et max. (limites)',
         'Les écarts sont de +0,41 et +0,40 dB (intervalles de −0,11 à +0,93 dB, p = 0,12 pour les deux', pair,
         '+0,41 et +0,40 dB, p = 0,12', '−0,11 à +0,93 dB', ordered=True)
    agents = [robustness.period_family('agents', 'rules', 'psnr')['p7'], robustness.scenario_family('gap', 'agents-rules', 'psnr')['j8']]
    claim('S14', 'PSNR, pile à agents − pile à règles à 7 s (Holm sur cinq périodes) et sur la grille de 30 m (Holm sur cinq variantes) '
          '(conclusions)',
          'La pile à agents passe sous la pile à règles à 7 s (−1,76 dB [−2,11 ; −1,41]) et sur cette grille (−1,93 dB [−2,41 ; −1,45], '
          'p < 0,001 pour les deux',
          gap_checks(agents[0], '−1,76 dB [−2,11 ; −1,41], p < 0,001') + gap_checks(agents[1], '−1,93 dB [−2,41 ; −1,45], p < 0,001'))
    text = '(−0,73 dB [−1,07 ; −0,38], p < 0,001'
    claim('S14', name + ' à 7 s, Holm sur cinq périodes : le seul niveau où la pile à accès seul passe sous la pile à règles, comme la pile '
          'hybride (résultats)', 'À 7 s, la pile à accès seul passe sous la pile à règles %s), comme la pile hybride' % text,
          gap_checks(a['load']['p7'], text) + [(below == [('load', 'p7')], '=', True, 0), (_verdict(hybrid['load']['p7']) == -1, '=', True, 0)])

    # ------------------------------------------ hybrid minus access-only stack
    h = {s: fam[s, 'hybrid - access'] for s in ar.SERIES}
    name = 'PSNR, pile hybride − pile à accès seul'
    at = {(s, k): e for s, es in h.items() if ar.FAMILY[s] for k, e in es.items()}
    span(name + ', charge, feu, scénario et débit égal, 19 niveaux, Holm dans chaque série : aucun p < 0,05 ; écarts min., max. ; Holm '
         'min. ; bornes min. et max.',
         'Face à la pile à accès seul, aucune différence statistiquement significative n\'a été détectée pour la pile hybride dans ces séries, '
         'hors coefficient 0,1 (−0,53 à +1,01 dB, intervalles de −1,46 à +2,06 dB, p ≥ 0,23',
         list(at.values()), '−0,53 à +1,01 dB, p ≥ 0,23', '−1,46 à +2,06 dB',
         also=[(len(at) == 19 and all(e.holm >= 0.05 and e.lo < 0 < e.hi for e in at.values()), '=', True, 0)])
    text = '(+0,40 dB [0,06 ; 0,74], p = 0,022, test unique'
    claim('S14', name + ' au coefficient 0,1, GOP 9-3, test unique : la pile hybride au-dessus, p non corrigé (résultats, limites, '
          'conclusions)',
          'Au coefficient 0,1, en revanche, la pile hybride dépasse la pile à accès seul %s non corrigé … Au coefficient 0,1, la pile '
          'hybride dépasse cette pile %s … Au coefficient de qualité 0,1, la pile hybride dépasse la pile à accès seul %s … Au GOP 9-3 et '
          'au coefficient 0,1, la pile hybride dépasse la pile à accès seul %s' % ((text,) * 4),
          gap_checks(h['coding']['q01'], text) + [(h['coding']['q01'].holm is None, '=', True, 0)])
