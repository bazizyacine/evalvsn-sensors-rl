"""S01 to S14: the numbers the second review round brings into the text,
recomputed from data/sensors-rl/article:

  S01  the gap of each comparison with its 95 % interval, the bounds
       uncorrected, and its p, Holm's within the family the text names
       (the families table) or a single test outside one; a range of gaps
       ('−5,2 à −3,2 points, intervalles de −9,5 à −0,5 point, p ≤ 0,032')
       by its ends, the ends of its intervals and the bound on p; what P02
       to P43, S07 to S10, S13, A01 to A11 and G01 to G08 check already is
       not repeated
  S02  Mauchly's test, the Greenhouse-Geisser correction and the 95 %
       interval of each partial eta squared by the noncentral F distribution
       (stats.eta_interval), as the text gives them
  S03  the tables of the results, the first round's with the second round's
       rows and columns, row by row (claims/tables.py)
  S04  the share of the packets sent that reach the sink in time, the delay
       and the missed deadlines
  S05  retired: what each declaration of a dead neighbour hits is P10
  S06  retired: the access-only stack against the agents stack is P17, the
       stacks above the PSNR threshold P08 and S13
  S07  to S10, the controls of study 11 (claims/round2.py)
  S11  the families of Holm's correction, what the fire and scenario series
       test outside them, and the assumptions of the tests
  S12  the numbers of section 2 (claims/methods.py)
  S13  the forms the abstract, the introduction, the discussion and the
       conclusions give (claims/synthesis.py)
  S14  the access-only stack in the series of E4 and E5 (tranche T7;
       claims/access_robustness.py)

The families table holds no number of its own but the size of each family. A
gap is checked as the text writes it, '+1,52 dB [1,12 ; 1,92], p < 0,001': its
difference and its bounds to the decimals written, its p in the text's form
(checks.p_text)."""
import sys

from ..analysis import assumptions, comparative, quality, robustness
from ..analysis import access_robustness as access_analysis
from ..analysis import round2 as round2_analysis
from ..tables import plan
from ..common import data, stats
from . import access_robustness, methods, round2, synthesis, tables
from .checks import Claims, fr, gap_checks, mean, pv, range_checks, report_unread, table

SPLITS = data.SPLITS
FIRES = data.FIRES
STACKS = data.STACKS


def main():
    rs = comparative.rows()
    if data.table('revision.tsv') is None or rs is None:
        sys.exit('data/sensors-rl/article/comparative.tsv and revision.tsv are needed')
    C = Claims(42, 40)
    claim = C.claim

    def gap(block, ident, label, text, e, sign=1):
        claim(block, '%s ; %s' % (label, ident), text, gap_checks(e, text, sign))

    def span(block, ident, label, text, es, numbers=None, also=()):
        """A range of gaps with its p and that of their intervals; numbers,
        as they would stand together, when text sets them apart."""
        es = list(es.values()) if isinstance(es, dict) else list(es)
        claim(block, '%s : écarts ; p ; bornes min. et max. ; %s' % (label, ident), text,
              range_checks(es, numbers or text) + list(also))

    hr = comparative.paired_gops(comparative.cells(rs, 'psnr'), 'hybrid', 'rules')

    # S01, what the other modules do not read. E0: the images that reach the
    # threshold (the bounds of the fair class are P42)
    gap('S01', 'USE-HR', 'images ≥ 28 dB, pile hybride − règles, trois GOP', '+1,43 image [1,18 ; 1,68], p < 0,001',
        quality.over_gops('hybrid', 'rules', 'usable'))
    es = quality.gops('hybrid', 'rules', 'usable')
    text = '+0,52 à +1,93 image, intervalles de 0,14 à 2,45 images, p ≤ 0,009'
    span('S01', 'usable-HR', 'images ≥ 28 dB, pile hybride − règles, Holm sur trois GOP, toutes sous 0,05', text, es,
         also=[(all(e.mean > 0 and e.holm < 0.05 for e in es.values()), '=', True, 0)])
    text = '+0,10 à +0,17 image, intervalles de −0,51 à +0,71 image, p ≥ 0,90'
    span('S01', 'USE-AR', 'images ≥ 28 dB, pile à agents − règles, Holm sur trois GOP', text, quality.gops('agents', 'rules', 'usable'))

    # E5: the fire parameters (the load is P28 to P30, the scenario G01 to G08)
    gain, change = robustness.fire_family('gain', 'psnr'), robustness.fire_family('change', 'psnr')
    text = '1,55 à 2,03 dB (intervalles de 1,05 à 2,59 dB, p < 0,001'
    span('S01', 'E5-sens', 'pile hybride − règles, sept variantes du feu, Holm sur sept, toutes au-dessus',
         'dépasse la pile à règles sous chacune des sept variantes du feu de E5 … ' + text, gain, text,
         also=[(len(gain) == 7 and all(e.mean > 0 and e.holm < 0.05 for e in gain.values()), '=', True, 0)])
    text = '−0,47 à +0,01 dB, intervalles de −1,07 à +0,40 dB, p ≥ 0,50'
    span('S01', 'E5-sensd', 'variation de l\'avance, sept variantes du feu − référence, Holm sur sept', text, change)
    # S02, the ANOVA: sphericity, the Greenhouse-Geisser correction and the 95 %
    # interval of each partial eta squared, by the noncentral F
    # distribution; its table is S03
    sph = comparative.sphericity(rs)
    terms = {t[0]: t for t in comparative.anova(rs)}
    eta = comparative.effect_sizes(rs)
    for s, name, w, pw, nd, text in (
            ('stack', 'pile', 0.87, 0.022, 3, 'rejette la sphéricité pour la pile (W = 0,87, p = 0,022)'),
            ('stack x split', 'pile × GOP', 0.73, 0.038, 3, 'et pour son interaction avec le GOP (W = 0,73, p = 0,038)'),
            ('split', 'GOP', 0.98, 0.51, 2, 'mais pas pour le GOP (W = 0,98, p = 0,51)')):
        claim('S02', 'Mauchly, %s : W ; p' % name, text, [(sph[s]['W'], '=', w, 2), pv(sph[s]['p'], '= ' + fr(pw, nd))])
    claim('S02', 'GOP ; pile : η² partiel et son intervalle à 95 % ; p corrigés (Greenhouse-Geisser)',
          'trouve un effet significatif du GOP (\\eta^2_p = 0,92 [0,90 ; 0,94]) et de la pile (\\eta^2_p = 0,48 [0,34 ; 0,57], p < 0,001 pour '
          'les deux',
          gap_checks(eta['split'], '0,92 [0,90 ; 0,94]') + gap_checks(eta['stack'], '0,48 [0,34 ; 0,57]')
          + [pv(terms['stack'][7], '< 0,001'), pv(terms['split'][7], '< 0,001')])
    claim('S02', 'pile × GOP : p corrigé (Greenhouse-Geisser) ; p ; η² partiel et son intervalle à 95 %',
          'p = 0,079, contre 0,068 sans correction, \\eta^2_p = 0,04 [0 ; 0,08]',
          [pv(terms['stack x split'][4], '= 0,068'), pv(terms['stack x split'][7], '= 0,079')]
          + gap_checks(eta['stack x split'], '0,04 [0 ; 0,08]'))
    claim('S02', 'feu, inter-graines : p ; pile × feu : p corrigé (Greenhouse-Geisser) ; η² partiels et leurs intervalles à 95 %',
          'sur le PSNR (p = 0,33, \\eta^2_p = 0,04 [0 ; 0,15]) ni sur l\'écart entre les piles (p = 0,25, \\eta^2_p = 0,05 [0 ; 0,11]',
          [pv(terms['fire'][4], '= 0,33'), pv(terms['stack x fire'][7], '= 0,25')]
          + gap_checks(eta['fire'], '0,04 [0 ; 0,15]') + gap_checks(eta['stack x fire'], '0,05 [0 ; 0,11]'))
    claim('S02', 'termes intra-graine : la correction de Greenhouse-Geisser ne change la significativité d\'aucun à 0,05 (méthode)',
          'corrige leurs valeurs de p sans changer la significativité d\'aucun terme',
          [(all((t[4] < 0.05) == (t[7] < 0.05) for t in terms.values() if t[7] is not None), '=', True, 0),
           (sum(t[7] is not None for t in terms.values()) == 6, '=', True, 0)])
    # S03, the tables of the results (claims/tables.py)
    tables.claims(C)

    # S04, the packets sent that reach the sink in time, over the
    # six stacks of the quality table: its rows are S03
    access = {s: round2_analysis.access_only(s) for s in SPLITS}
    six = [(a, s) for a in STACKS + ('pq-tuned',) for s in SPLITS] + [(access[s], s) for s in SPLITS]
    on_time = [quality.mean(a, 'on_time', s) for a, s in six]
    claim('S04', 'paquets envoyés reçus à temps, six piles du tableau de qualité, trois GOP : min., max. (%) (résultats, limites)',
          'avant leur échéance va de 22,9 à 56,4 % selon la pile et le GOP … 22,9 à 56,4 % des paquets envoyés y arrivent à temps',
          [(min(on_time), '=', 22.9, 1), (max(on_time), '=', 56.4, 1)])
    claim('S04', 'échéances manquées, six piles du tableau de qualité, trois GOP : max. sous 0,15 % des paquets reçus',
          'Une part d\'échéances manquées inférieure à 0,15 % des paquets reçus', [(max(quality.mean(a, 'late', s) for a, s in six), '<', 0.15, 2)])
    lost = [quality.mean(a, 'loss', s) for a, s in six]
    claim('S04', 'perte par pile et par GOP, six piles du tableau de qualité : min., max. (%) (limites)',
          'Or les piles du tableau \\ref{tab:fr-qualite} perdent 44 à 77 % des paquets, selon la pile et le GOP',
          [(min(lost), '=', 44, 0), (max(lost), '=', 77, 0)])
    shortest = {s: min(STACKS + ('pq-tuned', access[s]), key=lambda a: quality.mean(a, 'delay_mean', s)) for s in SPLITS}
    claim('S04', 'délai moyen des paquets reçus : la pile à accès seul la plus courte des six piles du tableau de qualité à chaque GOP',
          'La pile à accès seul a le délai moyen le plus court des six piles du tableau \\ref{tab:fr-qualite}, à chaque GOP',
          [(all(a == access[s] for s, a in shortest.items()), '=', True, 0)])
    delay = {s: {a: quality.mean(a, 'delay_mean', s) for a in STACKS} for s in SPLITS}
    claim('S04', 'délai moyen des paquets reçus : la pile hybride la plus courte des quatre piles à chaque GOP',
          'Parmi les quatre piles de E0, la pile hybride a aussi le délai moyen des paquets reçus le plus court à chaque GOP',
          [(all(min(d, key=d.get) == 'hybrid' for d in delay.values()), '=', True, 0)])
    empty = {s: [k for k in quality.values('pq', 'loss', s) if k not in quality.values('pq', 'delay_mean', s)] for s in SPLITS}
    claim('S04', 'AOMDV, note du tableau de qualité : simulations au délai relevé, à chaque GOP ; les deux autres n\'ont rien délivré',
          'Délai et échéances manquées sur 58 simulations, deux n\'ayant délivré aucun paquet (reçus à temps : 0 %)',
          [(len(quality.values('pq', 'delay_mean', s)), '=', 58, 0) for s in SPLITS]
          + [(all(len(v) == 2 for v in empty.values()), '=', True, 0),
             (all(quality.values('pq', 'loss', s)[k] == 100 and quality.values('pq', 'on_time', s)[k] == 0 for s, v in empty.items() for k in v),
              '=', True, 0)])

    # S11, the families of Holm's correction and the assumptions of the tests
    # (section 2.7), from
    # analysis/assumptions.py, which holds every test of the text, its tables
    # and its figures
    A = assumptions.summary()
    claim('S11', 'familles de Holm : lignes du tableau des familles ; familles qu\'elles comptent, plus d\'une pour certaines lignes',
          'donne les 62 familles en 20 lignes. Sa dernière colonne donne le nombre de tests de chaque famille ; une ligne peut valoir '
          'plusieurs familles',
          [(len(plan.FAMILIES), '=', 20, 0), (len(A['families']), '=', 62, 0), (len(A['families']) > len(plan.FAMILIES), '=', True, 0)])
    sizes = [f.size for f in plan.FAMILIES]
    claim('S11', 'tableau des familles : nombre de tests de chaque ligne, dans l\'ordre',
          ' … '.join('& %d' % n for n in sorted(set(sizes), reverse=True)),
          [(sizes == [9, 3, 3, 7, 6, 3, 2, 4, 3, 4, 2, 3, 3, 4, 2, 4, 2, 5, 7, 5], '=', True, 0),
           (all(any((b.experiment, b.family, len(b.tests)) == (f.experiment, f.en, f.size) for b in A['families']) for f in plan.FAMILIES),
            '=', True, 0)],
          source=table('revision-familles'))
    # the access-only stack in E4 and E5 (tranche T7): eight families,
    # one per series and comparison, and two single tests at the coefficient
    # 0.1, the levels and the sizes fixed before its results
    t7 = [b for b in A['blocks'] if b.title.startswith(('PSNR (dB), access - rules, ', 'PSNR (dB), hybrid - access, '))
          and b.title.endswith(tuple(access_analysis.TITLES.values()))]
    ones = next(b for b in A['blocks'] if b.title == 'the access-only stack at the coefficient 0.1')
    claim('S11', 'pile à accès seul dans E4 et E5 : huit familles de 2, 5, 5 et 7 tests par comparaison, deux tests uniques au '
          'coefficient 0,1', 'E4 et E5 mesurent aussi la pile à accès seul, face aux piles à règles et hybride … ou n\'a qu\'un niveau',
          [(sorted(len(b.tests) for b in t7) == [2, 2, 5, 5, 5, 5, 7, 7], '=', True, 0),
           (ones.family is None and len(ones.tests) == 2, '=', True, 0)])
    # the change of the gap hybrid - rules from the reference scenario is a
    # family of the fire series and one of the scenario series; the reference
    # itself is a single test there, the comparison of E0 at GOP 9-3
    variation = robustness.scenario_family('change', 'hybrid-rules', 'psnr')
    claim('S11', 'variation de l\'écart hybride − règles sous les variantes du scénario : une famille, ses tests (tableau des familles)',
          'Écart sous chaque variante du scénario & 5 variantes, par comparaison (PSNR), pour la variation et la perte M1 & 5',
          [(len(variation), '=', 5, 0), (sum(b.title.endswith('scenario variants, change hybrid-rules') for b in A['families']) == 1, '=', True, 0)],
          source=table('revision-familles'))
    refs = [stats.estimate(robustness.fire_contrast('gain', None, 'psnr').values()),
            stats.estimate(robustness.scenario_gap('hybrid-rules', None, 'psnr').values())]
    claim('S11', 'hybride − règles sous le scénario de référence, séries du feu et du scénario : tests uniques, la comparaison de E0 au '
          'GOP 9-3, corrigée dans sa famille',
          'comme toute comparaison hors des familles, telle celle du scénario de référence dans les séries du feu et du scénario … Un tel '
          'test reprend un écart corrigé dans une famille',
          [(all(e.holm is None and assumptions.same_comparison(e, hr['9M3D']) for e in refs), '=', True, 0),
           (hr['9M3D'].holm is not None, '=', True, 0)])
    claim('S11', 'écart moyen de deux piles sur les 60 graines : chaque graine moyennée sur ses trois GOP, un test unique',
          'L\'écart moyen entre deux piles se calcule sur les 60 graines, chaque graine moyennée sur ses trois GOP. Il fait l\'objet d\'un '
          'test unique',
          [(all(b.family is None and e.n == 60 and e.holm is None for b in A['blocks']
                if b.title == 'each seed averaged over the three GOPs' for _, e in b.tests), '=', True, 0), (data.SEEDS, '=', 60, 0)])
    # the tests and the comparisons they cover: a comparison tested in several
    # blocks (assumptions.same_comparison) counts once; the three of the power
    # agent, every seed at the same difference, have no shape to test
    shaped = [e for _, (label, e, *_) in A['tests'] if not assumptions.constant(e)]
    places = [sum(assumptions.same_comparison(x, e) for x in shaped) for _, _, e, *_ in A['distinct']]
    repeated = [n for n in places if n > 1]
    claim('S11', 'tests, comparaisons distinctes (cinq testées à deux, trois ou quatre endroits), les trois de l\'agent de puissance à '
          'différence constante ; Shapiro-Wilk à 0,05 : comparaisons rejetées, comparaisons à tester, rejets attendus',
          'Les 325 tests couvrent 315 comparaisons distinctes, car cinq d\'entre elles sont testées à deux, trois ou quatre endroits. Les '
          'trois comparaisons de l\'agent de puissance donnent la même différence pour chaque graine. Pour 60 des 312 autres, le test de '
          'Shapiro-Wilk … rejette la normalité au seuil de 0,05, contre 15,6 rejets attendus sous normalité',
          [(len(A['tests']), '=', 325, 0), (len(A['distinct']) + len(A['flat']), '=', 315, 0),
           (sum(places) == len(shaped) and len(repeated) == 5 and min(repeated) == 2 and max(repeated) == 4, '=', True, 0),
           (len(A['flat']) == 3 and all(label == 'power' for _, label, _ in A['flat']), '=', True, 0),
           (len(A['rejected']), '=', 60, 0), (len(A['distinct']), '=', 312, 0), (assumptions.ALPHA, '=', 0.05, 2),
           (assumptions.ALPHA * len(A['distinct']), '=', 15.6, 1)])
    claim('S11', 'Wilcoxon, Holm dans les mêmes familles : tests dont la conclusion change ; tests',
          'change la conclusion de 5 des 325 tests, 262 en familles et 63 uniques',
          [(len(A['differ']), '=', 5, 0), (len(A['tests']), '=', 325, 0), (A['family_tests'], '=', 262, 0),
           (len(A['tests']) - A['family_tests'], '=', 63, 0)])
    # the five tests whose conclusion Wilcoxon changes, in the order of the
    # text: a fixed CSMA/CA setting of the access-only stack against the
    # standard's (a single test of 3.3), F1 at GOP 6-6 (Table 12), the agents
    # stack under decaying exploration (3.5), the forest video and the swap (3.8)
    changed = {(b.title, label) for b, label, *_ in A['differ']}
    claim('S11', 'Wilcoxon : les cinq tests dont la conclusion change (méthode)',
          'L\'un compare un réglage CSMA/CA fixe de la pile à accès seul aux paramètres de la norme … Deux autres sont l\'écart hybride − '
          'règles sous F1 au GOP 6-6 … sont la perte M1 avec la vidéo forêt et l\'écart agents − règles quand la caméra et le puits sont '
          'échangés',
          [(changed == {('the single tests of E2: PSNR outside the families, the other measures',
                         'PSNR, fixed CSMA/CA be4nb5 on the rules stack - rules'),
                        ('PSNR (dB), hybrid - rules, per cell (20 seeds)', 'F1, GOP 6-6'),
                        ('PSNR (dB), the learning stacks - the access-only stack, decaying exploration', 'agents-edec'),
                        ('M1 loss (points), scenario variants, gap hybrid-rules', 'forest'),
                        ('PSNR (dB), scenario variants, gap agents-rules', 'swap')}, '=', True, 0)])
    an = A['anova']
    within = [x for x in an['normal'] if x[0] != 'seed means']
    seeds = next(x for x in an['normal'] if x[0] == 'seed means')
    box = an['box']['conditions']
    claim('S11', 'ANOVA : contrastes intra-graine, normalité rejetée (un sur huit) et son p ; moyennes des graines ; Box, 9 conditions',
          'rejette la normalité d\'un des huit contrastes orthonormés de Helmert des termes intra-graine, piles dans l\'ordre agents, '
          'hybride, règles (p = 0,047). Il rejette aussi celle des moyennes des graines (p = 0,010) … des neuf conditions de pile et de GOP (\\chi^2(90) = 100,2, p = 0,22',
          [(len(within) == 8, '=', True, 0), (sum(x[3] < assumptions.ALPHA for x in within) == 1, '=', True, 0),
           pv(min(x[3] for x in within), '= 0,047'), pv(seeds[3], '= 0,010'),
           (an['conditions'] == 9, '=', True, 0), (box['df'], '=', 90, 0), (box['chi2'], '=', 100.2, 1), pv(box['p_value'], '= 0,22')])
    def by_wilcoxon(title, label):
        """Wilcoxon's p, Holm in the family, of a test whose conclusion it changes."""
        return next(h for b, lb, e, pt, h, *_ in A['differ'] if b.title == title and lb == label)
    swap = by_wilcoxon('PSNR (dB), scenario variants, gap agents-rules', 'swap')
    claim('S11', 'Wilcoxon, Holm sur cinq variantes : pile à agents − règles, caméra et puits échangés',
          'Le test de Wilcoxon, corrigé dans la même famille, ne détecte pas le premier de ces écarts (p = 0,090', [pv(swap, '= 0,090')])

    forest = by_wilcoxon('M1 loss (points), scenario variants, gap hybrid-rules', 'forest')
    claim('S11', 'Wilcoxon, Holm sur cinq variantes : perte du niveau M1, pile hybride − règles, vidéo forêt, non détecté',
          'Corrigé dans la même famille, le test de Wilcoxon ne détecte pas l\'écart de la vidéo forêt (p = 0,066',
          [pv(forest, '= 0,066'), (forest >= 0.05, '=', True, 0)])
    agents = by_wilcoxon('PSNR (dB), the learning stacks - the access-only stack, decaying exploration', 'agents-edec')
    claim('S11', 'Wilcoxon, Holm sur deux : pile à agents sous exploration décroissante − pile à accès seul, détecté',
          'et le test de Wilcoxon, corrigé dans la même famille, détecte cet écart (p = 0,020',
          [pv(agents, '= 0,020'), (agents < 0.05, '=', True, 0)])
    fixed = next((e, h) for b, lb, e, pt, h, *_ in A['differ']
                 if lb == 'PSNR, fixed CSMA/CA be4nb5 on the rules stack - rules')
    claim('S11', 'Wilcoxon, test unique : réglage CSMA/CA fixe be4nb5 de la pile à accès seul − paramètres de la norme (dB), détecté',
          'Le test de Wilcoxon détecte toutefois l\'écart de l\'un d\'eux (+0,50 dB, p = 0,025',
          [(fixed[0].mean, '=', 0.50, 2), pv(fixed[1], '= 0,025'), (fixed[1] < 0.05, '=', True, 0)])

    # S12, section 2 (claims/methods.py); S07 to S10, study 11 (claims/round2.py); S13; S14
    methods.claims(C)
    round2.claims(C)
    synthesis.claims(C)
    access_robustness.claims(C)
    rc = C.report()
    return rc | report_unread()
