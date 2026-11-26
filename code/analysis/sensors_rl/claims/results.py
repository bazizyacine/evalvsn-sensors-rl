"""P02 to P43: the derived numbers of the results, the discussion and the
conclusions that the tables and figures do not print (the losses per cell,
the pooled p of the AOMDV control, the comparisons of E0 to E3 with their
intervals, the mechanism at T = 7 s, the oracle, the energy, the HELLO counts
and the rest), recomputed from data/sensors-rl/article: comparative.tsv,
revision.tsv, agent-trace.tsv, break-agent.tsv, break-cases.tsv,
overhead.tsv, frames.tsv, oracle-s10.tsv and codec-frames.tsv; the oracle of
P04 reads study 09's results/oracle.tsv, that of P29 and P32 study 11's
results for the access-only stack (analysis/access_robustness.lost_without_path),
and P12 the end of the exploration's decay in code/campaign/sets.conf. P38
and P40 compute from the radio and capture constants they name, P43 the
agents' memory from the simulator's headers (analysis/overhead.memory). A
line that quotes a reply of the first round names it as its source; the
cells of the tables are S03 (claims/tables.py)."""
import math
import re
import sys

from ..analysis import ablation, access_robustness, coding, comparative, controls, overhead, quality, robustness, round2
from ..common import data, paths, stats
from .checks import (LETTER_1, LETTER_2, Claims, ci_mean, gap_checks, holm, interval_checks, mean, pair_checks, paired, pooled, pv,
                     range_checks, rev, revision)

SPLITS = data.SPLITS
FIRES = data.FIRES
PERIODS = ('p7', 'p9', 'p12', 'p18', 'p30')
MAIN8 = (2, 3, 4, 5, 6, 8, 10, 12)                      # main frames after the first image, GOP 9-3
ORACLE_TEXT = ('Aucune perte des séries de la charge, du feu et du scénario (1 200, 1 260 et 1 500 simulations, pile à accès seul comprise) '
               'ne vient d\'une coupure du réseau')
P39_TEXT = 'une frame codée compte en moyenne plus d\'octets que l\'image brute, de 25 344 octets'

COMP = data.read_tsv('comparative.tsv')
REV = revision()
TRACE = data.read_tsv('agent-trace.tsv')
BRK = data.read_tsv('break-agent.tsv')
OVER = data.read_tsv('overhead.tsv')
FRAMES = data.read_tsv('frames.tsv')
ORACLE = data.read_tsv('oracle-s10.tsv')
CODEC = data.read_tsv('codec-frames.tsv')
ORACLE_E0 = data.read_tsv(paths.results(paths.STUDY_E0, 'oracle.tsv'))


def comp(stack, split, fire=None, m='psnr'):
    return data.stack(COMP, stack, split, m, fire)


def comp_pooled(stack, m='psnr'):
    ds = [comp(stack, s, m=m) for s in SPLITS]
    return {k: mean(d[k] for d in ds) for k in ds[0]}


def cell_means(stack, m='psnr'):
    return [mean(comp(stack, s, f, m).values()) for s in SPLITS for f in FIRES]


def brk(arm, cols):
    return {(r['fire'], r['realisation']): sum(float(r[c]) for c in cols) for r in BRK
            if r['arm'] == arm and all(r[c] != '' for c in cols)}


def trace(arm, agent, t, col):
    return float(next(r[col] for r in TRACE if r['arm'] == arm and r['agent'] == agent and r['t'] == str(t)))


def frames(arm, period):
    """Per simulation, its twelve image rows."""
    out = {}
    for r in FRAMES:
        if r['arm'] == arm and r['period'] == period:
            out.setdefault((r['fire'], r['realisation']), []).append(r)
    return out


def per_sim(arm, period, f):
    return {k: f(v) for k, v in frames(arm, period).items()}


def decay_ends():
    """The instants (s) at which the exploration of the -edec- sets reaches 0
    (rl_eps_end, code/campaign/sets.conf)."""
    return {int(m[1]) for line in open(paths.CONF, encoding='utf-8') if '-edec-' in line
            for m in [re.search(r'\brl_eps_end=(\d+)', line)] if m}


def main():
    if COMP is None or REV is None:
        sys.exit('data/sensors-rl/article/comparative.tsv and revision.tsv are needed')
    C = Claims(48, 42)
    claim = C.claim

    cells = comparative.cells(COMP, 'psnr')

    # P02, the rules and AOMDV per cell
    rm, am = cell_means('rules', 'm1loss'), cell_means('aomdv', 'm1loss')
    claim('P02', 'perte de M1 par cellule, min. et max. (%) : pile à règles ; AOMDV',
          'perte plus faible du niveau M1, de 14 à 32 % selon la cellule, contre 62 à 70 % pour AOMDV',
          [(min(rm), '=', 14, 0), (max(rm), '=', 32, 0), (min(am), '=', 62, 0), (max(am), '=', 70, 0)])
    rp = list(comparative.paired_cells(cells, 'rules', 'aomdv').values())
    text = '3,2 à 8,9 dB selon la cellule (intervalles de 2,1 à 9,9 dB, p < 0,001'
    claim('P02', 'pile à règles moins AOMDV par cellule, Holm sur neuf cellules : min., max. (dB) ; Holm max. ; bornes min. et max.',
          'L\'écart va de ' + text, range_checks(rp, text) + [(len(rp) == 9, '=', True, 0)])

    # P03, AOMDV control
    r = paired(pooled('pq-ctl'), pooled('pq'))
    claim('P03', 'AOMDV de contrôle moins AOMDV, 60 graines', 'sur les 60 graines, AOMDV de contrôle dépasse AOMDV (+0,07 dB [0,01 ; 0,14], p = 0,031',
          pair_checks(r, 0.07, 0.01, 0.14) + [pv(r['p'], '= 0,031'), (r['n'], '=', 60, 0)])
    text = '+0,07 à +0,08 dB, intervalles de −0,07 à +0,22 dB, p ≥ 0,20'
    claim('P03', 'même écart par GOP, Holm sur trois GOP : min., max. (dB) ; Holm min. ; bornes min. et max.', text,
          range_checks(list(quality.gops('pq-ctl', 'pq', 'psnr').values()), text))

    # P04, the oracle of E0, one row per simulation
    text = ('Pour chaque paquet perdu des 720 simulations, l\'oracle de connectivité trouve à l\'émission un chemin de nœuds vivants entre '
            'la caméra et le puits')
    claim('P04', 'étude principale E0, oracle : simulations, aucun paquet perdu sans chemin', text,
          [(None, '=', 0, 0)] if ORACLE_E0 is None else
          [(len(ORACLE_E0), '=', 720, 0), (len(COMP) == len(ORACLE_E0), '=', True, 0),
           (all(r['unreachable'] == '0' and r['recoverable'] == r['lost'] for r in ORACLE_E0), '=', True, 0),
           (sum(int(r['lost']) for r in ORACLE_E0) > 0, '=', True, 0)])

    # P05, E0: hybrid - rules over the three GOPs and per GOP, agents - rules
    # over the three GOPs
    e = comparative.per_seed(cells, 'hybrid', 'rules')[0]
    text = 'la pile hybride dépasse la pile à règles en moyenne sur les 60 graines (+1,52 dB [1,12 ; 1,92], p < 0,001'
    claim('P05', 'pile hybride moins règles, trois GOP, 60 graines', text, gap_checks(e, text) + [(e.n, '=', 60, 0)])
    hr = comparative.paired_gops(cells, 'hybrid', 'rules')
    claim('P05', 'pile hybride moins règles, GOP 3-9, 6-6 et 9-3, Holm sur trois GOP ; cellules',
          'détaillent les neuf cellules … Sur les 60 graines, l\'avance de la pile hybride sur la pile à règles est significative aux GOP 3-9, 6-6 et 9-3. Elle y '
          'est de +1,08 [0,34 ; 1,81] (p = 0,005), +1,47 [0,92 ; 2,02] et +2,02 dB [1,50 ; 2,53] (p < 0,001 pour ces deux',
          gap_checks(hr['3M9D'], '+1,08 [0,34 ; 1,81], p = 0,005') + gap_checks(hr['6M6D'], '+1,47 [0,92 ; 2,02], p < 0,001')
          + gap_checks(hr['9M3D'], '+2,02 dB [1,50 ; 2,53], p < 0,001')
          + [(len(SPLITS) * len(FIRES) == 9, '=', True, 0), (min(e.n for e in hr.values()), '=', 60, 0)])
    r = paired(comp_pooled('agents'), comp_pooled('rules'))
    claim('P05', 'pile à agents moins règles, trois GOP, 60 graines', '−0,01 dB [−0,32 ; 0,29], p = 0,94',
          pair_checks(r, -0.01, -0.32, 0.29) + [pv(r['p'], '= 0,94')])
    gar = list(comparative.paired_gops(cells, 'agents', 'rules').values())
    text = '−0,14 à +0,16 dB, intervalles de −0,73 à +0,82 dB, p = 1,00'
    claim('P05', 'pile à agents moins règles, trois GOP, Holm sur trois GOP : min., max. (dB) ; Holm de chacun ; bornes min. et max.',
          'ni à aucun GOP (%s pour chacun' % text, range_checks(gar, text) + [(len(gar) == 3, '=', True, 0)])

    # P06, frozen hybrid - rules
    r = paired(pooled('hybrid-frozen'), pooled('rules'))
    claim('P06', 'pile hybride figée moins règles, 60 graines', 'avec la pile à règles sur les 60 graines (−0,04 dB [−0,41 ; 0,33], p = 0,84',
          pair_checks(r, -0.04, -0.41, 0.33) + [pv(r['p'], '= 0,84'), (r['n'], '=', 60, 0)])
    per = quality.gops('hybrid-frozen', 'rules', 'psnr')
    text = '−0,20 à +0,08 dB, intervalles de −0,75 à +0,69 dB, p = 1,00'
    claim('P06', 'même écart par GOP : min., max. (dB) ; Holm de chacun ; bornes min. et max.', text, range_checks(list(per.values()), text))
    claim('P06', 'même écart par GOP : chaque borne haute sous l\'avance de la pile hybride qui apprend',
          'Ces intervalles excluent, à chaque GOP, l\'avance de la pile hybride qui apprend',
          [(all(per[g].hi < hr[g].mean for g in SPLITS), '=', True, 0)])
    text = '+1,56 dB [1,21 ; 1,91], p < 0,001'
    claim('P06', 'pile hybride moins pile hybride figée, trois GOP, 60 graines', 'dépasse la même pile sous politique figée (' + text,
          gap_checks(quality.over_gops('hybrid', 'hybrid-frozen', 'psnr'), text))
    text = '1,07 à 1,94 dB selon le GOP (intervalles de 0,48 à 2,48 dB, p < 0,001'
    claim('P06', 'même écart par GOP, Holm sur trois GOP : min., max. (dB) ; Holm max. ; bornes min. et max.', 'L\'écart va de ' + text,
          range_checks(list(quality.gops('hybrid', 'hybrid-frozen', 'psnr').values()), text))

    # P07, hybrid - agents, the one switch between the two stacks being the
    # link-break agent: over the three GOPs and at GOP 9-3
    r = paired(comp_pooled('hybrid'), comp_pooled('agents'))
    claim('P07', 'pile hybride moins pile à agents, trois GOP, 60 graines', 'sur les 60 graines (+1,53 dB [1,20 ; 1,87], p < 0,001',
          pair_checks(r, 1.53, 1.20, 1.87) + [pv(r['p'], '< 0,001'), (r['n'], '=', 60, 0)])
    six = paired(comp_pooled('hybrid'), comp_pooled('rules'))
    claim('P07', 'effet de l\'agent de rupture, effet des six autres : trois GOP ; GOP 9-3 (dB) ; à ce GOP, aucun gain sans l\'agent d\'accès',
          'abaisse donc, à lui seul, le PSNR de 1,53 dB, alors que les six autres agents le relèvent de 1,52 dB. Au GOP 9-3, ces écarts sont de '
          '2,07 et 2,02 dB, et aucun gain statistiquement significatif sur la pile à règles n\'a été détecté sans l\'agent de l\'accès au canal',
          [(r['d'], '=', 1.53, 2), (six['d'], '=', 1.52, 2), (paired(rev('hybrid'), rev('agents'))['d'], '=', 2.07, 2),
           (paired(rev('hybrid'), rev('rules'))['d'], '=', 2.02, 2), (len(ablation.HYBRID) == 6, '=', True, 0),
           (paired(rev('hybrid-noA'), rev('rules'))['p'] >= 0.05, '=', True, 0)])

    # P08, GOP 9-3 against the PSNR threshold, per fire: the means of the six
    # stacks of the PSNR table, the bounds of the rule and agents stacks
    by_fire = {st: [comp(st, '9M3D', f) for f in FIRES] for st in ('aomdv', 'rules', 'agents', 'hybrid')}
    by_fire.update({st: [rev(a, '9M3D', fire=f) for f in FIRES] for st, a in (('tuned', 'pq-tuned'), ('access', ablation.ACCESS_ONLY))})
    m93 = {st: [mean(v.values()) for v in vs] for st, vs in by_fire.items()}
    claim('P08', 'GOP 9-3 : les piles du tableau du PSNR dont la moyenne dépasse 28 dB sous chaque feu, les autres dessous sous chaque feu',
          'Au GOP 9-3, seules les piles à accès seul et hybride ont un PSNR moyen au-dessus du seuil de PSNR, 28 dB, sous chacun des trois '
          'feux',
          [(sorted(st for st, v in m93.items() if min(v) > 28) == ['access', 'hybrid'], '=', True, 0),
           (sorted(st for st, v in m93.items() if max(v) < 28) == ['agents', 'aomdv', 'rules', 'tuned'], '=', True, 0)])
    reach = {st: [ci_mean(v.values())[1] >= 28 for v in by_fire[st]] for st in ('rules', 'agents')}
    claim('P08', 'GOP 9-3 : les feux où la borne haute de l\'intervalle atteint 28 dB, pile à règles (trois), pile à agents (F3)',
          'Les intervalles de la pile à règles sous les trois feux, et celui de la pile à agents sous F3, atteignent cependant ce seuil',
          [(reach == {'rules': [True] * 3, 'agents': [False, False, True]}, '=', True, 0)])

    # P09, P10, break agent and declarations
    if BRK is None:
        claim('P09', 'traces de l\'agent de rupture', '', [(None, '=', 0, 0)])
    else:
        b3 = mean(brk('agents', ['best3']).values())
        tot = mean(brk('agents', ['best1', 'best2', 'best3', 'best5']).values())
        claim('P09', 'couples dont trois échecs ont la plus grande valeur, sur le total',
              'En fin de simulation, trois échecs gardent la plus grande valeur pour 36 des 41 couples de nœud et d\'état observés',
              [(b3, '=', 36, 0), (tot, '=', 41, 0)])
        one, counted = mean(brk('agents', ['decl1']).values()), mean(brk('agents', ['decl1', 'decl2', 'decl3', 'decl5']).values())
        claim('P10', 'déclarations que comptent les compteurs de l\'agent : d\'un seul échec, toutes ; part (%)',
              'Ces actions explorées produisent donc 13,1 des 18,6 déclarations que les compteurs de l\'agent enregistrent par simulation, soit 70 %',
              [(one, '=', 13.1, 1), (counted, '=', 18.6, 1), (100 * one / counted, '=', 70, 0)])
        n = mean(rev('agents-tr', m='declared').values())
        claim('P10', 'pile à agents : déclarations par simulation, dont après le dernier relevé des compteurs',
              'La pile à agents fait 19,9 déclarations par simulation (tableau \\ref{tab:fr-controles}), dont 1,3 après le dernier '
              'relevé de ces compteurs',
              [(n, '=', 19.9, 1), (n - counted, '=', 1.3, 1)])
    sa = {k: 100 * v / rev('agents-tr', m='declared')[k] for k, v in rev('agents-tr', m='false_declared').items() if rev('agents-tr', m='declared')[k] > 0}
    sr = {k: 100 * v / rev('rules', m='declared')[k] for k, v in rev('rules', m='false_declared').items() if rev('rules', m='declared')[k] > 0}
    # the three cases of the declarations (break-cases.tsv), the mean over the
    # simulations of each one's share; the third one, which the test compares,
    # also from revision.tsv
    shares = {a: [mean(controls.case_share(a, c).values()) for c in (['dead'], ['zone', 'range'], ['budget'])]
              for a in ('agents-tr', 'rules')} if controls.cases('rules', 'n') is not None else None
    claim('P10', 'cas des déclarations, moyenne par simulation, pile à agents tracée et règles : hors service ; vivant, lien sous P_CCA ; '
          'vivant, lien au-dessus (%) ; le troisième d\'après revision.tsv',
          'En moyenne par simulation, ces cas représentent 0,1, 2,3 et 97,6 % des déclarations, contre 0,3, 2,0 et 97,7 % pour la pile à '
          'règles',
          [(None, '=', 0, 0)] if shares is None else
          [(x, '=', v, 1) for a, vs in (('agents-tr', (0.1, 2.3, 97.6)), ('rules', (0.3, 2.0, 97.7))) for x, v in zip(shares[a], vs)]
          + [(mean(sa.values()), '=', 97.6, 1), (mean(sr.values()), '=', 97.7, 1)])
    r = paired(sa, sr)
    claim('P10', 'part à tort, agents moins règles, par graine (points)', '−0,1 point [−1,3 ; 1,1], p = 0,91',
          pair_checks(r, -0.1, -1.3, 1.1, 1) + [pv(r['p'], '= 0,91')])
    claim('P10', 'déclarations par simulation, agents et hybride tracées', 'La pile à agents compte 19,9 déclarations par simulation, contre 7,3 pour la pile hybride',
          [(mean(rev('agents-tr', m='declared').values()), '=', 19.9, 1), (mean(rev('hybrid-tr', m='declared').values()), '=', 7.3, 1)], source=LETTER_1)
    rq, re_ = paired(rev('agents-tr', m='rreq_all'), rev('hybrid-tr', m='rreq_all')), paired(rev('agents-tr', m='rerr'), rev('hybrid-tr', m='rerr'))
    claim('P10', 'RREQ et RERR, agents contre hybride tracées, et p', 'Elle envoie 2 195 demandes de route (RREQ) contre 1 034, et 174 messages d\'erreur de route (RERR) contre 61 (p < 0,001',
          [(mean(rev('agents-tr', m='rreq_all').values()), '=', 2195, 0), (mean(rev('hybrid-tr', m='rreq_all').values()), '=', 1034, 0),
           (mean(rev('agents-tr', m='rerr').values()), '=', 174, 0), (mean(rev('hybrid-tr', m='rerr').values()), '=', 61, 0),
           pv(max(rq['p'], re_['p']), '< 0,001')], source=LETTER_1)
    claim('P10', 'RREQ par simulation, agents moins hybride tracées, test unique',
          'La pile à agents envoie davantage de RREQ (+1 161 [1 046 ; 1 276], p < 0,001',
          pair_checks(rq, 1161, 1046, 1276, 0) + [pv(rq['p'], '< 0,001')])
    claim('P10', 'RERR par simulation, agents moins hybride tracées, test unique',
          'et de messages d\'erreur de route (RERR, +113 [95 ; 132], p < 0,001, test unique) que la pile hybride',
          pair_checks(re_, 113, 95, 132, 0) + [pv(re_['p'], '< 0,001')])

    # P11, decay at GOP 9-3
    ra, rh = paired(rev('agents-edec'), rev('agents')), paired(rev('hybrid-edec'), rev('hybrid'))
    h2 = holm([ra['p'], rh['p']])
    claim('P11', 'pile hybride sous décroissance moins pile hybride, Holm sur deux piles', '−0,34 dB [−0,84 ; 0,17], p = 0,19',
          pair_checks(rh, -0.34, -0.84, 0.17) + [pv(h2[1], '= 0,19')])
    claim('P11', 'pile à agents sous décroissance : déclarations par simulation ; moins pile à agents, Holm sur deux piles',
          'ramène la pile à agents à 9,3 déclarations par simulation et relève son PSNR (+1,55 dB [1,04 ; 2,05], p < 0,001',
          pair_checks(ra, 1.55, 1.04, 2.05) + [pv(h2[0], '< 0,001'), (mean(rev('agents-edec', m='declared').values()), '=', 9.3, 1)])
    text = '+1,88 dB [1,13 ; 2,64], p < 0,001'
    claim('P11', 'effet de la décroissance, pile à agents moins pile hybride, test unique',
          'L\'effet de l\'exploration décroissante diffère donc entre ces deux piles (' + text, gap_checks(controls.decay_difference(), text))

    # P12
    x, y, z = paired(rev('agents-edec'), rev('rules')), paired(rev('agents-edec'), rev('hybrid-edec')), paired(rev('hybrid'), rev('agents-edec'))
    h3 = holm([x['p'], y['p'], z['p']])
    claim('P12', 'agents sous décroissance moins hybride sous décroissance, Holm sur trois', '−0,19 dB [−0,67 ; 0,29], p = 0,43', pair_checks(y, -0.19, -0.67, 0.29) + [pv(h3[1], '= 0,43')])
    claim('P12', 'hybride moins agents sous décroissance, Holm sur trois ; PSNR de la pile hybride', 'Elle reste en revanche 0,53 dB sous la pile hybride à taux d\'exploration constant, à 29,31 dB (p = 0,036',
          [(z['d'], '=', 0.53, 2), pv(h3[2], '= 0,036'), (mean(rev('hybrid').values()), '=', 29.31, 2)], source=LETTER_2)
    claim('P12', 'agents sous décroissance moins règles, Holm sur trois',
          'Avec cette décroissance, la pile à agents dépasse aussi la pile à règles (+1,49 dB [0,89 ; 2,10], p < 0,001',
          pair_checks(x, 1.49, 0.89, 2.10) + [pv(h3[0], '< 0,001')])
    claim('P12', 'hybride moins agents sous décroissance, Holm sur trois', '+0,53 dB [0,09 ; 0,96], p = 0,036',
          pair_checks(z, 0.53, 0.09, 0.96) + [pv(h3[2], '= 0,036')])
    if BRK is not None:
        e = lambda a, rng: {k: v / 6 for k, v in brk(a, ['img%d' % i for i in rng]).items()}
        r1 = paired(e('hybrid', range(1, 7)), e('agents-edec', range(1, 7)))
        # the decay ends when image 7 is captured, 60 + 6 x 9 s
        claim('P12', 'images 1 à 6, hybride moins agents sous décroissance, test unique ; instant où l\'exploration atteint 0 (s)',
              'Cet écart se situe sur les images 1 à 6, capturées avant que \\varepsilon n\'atteigne 0 à 114 s (+1,09 dB [0,44 ; 1,74], p = 0,001',
              pair_checks(r1, 1.09, 0.44, 1.74) + [pv(r1['p'], '= 0,001'), (60 + 6 * 9, '=', 114, 0), (decay_ends() == {114}, '=', True, 0)])
        r7 = paired(e('hybrid', range(7, 13)), e('agents-edec', range(7, 13)))
        claim('P12', 'images 7 à 12, hybride moins agents sous décroissance, test unique',
              'Sur les images 7 à 12, aucune différence statistiquement significative n\'a été détectée entre les deux piles '
              '(−0,03 dB [−0,58 ; 0,51], p = 0,90', pair_checks(r7, -0.03, -0.58, 0.51) + [pv(r7['p'], '= 0,90')])
    r = paired(rev('agents-frozen'), rev('hybrid-frozen'))
    claim('P12', 'pile à agents figée moins pile hybride figée, GOP 9-3, test unique', '+0,15 dB [−0,42 ; 0,71], p = 0,60',
          pair_checks(r, 0.15, -0.42, 0.71) + [pv(r['p'], '= 0,60')])

    # P13 to P15, P35, the agents' traces
    if TRACE is None:
        claim('P13', 'traces des agents', '', [(None, '=', 0, 0)])
    else:
        nodes = [trace('hybrid', a, 999, 'nodes') for a in ('path', 'congestion', 'access')]
        med = [trace('hybrid', a, 999, 'median') for a in ('path', 'congestion', 'access')]
        claim('P13', 'nœuds qui décident, chemin, congestion, accès, min. et max.', 'de la congestion et de l\'accès au canal décident sur 69 à 70 nœuds', [(min(nodes), '=', 69, 0), (max(nodes), '=', 70, 0)], source=LETTER_1)
        claim('P13', 'médiane des décisions par nœud, min. et max.', 'avec une médiane de 529 à 541 décisions par nœud', [(min(med), '=', 529, 0), (max(med), '=', 541, 0)], source=LETTER_1)
        claim('P13', 'avant la détection, intervalle de 40 à 60 s : couples hors du choix initial, chemin, congestion et accès (%)',
              'Entre 40 et 60 s, avant cet instant, 0,1 % des couples des agents du chemin, de la congestion et de l\'accès au canal ont quitté ce '
              'choix',
              [(trace('hybrid', a, 40, 'changed'), '=', 0.1, 1) for a in ('path', 'congestion', 'access')])
        claim('P13', 'chemin hors du choix initial, intervalles de 120 à 140 s puis de 140 à 160 s (%)',
              'La part de l\'agent du chemin augmente encore de 17,6 % entre 120 et 140 s à 19,4 % entre 140 et 160 s',
              [(trace('hybrid', 'path', 120, 'changed'), '=', 17.6, 1), (trace('hybrid', 'path', 140, 'changed'), '=', 19.4, 1)])
        claim('P14', 'découverte : le seul nœud qui décide', 'La figure omet l\'agent de découverte, qui ne décide que sur la caméra',
              [(trace('hybrid', 'discovery', 999, 'nodes') == 1, '=', True, 0)])
        claim('P14', 'accès au canal : part de ses décisions aux paramètres de la norme (%)',
              'l\'agent garde pourtant les paramètres de la norme dans 85,5 % de ses décisions',
              [(100 * trace('hybrid', 'access', 999, 'a%d' % round2.STANDARD_ACTION) / trace('hybrid', 'access', 999, 'decisions'), '=', 85.5, 1)])
        # an action explored with probability 0.1 falls on each of the four counts alike
        claim('P14', 'détection de rupture : part d\'un seul échec (%) ; décisions ; part que l\'exploration donne à chaque nombre (%)',
              'L\'agent choisit trois échecs dans 60,7 % de ses 550 décisions et cinq dans 34,2 %. Il choisit un seul échec dans 2,4 % '
              'd\'entre elles, contre les 2,5 % que l\'exploration (\\varepsilon = 0,1 sur quatre nombres d\'échecs) attribue à chacun d\'eux',
              [(100 * trace('agents', 'break', 999, 'a%d' % a) / trace('agents', 'break', 999, 'decisions'), '=', v, 1)
               for a, v in ((2, 60.7), (3, 34.2), (0, 2.4))] + [
               (trace('agents', 'break', 999, 'decisions'), '=', 550, 0), (100 * 0.1 / len(controls.COUNTS), '=', 2.5, 1),
               (len(controls.COUNTS) == 4, '=', True, 0)])
        br = [trace('agents', 'break', t, 'changed') for t in (60, 80, 100, 120, 140)]
        claim('P15', 'détection de rupture hors du choix initial, 60 à 160 s, min. et max. (%)', 'reste entre 8,4 et 10,9 % de 60 à 160 s', [(min(br), '=', 8.4, 1), (max(br), '=', 10.9, 1)])
        claim('P35', 'médianes : rejet anticipé, détection de rupture, découverte', 'Le rejet anticipé décide 32 fois par nœud en médiane … La détection de rupture décide 2 fois par nœud en médiane … et la découverte 11 fois',
              [(trace('hybrid', 'discard', 999, 'median'), '=', 32, 0), (trace('agents', 'break', 999, 'median'), '=', 2, 0),
               (trace('hybrid', 'discovery', 999, 'median'), '=', 11, 0)], source=LETTER_1)

    # P16, P17, ablations
    alone, inside = ablation.effects('psnr')
    e = ablation.effects('declared')[0]['A']
    claim('P16', 'déclarations, règles avec l\'agent d\'accès moins règles, GOP 9-3 : les deux moyennes ; écart, test unique',
          'il le ramène de 22,0 à 7,4 par simulation (−14,6 [−16,0 ; −13,2], p < 0,001',
          [(mean(rev('rules', m='declared').values()), '=', 22.0, 1), (mean(rev('rules-onlyA', m='declared').values()), '=', 7.4, 1),
           (e.mean, '=', -14.6, 1), (e.lo, 'b', -16.0, 1), (e.hi, 'b', -13.2, 1), pv(e.p, '< 0,001')])
    r = paired(rev('rules-onlyA', m='m1loss'), rev('rules', m='m1loss'))
    claim('P16', 'perte de M1, règles avec l\'agent d\'accès moins règles (points), test unique',
          'La perte du niveau M1 baisse alors (−5,1 points [−7,7 ; −2,5], p < 0,001',
          pair_checks(r, -5.1, -7.7, -2.5, 1) + [pv(r['p'], '< 0,001')])
    r = paired(rev('hybrid-frozen', m='declared'), rev('rules', m='declared'))
    e = ablation.effects('declared')[1]['A']
    claim('P16', 'déclarations, pile hybride figée − règles, test unique ; l\'intervalle exclut la baisse que l\'agent d\'accès apporte dans la '
          'pile hybride',
          '+0,35 [−1,26 ; 1,96], p = 0,67 … Cet intervalle exclut une baisse de 14,8 déclarations, celle que l\'agent apporte dans la pile hybride',
          pair_checks(r, 0.35, -1.26, 1.96) + [pv(r['p'], '= 0,67'), (-e.mean, '=', 14.8, 1), (r['lo'] > e.mean, '=', True, 0)])
    found = {name: sorted(x for x, e in es.items() if e.holm < 0.05) for name, es in (('alone', alone), ('inside', inside))}
    claim('P17', 'GOP 9-3 : les agents à l\'effet significatif, seuls (Holm sur sept) et dans la pile hybride (Holm sur six, rupture : '
          'E0) : accès au-dessus, rupture au-dessous',
          'deux agents seulement ont un effet statistiquement significatif, en sens contraires',
          [(found == {'alone': ['A', 'B'], 'inside': ['A', 'B']}, '=', True, 0),
           (all(es['A'].mean > 0 > es['B'].mean for es in (alone, inside)), '=', True, 0)])
    # the channel-access agent alone on the rule stack is the access-only
    # stack, whose gap at GOP 9-3 is S09 (claims/round2.py)
    text = 'l\'agent de détection de rupture l\'abaisse (−1,42 dB [−2,08 ; −0,75], p < 0,001'
    claim('P17', 'règles avec le seul agent de rupture moins règles, Holm sur sept ; l\'agent d\'accès seul au-dessus, Holm < 0,05',
          'Seul sur la pile à règles, l\'agent de l\'accès au canal relève le PSNR, et ' + text,
          gap_checks(alone['B'], text) + [(alone['A'].mean > 0 and alone['A'].holm < 0.05, '=', True, 0)])
    five = [alone[x] for x in 'PCDET'] + [inside[x] for x in 'PCDET']
    text = '−0,10 à +0,52 dB, intervalles de −0,63 à +0,97 dB, p ≥ 0,13'
    claim('P17', 'cinq autres agents, seuls et dans la pile hybride : écarts min., max. (dB) ; Holm min. ; bornes min. et max.',
          'Pour les cinq autres agents, aucune différence statistiquement significative n\'a été détectée, ni seuls ni dans la pile hybride ('
          + text,
          range_checks(five, text) + [(all(e.holm >= 0.05 for e in five), '=', True, 0)])
    claim('P17', 'cinq autres agents : seul le rejet anticipé dans la pile hybride a l\'intervalle sans zéro, Holm ≥ 0,05 ; son intervalle',
          'L\'intervalle du rejet anticipé dans la pile hybride, non corrigé, exclut toutefois zéro ([0,06 ; 0,97]',
          [([x for x in 'PCDET' if round2.flagged(alone[x])] + [x for x in 'PCDET' if round2.flagged(inside[x])] == ['E'], '=', True, 0)]
          + interval_checks(inside['E'], '[0,06 ; 0,97]'))
    same = all(rev('rules-onlyT')[k] == rev('rules')[k] and rev('rules-onlyT', m='loss')[k] == rev('rules', m='loss')[k] for k in rev('rules'))
    claim('P17', 'agent de puissance seul : 60 simulations identiques aux règles, PSNR et pertes', 'Avec l\'agent de puissance, les 60 simulations restent identiques à celles qui emploient sa règle',
          [(same, '=', True, 0), (len(rev('rules')), '=', 60, 0)])
    text = 'sa règle. La pile hybride dépasse la pile à règles (+2,02 dB [1,50 ; 2,53], p < 0,001'
    claim('P17', 'pile hybride moins règles, GOP 9-3, Holm sur trois GOP (E0)', text, gap_checks(hr['9M3D'], text))
    text = 'Sans l\'agent de l\'accès au canal, son PSNR baisse (−2,13 dB [−2,62 ; −1,64], p < 0,001'
    claim('P17', 'pile hybride sans l\'agent d\'accès moins pile hybride, Holm sur six', text, gap_checks(inside['A'], text, sign=-1))
    text = '−0,11 dB [−0,83 ; 0,60], p = 0,75'
    claim('P17', 'pile hybride sans l\'agent d\'accès moins règles, test unique', text,
          gap_checks(stats.paired(rev('hybrid-noA'), rev('rules')), text))
    text = '+2,05 dB [1,51 ; 2,59], p < 0,001'
    claim('P17', 'pile à accès seul moins pile à agents, GOP 9-3, Holm sur deux', 'Au GOP 9-3, elle dépasse aussi la pile à agents (' + text,
          gap_checks(ablation.against_access(('hybrid', 'agents'))['agents'], text, sign=-1))
    decaying = ablation.against_access(('hybrid-edec', 'agents-edec'))
    claim('P17', 'sous exploration décroissante, GOP 9-3, Holm sur deux : pile hybride et pile à agents moins pile à accès seul ; aucun '
          'Holm < 0,05, l\'intervalle du second sans zéro',
          'Sous exploration décroissante des piles hybride et à agents, la pile à accès seul garde \\varepsilon = 0,1. Aucune différence '
          'statistiquement significative avec elle n\'a alors été détectée, ni pour la pile hybride (−0,31 dB [−0,74 ; 0,11], p = 0,15) ni pour la pile à agents (−0,51 dB [−0,97 ; −0,04], p = 0,069). Le second intervalle, non '
          'corrigé, exclut toutefois zéro',
          gap_checks(decaying['hybrid-edec'], '−0,31 dB [−0,74 ; 0,11], p = 0,15')
          + gap_checks(decaying['agents-edec'], '−0,51 dB [−0,97 ; −0,04], p = 0,069')
          + [([a for a, e in decaying.items() if round2.flagged(e)] == ['agents-edec'], '=', True, 0)])
    ADDITIVITY = '−0,36 dB [−2,03 ; 1,30], p = 0,66'
    inter = list(ablation.interactions('psnr').values())
    claim('P17', 'interaction : effet ensemble moins somme des six effets seuls, test unique ; par agent, aucun Holm < 0,05',
          ADDITIVITY + ' … ni entre l\'effet de chaque agent dans la pile hybride et son effet seul',
          gap_checks(ablation.additivity('psnr'), ADDITIVITY) + [(all(e.holm >= 0.05 for e in inter), '=', True, 0)])
    claim('P17', 'somme des effets des six agents seuls, leur effet ensemble (dB)',
          'La somme des effets des six agents de la pile hybride, mesurés seuls, est de 2,38 dB, et leur effet ensemble de 2,02 dB',
          [(mean(ablation.sum_of(ablation.HYBRID, 'psnr', 'alone').values()), '=', 2.38, 2), (hr['9M3D'].mean, '=', 2.02, 2),
           (len(ablation.HYBRID) == 6, '=', True, 0)])
    text = '−0,27 à +0,33 dB (intervalles de −0,91 à +1,06 dB, p = 1,00'
    claim('P17', 'effet dans la pile hybride moins effet seul, six agents, Holm sur six : écarts min., max. ; Holm de chacun ; bornes min. '
          'et max.', 'Par agent, les écarts vont de %s pour chacun' % text, range_checks(inter, text) + [(len(inter) == 6, '=', True, 0)])
    text = '−2,07 dB [−2,61 ; −1,54], p < 0,001'
    claim('P17', 'agent de rupture dans la pile hybride, agents moins hybride, Holm sur trois GOP (E0)',
          'Il abaisse aussi celui de la pile hybride, où il remplace la règle des trois échecs (' + text, gap_checks(inside['B'], text))
    on_decl = ablation.effects('declared')
    claim('P17', 'déclarations, agents de l\'accès et de rupture, seuls et dans la pile hybride : effets de sens contraires',
          'Ces deux agents agissent aussi en sens contraires sur le nombre de voisins déclarés morts',
          [(all(es['A'].hi < 0 < es['B'].lo for es in on_decl), '=', True, 0)])

    # P18, level M1
    m1 = comparative.cells(COMP, 'm1loss')
    hm = comparative.paired_gops(m1, 'hybrid', 'rules')
    text = '−5,2 à −3,2 points, intervalles de −9,5 à −0,5 point, p ≤ 0,032'
    claim('P18', 'perte de M1, hybride moins règles par GOP, Holm sur trois GOP : min., max. (points) ; Holm max. ; bornes min. et max.',
          'la pile hybride en perd aussi moins que la pile à règles à chaque GOP (' + text, range_checks(list(hm.values()), text))
    r, ra_ = comparative.per_seed(m1, 'hybrid', 'rules')[0], comparative.per_seed(m1, 'hybrid', 'agents')[0]
    rl = paired(comp_pooled('hybrid', 'loss'), comp_pooled('rules', 'loss'))
    claim('P18', 'perte de M1, hybride moins règles et moins agents, perte globale, hybride moins règles, 60 graines (points) ; p max.',
          'sa perte du niveau M1 est inférieure à celle des piles à règles (−4,4 points [−6,7 ; −2,2]) et à agents '
          '(−4,9 points [−6,8 ; −3,0]) … Sa perte globale est inférieure à celle de la pile à règles (−8,9 points [−10,5 ; −7,3], p < 0,001 '
          'pour les trois écarts',
          gap_checks(r, '−4,4 points [−6,7 ; −2,2]') + gap_checks(ra_, '−4,9 points [−6,8 ; −3,0]')
          + pair_checks(rl, 8.9, 7.3, 10.5, 1, sign=-1) + [pv(max(r.p, ra_.p, rl['p']), '< 0,001')])

    # P19, the gallery frame
    if FRAMES is None:
        claim('P19', 'frame 8 de la galerie', '', [(None, '=', 0, 0)])
    else:
        f8 = {r['arm']: r for r in FRAMES if r['period'] == 'p9' and r['fire'] == 'F1' and r['realisation'] == 'r01' and r['image'] == '8'}
        g = lambda arm, c: float(f8[arm][c]) if arm in f8 else None
        # the M1 loss and the PSNR the figure illustrates, and why AOMDV's
        # image is an earlier one: none of the packets of image 8 arrived
        claim('P19', 'frame 8, texte : perte (%) et PSNR (dB) des piles à règles et hybride, aucune perte de M1 ; perte de M1 (%) et PSNR '
              'de la pile à agents ; AOMDV, tous les paquets perdus',
              'Avec AOMDV, aucun paquet de cette image n\'arrive au puits … Les piles à règles et hybride en perdent 40 et 36 %, mais aucun du '
              'niveau M1, et l\'image atteint 33,2 et 32,5 dB. La pile à agents perd 19 % de ce niveau, et l\'image atteint 22,8 dB',
              [(g('rules', 'loss'), '=', 40, 0), (g('hybrid', 'loss'), '=', 36, 0),
               (g('rules', 'psnr'), '=', 33.2, 1), (g('hybrid', 'psnr'), '=', 32.5, 1),
               (g('rules', 'l1loss') == 0 and g('hybrid', 'l1loss') == 0, '=', True, 0), (g('agents', 'l1loss'), '=', 19, 0),
               (g('agents', 'psnr'), '=', 22.8, 1), (g('pq', 'loss') == 100, '=', True, 0)])

    # P21, P23
    dl = quality.gops('hybrid', 'rules', 'delay_mean')
    text = '−43,5 et −65,6 ms, intervalles de −74,7 à −31,8 ms, p < 0,001'
    claim('P21', 'délai moyen, hybride moins règles, Holm sur trois GOP : GOP 6-6 et 9-3 (ms), Holm max., bornes min. et max.',
          'Son écart avec la pile à règles est significatif aux GOP 6-6 et 9-3 (' + text,
          range_checks([dl['6M6D'], dl['9M3D']], text, ordered=True))
    text = '−7,3 ms [−17,8 ; 3,2], p = 0,17'
    claim('P21', 'délai moyen, hybride moins règles, GOP 3-9, Holm sur trois GOP', text, gap_checks(dl['3M9D'], text))
    late = quality.gops('hybrid', 'rules', 'late')
    text = '−0,074 à +0,022 point, intervalles de −0,147 à +0,070 point, p ≥ 0,13'
    claim('P23', 'échéances manquées, hybride moins règles, Holm sur trois GOP : min., max. (points) ; Holm min. ; bornes min. et max.', text,
          range_checks(list(late.values()), text))
    text = 'Au GOP 6-6, l\'intervalle non corrigé exclut toutefois zéro ([−0,147 ; −0,001]'
    claim('P23', 'échéances manquées, hybride moins règles : seul le GOP 6-6 a l\'intervalle sans zéro, Holm ≥ 0,05 ; son intervalle', text,
          [(sorted(s for s, e in late.items() if round2.flagged(e)) == ['6M6D'], '=', True, 0)]
          + interval_checks(late['6M6D'], '[−0,147 ; −0,001]'))
    cl = {st: cell_means(st, 'loss') for st in ('aomdv', 'rules', 'agents', 'hybrid')}
    claim('P23', 'perte par cellule, min. et max. (%) : AOMDV, piles à règles, à agents et hybride',
          'AOMDV perd 74 à 79 % des paquets vidéo, et la pile à règles 54 à 63 %. La pile à agents en perd 49 à 61 %, et la pile hybride 46 '
          'à 56 %',
          [(f(cl[st]), '=', v, 0) for st, vs in (('aomdv', (74, 79)), ('rules', (54, 63)), ('agents', (49, 61)), ('hybrid', (46, 56)))
           for f, v in zip((min, max), vs)])

    # P25, the ranking per cell over the six stacks of the PSNR table (discussion, 4.3)
    arms6 = {'aomdv': lambda s: 'pq', 'tuned': lambda s: 'pq-tuned', 'rules': lambda s: 'rules', 'access': round2.access_only,
             'agents': lambda s: 'agents', 'hybrid': lambda s: 'hybrid'}
    ranks = [{st: mean(x for k, x in quality.values(a(s), 'psnr', s).items() if k[0] == f) for st, a in arms6.items()}
             for s in SPLITS for f in FIRES]
    tops = [max(m, key=m.get) for m in ranks]
    claim('P25', 'neuf cellules, six piles du tableau du PSNR : AOMDV la plus basse dans chacune ; la plus haute, pile à accès seul (cinq) '
          'ou hybride (quatre)',
          'Dans les neuf cellules, en revanche, AOMDV a le PSNR moyen le plus faible, et la pile à accès seul (cinq cellules) ou hybride '
          '(quatre) le plus élevé',
          [(len(ranks) == 9 and all(min(m, key=m.get) == 'aomdv' for m in ranks), '=', True, 0),
           ((tops.count('access'), tops.count('hybrid')) == (5, 4), '=', True, 0)])

    # P26, P27, volume (packet counts of the methods: 5 738, 5 544 and 5 352)
    sh = coding.volume_shares()
    full = {s: paired(rev(s, '9M3D'), rev(s, '3M9D')) for s in ('rules', 'hybrid')}
    claim('P26', 'GOP 9-3 moins GOP 3-9 à 9 s, règles et hybride, tests uniques',
          'Du GOP 3-9 au GOP 9-3, la pile à règles gagne 5,72 dB [5,05 ; 6,40] et la pile hybride 6,66 dB [6,16 ; 7,17] (p < 0,001 pour les '
          'deux',
          pair_checks(full['rules'], 5.72, 5.05, 6.40) + pair_checks(full['hybrid'], 6.66, 6.16, 7.17)
          + [pv(max(full['rules']['p'], full['hybrid']['p']), '< 0,001')])
    eqd = {s: paired(rev(s, '9M3D'), rev(s, '3M9D', 'p9r65')) for s in ('rules', 'hybrid')}
    claim('P26', 'GOP 9-3 moins GOP 3-9 à débit égal, règles et hybride, tests uniques',
          'le GOP 9-3 dépasse encore le GOP 3-9. L\'écart est de 5,12 dB [4,39 ; 5,85] avec la pile à règles et de 5,63 dB [5,11 ; 6,14] avec la '
          'pile hybride (p < 0,001 pour les deux',
          pair_checks(eqd['rules'], 5.12, 4.39, 5.85) + pair_checks(eqd['hybrid'], 5.63, 5.11, 6.14)
          + [pv(max(eqd['rules']['p'], eqd['hybrid']['p']), '< 0,001')])
    text = '+0,61 dB [−0,11 ; 1,32], p = 0,19'
    claim('P26', 'part du volume, règles au GOP 3-9 : % de l\'effet ; dB, Holm sur quatre',
          'Avec la pile à règles, cet écart varie de 11 % de sa valeur à T = 9 s, mais aucune différence statistiquement significative '
          'n\'a été détectée (' + text,
          gap_checks(sh['rules', '3M9D'], text) + [(100 * sh['rules', '3M9D'].mean / full['rules']['d'], '=', 11, 0)])
    text = 'Avec la pile hybride, il varie de 1,04 dB [0,39 ; 1,69], soit 16 % (p = 0,009'
    claim('P26', 'part du volume, hybride au GOP 3-9 : dB, % de l\'effet, Holm sur quatre', text,
          gap_checks(sh['hybrid', '3M9D'], text) + [(100 * sh['hybrid', '3M9D'].mean / full['hybrid']['d'], '=', 16, 0)])
    r1, r2 = paired(rev('rules', '9M3D'), rev('rules', '6M6D', 'p9r32')), paired(rev('hybrid', '9M3D'), rev('hybrid', '6M6D', 'p9r32'))
    claim('P26', 'GOP 9-3 moins GOP 6-6 à débit égal, règles et hybride, tests uniques',
          'À débit égal, le GOP 6-6 reste sous le GOP 9-3, de 1,82 dB [1,15 ; 2,49] (règles) et 2,00 dB [1,47 ; 2,54] (hybride, '
          'p < 0,001 pour les deux',
          pair_checks(r1, 1.82, 1.15, 2.49) + pair_checks(r2, 2.00, 1.47, 2.54) + [pv(max(r1['p'], r2['p']), '< 0,001')])
    for s, text in (('rules', '+0,09 dB [−0,55 ; 0,74], p = 0,77'), ('hybrid', '+0,46 dB [0,02 ; 0,90], p = 0,12')):
        claim('P26', 'part du volume, %s au GOP 6-6, Holm sur quatre' % ('règles' if s == 'rules' else 'hybride'), text,
              gap_checks(sh[s, '6M6D'], text))
    claim('P26', 'part du volume au GOP 6-6 : seul l\'intervalle de la pile hybride exclut zéro, Holm ≥ 0,05',
          'Le second intervalle, non corrigé, exclut toutefois zéro',
          [([s for s in ('rules', 'hybrid') if round2.flagged(sh[s, '6M6D'])] == ['hybrid'], '=', True, 0)])
    eq = coding.equal_rate_gaps()
    claim('P27', 'hybride moins règles à débit égal, GOP 6-6 et 3-9, Holm sur deux',
          'À débit égal, la pile hybride dépasse encore la pile à règles, de 1,84 dB [1,22 ; 2,45] au GOP 6-6 et de 1,51 dB [0,80 ; 2,22] au '
          'GOP 3-9 (p < 0,001 pour les deux',
          gap_checks(eq['6M6D'], '1,84 dB [1,22 ; 2,45], p < 0,001') + gap_checks(eq['3M9D'], '1,51 dB [0,80 ; 2,22], p < 0,001'))

    # P37, the quality coefficient 0.1, second series of E4, its sets
    # simulated for 168 s like their counterparts: the two families fixed
    # before the results.
    test1, test2 = coding.coefficient_tests()
    gains = ('1,45 dB [0,92 ; 1,98]', '1,27 dB [0,70 ; 1,85]', '1,25 dB [0,65 ; 1,85]', '0,96 dB [0,55 ; 1,38]')
    claim('P37', 'PSNR au coefficient 0,1 moins 0,01 : AOMDV, règles, agents, hybride (dB) ; Holm sur quatre',
          'Le PSNR gagne %s avec AOMDV et %s avec la pile à règles. Il gagne %s avec la pile à agents et %s avec la pile hybride (p < 0,001 '
          'pour les quatre' % gains,
          [c for (s, label), x in zip(coding.STACKS, gains) for c in gap_checks(test2['%s 0.1 - 0.01' % label], x + ', p < 0,001')])
    text = 'À ce coefficient, la pile hybride dépasse la pile à règles de 1,71 dB [1,19 ; 2,22] (p < 0,001'
    claim('P37', 'coefficient 0,1 : hybride moins règles (dB), Holm sur deux', text, gap_checks(test1['hybrid - rules'], text))
    text = '−0,08 dB [−0,67 ; 0,51], p = 0,79'
    claim('P37', 'coefficient 0,1 : agents moins règles (dB), Holm sur deux', text, gap_checks(test1['agents - rules'], text))
    # the camera's mean rate at GOP 9-3, the same for every stack: the
    # equal-rate series of the methods
    claim('P37', 'débit moyen de la caméra au GOP 9-3 (paquets/s) : méthode', 'pour égaler le débit moyen du GOP 9-3, 49,6 paquets par seconde',
          [(coding.rate(coding.PACKETS['9M3D'], 'p9'), '=', 49.6, 1)])

    # P28 to P30, load: hybrid minus rules, one Holm family over the five
    # periods for each metric
    hy = robustness.period_family('hybrid', 'rules', 'psnr')
    text = '2,02 et 2,42 dB (intervalles de 1,50 à 3,02 dB, p < 0,001'
    claim('P28', 'hybride moins règles à 9 et 12 s, Holm sur cinq périodes : écarts (dB) ; Holm max. ; bornes min. et max. ; les seules '
          'périodes au-dessus, 7 s seule au-dessous',
          'L\'avance de la pile hybride sur la pile à règles n\'y est significative qu\'à 9 et 12 s, de ' + text,
          range_checks([hy['p9'], hy['p12']], text, ordered=True)
          + [([p for p in PERIODS if hy[p].mean > 0 and hy[p].holm < 0.05] == ['p9', 'p12'], '=', True, 0),
             ([p for p in PERIODS if hy[p].mean < 0 and hy[p].holm < 0.05] == ['p7'], '=', True, 0)])
    for p, name, text in (('p7', '7 s', 'la pile hybride passe sous la pile à règles (−0,92 dB [−1,27 ; −0,57], p < 0,001'),
                          ('p18', '18 s', '+0,89 dB [−0,18 ; 1,97] (p = 0,20'), ('p30', '30 s', '−0,53 dB [−1,44 ; 0,38] (p = 0,25')):
        claim('P28', 'hybride moins règles à %s, Holm sur cinq périodes' % name, text, gap_checks(hy[p], text))
    hl = {m: robustness.period_family('hybrid', 'rules', m) for m in ('loss', 'm1loss')}
    claim('P29', 'perte globale, hybride moins règles à 7 et 12 s (points), Holm sur cinq périodes',
          'Sa perte globale y est pourtant plus faible (−5,4 points [−6,9 ; −4,0], p < 0,001), comme à 12 s (−10,6 points [−12,8 ; −8,4], '
          'p < 0,001',
          gap_checks(hl['loss']['p7'], '−5,4 points [−6,9 ; −4,0], p < 0,001') + gap_checks(hl['loss']['p12'], '−10,6 points [−12,8 ; −8,4], p < 0,001'))
    claim('P29', 'perte de M1, hybride moins règles à 7 et 12 s (points), Holm sur cinq périodes',
          'n\'a été détectée ni à 7 ni à 12 s (+1,3 point [−0,7 ; 3,4] et −1,1 point [−2,9 ; 0,8], p = 0,79 pour les deux',
          gap_checks(hl['m1loss']['p7'], '+1,3 point [−0,7 ; 3,4], p = 0,79') + gap_checks(hl['m1loss']['p12'], '−1,1 point [−2,9 ; 0,8], p = 0,79'))
    if FRAMES is None:
        claim('P29', 'mécanisme à 7 s', '', [(None, '=', 0, 0)])
    else:
        le5 = lambda arm: per_sim(arm, 'p7', lambda v: sum(1 for i in v if int(i['image']) in MAIN8 and float(i['l1loss']) <= 5))
        a, b = le5('hybrid'), le5('rules')
        r = paired(a, b)
        claim('P29', 'frames principales 2 à 12 à au plus 5 % de perte de M1, règles et hybride ; écart',
              'celles dont le niveau M1 perd au plus 5 % de ses paquets passent de 2,77 (règles) à 0,47 (hybride) par simulation. L\'écart est de '
              '−2,30 frames [−2,68 ; −1,92] (p < 0,001',
              [(mean(b.values()), '=', 2.77, 2), (mean(a.values()), '=', 0.47, 2), (len(MAIN8) == 8, '=', True, 0)]
              + pair_checks(r, -2.30, -2.68, -1.92) + [pv(r['p'], '< 0,001')])
    ag = robustness.period_family('agents', 'rules', 'psnr')
    text = '(−1,76 dB [−2,11 ; −1,41], p < 0,001'
    claim('P29', 'pile à agents moins règles à 7 s, Holm sur cinq périodes : la seule période significative',
          'une différence statistiquement significative n\'a été détectée qu\'à 7 s ' + text,
          gap_checks(ag['p7'], text) + [([p for p in PERIODS if ag[p].holm < 0.05] == ['p7'], '=', True, 0)])
    text = '−0,53 à +0,41 dB, intervalles de −1,51 à +1,42 dB, p ≥ 0,66'
    claim('P29', 'pile à agents moins règles à 9, 12, 18 et 30 s, Holm sur cinq périodes : écart min. et max. (dB) ; Holm min. ; bornes min. '
          'et max.', 'Aux quatre autres périodes, aucune différence statistiquement significative n\'a été détectée (' + text,
          range_checks([ag[p] for p in PERIODS if p != 'p7'], text))
    # the oracle of studies 10 (the stacks of the first round) and 11 (the
    # access-only stack, tranche T7), each series by itself
    access = {s: access_robustness.lost_without_path((s,)) for s in ('load', 'fire')}
    load = [r for r in ORACLE or () if r['period'] in ('p7', 'p12', 'p18', 'p30')]
    sens = [r for r in ORACLE or () if r['period'] == 'p9' and any(t in r['arm'] for t in ('-az', '-pf', '-fd1'))]
    for block, series, name, rows, count in (('P29', 'load', 'des quatre nouvelles périodes', load, 1200),
                                             ('P32', 'fire', 'des sept variantes', sens, 1260)):
        label = 'oracle %s, pile à accès seul comprise : simulations, aucun paquet perdu sans chemin' % name
        if ORACLE is None or access[series] is None:
            claim(block, label, ORACLE_TEXT, [(None, '=', 0, 0)])
            continue
        n, _, cut = access[series]
        claim(block, label, ORACLE_TEXT, [(len(rows) + n, '=', count, 0),
                                          (sum(int(r['unreachable']) for r in rows) + cut == 0, '=', True, 0)])
    claim('P30', 'perte des règles à 9 et 12 s (%)', 'Sous ces deux charges, la pile à règles perd 56,2 et 35,6 % des paquets',
          [(mean(rev('rules', period=p, m='loss').values()), '=', v, 1) for p, v in (('p9', 56.2), ('p12', 35.6))], source=LETTER_1)
    claim('P30', 'perte des règles à 18 et 30 s (%)', 'À 18 et 30 s, où la pile à règles ne perd plus que 1,5 et 0,5 % des paquets',
          [(mean(rev('rules', period=p, m='loss').values()), '=', v, 1) for p, v in (('p18', 1.5), ('p30', 0.5))])

    # P32, sensitivity
    sl = [mean(rev('rules-' + v, m='loss').values()) for v in ('az015', 'az05', 'az165', 'pf0', 'pf025', 'pf075', 'fd1')]
    claim('P32', 'perte des règles sur les sept variantes, min. et max. ; référence (%)', 'La pile à règles perd 55,5 à 56,5 % des paquets, contre 56,2 % dans le scénario de référence',
          [(min(sl), '=', 55.5, 1), (max(sl), '=', 56.5, 1), (mean(rev('rules', m='loss').values()), '=', 56.2, 1)])

    # P33, P36, energy (radio powers of radio-params.tcl: 37 and 42 mW)
    if OVER is None:
        claim('P33', 'énergie', '', [(None, '=', 0, 0)])
    else:
        # s3 over the nine cells of the rule, hybrid and agents stacks; s4 with
        # the access-only stack, whose rows are at GOP 9-3 only (three cells)
        s3 = s4 = 0.0
        cells4 = 0
        for g in SPLITS:
            for f in FIRES:
                e = {r['stack']: float(r['e_node']) for r in OVER if r['split'] == g and r['fire'] == f}
                x = [e[s] for s in ('rules', 'agents', 'hybrid')]
                s3 = max(s3, (max(x) - min(x)) / min(x))
                if 'access' in e:
                    x4 = x + [e['access']]
                    s4, cells4 = max(s4, (max(x4) - min(x4)) / min(x4)), cells4 + 1
        claim('P33', 'écart d\'énergie maximal par cellule, piles à règles, hybride et à agents, neuf cellules (%)',
              'L\'énergie de la radio varie d\'au plus 0,09 % entre les piles à règles, hybride et à agents, dans chacune des neuf cellules',
              [(100 * s3, '=', 0.09, 2)])
        claim('P33', 'avec la pile à accès seul : écart maximal par cellule, ses trois cellules du GOP 9-3 seules (%)',
              'En comptant la pile à accès seul, elle varie d\'au plus 0,12 % dans chacune des trois cellules du GOP 9-3, celui du tableau '
              '\\ref{tab:fr-couts}',
              [(100 * s4, '=', 0.12, 2), (cells4 == 3 and all(r['split'] == '9M3D' for r in OVER if r['stack'] == 'access'), '=', True, 0)])
    claim('P36', 'opérations par paquet : 20 comparaisons + 4 × 3 mises à jour + 8 tirages', 'au plus 40 opérations par paquet', [(20 + 4 * 3 + 8, '=', 40, 0)])

    # P43, the memory the agents add to a node (analysis/overhead.memory: the
    # value tables sized from the simulator's headers and the context of the
    # decisions awaiting their outcome), per stack, its number of agents, and
    # its share of the ATmega128L's 4 Kbytes of SRAM (one agent
    # and 338 bytes against six agents and 863 bytes, seven and 927)
    values, mem = overhead.memory()
    n_agents = {s: len(a) for s, a in overhead.AGENTS.items()}
    claim('P43', 'mémoire des agents par nœud (octets), la plus petite et la plus grande ; piles à agents, hybride et à accès seul ; 7, 6 et '
          '1 agents',
          'les agents occupent 338 à 927 octets selon la pile … Les agents occupent 927 octets par nœud dans la pile à agents, 863 dans la '
          'pile hybride et 338 dans la pile à accès seul',
          [(min(m['node'] for m in mem.values()), '=', 338, 0), (max(m['node'] for m in mem.values()), '=', 927, 0),
           (mem['agents']['node'], '=', 927, 0), (mem['hybrid']['node'], '=', 863, 0), (mem['access']['node'], '=', 338, 0),
           (n_agents == {'access': 1, 'hybrid': 6, 'agents': 7}, '=', True, 0)])
    claim('P43', 'mêmes piles : part des 4 Kio de l\'ATmega128L (%) ; valeurs des tables',
          'Ces tailles représenteraient 23, 21 et 8 % des 4 Kio … Elles comprennent les tables des agents, 151, 143 et 81 valeurs de quatre octets',
          [(100.0 * mem[s]['node'] / overhead.SRAM_REF, '=', v, 0) for s, v in (('agents', 23), ('hybrid', 21), ('access', 8))]
          + [(mem[s]['values'], '=', v, 0) for s, v in (('agents', 151), ('hybrid', 143), ('access', 81))]
          + [(overhead.SRAM_REF == 4 * 1024 and overhead.FLOAT == 4, '=', True, 0)])
    # P34, control traffic
    hel = [mean(rev(a, m='hello').values()) for a in ('rules', 'hybrid-tr', 'agents-tr')]
    claim('P34', 'HELLO par simulation, piles inter-couches min. et max. ; AOMDV', '3 212 à 3 214 par simulation, contre 16 153',
          [(min(hel), '=', 3212, 0), (max(hel), '=', 3214, 0), (mean(rev('pq', m='hello').values()), '=', 16153, 0)], source=LETTER_1)

    # P38 to P41
    # P38, the margin of a 40 m link (section 3.4): the shadowing model with
    # sigma 0 (log-distance) and the radio of code/campaign/radio-params.tcl,
    # Friis at 1 m (Pt 0.002 W, 2.4 GHz, unit gains, L = 1), exponent 3.2,
    # against CSThresh_ 7.94e-13 W (-91 dBm); the step down needs 1 + 1.7 dB,
    # the steps those of the simulator (mac-802_15_4EvalVSN.cc).
    # The wavelength takes the simulator's speed of light, 3e8 m/s
    # (ns-2.35 mobile/propagation.h:43, SPEED_OF_LIGHT; mac/wireless-phy.cc:101,
    # lambda_ = SPEED_OF_LIGHT / freq_), as metrics/fire_oracle.py does: 2.700 dB,
    # which reaches the 2.7 dB (with 299 792 458 m/s it would be 2.694 dB)
    lam = 3e8 / 2.4e9
    pr1 = 0.002 * lam ** 2 / (4 * math.pi) ** 2
    marge = 10 * math.log10(pr1 / 7.94e-13) - 10 * 3.2 * math.log10(40)
    steps = [float(x) for x in re.search(r'kRlpStepsDbm\[\] = \{([^}]*)\}', open(overhead.MAC_CC).read())[1].split(',')]
    claim('P38', 'marge d\'un lien de 40 m au-dessus de P_CCA, sans interférence (dB) ; atteint les 2,7 exigés, un décibel et le premier pas '
          '(dBm)',
          'Celui-ci garde le lien à un décibel au moins au-dessus de P_{\\mathrm{CCA}} … '
          'descendre de +3 dBm à son premier pas inférieur, +1,3 dBm, que si le lien est reçu 2,7 dB au moins au-dessus de ce seuil. Sans '
          'interférence, un lien de 40 m est reçu 2,70 dB au-dessus … le fait passer sous ces 2,7 dB',
          [(marge, '=', 2.70, 2), (steps[0], '=', 3, 0), (steps[1], '=', 1.3, 1), (1 + (steps[0] - steps[1]), '=', 2.7, 1),
           (marge >= 1 + (steps[0] - steps[1]), '=', True, 0)])
    if TRACE is not None:
        claim('P38', 'agent de puissance, grille de 40 m : part de ses décisions à +3 dBm (%)',
              'L\'agent reste ainsi à +3 dBm dans plus de 99,99 % de ses décisions sur la grille de 40 m',
              [(100 * trace('hybrid', 'power', 999, 'a0') / trace('hybrid', 'power', 999, 'decisions'), '>', 99.99, 2)])
    # P39, the coded frames against the raw image (section 2.6)
    if CODEC is None:
        claim('P39', 'image brute (octets) ; tailles moyennes M et D au-dessus, trois GOP', P39_TEXT, [(None, '=', 0, 0)])
    else:
        cv = {r['key']: r['value'] for r in CODEC}
        sizes = [float(cv['%s %s mean bytes' % (g, t)]) for g in ('3-9', '6-6', '9-3') for t in 'MD']
        raw = float(cv['raw image'])
        claim('P39', 'image brute (octets) ; tailles moyennes M et D au-dessus, trois GOP', P39_TEXT,
              [(raw, '=', 25344, 0), (min(sizes) > raw, '=', True, 0)])
    # P40, the equal-rate periods (5 352 packets of GOP 9-3 against 5 544 and
    # 5 738) and the delay of the twelfth capture, at 60 + 11 T s (sets.conf,
    # capture period:ipt:detect), against 159 s at 9 s (section 4.4)
    t66, t39 = 9 * 5544 / 5352, 9 * 5738 / 5352
    claim('P40', 'périodes à débit égal, GOP 6-6 et 3-9 (s)', '9,32 et 9,65', [(t66, '=', 9.32, 2), (t39, '=', 9.65, 2)])
    claim('P40', 'dernière capture retardée à 9,32 et 9,65 s, 11 × (T − 9) (s)', 'retardent la dernière capture de 3,5 et 7,2 s',
          [(11 * (9.32 - 9), '=', 3.5, 1), (11 * (9.65 - 9), '=', 7.2, 1)])

    # P42, hybrid - rules in usable images at the bounds of the fair class, 25 and
    # 31 dB, per GOP, Holm over the three GOPs (section 3.6; the quality
    # report prints the same tests)
    u = {m: quality.gops('hybrid', 'rules', m) for m in ('usable25', 'usable31')}
    text = '+1,07 à +2,03 images, intervalles de 0,35 à 2,61 images, p ≤ 0,005'
    claim('P42', 'images ≥ 25 dB, hybride moins règles, trois GOP : min., max. ; Holm max. ; bornes min. et max.', text,
          range_checks(list(u['usable25'].values()), text))
    text = '+0,98 et +1,28 image, intervalles de 0,57 à 1,82 image, p < 0,001'
    claim('P42', 'images ≥ 31 dB, hybride moins règles, GOP 6-6 et 9-3 : écarts ; Holm max. ; bornes min. et max.', text,
          range_checks([u['usable31']['6M6D'], u['usable31']['9M3D']], text, ordered=True))
    text = '+0,27 image [−0,01 ; 0,54], p = 0,055'
    claim('P42', 'images ≥ 31 dB, hybride moins règles, GOP 3-9, Holm sur trois GOP', text, gap_checks(u['usable31']['3M9D'], text))
    return C.report()
