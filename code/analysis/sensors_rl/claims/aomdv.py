"""A01 to A11: every number of the tuned AOMDV series of experiment E1 in
section 3.2, the introduction, the discussion and the conclusions,
recomputed from revision.tsv; the sets of the series and their seeds are
read from study 10's results/runs.tsv (seeds checked against each set's
PROGRESS.txt when it was compiled), so that the raw sets are not needed.
Holm runs over the three GOPs of one comparison; a pooled value is, per
seed, the mean over the three GOPs."""
import sys

from ..analysis import quality
from ..common import data, paths
from . import checks
from .checks import Claims, mean, pair_checks, paired, pooled, pv, range_checks, revision

SPLITS = data.SPLITS
FIRES = data.FIRES
GC = {'3M9D': '0p01597', '6M6D': '0p02525', '9M3D': '0p03'}
FIRE_SET = {'F1': 'fire', 'F2': 'fire2', 'F3': 'fire3'}

REV = revision()


def rev(arm, split='9M3D', m='psnr', fire=None):
    """{seed: value} at T = 9 s on the 40 m grid (GOP, metric and fire in this order)."""
    return checks.rev(arm, split, m=m, fire=fire)


def per_gop(a, b, m='psnr'):
    """The Estimates of a - b per GOP, Holm over the three GOPs, in the order of SPLITS."""
    return list(quality.gops(a, b, m).values())


def cells(arm, m):
    return [mean(rev(arm, g, m, f).values()) for g in SPLITS for f in FIRES]


def set_name(arm, split, fire):
    return 'set_AOMDV_GC-PN-%s-13_p9-n100-d40-%s-%s-s10' % (GC[split], FIRE_SET[fire], arm)


RUNS = data.read_tsv(paths.results(paths.STUDY_R1, 'runs.tsv'))


def seeds(name):
    """realisation -> seed of a set, from runs.tsv; None when it holds no row of the set."""
    if RUNS is None:
        return None
    out = {r['realisation']: int(r['seed']) for r in RUNS if r['set'] == name}
    return out or None


def main():
    if REV is None:
        sys.exit('data/sensors-rl/article/revision.tsv is needed')
    C = Claims(36, 40)
    claim = C.claim

    # A01, the control AOMDV series of E1 as section 3.2 writes it (reproduction of P03)
    e2 = paired(pooled('pq-ctl'), pooled('pq'))
    claim('A01', 'AOMDV de contrôle − AOMDV, 60 graines (dB) ; p', '+0,07 dB [0,01 ; 0,14], p = 0,031',
          pair_checks(e2, 0.07, 0.01, 0.14) + [pv(e2['p'], '= 0,031')])
    g2 = per_gop('pq-ctl', 'pq')
    text = '+0,07 à +0,08 dB, intervalles de −0,07 à +0,22 dB, p ≥ 0,20'
    claim('A01', 'même écart par GOP : aucun GOP après Holm ; écarts min. et max. (dB) ; Holm min. ; bornes min. et max.', text,
          range_checks(g2, text) + [(all(e.holm >= 0.05 for e in g2), '=', True, 0)])
    rp = paired(pooled('rules'), pooled('pq'))
    claim('A01', 'pile à règles − AOMDV, 60 graines (dB) ; p : conclusions, résultats',
          'La pile à règles dépasse AOMDV en moyenne sur les 60 graines (+6,2 dB [5,8 ; 6,7], p < 0,001 … '
          '+6,2 dB [5,8 ; 6,7], p < 0,001',
          pair_checks(rp, 6.2, 5.8, 6.7, 1) + [pv(rp['p'], '< 0,001'), (rp['n'], '=', 60, 0)])

    # A02, the share of the timers (pq-tuned - pq-ctl)
    t = paired(pooled('pq-tuned'), pooled('pq-ctl'))
    claim('A02', 'AOMDV aux temporisations inter-couches − AOMDV de contrôle, 60 graines (dB) ; p',
          'AOMDV aux temporisations inter-couches dépasse AOMDV de contrôle (+2,04 dB [1,73 ; 2,34], p < 0,001',
          pair_checks(t, 2.04, 1.73, 2.34) + [pv(t['p'], '< 0,001')])
    gt = per_gop('pq-tuned', 'pq-ctl')
    text = '1,60 à 2,35 dB selon le GOP (intervalles de 1,21 à 2,83 dB, p < 0,001'
    claim('A02', 'même écart par GOP : min., max. (dB) ; Holm max. ; bornes min. et max.', 'p < 0,001, test unique), de ' + text, range_checks(gt, text))

    # A04, the size of the tuned AOMDV series
    claim('A04', 'simulations d\'AOMDV aux temporisations inter-couches ; moyennes sur 60 graines = moyennes sur 180 simulations', 'dans ses 180 simulations',
          [(sum(len(rev('pq-tuned', g)) for g in SPLITS), '=', 180, 0), (len(pooled('pq-tuned')) == 60, '=', True, 0)])

    # A05, the gap that remains (rules - pq-tuned)
    rt = paired(pooled('rules'), pooled('pq-tuned'))
    claim('A05', 'pile à règles − AOMDV aux temporisations inter-couches, 60 graines (dB) ; p',
          'La pile à règles dépasse encore AOMDV aux temporisations inter-couches (+4,13 dB [3,83 ; 4,42], p < 0,001 … '
          'AOMDV aux temporisations inter-couches ([3,83 ; 4,42], p < 0,001',
          pair_checks(rt, 4.13, 3.83, 4.42) + [pv(rt['p'], '< 0,001')])
    gr = per_gop('rules', 'pq-tuned')
    claim('A05', 'même écart par GOP : 3-9, le plus faible, et 9-3, le plus fort (dB) ; Holm max. ; bornes min. et max.',
          'L\'écart va de 1,84 dB au GOP 3-9 à 6,06 dB au GOP 9-3 (intervalles de 1,30 à 6,55 dB, p < 0,001',
          [(gr[0].mean, '=', 1.84, 2), (gr[2].mean, '=', 6.06, 2),
           (min(e.mean for e in gr) == gr[0].mean and max(e.mean for e in gr) == gr[2].mean, '=', True, 0),
           pv(max(e.holm for e in gr), '< 0,001'), (min(e.lo for e in gr), 'b', 1.30, 2), (max(e.hi for e in gr), 'b', 6.55, 2)])

    # A06, losses of tuned AOMDV and the rules, per cell; the rules' shares are
    # P23 (loss, 3.1) and P02 (level M1), in claims/results.py
    tl, tm = cells('pq-tuned', 'loss'), cells('pq-tuned', 'm1loss')
    gl, gm = per_gop('rules', 'pq-tuned', 'loss'), per_gop('rules', 'pq-tuned', 'm1loss')
    text = '+11,9 à +18,0 points selon le GOP (intervalles de 9,6 à 20,8 points, p < 0,001'
    claim('A06', 'perte, AOMDV aux temporisations inter-couches par cellule, min. et max. (%) ; pile à règles au-dessus à chaque GOP : écarts '
          'min., max. (points) ; Holm max. ; bornes min. et max.',
          'La perte globale de la pile à règles est pourtant plus forte que celle d\'AOMDV aux temporisations inter-couches (42 à 48 % selon la '
          'cellule). L\'écart va de ' + text,
          range_checks(gl, text) + [(min(tl), '=', 42, 0), (max(tl), '=', 48, 0), (all(e.mean > 0 for e in gl), '=', True, 0)])
    text = '−20,9 à −11,5 points, intervalles de −24,0 à −6,9 points, p < 0,001'
    claim('A06', 'perte du niveau M1, pile à règles au-dessous d\'AOMDV aux temporisations inter-couches à chaque GOP : écarts min., max. '
          '(points) ; Holm max. ; bornes min. et max.', 'La pile à règles perd en revanche moins de paquets du niveau M1 (' + text,
          range_checks(gm, text) + [(all(e.mean < 0 for e in gm), '=', True, 0)])
    claim('A06', 'AOMDV aux temporisations inter-couches : perte du niveau M1 par cellule, min. et max. (%) ; images ≥ 28 dB, aucune ; '
          'simulations',
          'Cette variante d\'AOMDV en perd 32 à 45 % et ne restitue aucune image qui atteigne le seuil de PSNR dans ses 180 simulations',
          [(min(tm), '=', 32, 0), (max(tm), '=', 45, 0), (sum(sum(rev('pq-tuned', g, 'usable').values()) for g in SPLITS) == 0, '=', True, 0),
           (sum(len(rev('pq-tuned', g, 'usable')) for g in SPLITS), '=', 180, 0)])

    # A08, the decomposition section 3.2 writes, in the order of the two series of E1
    claim('A08', '0,07 + 2,04 + 4,13 = règles − AOMDV, à 1e-9 près (identité des moyennes appariées) ; les trois parts ; arrondi',
          'ces 6,2 dB comprennent 0,07 dB pour la couche d\'accès, 2,04 dB pour les temporisations et la file de route, et 4,13 dB pour les '
          'autres différences',
          [(abs(e2['d'] + t['d'] + rt['d'] - rp['d']) < 1e-9, '=', True, 0), (e2['d'] + t['d'] + rt['d'], '=', 6.2, 1),
           (e2['d'], '=', 0.07, 2), (t['d'], '=', 2.04, 2), (rt['d'], '=', 4.13, 2)])

    # A11, the seeds of the series
    same = None
    if RUNS is not None:
        same = True
        for g in SPLITS:
            for f in FIRES:
                st, sc = seeds(set_name('pq-tuned', g, f)), seeds(set_name('pq-ctl', g, f))
                same = same and st is not None and st == sc and len(st) == 20
    claim('A11', 'neuf jeux de 20 simulations, graines identiques à AOMDV de contrôle (PROGRESS.txt)',
          'La graine d\'une simulation dérive du nom du feu et du numéro de la simulation, non de la pile ni du GOP',
          [(same, '=', True, 0)] if same is not None else [(None, '=', 0, 0)])
    return C.report()
