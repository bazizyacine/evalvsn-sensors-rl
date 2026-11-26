"""S13: the numbers of the abstract, the introduction, the discussion and the
conclusions, each recomputed by the package's functions, as P02 to P43, S01
to S10 and A01 to A11 recompute the same comparisons in the results; and, in
sections 3.7 and 3.9, the counts and the settings no other line recomputes:

  the scenario: the size of the main study, the rule stack's losses per cell
       and their oracle, the gap with AOMDV and with AOMDV with the
       cross-layer timers, the agent of the transmission power
  the access-only stack: its gain over the rule stack at the three GOPs, its
       frozen configurations, the hybrid stack against it, the memory of the
       agents on a node, the only agent with a significant gain
  the link-break agent: alone on the rule stack, without exploration or with
       its exploration decaying alone, the stacks that neither learn nor
       explore, its table and its declarations, and where the rule's lead was
       detected
  the hybrid stack: its lead over the three GOPs, the crossing of learning
       and exploration, the level M1 and the cases where its link to the PSNR
       was not detected, the GOP at equal packet rate and the leads that stay
       lower than its effect, the 28 dB threshold, the fire variants; in the
       limits, the radio of the sets and the margin of a link, the law of the
       decay
  sections 3.7 and 3.9: the simulations of the ANOVA, what the coefficient 0.1
       moves, the operations, the radio and the hellos of the costs

The level M1, the images, the delay, the deadlines and the series of sections
3.6 to 3.8 are S09, P18 to P42, S01 to S04, S14 and G01 to G08.

A range is checked by both ends, its bounds by the smallest lower and the
largest upper bound, and the p the text gives with it by the bound on p over
the comparisons it covers (checks.span_checks)."""
import math
import os
import re

from ..analysis import ablation, coding, comparative, controls, overhead, quality, robustness, round2
from ..analysis import access_robustness as access_series
from ..common import data, paths, stats
from ..tables import plan
from .checks import gap_checks, interval_checks, mean, pv, rev, span_checks

SPLITS, FIRES = data.SPLITS, data.FIRES
CROSS = ('rules', 'agents', 'hybrid')                       # the cross-layer stacks of E0


def _fire_values(prefix):
    """The values of a fire parameter its variants measure, from their names (az015: 0.15, pf075: 0.75)."""
    return [float(d[0] + '.' + d[1:]) if len(d) > 1 else float(d) for v in robustness.FIRE_VARIANTS if v.startswith(prefix)
            for d in [v[len(prefix):]]]


AZ, PF = _fire_values('az'), _fire_values('pf')


def holm_or_p(e):
    return e.p if e.holm is None else e.holm


def significant(e, sign=1):
    """The gap is significant (Holm's p, or the single test's) and has the sign given."""
    return holm_or_p(e) < 0.05 and sign * e.mean > 0


class Lines:
    """The two forms of the lines of a block: a gap with its interval and its
    p, a range of gaps with the range of their intervals and the bound on
    their p."""

    def __init__(self, C, block):
        self.C, self.block = C, block

    def claim(self, label, text, checks):
        self.C.claim(self.block, label, text, checks)

    def gap(self, label, text, e, written=None, also=()):
        """written: the gap as text writes it, where text holds other numbers before it."""
        self.claim(label, text, gap_checks(e, written or text) + list(also))

    def span(self, label, text, es, gaps, bounds, ordered=False, also=()):
        """text holds gaps, 'a à b dB, p ...' (its first range and its p), and bounds, the range of the intervals."""
        self.claim(label, text, span_checks([e.mean for e in es], gaps, [holm_or_p(e) for e in es], ordered=ordered)
                   + span_checks([e.lo for e in es] + [e.hi for e in es], bounds) + list(also))


def claims(C):
    """Adds the rows of S13 to the Claims C."""
    import sets     # code/metrics, on sys.path by common/paths
    L = Lines(C, 'S13')
    claim, gap, span = L.claim, L.gap, L.span
    rs = comparative.rows()
    psnr, m1, loss = (comparative.cells(rs, m) for m in ('psnr', 'm1loss', 'loss'))
    alone, inside = ablation.effects('psnr')

    # ------------------------------------------------------- the scenario
    claim('étude principale E0 : configurations, simulations par configuration, simulations (introduction)',
          'soit 36 configurations de vingt simulations, une par graine, et 720 simulations en tout',
          [(len(psnr), '=', 36, 0), (all(len(v) == 20 for v in psnr.values()), '=', True, 0), (len(rs), '=', 720, 0)])
    rules = [mean(loss[f, s, 'rules'].values()) for f in FIRES for s in SPLITS]
    oracle = [r for r in data.read_tsv(paths.results(paths.STUDY_E0, 'oracle.tsv')) or () if sets.keys(r['set'])[0] == 'rules']
    claim('pile à règles, E0 : perte par cellule, min. et max. (%) ; oracle, 180 simulations, aucun paquet perdu sans chemin '
          '(introduction, conclusions)',
          'À la période d\'alarme T = 9 s, la pile à règles perd 54 à 63 % des paquets selon le feu et le GOP, toujours alors qu\'un '
          'chemin existe … À T = 9 s, toutes les pertes de la pile à règles surviennent alors qu\'un chemin existe',
          [(min(rules), '=', 54, 0), (max(rules), '=', 63, 0),
           (len(oracle) == 180 and sum(int(r['unreachable']) for r in oracle) == 0, '=', True, 0)])
    near = [mean(loss[f, '9M3D', 'rules'].values()) for f in FIRES]
    claim('pile à règles, GOP 9-3 : perte sous chaque feu dans la plage visée, 40 à 60 % (limites)',
          'pour que la pile à règles perde 40 à 60 % des paquets au GOP 9-3', [(40 <= min(near) <= max(near) <= 60, '=', True, 0)])
    gap('PSNR, pile à règles − AOMDV, trois GOP, 60 graines (conclusions)',
        '+6,2 dB [5,8 ; 6,7], p < 0,001', comparative.per_seed(psnr, 'rules', 'aomdv')[0])
    e = quality.over_gops('rules', 'pq-tuned', 'psnr')
    claim('PSNR, pile à règles − AOMDV aux temporisations inter-couches, trois GOP, 60 graines (limites)',
          'La pile à règles dépasse encore de 4,13 dB AOMDV aux temporisations inter-couches ([3,83 ; 4,42], p < 0,001',
          [(e.mean, '=', 4.13, 2)] + interval_checks(e, '[3,83 ; 4,42]') + [pv(e.p, '< 0,001')])
    full = [100 * float(r['a0']) / float(r['decisions']) for r in data.read_tsv('agent-trace.tsv') or ()
            if r['agent'] == 'power' and r['t'] == '999']
    claim('agent de puissance, piles à agents et hybride tracées : part de ses décisions à +3 dBm, au-dessus de 99,99 % (limites)',
          'l\'agent de puissance choisit +3 dBm dans plus de 99,99 % de ses décisions',
          [(min(full), '>', 99.99, 2), (len(full) == 2, '=', True, 0)])
    same = all(rev('rules-onlyT', m=m) == rev('rules', m=m) for m in ('psnr', 'loss', 'm1loss'))
    claim('agent de puissance seul sur la pile à règles, GOP 9-3 : les 60 simulations identiques à celles de sa règle (conclusions)',
          'Au GOP 9-3, celui de la puissance ne change aucune simulation', [(same, '=', True, 0)])

    # ---------------------------------------------- the access-only stack
    ar = round2.access_gops('access - rules')
    span('PSNR, pile à accès seul − pile à règles, trois GOP : min., max. ; Holm max. ; bornes min. et max. (résumé, introduction, '
         'discussion, conclusions)',
         'sur trois feux simulés réunis, à chacun de trois codages, la première relève le rapport signal sur bruit de crête de 1,06 à 2,00 dB '
         '(intervalles de confiance à 95 % de 0,37 à 2,62 dB, p ≤ 0,004 … cet agent en relève le PSNR aux trois GOP (+1,06 à +2,00 dB, intervalles de 0,37 à 2,62 dB, p ≤ 0,004 … La pile à accès seul '
         'dépasse la pile à règles aux trois GOP (+1,06 à +2,00 dB, intervalles de 0,37 à 2,62 dB, p ≤ 0,004 … La pile à accès seul '
         'dépasse la pile à règles aux trois GOP',
         list(ar.values()), '1,06 à 2,00 dB, p ≤ 0,004', '0,37 à 2,62 dB',
         also=[(len(ar) == 3 and all(significant(e) for e in ar.values()), '=', True, 0)])
    ls = round2.learned_csma('rules', 'standard')
    span('PSNR, configurations apprises, puis figées, de la pile à accès seul − pile à règles, GOP 9-3, celui du gain maximal : min., '
         'max. ; Holm max. ; bornes min. et max. (résumé, discussion, conclusions)',
         'Au codage du gain maximal, ses configurations apprises … 2,02 à 2,33 dB (intervalles de 1,53 à 2,88 dB, p < 0,001 … À ce GOP, '
         'les configurations apprises de la pile à accès seul, puis figées, dépassent aussi la pile à règles … +2,02 à +2,33 dB, '
         'intervalles de 1,53 à 2,88 dB, p < 0,001',
         list(ls.values()), '2,02 à 2,33 dB, p < 0,001', '1,53 à 2,88 dB',
         also=[(max(ar, key=lambda s: ar[s].mean) == '9M3D' and all(significant(e) for e in ls.values()), '=', True, 0)])
    # the period of the main comparison and the one where its lead reverses at
    # GOP 9-3, the GOP of the largest gain (S14 checks the load series)
    e0 = sorted({sets.keys(n)[3:] for n in plan.names(paths.study(paths.STUDY_E0, 'sets.txt'))})   # (period, grid) of E0
    load = access_series.families()['load', 'access - rules']
    reversed_ = [p for p, e in load.items() if significant(e, -1)] or ['p0']
    claim('PSNR, pile à accès seul − pile à règles : période d\'alarme de E0 et de cette comparaison (s) ; au GOP du gain maximal, la '
          'seule période où elle passe sous la pile à règles, Holm sur cinq périodes (s) (résumé)',
          'À une image toutes les 9 s, sur trois feux simulés réunis … et son avance s\'inverse à 7 s',
          [(float(e0[0][0][1:]), '=', 9, 0), (float(reversed_[0][1:]), '=', 7, 0),
           (len(e0) == 1 and len(reversed_) == 1 and access_series.REFERENCE.period == e0[0][0]
            and abs(load[e0[0][0]].mean - ar['9M3D'].mean) < 1e-9, '=', True, 0)])
    la = list(round2.learned_csma('rules', 'agent').values())
    span('PSNR, configurations figées de la pile à accès seul − l\'agent qui apprend, GOP 9-3 : min., max. ; Holm min. ; bornes min. et '
         'max. (discussion)',
         '+0,02 à +0,34 dB, intervalles de −0,45 à +0,77 dB, p ≥ 0,46', la, '+0,02 à +0,34 dB, p ≥ 0,46', '−0,45 à +0,77 dB',
         also=[(all(e.holm >= 0.05 for e in la), '=', True, 0)])
    # the four fixed, uniform settings of before the learned configurations (round2.fixed_csma): against the
    # standard's setting, the largest in the access-only stack; each below the gain of
    # the agent in its stack, and each below the learning agent (single tests, S08)
    fixed = {(st, ref): list(round2.fixed_csma(st, ref).values()) for st in ('rules', 'hybrid') for ref in ('standard', 'agent')}
    agent_gain = {'rules': ar['9M3D'], 'hybrid': stats.paired(round2.values('hybrid', 'psnr'), round2.values('hybrid-noA', 'psnr'))}
    claim('PSNR, quatre réglages CSMA/CA fixes − les paramètres de la norme, GOP 9-3 : le plus grand, pile à accès seul (dB) ; dans chaque '
          'pile, tous sous le gain de l\'agent et sous l\'agent qui apprend (p < 0,05, tests uniques) ; configurations figées − l\'agent, '
          'aucun Holm < 0,05 (discussion)',
          'Un réglage uniforme ne retrouve donc qu\'une partie du gain de l\'agent (jusqu\'à +0,71 dB dans la pile à accès seul … Au GOP '
          '9-3, le gain entier n\'a été atteint qu\'avec des paramètres appris pour chaque nœud et chaque état',
          [(max(e.mean for e in fixed['rules', 'standard']), '=', 0.71, 2),
           (all(max(e.mean for e in fixed[st, 'standard']) < agent_gain[st].mean and significant(agent_gain[st])
                and all(e.mean < 0 and e.p < 0.05 for e in fixed[st, 'agent']) for st in agent_gain), '=', True, 0),
           (all(e.holm >= 0.05 for e in la), '=', True, 0)])
    lh = round2.learned_csma('hybrid', 'agent')
    gap('PSNR, configuration k4 figée de la pile hybride − l\'agent qui apprend, GOP 9-3, Holm sur quatre : la seule des quatre sous '
        'l\'agent avec Holm < 0,05 (limites)',
        'une configuration figée sur quatre passe sous l\'agent qui apprend (−2,06 dB [−2,45 ; −1,66], p < 0,001', lh[4],
        also=[(len(lh) == 4 and [k for k, e in lh.items() if significant(e, -1)] == [4], '=', True, 0)])
    ld = list(round2.learned_csma('rules', 'agent', 'declared').values())
    span('voisins déclarés morts par simulation, configurations figées de la pile à accès seul − l\'agent qui apprend, GOP 9-3, tests '
         'uniques : min., max. ; p max. ; bornes min. et max. ; toutes au-dessous (limites)',
         'ses configurations apprises, figées sans exploration pendant la mission, les réduisent davantage que l\'agent qui apprend dans la '
         'pile à accès seul (−4,1 à −1,9 par simulation, intervalles de −5,0 à −0,8, p ≤ 0,002, tests uniques',
         ld, '−4,1 à −1,9 par simulation, p ≤ 0,002', '−5,0 à −0,8',
         also=[(len(ld) == 4 and all(e.holm is None and significant(e, -1) for e in ld), '=', True, 0)])
    ha = round2.access_gops('hybrid - access')
    span('PSNR, pile hybride − pile à accès seul, trois GOP : min., max. ; Holm min. ; bornes min. et max. (résumé, introduction, '
         'discussion, conclusions)',
         '−0,23 à +0,02 dB, intervalles de −0,66 à +0,69 dB, p ≥ 0,84 … −0,23 à +0,02 dB (intervalles de −0,66 à +0,69 dB, p ≥ 0,84',
         list(ha.values()), '−0,23 à +0,02 dB, p ≥ 0,84', '−0,66 à +0,69 dB',
         also=[(len(ha) == 3 and all(e.holm >= 0.05 for e in ha.values()), '=', True, 0)])
    claim('pile retenue par la règle de choix, dans son domaine : période d\'alarme (s) et espacement de la grille (m) de E0, où la perte '
          'du niveau M1 est comparée ; pile hybride − pile à accès seul, aucun Holm < 0,05 aux trois GOP (discussion, conclusions)',
          'À T = 9 s, la pile hybride conserve aussi cette protection … À T = 9 s, sur la grille de 40 m et au coefficient de qualité 0,01, '
          'la pile à accès seul est donc retenue',
          [(float(e0[0][0][1:]), '=', 9, 0), (float(e0[0][1]), '=', 40, 0),
           (len(e0) == 1 and all(e.holm >= 0.05 for e in ha.values()), '=', True, 0)])
    # the coefficient 0.1, measured at GOP 9-3 alone (its sets in studies 10 and 11)
    coded = {sets.keys(n)[2] for study in (paths.STUDY_R1, paths.STUDY_R2) for n in plan.names(paths.study(study, 'sets.txt'))
             if 'GC-QC-0p1' in n}
    claim('série au coefficient de qualité 0,1 : le GOP de tous ses jeux (introduction)',
          'Au GOP 9-3 et au coefficient 0,1, la pile hybride dépasse la pile à accès seul', [(coded == {'9M3D'}, '=', True, 0)])
    # the memory the agents take on a node (analysis/overhead.memory, which
    # P43 checks in 3.9), one agent against six
    _, mem = overhead.memory()
    claim('mémoire des agents par nœud (octets) : pile à accès seul, un agent ; pile hybride, six agents, cinq de plus (résumé, '
          'introduction, discussion, conclusions)',
          'La pile hybride confie '
          'à des agents cinq décisions de plus que la pile à accès seul … six agents et 863 octets par nœud, contre un agent et 338 '
          'octets … Elle compte six agents (863 octets par nœud), contre un (338 octets) pour la pile à accès seul',
          [(mem['access']['node'], '=', 338, 0), (mem['hybrid']['node'], '=', 863, 0),
           ((len(overhead.AGENTS['access']), len(overhead.AGENTS['hybrid'])) == (1, 6), '=', True, 0)])
    claim('PSNR, agents seuls sur la pile à règles et retirés de la pile hybride, GOP 9-3, coefficient 0,01 : l\'accès au canal, le seul '
          'au-dessus avec Holm < 0,05 (discussion)',
          'Au GOP 9-3 et au coefficient de qualité de 0,01, l\'agent de l\'accès au canal est le seul dont un gain statistiquement '
          'significatif ait été détecté',
          [([x for x, e in alone.items() if significant(e)] == ['A'], '=', True, 0),
           ([x for x, e in inside.items() if significant(e)] == ['A'], '=', True, 0)])

    # ------------------------------------------------ the link-break agent
    ah = comparative.paired_gops(psnr, 'hybrid', 'agents')
    gap('PSNR, agent de détection de rupture seul sur la pile à règles, GOP 9-3, Holm sur sept ; il abaisse aussi celui de la pile '
        'hybride à ce GOP, Holm sur trois GOP (introduction, discussion)',
        'ajouté seul à la pile à règles, en abaisse le PSNR au GOP 9-3 (−1,42 dB [−2,08 ; −0,75], p < 0,001 … Au GOP 9-3 et à taux '
        'd\'exploration constant, cet agent abaisse le PSNR de la pile à règles comme celui de la pile hybride',
        alone['B'], written='−1,42 dB [−2,08 ; −0,75], p < 0,001',
        also=[(significant(alone['B'], -1) and significant(inside['B'], -1) and significant(ah['9M3D']), '=', True, 0)])
    gap('PSNR, pile à agents − pile à règles, trois GOP, 60 graines (introduction, conclusions)',
        '−0,01 dB [−0,32 ; 0,29], p = 0,94',
        comparative.per_seed(psnr, 'agents', 'rules')[0])
    gap('PSNR, pile à agents, exploration des sept agents décroissante − constante, GOP 9-3, Holm sur deux (conclusions)',
        'gagne 1,55 dB ([1,04 ; 2,05], p < 0,001 … elle gagne aussi au GOP 9-3 (+1,55 dB [1,04 ; 2,05], p < 0,001', controls.decay()['agents'])
    claim('PSNR, agent de détection de rupture seul sur la pile à règles, Holm sur sept : le seul agent sous sa règle avec Holm < 0,05, '
          'seul et dans la pile hybride (conclusions)',
          'cet agent, ajouté seul à la pile à règles, est le seul dont une baisse statistiquement significative du PSNR ait été détectée à ce '
          'GOP (−1,42 dB [−2,08 ; −0,75], p < 0,001',
          gap_checks(alone['B'], '−1,42 dB [−2,08 ; −0,75], p < 0,001')
          + [([x for x, e in alone.items() if significant(e, -1)] == ['B'] and [x for x, e in inside.items() if significant(e, -1)] == ['B'],
              '=', True, 0)])
    tuned = quality.over_gops('rules', 'pq-tuned', 'psnr')
    claim('PSNR, pile à règles − AOMDV et − AOMDV aux temporisations inter-couches, trois GOP, 60 graines, tests uniques (conclusions)',
          'Elle dépasse AOMDV en PSNR (+6,2 dB [5,8 ; 6,7]) et dépasse encore AOMDV aux temporisations inter-couches (+4,13 dB [3,83 ; 4,42], '
          'p < 0,001 pour les deux',
          gap_checks(comparative.per_seed(psnr, 'rules', 'aomdv')[0], '+6,2 dB [5,8 ; 6,7], p < 0,001')
          + gap_checks(tuned, '+4,13 dB [3,83 ; 4,42], p < 0,001'))
    greedy, decay = ({ref: round2.link_break(lv, ref) for ref in round2.BREAK_REFERENCES} for lv, _ in round2.LEVELS)
    gained, slow = list(greedy['agents'].values()), list(decay['agents'].values())
    span('PSNR, agent de détection de rupture sans exploration − pile à agents, trois GOP : min., max. ; Holm max. ; bornes min. et max. '
         '(résumé, introduction)',
         'fait gagner à la pile à agents 1,39 à 2,21 dB (intervalles de 0,71 à 2,62 dB, p < 0,001 … gagne de 1,39 à 2,21 dB selon le GOP '
         '(intervalles de 0,71 à 2,62 dB, p < 0,001',
         gained, '1,39 à 2,21 dB, p < 0,001', '0,71 à 2,62 dB')
    text = ('Aux trois GOP, elle gagne 1,18 à 1,72 dB quand décroît l\'exploration de son seul agent de détection de rupture, et 1,39 à '
            '2,21 dB sans cette exploration (intervalles de 0,63 à 2,62 dB pour les deux gains, p < 0,001 … Quand seule '
            'l\'exploration de l\'agent de détection de rupture décroît, la pile à agents gagne en PSNR aux trois GOP')
    claim('PSNR, agent de détection de rupture à exploration décroissante seule − pile à agents, puis sans exploration − pile à agents, '
          'trois GOP : min., max. de chacun ; bornes min. et max. des deux ; Holm max. des deux (conclusions, discussion)', text,
          span_checks([e.mean for e in slow], '1,18 à 1,72 dB') + span_checks([e.mean for e in gained], '1,39 à 2,21 dB')
          + span_checks([e.lo for e in slow + gained] + [e.hi for e in slow + gained], '0,63 à 2,62 dB')
          + [pv(max(e.holm for e in slow + gained), '< 0,001'), (all(significant(e) for e in slow + gained), '=', True, 0)])
    under = list(greedy['hybrid'].values())
    span('PSNR, agent de détection de rupture sans exploration − pile hybride, trois GOP : min., max. ; Holm min. ; bornes min. et max. '
         '(discussion)',
         '+0,14 à +0,51 dB, intervalles de −0,24 à +1,09 dB, p ≥ 0,071', under, '+0,14 à +0,51 dB, p ≥ 0,071', '−0,24 à +1,09 dB',
         also=[(all(e.holm >= 0.05 for e in under), '=', True, 0)])
    claim('PSNR, agent de détection de rupture sans exploration − pile hybride : seul le GOP 6-6 a l\'intervalle sans zéro, Holm ≥ 0,05 '
          '(discussion, conclusions)',
          'Quand l\'agent de détection de rupture n\'explore pas (\\varepsilon = 0), aucune différence statistiquement significative n\'a été '
          'détectée entre elles, aux trois GOP (+0,14 à +0,51 dB, intervalles de −0,24 à +1,09 dB, p ≥ 0,071). L\'intervalle du GOP 6-6 '
          'exclut toutefois zéro … Avec \\varepsilon = 0 pour cet agent, aucune différence statistiquement significative n\'a été détectée '
          'entre les piles à agents et hybride, à aucun GOP (+0,14 à +0,51 dB, intervalles de −0,24 à +1,09 dB, p ≥ 0,071). L\'intervalle '
          'du GOP 6-6 exclut toutefois zéro',
          [(sorted(s for s, e in greedy['hybrid'].items() if round2.flagged(e)) == ['6M6D'], '=', True, 0)])
    frozen = stats.paired(quality.values('agents-frozen', 'psnr', '9M3D'), quality.values('hybrid-frozen', 'psnr', '9M3D'))
    gap('PSNR, pile à agents − pile hybride sans apprentissage ni exploration, GOP 9-3, test unique (discussion, conclusions)',
        '+0,15 dB [−0,42 ; 0,71], p = 0,60', frozen)
    lead = {name: sorted(s for s, e in es.items() if significant(e, -1)) for name, es in (
        ('constant', {s: stats.paired(quality.values('agents', 'psnr', s), quality.values('hybrid', 'psnr', s)) for s in SPLITS}),
        ('decaying', decay['hybrid']), ('none', greedy['hybrid']), ('frozen', {'9M3D': frozen}))}
    claim('PSNR, agent de détection de rupture − la règle : les GOP où la règle est au-dessus, p ou Holm < 0,05 ; exploration constante '
          '(E0, trois GOP), décroissante seule (GOP 9-3), nulle et pile figée (aucun) ; au GOP 9-3, la pile hybride au-dessus de la pile à '
          'agents dont les sept agents ont une exploration décroissante, Holm sur trois (discussion, conclusions)',
          'Dans les deux cas, elle reste sous la pile hybride au GOP 9-3 … L\'avantage de la règle n\'a donc été détecté qu\'avec cette '
          'exploration, persistante ou, au GOP 9-3, décroissante … La déclaration d\'un voisin mort gagne donc à rester une règle, mais cet '
          'avantage n\'a été détecté qu\'en présence de l\'exploration de son agent',
          [(lead == {'constant': sorted(SPLITS), 'decaying': ['9M3D'], 'none': [], 'frozen': []}, '=', True, 0),
           (all(significant(e) for e in ah.values()) and significant(controls.decayed_agents()['hybrid']), '=', True, 0)])
    # its table and its decisions in the traced runs, GOP 9-3 (break-agent.tsv)
    pick, best, declared = ({k: controls.brk('agents', '%s%d' % (c, k)) for k in controls.COUNTS} for c in ('pick', 'best', 'decl'))
    claim('agent de détection de rupture : couples où trois échecs ont la plus grande valeur, sur le total, pas tous (résumé, '
          'introduction, discussion, conclusions)',
          'le choix de la règle, trois échecs, garde la plus grande valeur pour 36 des 41 couples de nœud et d\'état observés. La table '
          'ne préfère donc pas partout la règle … la table de cet agent ne préfère pas partout la règle des trois échecs … la table de '
          'l\'agent de détection de rupture ne préfère pas partout la règle',
          [(best[3], '=', 36, 0), (sum(best.values()), '=', 41, 0), (best[3] < sum(best.values()), '=', True, 0)])
    claim('agent de détection de rupture : part de ses décisions, et de ses déclarations, d\'un seul échec (%) (introduction, '
          'discussion, conclusions)',
          'Les actions explorées d\'un seul échec, 2,4 % de ses décisions, produisent pourtant 70 % des déclarations que ses compteurs '
          'enregistrent … 70 % des déclarations que ses compteurs enregistrent dans la pile à agents viennent d\'actions explorées d\'un '
          'seul échec … et son exploration persistante d\'un seul échec produit 70 % des déclarations que ses compteurs enregistrent',
          [(100 * pick[1] / sum(pick.values()), '=', 2.4, 1), (100 * declared[1] / sum(declared.values()), '=', 70, 0)])

    # --------------------------------------------------- the hybrid stack
    gap('PSNR, pile hybride − pile à règles, trois GOP, 60 graines (introduction, conclusions)',
        '+1,52 dB [1,12 ; 1,92], p < 0,001 … dépasse la pile à règles de 1,52 dB [1,12 ; 1,92] sur les trois GOP (p < 0,001',
        comparative.per_seed(psnr, 'hybrid', 'rules')[0])
    gap('PSNR, pile hybride sans exploration − pile hybride figée, GOP 9-3, Holm sur quatre (discussion, conclusions)',
        '+1,61 dB [1,11 ; 2,10], p < 0,001 … Au GOP 9-3, la pile '
        'hybride qui apprend sans explorer dépasse la pile hybride figée', round2.crossing()['learning alone'])
    gap('perte du niveau M1, pile hybride − pile à règles, trois GOP, 60 graines (discussion, conclusions)',
        '−4,4 points [−6,7 ; −2,2], p < 0,001',
        comparative.per_seed(m1, 'hybrid', 'rules')[0])
    am1 = round2.access_gops('access - rules', 'm1loss')
    claim('perte du niveau M1, pile à accès seul − pile à règles, tests uniques : sous zéro avec p < 0,05 aux GOP 6-6 et 9-3 seuls '
          '(discussion)',
          'À T = 9 s et aux GOP 6-6 et 9-3, la pile à accès seul perd moins de paquets M1 que la pile à règles',
          [([s for s in SPLITS if significant(am1[s], -1)] == ['6M6D', '9M3D'], '=', True, 0)])
    pf = {m: robustness.period_family('hybrid', 'rules', m) for m in ('psnr', 'm1loss', 'loss')}
    sv = {m: robustness.scenario_family('gap', 'hybrid-rules', m) for m in ('psnr', 'm1loss')}
    three = [pf['m1loss'][p] for p in ('p7', 'p12', 'p18', 'p30')] + [sv['m1loss']['swap'], sv['m1loss']['j8']]
    span('perte du niveau M1, pile hybride − pile à règles à 7, 12, 18 et 30 s, caméra et puits échangés, grille de 30 m : min., max. '
         '(points) ; Holm min. ; bornes min. et max. (discussion)',
         'À 7, 12, 18 et 30 s, aucune différence statistiquement significative de cette perte n\'a été détectée entre ces deux piles … Aucune '
         'ne l\'a été non plus quand la caméra et le puits sont échangés, ni sur la grille de 30 m. Les écarts vont de −1,9 à +1,3 point '
         '(intervalles de −3,8 à +3,4 points, p ≥ 0,10', three, '−1,9 à +1,3 point, p ≥ 0,10', '−3,8 à +3,4 points',
         also=[(all(e.holm >= 0.05 for e in three), '=', True, 0)])
    seven = access_series.families()['load', 'access - rules']['p7']
    claim('pile hybride − pile à règles : caméra et puits échangés et 12 s, PSNR au-dessus ; 12 s, perte globale au-dessous ; 7 s, PSNR '
          'au-dessous, comme celui de la pile à accès seul (Holm < 0,05, discussion, limites)',
          'La pile hybride dépasse pourtant la pile à règles à 12 s et quand la caméra et le puits sont échangés. À 12 s, sa perte globale '
          'est plus faible … À 7 s, elle passe sous la pile à règles, comme la pile à accès seul … jusqu\'à 7 s, où les piles à accès seul et hybride passent sous la pile à règles',
          [(all(significant(e) for e in (pf['psnr']['p12'], sv['psnr']['swap'])), '=', True, 0),
           (all(significant(e, -1) for e in (pf['loss']['p12'], pf['psnr']['p7'], seven)), '=', True, 0)])
    eqd = {s: stats.paired(rev(s, '9M3D'), rev(s, '3M9D', 'p9r65')) for s in ('rules', 'hybrid')}
    claim('PSNR, GOP 9-3 − GOP 3-9 à débit égal, piles à règles et hybride, tests uniques (discussion)',
          'l\'avance du GOP 9-3 sur le GOP 3-9 est de 5,12 dB [4,39 ; 5,85] avec la pile à règles. Elle est de 5,63 dB [5,11 ; 6,14] avec '
          'la pile hybride (p < 0,001 pour les deux',
          gap_checks(eqd['rules'], '5,12 dB [4,39 ; 5,85]') + gap_checks(eqd['hybrid'], '5,63 dB [5,11 ; 6,14]')
          + [pv(max(e.p for e in eqd.values()), '< 0,001')])
    leads = list(comparative.paired_cells(psnr, 'hybrid', 'rules').values()) + list(round2.access_cells('access - rules').values())
    claim('avances des piles hybride et à accès seul sur la pile à règles, neuf cellules chacune (tableau des écarts) : la plus haute, et '
          'la plus haute borne, sous celle du GOP 9-3 sur le GOP 3-9 à débit égal et sous sa plus basse borne (discussion)',
          'Les avances des piles à accès seul et hybride sur la pile à règles restent plus faibles',
          [(max(e.mean for e in leads) < min(e.mean for e in eqd.values()), '=', True, 0),
           (max(e.hi for e in leads) < min(e.lo for e in eqd.values()) and len(leads) == 18, '=', True, 0)])
    terms = {t[0]: t for t in comparative.anova(rs)}
    claim('ANOVA de E0 : feu, pile × feu, p ≥ 0,05 ; η² partiel du GOP au-dessus de celui de la pile (discussion, conclusions)',
          'aucun effet statistiquement significatif du feu n\'a été détecté, ni sur le PSNR ni sur l\'écart entre les piles inter-couches … '
          'la qualité dépend davantage du GOP que du choix entre les trois piles inter-couches',
          [(bool(terms['fire'][4] >= 0.05 and terms['stack x fire'][7] >= 0.05), '=', True, 0),
           (bool(terms['split'][5] > terms['stack'][5]), '=', True, 0)])
    # the PSNR of the stacks of the PSNR table in each cell
    arms = {'aomdv': lambda s: 'pq', 'tuned': lambda s: 'pq-tuned', 'rules': lambda s: 'rules', 'access': round2.access_only,
            'hybrid': lambda s: 'hybrid', 'agents': lambda s: 'agents'}
    cell = {(st, s, f): mean(x for k, x in quality.values(a(s), 'psnr', s).items() if k[0] == f)
            for st, a in arms.items() for s in SPLITS for f in FIRES}
    claim('PSNR moyen par cellule, six piles du tableau du PSNR : aucune à 28 dB aux GOP 3-9 et 6-6 ; au GOP 9-3, les piles à accès seul '
          'et hybride seules au-dessus, sous les trois feux (discussion)',
          'peut atteindre le seuil de PSNR de 28 dB. Aucune pile ne l\'atteint aux GOP 3-9 et 6-6. Au GOP 9-3, seules les piles à accès seul '
          'et hybride le dépassent, sous les trois feux',
          [(max(x for (st, s, f), x in cell.items() if s != '9M3D') < 28, '=', True, 0),
           (all(sorted(st for st in arms if cell[st, '9M3D', f] > 28) == ['access', 'hybrid'] for f in FIRES), '=', True, 0)])
    level = {(series, v.key): v for series in ('load', 'scenario') for v in access_series.SERIES[series]}

    def at(st, key):
        """The mean PSNR of a stack at a level of the load or scenario series."""
        if st == 'access':
            return access_series.mean(st, level[key])
        return robustness.mean_of(robustness.arm(st, level[key].variant), 'psnr', level[key].period)
    cross = ('rules', 'access', 'agents', 'hybrid')
    q01 = {st: (access_series.mean('access', access_series.SERIES['coding'][0]) if st == 'access'
                else coding.mean(st + '-q01', '9M3D', 'p9', 'psnr')) for st in cross}
    claim('PSNR moyen au GOP 9-3 : les quatre piles inter-couches au-dessus de 28 dB à 12, 18 et 30 s, sous la vidéo fumée et au '
          'coefficient 0,1 ; sur la grille de 30 m, toutes sauf la pile à agents ; AOMDV à 18 et 30 s ; aucune pile sous la vidéo forêt '
          '(discussion)',
          'À ce GOP, les quatre piles inter-couches le dépassent aussi à 12, 18 et 30 s, avec la vidéo fumée et au coefficient de 0,1. Sur '
          'la grille de 30 m, toutes le dépassent sauf la pile à agents. AOMDV le dépasse à 18 et 30 s, mais aucune pile avec la vidéo forêt',
          [([p for p in robustness.PERIODS if all(at(st, ('load', p)) > 28 for st in cross)] == ['p12', 'p18', 'p30'], '=', True, 0),
           ([p for p in robustness.PERIODS if at('pq', ('load', p)) > 28] == ['p18', 'p30'], '=', True, 0),
           (all(at(st, ('scenario', 'smoke')) > 28 for st in cross) and all(v > 28 for v in q01.values()), '=', True, 0),
           ([st for st in cross if at(st, ('scenario', 'j8')) <= 28] == ['agents'], '=', True, 0),
           (all(at(st, ('scenario', 'forest')) < 28 for st in cross + ('pq',)), '=', True, 0)])
    gain = robustness.fire_family('gain', 'psnr')
    again = access_series.families()['fire', 'access - rules']
    claim('piles hybride et à accès seul − règles, sept variantes du feu et référence : l\'avance significative sous chacune ; valeurs de '
          'AZ (dB/m) et de PF (limites)',
          'Les avances des piles à accès seul et hybride restent significatives à chaque valeur mesurée de AZ et de PF, et sous deux lois de '
          'ces instants. Ces valeurs vont de 0,15 à 1,65 dB/m pour AZ et de 0 à 0,75 pour PF',
          [(all(significant(e) for e in list(gain.values()) + list(again.values())) and len(gain) == len(again) == 7, '=', True, 0),
           (significant(robustness.fire()['reference']['psnr']), '=', True, 0),
           (min(AZ), '=', 0.15, 2), (max(AZ), '=', 1.65, 2), (min(PF), '=', 0, 0), (max(PF), '=', 0.75, 2)])
    # the limits: the margin of a 40 m link (P38, section 3.4, from the settings
    # of code/campaign; the simulator's speed of light) and the law of the decay
    lam = 3e8 / parameter('freq_')
    margin = 10 * math.log10(parameter('Pt_') * (lam / (4 * math.pi)) ** 2 / parameter('CSThresh_')) - 10 * 3.2 * math.log10(40)
    studied = {n for study in (paths.STUDY_E0, paths.STUDY_R1, paths.STUDY_R2) for n in plan.names(paths.study(study, 'sets.txt'))}
    propagation = {line.split()[8] for line in open(paths.CONF, encoding='utf-8') if line.split()[:1] and line.split()[0] in studied}
    claim('modèle de radio des jeux des trois études : loi log-distance d\'exposant 3,2 sans terme aléatoire (écart type 0) ; marge d\'un lien '
          'de 40 m au-dessus de P_CCA, sans interférence (dB) (limites)',
          'Le modèle de radio omet les évanouissements … les liens de la grille, dont la marge est de 2,7 dB',
          [(propagation == {'shadowing:3.2:0'}, '=', True, 0), (margin, '=', 2.7, 1)])
    decays = [(line.split()[0], k, float(v)) for line in open(paths.CONF, encoding='utf-8') if not line.startswith('#')
              for k, v in re.findall(r'\brl_(?:break_)?eps_(start|end)=([\d.]+)', line)]
    claim('décroissance de l\'exploration : ses instants de début et de fin dans tous ses jeux (s) ; celle de tous les agents, au GOP 9-3 '
          'seulement (limites)',
          'La décroissance de l\'exploration suit une seule loi, de 60 à 114 s, et celle de tous les agents n\'a été mesurée qu\'au GOP 9-3',
          [({v for _, k, v in decays if k == 'start'} == {60} and {v for _, k, v in decays if k == 'end'} == {114}, '=', True, 0),
           ({sets.keys(n)[2] for n, _, _ in decays if '-edec-' in n} == {'9M3D'}, '=', True, 0)])
    results(C)


def results(C):
    """Sections 3.7 and 3.9: what P18 to P43 (claims/results.py), S09 (claims/round2.py), S01 to S04 and S11 (claims/review.py) leave."""
    claim = Lines(C, 'S13').claim
    rs = comparative.rows()

    # 3.7, the simulations of the ANOVA
    claim('ANOVA de E0 : simulations des trois piles inter-couches, graines (légende du tableau de l\'ANOVA)',
          'Analyse à mesures répétées du PSNR, 540 simulations sur 60 graines',
          [(sum(r['stack'] in CROSS for r in rs), '=', 540, 0), (len({(r['fire'], r['realisation']) for r in rs}), '=', 60, 0)])

    # 3.7, the coefficient 0.1
    def moves(metric, stack, sign):
        """The metric moves with the sign given from the coefficient 0.01 to 0.1."""
        return sign * (coding.mean(stack + '-q01', '9M3D', 'p9', metric) - coding.mean(stack, '9M3D', 'p9', metric)) > 0
    claim('coefficient 0,1 au lieu de 0,01, GOP 9-3 : perte globale en baisse, quatre piles ; images ≥ 28 dB en hausse, trois piles '
          'inter-couches (3.7)',
          'La perte globale baisse avec ces quatre piles, et le nombre d\'images qui atteignent le seuil de PSNR augmente avec les trois '
          'piles inter-couches',
          [(all(moves('loss', s, -1) for s, _ in coding.STACKS) and all(moves('usable', s, 1) for s in CROSS), '=', True, 0)])

    # 3.9, the costs: the operations, the radio and the hellos
    claim('opérations par paquet : comparaisons des quatre agents ; trois opérations de mise à jour par agent ; deux tirages par agent (3.9)',
          'ajoutent au plus 40 opérations par paquet … parmi cinq, quatre, neuf et au plus six actions … soit au plus 20 en tout … 12 '
          'opérations pour les quatre … au plus huit nombres aléatoires uniformes, deux par agent',
          [(sum(k - 1 for k in (5, 4, 9, overhead.power_steps())), '=', 20, 0), (4 * 3, '=', 12, 0), (2 * 4 == 8, '=', True, 0),
           (sum(k - 1 for k in (5, 4, 9, overhead.power_steps())) + 4 * 3 + 2 * 4, '=', 40, 0)])
    claim('décisions de la caméra par seconde, quatre par paquet, un paquet toutes les 15 ms (3.9)',
          'qui émet un paquet toutes les 15 ms pendant l\'envoi d\'une image, prend au plus quatre décisions par paquet, soit 267 par seconde',
          [(1000 * overhead.EMIT, '=', 15, 0), (4 / overhead.EMIT, '=', 267, 0)])
    radio = data.radio()
    claim('puissances de la radio en réception, en écoute et en émission (mW) (3.9)',
          '(37 mW en réception comme en écoute, 42 mW en émission',
          [(1000 * radio['rx'], '=', 37, 0), (radio['rx'] == radio['idle'], '=', True, 0), (1000 * radio['tx'], '=', 42, 0)])
    default = re.search(r'^Agent/AOMDV set HELLO_INTERVAL_\s+(\S+)', open(os.path.join(paths.NS2, 'tcl', 'lib', 'ns-agent.tcl')).read(), re.M)
    claim('période des HELLO des piles inter-couches (s), AOMDV à sa valeur par défaut d\'une seconde (3.9)',
          'Les piles inter-couches envoient leurs HELLO toutes les 5 s, contre chaque seconde dans AOMDV',
          [(parameter('helloInterval_'), '=', 5, 0), (float(default[1]) == 1, '=', True, 0)])


def parameter(name):
    """A numeric setting of code/campaign/radio-params.tcl, 'set name value' or '... set name value'."""
    return float(re.search(r'\bset %s\s+(\S+)' % re.escape(name), open(paths.RADIO, encoding='utf-8').read())[1])
