"""S12: the numbers of section 2 that the data, the sets or the simulator's
sources give, each recomputed here (the Holm families and the assumptions of
the tests, section 2.7, are S11, claims/review.py; the mean rate, the raw
image and the equal-rate periods P37, P39 and P40, claims/results.py):

  the radio     the link budget of the log-distance model, from the radio
                constants of code/campaign/radio-params.tcl, and the links of
                the two grids (methode-mesures.tsv)
  the sets      the duration of the simulations, the counts of the plan
                table, the interval between two packets and the traced
                simulations, from the lists of sets and sets.conf
  the fire      the three fires and their shared parameters (sets.conf), the
                losses of the rule stack at GOP 9-3 and what the oracle finds
                under the worst failures
  the stacks    the routing timers, the paths, the agents' rates, from the
                simulator's sources; the bound of the two link profiles
  the video     the packets, the bytes and the energies of the coded frames
                (codec-frames.tsv, methode-mesures.tsv)
  the pairing   the calendars of failures per seed
  the seeds     E0 without the ten seeds of the preliminary trial, and its
                interim analysis: the intervals at ten seeds per fire, the
                ten added seeds alone
  the rule      the stack the choice rule of 2.6 retains at each level of
                the series of E4 and E5, inside and outside its domain"""
import math
import os
import re

from ..analysis import access_robustness as access_analysis
from ..analysis import coding, comparative, overhead, quality, robustness
from ..analysis import round2 as round2_analysis
from ..common import data, paths, stats
from ..tables import plan
from .checks import gap_checks, range_checks, table

FIRES, SPLITS, GOP = data.FIRES, data.SPLITS, data.GOP
EXPONENT = 3.2          # the log-distance exponent of section 2.1 (sets.conf, shadowing:3.2:0)
SPACING = 40.0          # m, the grid
LIGHT = 3e8             # m/s, the simulator's speed of light (claims/results.py, P38)
EDGE = 10 - 1           # the steps of a side of the 10 x 10 grid


def source(pattern, *path):
    """The number that pattern captures, once, in a file of the simulator or
    of the campaign."""
    found = set(re.findall(pattern, open(os.path.join(*path), encoding='utf-8').read(), re.M))
    if len(found) != 1:
        raise ValueError('%s: %d values of %s' % (os.path.join(*path), len(found), pattern))
    return float(found.pop())


def numbers(text):
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?', text)]


def claims(C):
    """Adds the rows of S12 to the Claims C."""

    def claim(label, written, checks, **kw):
        C.claim('S12', label, written, checks, **kw)

    mes = {(r['kind'], r['key']): r['value'] for r in data.table('methode-mesures.tsv')}
    codec = {(r['quantity'], r['key']): r['value'] for r in data.table('codec-frames.tsv')}

    # ---------------------------------------------------------- the radio
    radio = {k: source(r'^\$val\(netif\) set %s\s+(\S+)' % k, paths.RADIO) for k in ('CSThresh_', 'RXThresh_', 'Pt_', 'freq_', 'CPThresh_')}
    at_1m = radio['Pt_'] * (LIGHT / radio['freq_']) ** 2 / (4 * math.pi) ** 2      # Friis, unit gains, L = 1
    received = 10 * math.log10(1000 * at_1m) - 10 * EXPONENT * math.log10(SPACING)
    reach = lambda threshold: (at_1m / threshold) ** (1 / EXPONENT)                # noqa: E731
    claim('bilan de liaison à 40 m : puissance reçue (dBm), marge sur P_CCA (dB), portée (m)',
          'À 40 m, le signal d\'un voisin est reçu à -88,3 dBm, 2,7 dB au-dessus de P_{\\mathrm{CCA}}, et la portée s\'arrête à 48,6 m … '
          'portée de 48,6 m … Avec 2,7 dB de marge à 40 m',
          [(received, '=', -88.3, 1), (received - 10 * math.log10(1000 * radio['CSThresh_']), '=', 2.7, 1), (reach(radio['CSThresh_']), '=', 48.6, 1)])
    claim('seuil de détection de porteuse égal à la sensibilité : distance de porteuse (m) ; pas de grille',
          'Avec un seuil de -101 dBm, égal à la sensibilité, un nœud entendrait la porteuse jusqu\'à 99,7 m, deux pas et demi de grille',
          [(reach(radio['RXThresh_']), '=', 99.7, 1), (round(reach(radio['RXThresh_']) / SPACING, 1) == 2.5, '=', True, 0),
           (10 * math.log10(1000 * radio['RXThresh_']), '=', -101, 0)])
    claim('seuil de CCA (dBm), puissance d\'émission (dBm), sensibilité (dBm) ; capture (dB)',
          'P_{\\mathrm{CCA}} = -91 dBm … émission à +3 dBm, sensibilité de -101 dBm … dépasse d\'au moins 3 dB le maximum',
          [(-10 * math.log10(1000 * radio['CSThresh_']), '=', 91, 0), (10 * math.log10(1000 * radio['Pt_']), '=', 3, 0),
           (-10 * math.log10(1000 * radio['RXThresh_']), '=', 101, 0), (10 * math.log10(radio['CPThresh_']), '=', 3, 0)])
    claim('grille de 40 m : liens diagonaux à portée ; sauts au moins (deux côtés de la grille)',
          'Aucun lien diagonal n\'est donc à portée, et la vidéo traverse au moins dix-huit sauts',
          [(numbers(mes['topo', '40 m diagonal links'])[0] == 0, '=', True, 0),
           (int(mes['topo', '40 m fewest hops']) == 2 * EDGE == 18, '=', True, 0)])
    moved = numbers(mes['topo', '30 m largest displacement'])
    claim('grille de 30 m : des liens diagonaux à portée ; points d\'allumage (30 m sur 40 m) ; déplacement des nœuds par axe, max. (m)',
          'Sur la grille de 30 m, où des diagonales sont à portée, les coordonnées des allumages sont multipliées par 0,75 et les nœuds '
          'déplacés de 8 m au plus sur chaque axe',
          [(numbers(mes['topo', '30 m diagonal links'])[0] > 0, '=', True, 0), (30 / SPACING, '=', 0.75, 2),
           (max(moved) <= 8, '=', True, 0), (max(moved), '=', 8, 0)])

    # ----------------------------------------------------------- the sets
    simt = {k: float(v) for (kind, k), v in mes.items() if kind in ('load', 'volume') and k.endswith('simt')}
    e0 = {g: {v for k, v in simt.items() if k.startswith(p)} for g, p in (('9-3', 'p9 '), ('6-6', '6M6D p9 '), ('3-9', '3M9D p9 '))}
    names = {n for study in (paths.STUDY_E0, paths.STUDY_R1, paths.STUDY_R2) for n in plan.names(paths.study(study, 'sets.txt'))}
    coded = [n for n in names if plan.experiment(n) == ('E4', 'coding')]
    claim('durée simulée de E0 selon le GOP (s) : 9-3 ; 6-6 et 3-9 ; celle du coefficient 0,1, des noms de ses jeux (-t168-)',
          '168 ou 169 s selon la structure de groupe d\'images (GOP) … Comme celles-ci, les simulations de la série durent 168 s',
          [(e0['9-3'] == {168.0}, '=', True, 0), (e0['6-6'] == e0['3-9'] == {169.0}, '=', True, 0),
           (len(coded) > 0 and all('-t168-' in n for n in coded), '=', True, 0)])
    load = [v for k, v in simt.items() if re.match(r'p\d+ ', k)]
    claim('durée simulée de la série de la charge : min., max. (s)', 'La durée simulée croît avec la période, de 145 à 415 s',
          [(min(load), '=', 145, 0), (max(load), '=', 415, 0)])
    rows = plan.collect()
    for e, n, sims in (('E0', 36, 720), ('E1', 18, 360), ('E2', 77, 1388), ('E3', 48, 960), ('E4', 33, 660), ('E5', 198, 3960)):
        claim('%s : configurations et simulations (tableau du plan)' % e,
              '& %d (%s) &' % (n, '{:,}'.format(sims).replace(',', ' ')),
              [(sum(r['n'] for r in rows[e].values()), '=', n, 0), (sum(r['sims'] for r in rows[e].values()), '=', sims, 0)],
              source=table('revision-plan'))
    runs = {(r['fire'], r['split'], r['stack']): 0 for r in comparative.rows()}
    for r in comparative.rows():
        runs[r['fire'], r['split'], r['stack']] += 1
    claim('E0 : simulations par pile, feu et GOP, en tout ; graines', '20 par pile, feu et GOP, 720 en tout … Il y a vingt graines par '
          'feu, 60 en tout',
          [(set(runs.values()) == {20}, '=', True, 0), (sum(runs.values()), '=', 720, 0), (data.SEEDS, '=', 60, 0),
           (len(runs) == 36, '=', True, 0)])
    claim('simulations tracées des piles hybride et à agents au GOP 9-3', 'Les 120 simulations de E0 des piles hybride et à agents',
          [(sum(r['sims'] for r in rows['traces'].values()), '=', 120, 0), (rows['traces'][None]['gops'] == {'9-3'}, '=', True, 0),
           (rows['traces'][None]['stacks'] == {'agents', 'hybrid'}, '=', True, 0)])
    conf = {l.split()[0]: l.split() for l in open(paths.CONF, encoding='utf-8') if l.startswith('set_') and l.split()[0] in names}
    claim('propagation de tous les jeux (sets.conf) : exposant, sans terme aléatoire',
          'sans terme aléatoire et d\'exposant \\beta = 3,2 … log-distance d\'exposant 3,2',
          [({v[8] for v in conf.values()} == {'shadowing:%s:0' % EXPONENT}, '=', True, 0), (EXPONENT, '=', 3.2, 1)])
    capture = [v[6].split(':') for v in conf.values()]
    claim('intervalle entre les paquets d\'une image, série de la charge : T/600 de 7 à 30 s (ms)',
          'l\'intervalle entre les paquets d\'une image, T/600, va aussi de 11,7 à 50 ms avec la période',
          [(1000 * 7 / 600, '=', 11.7, 1), (1000 * 30 / 600, '=', 50, 0), (robustness.PERIODS[0] == 'p7' and robustness.PERIODS[-1] == 'p30', '=', True, 0)])
    dead = sum(float(r['declarer_dead']) for r in data.table('break-cases.tsv') or ())
    claim('déclarations faites par un nœud lui-même hors service, simulations tracées (tableau des métriques)',
          'hors les 4 déclarations d\'un nœud lui-même hors service', [(dead, '=', 4, 0)])
    claim('intervalle entre les paquets d\'une image : T/600 dans chaque jeu ; à 9 s (ms)',
          'L\'intervalle entre les paquets d\'une image, T/600, soit 15 ms à 9 s … en paquets émis toutes les 15 ms',
          [(len(capture) > 0 and all(abs(float(c[1]) - float(c[0]) / 600) < 1e-6 for c in capture), '=', True, 0),
           (1000 * 9 / 600, '=', 15, 0)])

    # ----------------------------------------------------------- the fire
    # column 11 of sets.conf, t0:v:x:y of the front, and its knobs
    def fire(number):
        """{what: value} of a fire in the sets of E0, the same in all of them."""
        out = set()
        for n in plan.names(paths.study(paths.STUDY_E0, 'sets.txt')):
            if re.search(r'-fire%s-' % number, n):
                knobs = dict(re.findall(r'(fire\w+)=([^,]+)', conf[n][-1]))
                out.add(tuple(float(x) for x in conf[n][10].split(':')[1:] + [knobs[k] for k in (
                    'firewind', 'firedir', 'firealpha', 'firezone', 'firefail', 'firefailwin')]))
        v, x, y, wind, direction, az, tz, pf, tf = out.pop() if len(out) == 1 else [None] * 9
        return dict(v=v, x=x, y=y, wind=wind, dir=direction, shared=(az, tz, pf, tf))
    fires = {f: fire(n) for f, n in (('F1', ''), ('F2', '2'), ('F3', '3'))}
    for f, text, (wind, v, lb, x, y, direction) in (
            ('F1', '6,00 & 1,30 &4,15 & (180, 180) & \\ang{315}', (6.00, 1.30, 4.15, 180, 180, 315)),
            ('F2', '4,17 & 0,83 & 2,57 & (120, 40) & \\ang{135}', (4.17, 0.83, 2.57, 120, 40, 135)),
            ('F3', '5,56 & 1,11 & 3,70 & (240, 320) & \\ang{315}', (5.56, 1.11, 3.70, 240, 320, 315))):
        x_ = fires[f]
        ratio = 0.936 * math.exp(0.2566 * x_['wind']) + 0.461 * math.exp(-0.1548 * x_['wind']) - 0.397
        claim('%s, jeux de E0 : vent U (m/s), vitesse de tête V (m/s), rapport LB de la loi d\'Anderson, allumage (m), direction '
              '(tableau des feux)' % f, text,
              [(x_['wind'], '=', wind, 2), (x_['v'], '=', v, 2), (ratio, '=', lb, 2), (x_['x'], '=', x, 0), (x_['y'], '=', y, 0),
               (x_['dir'], '=', direction, 0)])
    claim('F2 et F3 : le vent ouvert (km/h, m/s), sa moitié à hauteur de flamme et le dixième en tête',
          'vent ouvert de 8,3 m/s (30 km/h), règle des 10 % … vent ouvert de 11,1 m/s (40 km/h), règle des 10 % … '
          'le vent à hauteur de flamme est la moitié du vent ouvert',
          [(30 / 3.6, '=', 8.3, 1), (40 / 3.6, '=', 11.1, 1)]
          + [(abs(fires[f]['wind'] - k / 3.6 / 2) < 0.005 and abs(fires[f]['v'] - k / 3.6 / 10) < 0.005, '=', True, 0)
             for f, k in (('F2', 30), ('F3', 40))])
    claim('paramètres communs des trois feux, jeux de E0 : AZ (dB/m), TZ et TF (s), PF',
          '\\mathrm{AZ} = 1 dB/m, \\mathrm{TZ} = \\mathrm{TF} = 60 s et \\mathrm{PF} = 0,5',
          [(all(fires[f]['shared'] == (1.0, 60.0, 0.5, 60.0) for f in FIRES), '=', True, 0)])
    lost = [stats.mean(comparative.cells(comparative.rows(), 'loss')[f, '9M3D', 'rules'].values()) for f in FIRES]
    claim('GOP 9-3, pile à règles : perte selon le feu, min., max. (%)', 'Au GOP 9-3, la pile à règles perd ainsi 54,1 à 57,3 % des paquets',
          [(min(lost), '=', 54.1, 1), (max(lost), '=', 57.3, 1)])
    claim('même perte : dans l\'intervalle visé par le choix de la période (%)', 'perde entre 40 et 60 % des paquets au GOP 9-3',
          [(min(lost), '>', 40, 0), (max(lost), '<', 60, 0)])
    oracle = data.read_tsv(paths.results(paths.STUDY_E0, 'oracle.tsv'))
    cut = oracle and [int(r['unreachable']) for r in oracle if re.search(r'GC-PN-0p03-13_p9.*-rules$', r['set'])]
    claim('même perte : paquets perdus sans chemin à l\'émission, 60 simulations', 'toutes ces pertes survenant alors qu\'un chemin existe',
          [(None, '=', 0, 0)] if oracle is None else [(len(cut) == data.SEEDS and sum(cut) == 0, '=', True, 0)])
    worst = [v for (kind, _), v in mes.items() if kind == 'worst']
    claim('oracle, tous les nœuds en panne 60 s avant le front : caméra et puits reliés jusqu\'à la fin, neuf cellules',
          'aucun feu ne sépare la caméra du puits pendant la simulation, même si tous les nœuds tombaient en panne 60 s avant le front',
          [(len(worst) == 9 and all(v in ('connected to 168 s', 'connected to 169 s') for v in worst), '=', True, 0)])
    claim('avance médiane de la panne, TF = 60 s, u uniforme : TF u puis TF u² (s)', 'passe de 30 à 15 s',
          [(60 * 0.5, '=', 30, 0), (60 * 0.5 ** 2, '=', 15, 0)])

    # --------------------------------------------------------- the stacks
    aomdv = lambda name: source(r'^\s*%s = (\S+);' % name, paths.NS2, 'aomdv', 'aomdv.cc')         # noqa: E731
    own = lambda name: source(r'^set %s\s+(\S+)' % name, paths.RADIO)                              # noqa: E731
    # the HELLO interval drawn uniformly between 0.75 and 1.25 times its mean (aomdv_qpv.cc)
    j = re.search(r'interval = ([\d.]+) \* agent->hello_interval_ \+ \(([\d.]+) \* agent->hello_interval_ \* Random::uniform\(\)\)',
                  open(os.path.join(paths.NS2, 'aomdv_qpv', 'aomdv_qpv.cc')).read())
    jitter = (float(j[1]), float(j[1]) + float(j[2]))
    claim('temporisations des piles inter-couches et d\'AOMDV : HELLO (s), demande de route (s) ; tirage de l\'intervalle H (s)',
          'Il envoie un message de voisinage toutes les 5 s au lieu de chaque seconde, et attend au plus 10 s au lieu de 1 avant … '
          'un choix à chaque message de voisinage, en moyenne toutes les 5 s (H tiré entre 3,75 et 6,25 s)',
          [(own('helloInterval_'), '=', 5, 0), (aomdv('hello_interval_') == 1, '=', True, 0), (own('maxRreqTimeout_'), '=', 10, 0),
           (aomdv('max_rreq_timeout_'), '=', 1, 0)] + [(k * own('helloInterval_'), '=', v, 2) for k, v in zip(jitter, (3.75, 6.25))])
    claim('mêmes piles : route active (s), paquets en attente d\'une route',
          'Une route active dure 35 s au lieu de 10, et 16 paquets au lieu de 64 peuvent attendre une route',
          [(own('activeRouteTimeout_'), '=', 35, 0), (aomdv('active_route_timeout_'), '=', 10, 0),
           (source(r'^\s*set val\(ifqlen\) (\d+)', paths.RADIO), '=', 16, 0),
           (source(r'^#define AOMDV_RTQ_MAX_LEN\s+(\d+)', paths.NS2, 'aomdv', 'aomdv_rqueue.h'), '=', 64, 0)])
    claim('chemins gardés, piles inter-couches (2 par niveau, 13 niveaux) et AOMDV',
          'jusqu\'à 26 chemins, 2 par niveau de priorité, contre 3 pour AOMDV',
          [(source(r'aomdv_qpv_max_paths_\s+\[expr (\d+) \* \$maxPrioNb_\]', paths.CAMPAIGN, 'evalvsn.tcl'), '=', 2, 0), (2 * 13, '=', 26, 0),
           (aomdv('aomdv_max_paths_'), '=', 3, 0)])
    delay = {'aomdv': source(r'\*\s*Jitter the sending of broadcast packets by (\d+)ms', paths.NS2, 'aomdv', 'aomdv.cc'),
             'qpv': 1000 * source(r'^\s*double window = (\S+);', paths.NS2, 'aomdv_qpv', 'aomdv_qpv.cc')}
    claim('délai de rediffusion d\'une demande de route, au plus (ms) : piles inter-couches, AOMDV',
          'rediffusent une demande de route après 50 ms au plus, contre 10 … après un délai aléatoire de 50 ms au plus',
          [(delay['qpv'], '=', 50, 0), (delay['aomdv'], '=', 10, 0)])
    default = lambda name: source(r'^\S+ set %s\s+(\S+)' % name, paths.NS2, 'tcl', 'lib', 'ns-default.tcl')    # noqa: E731
    claim('taux d\'apprentissage des agents de l\'accès et de la puissance, des cinq autres ; exploration',
          '\\nu vaut 0,2 pour les agents codés dans la couche d\'accès (accès au canal et puissance) et 0,3 pour les cinq autres, codés dans '
          'celle de routage … avec la probabilité \\varepsilon = 0,1 … taux d\'apprentissage de 0,3 (routage) et 0,2 (accès), exploration '
          'de 0,1',
          [(default('RL_MAC_ALPHA_'), '=', 0.2, 1), (default('RL_ALPHA_'), '=', 0.3, 1), (default('RL_EPSILON_'), '=', 0.1, 1),
           (default('RL_MAC_EPSILON_'), '=', 0.1, 1)])
    claim('profils (0,6 ; 0,2 ; 0,2) et (0,2 ; 0,6 ; 0,2), λ et γ normalisés à 1/255 près : écart de coût au plus',
          '\\tilde\\gamma à 1/255 près … ces deux derniers donnent le même coût à 0,002 près',
          [((0.6 - 0.2) / 255, '=', 0.002, 3), ((0.6 - 0.2) / 255 <= 0.002, '=', True, 0)])
    claim('mémoire : voisins, paquets en attente, mémoire vive de l\'ATmega128L (Kio) (tableau des métriques)',
          '4 voisins et 17 paquets en attente ; 4 Kio sur l\'ATmega128L',
          [(overhead.NEIGHBOURS, '=', 4, 0), (overhead.HELD, '=', 17, 0), (overhead.SRAM_REF / 1024, '=', 4, 0)])
    nodes = {f: {round(float(r['e_total']) / float(r['e_node'])) for r in data.table('overhead.tsv') if r['fire'] == f} for f in FIRES}
    claim('nœuds qui émettent ou reçoivent au moins une trame, chaque pile et chaque GOP : F1, F2, F3 (énergie du réseau sur celle par nœud)',
          'sur les nœuds qui émettent ou reçoivent au moins une trame (99 sous F1 et F2, 98 sous F3)',
          [(nodes == {'F1': {99}, 'F2': {99}, 'F3': {98}}, '=', True, 0)])

    # ---------------------------------------------------------- the video
    # the first interval: the coded image k is source image 1 + 26 (k - 1), and
    # the first two source images are the same (the table of EvalVSN), so the
    # second coded image comes 25 images, 1.00 s, after the first
    claim('vidéo source : images, pas, intervalle (s) ; premier intervalle, les deux premières images identiques (s)',
          '12 des 301 images extraites de la source, dont deux identiques, à 25 images par seconde, soit une sur 26, toutes les 1,04 s après '
          'un premier intervalle de 1,00 s … prises une sur 26 dans la vidéo source, soit une toutes les 1,04 s après un premier intervalle '
          'de 1,00 s … prise au moins 1,00 s plus tôt dans la vidéo source',
          [(numbers(codec['source', 'images'])[0], '=', 301, 0), (numbers(codec['source', 'step'])[0], '=', 26, 0),
           (numbers(codec['source', 'interval'])[0], '=', 1.04, 2), (26 / 25, '=', 1.04, 2), ((26 - 1) / 25, '=', 1.00, 2)])
    frames = {g: (int(codec['bytes', g + ' M frames']), int(codec['bytes', g + ' D frames'])) for g in GOP.values()}
    claim('frames M et D par GOP', 'trois, six et neuf frames M sur douze, structures notées GOP 3-9, 6-6 et 9-3',
          [(frames == {'3-9': (3, 9), '6-6': (6, 6), '9-3': (9, 3)}, '=', True, 0)])
    claim('paquets envoyés par GOP', 'paquets envoyés, 5 738, 5 544 et 5 352 respectivement',
          [(coding.PACKETS[s], '=', n, 0) for s, n in zip(SPLITS, (5738, 5544, 5352))])
    size = {t: [float(codec['bytes', '%s %s mean bytes' % (g, t)]) / 1000 for g in GOP.values()] for t in 'MD'}
    claim('octets moyens d\'une frame D, d\'une frame M, trois GOP : min., max. (milliers)',
          'une frame D en compte en moyenne 35,2 à 35,8 milliers, contre 31,5 à 31,8 milliers pour une frame M',
          [(min(size['D']), '=', 35.2, 1), (max(size['D']), '=', 35.8, 1), (min(size['M']), '=', 31.5, 1), (max(size['M']), '=', 31.8, 1)])
    ratio = numbers(codec['energy', 'AC per pair'])
    claim('énergie du résidu sur celle de l\'image, hors moyenne de bloc, 15 couples : min., max.',
          'Hormis la moyenne de chaque bloc, cette différence a de 1,12 à 1,81 fois l\'énergie de l\'image sur les 15 couples distincts de '
          'frames D et M des trois GOP',
          [(ratio[0], '=', 1.12, 2), (ratio[1], '=', 1.81, 2), (codec['energy', 'AC pairs above 1'] == '15 of 15', '=', True, 0)])
    ref = [x for g in GOP.values() for x in numbers(mes['frames', g + ' refPSNR'])]
    claim('PSNR des frames codées sans perte, trois GOP : min., max. (dB)', 'les frames codées ont un PSNR de 59,6 à 68,3 dB',
          [(min(ref), '=', 59.6, 1), (max(ref), '=', 68.3, 1)])

    # -------------------------------------------------------- the pairing
    calendar = mes['calendar', 'E0']
    claim('calendriers de pannes : graines, simulations, calendriers par graine',
          'Sur les 720 simulations, chacune des 60 graines donne un seul calendrier de pannes',
          [(calendar == '60 seeds over 720 runs, at most 1 schedule(s) per seed', '=', True, 0)])

    # ---------------------------------------------------------- the seeds
    # The conclusion of a test: 0 no difference detected (Holm's p within its
    # family at 0.05), 1 above, -1 below.
    def verdict(e):
        return 0 if not stats.detected(e) else 1 if e.mean > 0 else -1

    # The preliminary trial of the link-break agent: ten simulations under F1
    # at GOP 9-3, on the seeds r01 to r10 that E0 reuses (section 2.6, the
    # article's own account of it). Without them,
    # each family of E0 (the per-GOP and per-cell families of
    # analysis/assumptions.blocks) is recomputed, Holm within it as in E0.
    rs = comparative.rows()
    trial = {('F1', 'r%02d' % i) for i in range(1, 11)}
    kept = [r for r in rs if not (r['split'] == '9M3D' and (r['fire'], r['realisation']) in trial)]

    def e0(rows, drop):
        """The families of E0 on rows, the trial's seeds dropped from GOP 9-3
        of revision.tsv when drop: {(metric, a, b): {split: Estimate}}, then
        {(a, b): {(fire, split): Estimate}}."""
        psnr, m1 = comparative.cells(rows, 'psnr'), comparative.cells(rows, 'm1loss')
        gops = {('psnr', a, b): comparative.paired_gops(psnr, a, b) for a, b in (('hybrid', 'rules'), ('agents', 'rules'), ('hybrid', 'agents'))}
        gops['m1loss', 'hybrid', 'rules'] = comparative.paired_gops(m1, 'hybrid', 'rules')
        for m, pairs in (('usable', (('hybrid', 'rules'), ('agents', 'rules'))), ('usable25', (('hybrid', 'rules'),)),
                         ('usable31', (('hybrid', 'rules'),)), ('delay_mean', (('hybrid', 'rules'),)), ('late', (('hybrid', 'rules'),))):
            for a, b in pairs:
                gops[m, a, b] = stats.family({s: stats.paired({k: v for k, v in quality.values(a, m, s).items()
                                                               if not (drop and s == '9M3D' and k in trial)},
                                                              quality.values(b, m, s)) for s in SPLITS})
        return gops, {(a, b): comparative.paired_cells(psnr, a, b) for a, b in comparative.PAIRS}

    (full_gops, full_cells), (cut_gops, cut_cells) = e0(rs, False), e0(kept, True)
    cell = ('F1', '9M3D')
    hr = cut_cells['hybrid', 'rules'][cell]
    claim('E0 sans les dix graines de l\'essai préliminaire (F1, GOP 9-3, r01 à r10) : conclusion de chaque test des dix familles par GOP, '
          'signe des quatre écarts de la cellule F1 au GOP 9-3 ; écart hybride − règles de cette cellule, Holm sur neuf cellules, non détecté',
          'Sans elles, les conclusions de E0 à ce GOP, sur les trois feux, ne changent pas. Dans la cellule F1 au GOP 9-3, il reste dix '
          'graines, et les écarts gardent leur signe. Aucune différence statistiquement significative n\'y a été détectée entre les piles '
          'hybride et à règles (+1,60 dB [0,38 ; 2,82], p = 0,078',
          [(len(cut_gops) == 10 and len(cut_cells) == 4, '=', True, 0),
           (all(verdict(full_gops[k][s]) == verdict(cut_gops[k][s]) for k in full_gops for s in SPLITS), '=', True, 0),
           (all((full_cells[k][cell].mean > 0) == (cut_cells[k][cell].mean > 0) for k in full_cells), '=', True, 0),
           (hr.n == 10 and verdict(hr) == 0 and verdict(full_cells['hybrid', 'rules'][cell]) == 1, '=', True, 0)]
          + gap_checks(hr, '+1,60 dB [0,38 ; 2,82], p = 0,078'))

    # The interim analysis of E0: its sets ran with ten seeds per fire (r01 to
    # r10), then were completed to twenty (data/sensors-rl/0-comparative,
    # "Size"); the ten added seeds alone (r11 to r20), hybrid - rules per GOP
    # over the three fires, Holm over the three GOPs as in E0.
    ten = [r for r in rs if int(r['realisation'][1:]) <= 10]
    added = [r for r in rs if int(r['realisation'][1:]) > 10]
    widths = {k: comparative.half_width(v.values()) for k, v in comparative.cells(ten, 'psnr').items()}
    claim('E0 à dix graines par feu (r01 à r10) : demi-largeur de l\'intervalle à 95 % d\'une moyenne de cellule, quatre piles, neuf '
          'cellules : min., max. (dB, à l\'unité)',
          'l\'intervalle d\'une moyenne de cellule valait \\pm 1 à \\pm2 dB',
          [(len(widths) == 36 and all(len(v) == 10 for v in comparative.cells(ten, 'psnr').values()), '=', True, 0),
           (min(widths.values()), '=', 1, 0), (max(widths.values()), '=', 2, 0)])
    for metric, name, written in (
            ('psnr', 'PSNR (dB)', 'L\'écart de PSNR va de +1,63 à +1,99 dB (intervalles de 0,92 à 2,98 dB, p < 0,001'),
            ('m1loss', 'perte du niveau M1 (points)',
             'Celui de la perte M1 va de −10,4 à −4,3 points (intervalles de −16,3 à −0,5 point, p ≤ 0,029')):
        es = comparative.paired_gops(comparative.cells(added, metric), 'hybrid', 'rules')
        whole = comparative.paired_gops(comparative.cells(rs, metric), 'hybrid', 'rules')
        claim('E0, les dix graines ajoutées seules (r11 à r20), %s, pile hybride − règles, Holm sur trois GOP : écarts min., max. ; p max. ; '
              'bornes ; la conclusion de chaque GOP, celle des vingt graines' % name,
              'Les graines ajoutées, seules, donnent les mêmes conclusions pour la pile hybride face à la pile à règles à chaque GOP … '
              + written,
              range_checks(list(es.values()), written)
              + [(all(e.n == 30 for e in es.values()), '=', True, 0),
                 (all(verdict(es[s]) == verdict(whole[s]) != 0 for s in SPLITS), '=', True, 0)])

    # ----------------------------------------------------------- the rule
    # The choice rule of 2.6: the access-only stack is retained over the rule
    # stack if its PSNR gain is detected (Holm within its series, the
    # coefficient 0.1 a single test), then the hybrid stack over the stack so
    # retained if its own gain is; otherwise the simpler stack. Its domain is
    # T = 9 s on the 40 m grid, at the three GOPs and the coefficient 0.01:
    # the load series at 9 s, the fire variants, the scenario variants but the
    # 30 m grid, and E2 at the three GOPs.
    fam = access_analysis.families()
    over_rules = dict(robustness.period_family('hybrid', 'rules', 'psnr'))
    over_rules.update(robustness.scenario_family('gap', 'hybrid-rules', 'psnr'))

    def gain(e):
        return e is not None and verdict(e) == 1

    def retained(series, key):
        if gain(fam[series, 'access - rules'][key]):
            return 'hybrid' if gain(fam[series, 'hybrid - access'][key]) else 'access'
        e = over_rules.get(key) if series in ('load', 'scenario') else None
        return None if e is None else 'hybrid' if gain(e) else 'rules'

    levels = {(s, lv.key): lv for s, lvs in access_analysis.SERIES.items() for lv in lvs}
    inside = [k for k, lv in levels.items() if lv.period == 'p9' and lv.dist == '40' and lv.variant != 'q01']
    outside = {k: retained(*k) for k in levels if k not in inside}
    e2 = {s: (round2_analysis.access_gops('access - rules')[s], round2_analysis.access_gops('hybrid - access')[s]) for s in SPLITS}
    claim('règle de choix de 2.6 : pile retenue à chaque niveau des séries de E4 et E5 hors de son domaine (7, 12, 18 et 30 s ; grille de '
          '30 m ; débit égal ; coefficient 0,1) ; la pile à accès seul dans le domaine (9 s, variantes du feu, quatre variantes du '
          'scénario, E2 aux trois GOP)',
          'Hors de ce domaine, elle retiendrait la pile à règles à 7, 18 et 30 s et sur la grille de 30 m, et la pile hybride au '
          'coefficient 0,1',
          [(outside == {('load', 'p7'): 'rules', ('load', 'p12'): 'access', ('load', 'p18'): 'rules', ('load', 'p30'): 'rules',
                        ('scenario', 'j8'): 'rules', ('rate', '3M9D'): 'access', ('rate', '6M6D'): 'access',
                        ('coding', 'q01'): 'hybrid'}, '=', True, 0),
           (len(inside) == 12 and all(retained(*k) == 'access' for k in inside), '=', True, 0),
           (all(gain(a) and not gain(h) for a, h in e2.values()), '=', True, 0)])
