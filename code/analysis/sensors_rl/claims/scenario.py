"""G01 to G08: every number of the scenario series of experiment E5 (two
other videos, a 30 m grid, camera and sink exchanged, the head speed times
1.5) in the results, the discussion, the conclusions and the introduction,
recomputed from revision.tsv and the oracle of
oracle-s10.tsv. Holm runs over the five variants within each family; the gap
in the reference scenario is a single test."""
import sys

from ..analysis import access_robustness, robustness
from ..common import data
from .checks import LETTER_1, Claims, holm, mean, pair_checks, paired, pv, revision

VARIANTS = ('forest', 'smoke', 'j8', 'swap', 'v15')
FIRES = data.FIRES
STACKS = ('pq', 'rules', 'hybrid', 'agents')
ORACLE_TEXT = ('Aucune perte des séries de la charge, du feu et du scénario (1 200, 1 260 et 1 500 simulations, pile à accès seul comprise) '
               'ne vient d\'une coupure du réseau')

REV = revision()
ORACLE = None
_o = data.read_tsv('oracle-s10.tsv')
if _o:
    ORACLE = [r for r in _o if r['arm'].endswith(tuple('-' + v for v in VARIANTS))] or None


def arm(stack, v=None):
    return stack if v is None else '%s-%s' % (stack, v)


def rev10(a, m='psnr', fire=None):
    """GOP 9-3, T = 9 s; the 30 m grid's sets carry d30, the others d40."""
    return robustness.values(a, m, fire=fire)


def gap(a, b, v=None, m='psnr'):
    return paired(rev10(arm(a, v), m), rev10(arm(b, v), m))


def gaps(a, b, m='psnr'):
    """The five variants of one family, with their Holm p."""
    r = {v: gap(a, b, v, m) for v in VARIANTS}
    for v, p in zip(VARIANTS, holm([r[v]['p'] for v in VARIANTS])):
        r[v]['holm'] = p
    return r


def changes(a, b, m='psnr'):
    g0 = data.difference(rev10(a, m), rev10(b, m))
    r = {}
    for v in VARIANTS:
        g = data.difference(rev10(arm(a, v), m), rev10(arm(b, v), m))
        r[v] = paired(g, g0)
    for v, p in zip(VARIANTS, holm([r[v]['p'] for v in VARIANTS])):
        r[v]['holm'] = p
    return r


def cell_mean(a, m, fire=None):
    return mean(rev10(a, m, fire).values())


def main():
    if REV is None:
        sys.exit('data/sensors-rl/article/revision.tsv is needed')
    C = Claims(44, 44)
    claim = C.claim
    four = ('forest', 'smoke', 'swap', 'v15')
    three = ('forest', 'smoke', 'v15')
    hr, ar = gaps('hybrid', 'rules'), gaps('agents', 'rules')
    chr_ = changes('hybrid', 'rules')

    # G01, the hybrid stack's lead (first paragraph, abstract, conclusions)
    claim('G01', 'hybride − règles, quatre variantes sur cinq : min., max. ; bornes min. et max. ; Holm max. (dB)',
          'La pile hybride dépasse aussi la pile à règles sous quatre des cinq variantes du scénario de E5 … Son avance va de 1,18 à 1,90 dB '
          '(intervalles de 0,65 à 2,46 dB, p < 0,001',
          [(min(hr[v]['d'] for v in four), '=', 1.18, 2), (max(hr[v]['d'] for v in four), '=', 1.90, 2),
           (min(hr[v]['lo'] for v in four), 'b', 0.65, 2), (max(hr[v]['hi'] for v in four), 'b', 2.46, 2),
           pv(max(hr[v]['holm'] for v in four), '< 0,001'),
           (sorted(v for v in VARIANTS if hr[v]['holm'] < 0.05) == sorted(four), '=', True, 0)])
    claim('G01', 'grille de 30 m, hybride − règles (dB) ; Holm', '+0,40 dB [−0,11 ; 0,91], p = 0,12',
          pair_checks(hr['j8'], 0.40, -0.11, 0.91) + [pv(hr['j8']['holm'], '= 0,12')])
    claim('G01', 'grille de 30 m, baisse de l\'écart (dB) ; Holm', '−1,62 dB [−2,30 ; −0,95], p < 0,001',
          pair_checks(chr_['j8'], 1.62, 0.95, 2.30, sign=-1) + [pv(chr_['j8']['holm'], '< 0,001')])

    # G02, ranking, AOMDV and the agents stack
    claim('G02', 'agents − règles, forêt, fumée, vitesse : min., max. (dB) ; Holm min.', 'écarts de −0,59 à −0,09 dB, p ≥ 0,33',
          [(min(ar[v]['d'] for v in three), '=', -0.59, 2), (max(ar[v]['d'] for v in three), '=', -0.09, 2),
           pv(min(ar[v]['holm'] for v in three), '≥ 0,33')], source=LETTER_1)
    claim('G02', 'échange, agents − règles (dB) ; Holm', '−0,80 dB [−1,41 ; −0,19], p = 0,046',
          pair_checks(ar['swap'], 0.80, 0.19, 1.41, sign=-1) + [pv(ar['swap']['holm'], '= 0,046')])
    claim('G02', 'grille de 30 m, agents − règles (dB) ; Holm', '−1,93 dB [−2,41 ; −1,45], p < 0,001',
          pair_checks(ar['j8'], 1.93, 1.45, 2.41, sign=-1) + [pv(ar['j8']['holm'], '< 0,001')])

    ha = gaps('hybrid', 'agents')
    claim('G02', 'hybride − agents, cinq variantes : min., max. ; bornes min. et max. ; Holm max.',
          'La pile hybride dépasse la pile à agents sous chacune des cinq variantes, de 1,48 à 2,33 dB (intervalles de 0,94 à 2,93 dB, '
          'p < 0,001',
          [(min(ha[v]['d'] for v in VARIANTS), '=', 1.48, 2), (max(ha[v]['d'] for v in VARIANTS), '=', 2.33, 2),
           (min(ha[v]['lo'] for v in VARIANTS), 'b', 0.94, 2), (max(ha[v]['hi'] for v in VARIANTS), 'b', 2.93, 2),
           pv(max(ha[v]['holm'] for v in VARIANTS), '< 0,001')])

    # G03, the 30 m grid
    claim('G03', 'perte des règles, grille de 30 m ; référence (%)', 'La pile à règles y perd 44,7 % des paquets, contre 56,2 %',
          [(cell_mean('rules-j8', 'loss'), '=', 44.7, 1), (cell_mean('rules', 'loss'), '=', 56.2, 1)], source=LETTER_1)
    claim('G03', 'déclarations par simulation : règles 30 m ; règles référence',
          'La pile à règles n\'y déclare morts que 9,1 voisins par simulation, contre 22,0 sur la grille de 40 m',
          [(cell_mean('rules-j8', 'declared'), '=', 9.1, 1), (cell_mean('rules', 'declared'), '=', 22.0, 1)])

    # G04, loss regime, severity, oracle
    per = {v: [cell_mean(arm('rules', v), 'loss', f) for f in FIRES] for v in (None,) + VARIANTS}
    e10 = [x for v in VARIANTS for x in per[v]]
    claim('G04', 'perte des règles par cellule, quinze cellules : min., max. ; référence (%)', 'La pile à règles perd 43,0 à 62,3 % des paquets selon la variante et le feu, contre 54,1 à 57,3 % dans le scénario de référence',
          [(min(e10), '=', 43.0, 1), (max(e10), '=', 62.3, 1), (min(per[None]), '=', 54.1, 1), (max(per[None]), '=', 57.3, 1)])
    label = 'oracle des cinq variantes, pile à accès seul comprise : simulations, aucun paquet perdu sans chemin'
    access = access_robustness.lost_without_path(('scenario',))
    if ORACLE is None or access is None:
        claim('G04', label, ORACLE_TEXT, [(None, '=', 0, 0)])
    else:
        claim('G04', label, ORACLE_TEXT, [(len(ORACLE) + access[0], '=', 1500, 0),
                                          (sum(int(r['unreachable']) for r in ORACLE) + access[2] == 0, '=', True, 0)])

    # G05, level M1, the 28 dB threshold
    m1 = gaps('hybrid', 'rules', 'm1loss')
    # The text writes this difference and its bounds at two decimals: at one,
    # the upper bound would print 0.0 and hide that it is positive.
    claim('G05', 'échange et grille de 30 m, perte de M1 (points) ; Holm',
          'Pour cette perte, aucune différence statistiquement significative n\'a été détectée quand la caméra et le puits sont échangés '
          '(−1,90 point [−3,82 ; 0,01], p = 0,10) ni sur la grille de 30 m (−1,01 point [−3,27 ; 1,25], p = 0,37',
          pair_checks(m1['swap'], -1.90, -3.82, 0.01) + [pv(m1['swap']['holm'], '= 0,10')]
          + pair_checks(m1['j8'], -1.01, -3.27, 1.25) + [pv(m1['j8']['holm'], '= 0,37')])
    three = ('forest', 'smoke', 'v15')
    claim('G05', 'forêt, fumée, vitesse × 1,5, perte de M1, hybride − règles : min., max. (points) ; bornes min. et max. ; Holm max.',
          'la pile hybride perd moins de paquets du niveau M1 que la pile à règles (−4,2 à −2,6 points, intervalles de −6,5 à −0,6 point, '
          'p ≤ 0,032',
          [(min(m1[v]['d'] for v in three), '=', -4.2, 1), (max(m1[v]['d'] for v in three), '=', -2.6, 1),
           (min(m1[v]['lo'] for v in three), 'b', -6.5, 1), (max(m1[v]['hi'] for v in three), 'b', -0.6, 1),
           pv(max(m1[v]['holm'] for v in three), '≤ 0,032'), (all(m1[v]['d'] < 0 and m1[v]['holm'] < 0.05 for v in three), '=', True, 0)])
    ch = changes('hybrid', 'rules')
    four = ('forest', 'smoke', 'swap', 'v15')
    claim('G05', 'variation de l\'écart hybride − règles, quatre variantes hors grille de 30 m : min., max. ; bornes min. et max. ; Holm '
          'min. ; intervalles sans zéro, forêt et échange',
          'Entre ces écarts et celui du scénario de référence, aucune différence statistiquement significative n\'a été détectée (−0,84 à '
          '−0,12 dB, intervalles de −1,56 à +0,62 dB, p ≥ 0,085). Les intervalles non corrigés de la vidéo forêt et de l\'échange excluent '
          'toutefois zéro',
          [(min(ch[v]['d'] for v in four), '=', -0.84, 2), (max(ch[v]['d'] for v in four), '=', -0.12, 2),
           (min(ch[v]['lo'] for v in four), 'b', -1.56, 2), (max(ch[v]['hi'] for v in four), 'b', 0.62, 2),
           pv(min(ch[v]['holm'] for v in four), '≥ 0,085'),
           (sorted(v for v in four if ch[v]['holm'] >= 0.05 and (ch[v]['hi'] < 0 or ch[v]['lo'] > 0)) == ['forest', 'swap'], '=', True, 0)])

    # G06, closing paragraph
    three = ('forest', 'smoke', 'v15')
    claim('G06', 'agents − règles, forêt, fumée, vitesse × 1,5 : aucun Holm < 0,05 ; min., max. ; bornes min. et max. ; Holm min. ; '
          'au-dessous sous les deux autres, l\'échange et la grille de 30 m',
          'Avec les vidéos forêt et fumée et la vitesse de tête \\times 1,5, aucune différence statistiquement significative n\'a été détectée '
          'entre les piles à agents et à règles (−0,59 à −0,09 dB, intervalles de −1,32 à +0,48 dB, p ≥ 0,33). La pile à agents passe sous '
          'la pile à règles quand la caméra et le puits sont échangés (−0,80 dB [−1,41 ; −0,19], p = 0,046) et sur la grille de 30 m',
          [(min(ar[v]['d'] for v in three), '=', -0.59, 2), (max(ar[v]['d'] for v in three), '=', -0.09, 2),
           (min(ar[v]['lo'] for v in three), 'b', -1.32, 2), (max(ar[v]['hi'] for v in three), 'b', 0.48, 2),
           pv(min(ar[v]['holm'] for v in three), '≥ 0,33'), (all(ar[v]['holm'] >= 0.05 for v in three), '=', True, 0),
           (sorted(v for v in VARIANTS if ar[v]['d'] < 0 and ar[v]['holm'] < 0.05) == ['j8', 'swap'], '=', True, 0)])

    # G07, methods sentences and the fairness table


    # G08, the counts of the scenario series
    claim('G08', 'configurations et simulations de la série scénario de E5 : 4 piles × 5 variantes × 3 feux, × 20', 'soit 60 configurations et 1 200 simulations',
          [(4 * 5 * 3, '=', 60, 0), (sum(len(rev10(arm(s, v))) for s in STACKS for v in VARIANTS), '=', 1200, 0)], source=LETTER_1)
    return C.report()
