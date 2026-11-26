"""Numbers the article quotes from the sets rather than from one row per
simulation: methode-mesures.tsv (the methods' numbers: simulated time and
nodes out of service, the worst-case connectivity, correlations, frame sizes,
packets, failure schedules, the deployments and their links) and
overhead.tsv (the radio energy per set, read from the sets' graphs)."""
import glob
import math
import os
import statistics
import sys
from collections import deque

import fire_oracle as fo

from ..common import data, paths, stats

FIRES = (('fire', 'F1'), ('fire2', 'F2'), ('fire3', 'F3'))
GC = (('0p01597', '3-9'), ('0p02525', '6-6'), ('0p03', '9-3'))


def _fire_runs(pattern):
    return sorted(glob.glob(os.path.join(paths.SETS, pattern, 'r[0-9][0-9]', '*', 'fire-nodes.dat')))


def _hops(adj, s, t):
    """The fewest hops from s to t in an adjacency list."""
    seen, q = {s: 0}, deque([s])
    while q:
        a = q.popleft()
        for b in adj[a]:
            if b not in seen:
                seen[b] = seen[a] + 1
                q.append(b)
    return seen.get(t)


def methods():
    """methode-mesures.tsv: kind, key, value, source."""
    rows = []

    def add(kind, key, value, source):
        # a file under the sets folder is named from there: an absolute path is this machine's
        if os.path.isabs(source):
            source = os.path.relpath(source, paths.SETS)
        rows.append((kind, key, value, source))

    def out_of_service(name):
        runs = _fire_runs(name)
        simts, out = set(), []
        for path in runs:
            params, nodes = fo.read_fire_nodes(path)
            simt = float(params['simt'])
            simts.add(simt)
            out.append(sum(1 for nd in nodes if nd[4] < simt))
        return runs, simts, out

    # load: simulated time and nodes out of service before the end, per T and fire
    for per in ('p7', 'p9', 'p12', 'p18', 'p30'):
        for f, F in FIRES:
            name = 'set_AOMDV_QPV_GC-PN-0p03-13_%s-n100-d40-%s-rules%s' % (per, f, '' if per == 'p9' else '-s10')
            runs, simts, out = out_of_service(name)
            add('load', '%s %s simt' % (per, F), '/'.join('%g' % s for s in sorted(simts)), name)
            add('load', '%s %s hors-service' % (per, F), '%.1f' % statistics.mean(out), '%s, %d runs' % (name, len(runs)))

    # volume: the same at equal mean packet rate (T = 9.32 and 9.65 s), against the same GOP at T = 9 s
    for gc, g, per in (('0p02525', '6M6D', 'p9r32'), ('0p01597', '3M9D', 'p9r65')):
        for tag, suffix in (('p9', ''), (per, '-s10')):
            for f, F in FIRES:
                name = 'set_AOMDV_QPV_GC-PN-%s-13_%s-n100-d40-%s-rules%s' % (gc, tag, f, suffix)
                runs, simts, out = out_of_service(name)
                add('volume', '%s %s %s simt' % (g, tag, F), '/'.join('%g' % s for s in sorted(simts)), name)
                add('volume', '%s %s %s hors-service' % (g, tag, F), '%.1f' % statistics.mean(out), '%s, %d runs' % (name, len(runs)))

    # worst: every node fails TF = 60 s before its front
    for f, F in FIRES:
        for gc, g in GC:
            path = _fire_runs('set_AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-%s-rules' % (gc, f))[0]
            params, nodes = fo.read_fire_nodes(path)
            simt = float(params['simt'])
            worst = [(i, x, y, fr, min(fr - 60.0, d)) for (i, x, y, fr, d) in nodes]
            o = fo.Oracle(params, worst)
            t, cut = 0.0, None
            while t <= simt + 1e-9:
                if not o.reachable(t):
                    cut = t
                    break
                t += fo.GRID
            add('worst', '%s %s' % (F, g), 'connected to %g s' % simt if cut is None else 'cut at %.1f s' % cut, path)

    # corr and calib, from comparative.tsv
    comp = data.read_tsv('comparative.tsv')
    for label, sub in (('720', comp), ('540 cross-layer', [r for r in comp if r['stack'] != 'aomdv'])):
        ps = [float(r['psnr']) for r in sub]
        for k in ('m1loss', 'm1to3loss', 'mloss', 'dloss', 'loss'):
            add('corr', '%s %s' % (label, k), '%.2f' % stats.pearson([float(r[k]) for r in sub], ps), 'comparative.tsv')
    for _, g in GC:
        sp = {'3-9': '3M9D', '6-6': '6M6D', '9-3': '9M3D'}[g]
        for _, F in FIRES:
            v = statistics.mean(float(r['loss']) for r in comp if r['stack'] == 'rules' and r['split'] == sp and r['fire'] == F)
            add('calib', 'rules %s %s loss' % (g, F), '%.2f' % v, 'comparative.tsv')
        for k in ('m1loss', 'mloss', 'dloss'):
            v = statistics.mean(float(r[k]) for r in comp if r['stack'] == 'aomdv' and r['split'] == sp)
            add('calib', '%s %s %s' % ('aomdv', g, k), '%.1f' % v, 'comparative.tsv')

    # frames: sizes by type and reference PSNR, fire video
    for gc, g in GC:
        path = glob.glob(os.path.join(paths.SETS, 'set_AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-fire-rules' % gc, 'encoding', '*', 'st-frame.dat'))[0]
        size = {'M': [], 'D': []}
        ref = []
        for l in open(path):
            if l.startswith('#') or not l.strip():
                continue
            v = l.rstrip('\n').split('\t')
            size[v[1]].append(int(v[2]))
            ref.append(float(v[3]))
        add('frames', '%s M' % g, '%d frames, %.0f bytes' % (len(size['M']), statistics.mean(size['M'])), path)
        add('frames', '%s D' % g, '%d frames, %.0f bytes' % (len(size['D']), statistics.mean(size['D'])), path)
        add('frames', '%s refPSNR' % g, '%.1f to %.1f dB' % (min(ref), max(ref)), path)

    # packets: packets of the fire video per GOP, from the encodings of the main study
    for gc, g in GC:
        path = glob.glob(os.path.join(paths.SETS, 'set_AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-fire-rules' % gc, 'encoding', '*', 'st-priority.dat'))[0]
        n = sum(1 for l in open(path) if l.strip() and not l.startswith('#'))
        add('packets', g, '%d packets' % n, path)

    # calendar: failure schedules (front and failure instant of every node) per
    # seed (fire, realisation) over the four stacks and three GOPs of the main study
    cals, nruns = {}, 0
    for f, F in FIRES:
        for gc, g in GC:
            for stack in ('AOMDV_GC-PN-%s-13_p9-n100-d40-%s-pq', 'AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-%s-rules',
                          'AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-%s-hybrid', 'AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-%s-agents'):
                for path in _fire_runs('set_' + stack % (gc, f)):
                    r = os.path.basename(os.path.dirname(os.path.dirname(path)))
                    params, nodes = fo.read_fire_nodes(path)
                    cals.setdefault((F, r), set()).add(tuple((nd[0], nd[3], nd[4]) for nd in nodes))
                    nruns += 1
    add('calendar', 'E0', '%d seeds over %d runs, at most %d schedule(s) per seed'
        % (len(cals), nruns, max(len(v) for v in cals.values())),
        'set_*_p9-n100-d40-{fire,fire2,fire3}-{pq,rules,hybrid,agents}, fire-nodes.dat')

    # videos: packets of the other videos of the scenario series
    for video, gc in (('forest', '0p01597'), ('smoke', '0p15671')):
        path = glob.glob(os.path.join(paths.SETS, 'set_AOMDV_QPV_GC-PN-%s-13_p9-n100-d40-fire-rules-%s-s10' % (gc, video), 'encoding', '*', 'st-priority.dat'))[0]
        n = sum(1 for l in open(path) if l.strip() and not l.startswith('#'))
        frames = glob.glob(os.path.join(os.path.dirname(path), 'st-frame.dat'))[0]
        types = [l.split('\t')[1] for l in open(frames) if l.strip() and not l.startswith('#')]
        add('videos', video, '%d packets, %d M and %d D frames' % (n, types.count('M'), types.count('D')), path)

    # variants: nodes out of service before the end, per scenario variant and fire, rules stack
    for suffix, d in (('j8', '30'), ('v15', '40')):
        for f, F in FIRES:
            name = 'set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d%s-%s-rules-%s-s10' % (d, f, suffix)
            runs = _fire_runs(name)
            out = []
            for path in runs:
                params, nodes = fo.read_fire_nodes(path)
                out.append(sum(1 for nd in nodes if nd[4] < float(params['simt'])))
            add('variants', '%s %s hors-service' % (suffix, F), '%.1f' % statistics.mean(out), '%s, %d runs' % (name, len(runs)))

    # topo: links above the floor at full power (the oracle's budget, no fire),
    # by grid offset, and the fewest hops from camera to sink
    for label, pattern in (('40 m', 'set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-fire-rules'),
                           ('30 m', 'set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d30-fire-rules-j8-s10')):
        files = _fire_runs(pattern.replace('AOMDV_QPV_', 'AOMDV*_').replace('-fire-', '-fire*-').replace('-rules', '-*', 1))
        deployments = {tuple((x, y) for _, x, y, _, _ in fo.read_fire_nodes(f)[1]) for f in files}
        params, nodes = fo.read_fire_nodes(files[0])
        orc = fo.Oracle(params, nodes)
        n = len(nodes)
        side = int(round(math.sqrt(n)))
        adj = [[b for b in range(n) if b != a and orc.margin0 - orc.pathloss[a][b] >= 0] for a in range(n)]
        cls = {}
        for a in range(n):
            for b in adj[a]:
                if a < b:
                    k = tuple(sorted((abs(a // side - b // side), abs(a % side - b % side))))
                    cls[k] = cls.get(k, 0) + 1
        add('topo', '%s deployments' % label, '%d over %d runs' % (len(deployments), len(files)), pattern)
        add('topo', '%s grid links' % label, '%d of %d' % (cls.get((0, 1), 0), 2 * side * (side - 1)), pattern)
        add('topo', '%s diagonal links' % label, '%d of %d' % (cls.get((1, 1), 0), 2 * (side - 1) ** 2), pattern)
        add('topo', '%s two-step links' % label, '%d' % cls.get((0, 2), 0), pattern)
        add('topo', '%s fewest hops' % label, '%d' % _hops(adj, orc.camera, orc.sink), pattern)
        step = float(label.split()[0])
        add('topo', '%s largest displacement' % label, '%.2f m on x, %.2f m on y' % (
            max(abs(x - (i // side) * step) for i, x, _, _, _ in nodes),
            max(abs(y - (i % side) * step) for i, _, y, _, _ in nodes)), pattern)
    beta = float(params['plexp'])
    for d in (30.0, 40.0, 30.0 * math.sqrt(2)):
        add('topo', 'margin %.1f m link' % d, '%+.1f dB' % (orc.margin0 - 10 * beta * math.log10(d)), 'oracle link budget')
    add('topo', '30 m against 40 m', '%.1f dB stronger' % (10 * beta * math.log10(40.0 / 30.0)), 'oracle link budget')

    out = paths.data('methode-mesures.tsv')
    with open(out, 'w') as f:
        f.write('# compiled by code/analysis/sensors_rl/compile/measures.py from sets/ and data/sensors-rl/article/comparative.tsv\n')
        f.write('kind\tkey\tvalue\tsource\n')
        for r in rows:
            f.write('\t'.join(r) + '\n')
    print('%s: %d numbers' % (os.path.relpath(out), len(rows)))


# --------------------------------------------------------------- overhead.tsv

ENERGY_SPLIT = {'0p03': '9M3D', '0p02525': '6M6D', '0p01597': '3M9D'}
ENERGY_FIRE = {'fire': 'F1', 'fire2': 'F2', 'fire3': 'F3'}
# stack, the set's name, the arm of revision.tsv its control messages are read
# from (the traced arms, and the access-only stack's arm of study 10); the
# access-only stack has its sets at GOP 9-3 only, the series
# of study 11 at the two other GOPs not being in this file
ENERGY_STACKS = (('pq', 'set_AOMDV_GC-PN-{gc}-13_p9-n100-d40-{fire}-pq', None),
                 ('pq-ctl', 'set_AOMDV_GC-PN-{gc}-13_p9-n100-d40-{fire}-pq-ctl-s10', 'pq-ctl'),
                 ('pq-tuned', 'set_AOMDV_GC-PN-{gc}-13_p9-n100-d40-{fire}-pq-tuned-s10', 'pq-tuned'),
                 ('rules', 'set_AOMDV_QPV_GC-PN-{gc}-13_p9-n100-d40-{fire}-rules', None),
                 ('agents', 'set_AOMDV_QPV_GC-PN-{gc}-13_p9-n100-d40-{fire}-agents', 'agents-tr'),
                 ('hybrid', 'set_AOMDV_QPV_GC-PN-{gc}-13_p9-n100-d40-{fire}-hybrid', 'hybrid-tr'),
                 ('access', 'set_AOMDV_QPV_GC-PN-{gc}-13_p9-n100-d40-{fire}-rules-onlyA-s10', 'rules-onlyA'))
ENERGY_COLS = ('stack', 'fire', 'split', 'n', 'e_node', 'e_node_sd', 'e_total', 'e_total_sd', 'lifetime', 'lifetime_sd', 'e_max')
OVERHEAD_HEAD = ('# compiled by code/analysis/sensors_rl/compile/measures.py from the sets\' graphs (setGraphs.pl): '
                 'radio energy per simulation, means over n realisations; e_max = (1 - lifetime/100) x %g J')
# The rows compiled once the raw sets were purged (data/README.md), from the
# sets' graphs kept in a light archive, read by data --only overhead --sets
# with SETS_DIR on an extraction of the archive; the first line of the file
# names where they come from. The archive holds the graphs as setGraphs.pl
# wrote them: recompiled from it the same way, the rules row of F1 and the
# hybrid row of F2 at GOP 9-3 are identical to the rows stored before.
ARCHIVED = {'access': 'the access rows (study 10, GOP 9-3 only, sets *-{fire,fire2,fire3}-rules-onlyA-s10) were compiled '
                      'on 23 November 2026 by the same function from their graphs in the light archive '
                      'sensors-rl-light-2026-11-21.tar.xz (sha256 5b8130446d5ef45885993ef3d27373a942825c2500e06d8ef0a63037433a235f)',
            'pq-tuned': 'the pq-tuned rows (study 10, AOMDV with cross-layer timers, GOP 9-3 only, sets '
                        '*-{fire,fire2,fire3}-pq-tuned-s10) were compiled on 23 November 2026 the same way from the same archive'}


def read_dat(path):
    """mean, standard deviation and count of a set's graphs/<metric>/<metric>.dat."""
    v = open(path).read().split()
    return float(v[1]), float(v[2]), int(v[3])


def energy_of(setdir):
    """(energy per node, per network, life time) of a set's graphs, each as
    (mean, sd, n); None when the set has no energy graphs."""
    g = os.path.join(setdir, 'graphs')
    try:
        return tuple(read_dat(os.path.join(g, m, m + '.dat')) for m in ('Energy Consumption', 'Power Consumption', 'Life Time'))
    except (OSError, IndexError, ValueError):
        return None


def energy_row(setdir, stack, f, split, e0):
    """The line of overhead.tsv of one set, None when the set has no energy
    graphs."""
    e = energy_of(setdir)
    if e is None:
        return None
    en, tot, lt = e
    r = (stack, f, split, en[2], en[0], en[1], tot[0], tot[1], lt[0], lt[1], (1.0 - lt[0] / 100.0) * e0)
    return '\t'.join(str(x) if isinstance(x, (str, int)) else '%.6f' % x for x in r)


def overhead(only=None):
    """overhead.tsv: per set at the three GOPs, the radio energy per node and
    per network and the life time, means over the realisations; the busiest
    node's consumption is (1 - life time) x the initial energy. With only
    (data --only overhead --sets NAME ...), only the sets named are read, and
    every other row is kept as the file stores it, so that the sets read from
    a light archive once the raw sets were purged join the file (ARCHIVED);
    a set named that has no energy graphs stops the step."""
    e0 = data.radio()['initeng']
    names = {pattern.format(gc=gc, fire=fire): (stack, f, split)
             for gc, split in ENERGY_SPLIT.items() for fire, f in ENERGY_FIRE.items() for stack, pattern, _ in ENERGY_STACKS}
    unknown = [s for s in only or () if s not in names]
    if unknown:
        sys.exit('overhead: not a set of ENERGY_STACKS: %s' % ' '.join(unknown))
    out = paths.data('overhead.tsv')
    stored = {}
    if only:
        lines = [l.rstrip('\n') for l in open(out) if not l.startswith('#') and l.strip()]
        if lines[0].split('\t') != list(ENERGY_COLS):
            sys.exit('overhead.tsv: its columns are not ENERGY_COLS; not rewritten')
        stored = {tuple(l.split('\t')[:3]): l for l in lines[1:]}
    rows, read = [], 0
    for name, key in names.items():
        if only and name not in only:
            if key in stored:
                rows.append(stored.pop(key))
            continue
        line = energy_row(os.path.join(paths.SETS, name), key[0], key[1], key[2], e0)
        if line is None:
            if only:
                sys.exit('overhead: %s has no energy graphs under %s; overhead.tsv not rewritten' % (name, paths.SETS))
            print('  %s: no energy graphs, left out' % name)
            continue
        stored.pop(key, None)
        rows.append(line)
        read += 1
    if stored:
        sys.exit('overhead.tsv holds rows of no set of ENERGY_STACKS (%s); not rewritten' % ' '.join('-'.join(k) for k in stored))
    held = {l.split('\t')[0] for l in rows}
    notes = [ARCHIVED[s] for s in ARCHIVED if s in held]
    with open(out + '.tmp', 'w') as fh:
        fh.write(OVERHEAD_HEAD % e0 + ''.join('; ' + n for n in notes) + '\n')
        fh.write('\t'.join(ENERGY_COLS) + '\n')
        for l in rows:
            fh.write(l + '\n')
    os.replace(out + '.tmp', out)
    print('%s: %d sets, %d read now' % (os.path.relpath(out), len(rows), read))
