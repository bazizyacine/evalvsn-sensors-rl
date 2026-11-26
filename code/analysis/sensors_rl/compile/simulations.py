"""One row per simulation, compiled from the sets of studies 09, 10 and 11:
comparative.tsv (the main study), fire-map-F1..F3.tsv (the node schedule of
each fire), revision.tsv (quality, delay, neighbour-death declarations and
control traffic of every arm of studies 09 and 10), round2.tsv (the same
columns, the sets of study 11), frames.tsv (one row per image of the load
series) and oracle-s10.tsv (the packets lost while no path of live nodes
joined camera and sink).

revision.tsv is frozen as the first revision deposited it: the routing
counters completed since then for study 09 and the twelve sets of the
coefficient 0.1 would change it, and the claims count its arms (P34). The
second round's rows go to round2.tsv, which keeps the rows of a set once
stored, so that the set can be purged; its routing cells left empty (no
events.tsv when the set was compiled) are filled from study 11's
results/runs.tsv."""
import csv
import glob
import os
import sys

import fire_oracle
import sets

from ..common import paths

FIRES = (('F1', 'fire', '180 180', '1.3', '6', '315'),
         ('F2', 'fire2', '120 40', '0.83', '4.17', '135'),
         ('F3', 'fire3', '240 320', '1.11', '5.56', '315'))
SPLITS = (('3M9D', 'GC-PN-0p01597-13'), ('6M6D', 'GC-PN-0p02525-13'), ('9M3D', 'GC-PN-0p03-13'))
STACKS = (('aomdv', 'set_AOMDV_{c}_p9-n100-d40-{f}-pq'), ('rules', 'set_AOMDV_QPV_{c}_p9-n100-d40-{f}-rules'),
          ('agents', 'set_AOMDV_QPV_{c}_p9-n100-d40-{f}-agents'), ('hybrid', 'set_AOMDV_QPV_{c}_p9-n100-d40-{f}-hybrid'))
FLOOR_DB = 28.0
HEADER = {
    'comparative.tsv': '# compiled by code/analysis/sensors_rl/compile/simulations.py from sets/ (study 09)',
    'fire-map': '# compiled by code/analysis/sensors_rl/compile/simulations.py from the rule stack, 9M/3D, r01',
    'revision.tsv': '# compiled by code/analysis/sensors_rl/compile/simulations.py from sets/ (studies 09 and 10)',
    'frames.tsv': '# compiled by code/analysis/sensors_rl/compile/simulations.py from sets/ (studies 09 and 10, GOP 9-3, T = 7, 9 and 12 s)',
    'oracle-s10.tsv': '# compiled by code/analysis/sensors_rl/compile/simulations.py from sets/ (study 10) with code/metrics/fire_oracle.py',
    'round2.tsv': '# compiled by code/analysis/sensors_rl/compile/simulations.py from sets/ (study 11): %d of %d sets',
}


def _complete(setdir):
    """The realisations of a set once all of them are harvested, else None."""
    reals = sets.realisations(setdir)
    if not reals or any(not sets.first(r, 'sim', 'mt.dat') for r in reals):
        return None
    return reals


def _mt_row(rdir):
    return [l for l in open(sets.first(rdir, 'sim', 'mt.dat')) if not l.startswith('#') and l.strip()][0].split('\t')


def comparative():
    """comparative.tsv: fire, split, stack, realisation, PSNR, the losses and
    the share of the packets the oracle finds recoverable."""
    rows, missing = [], []
    for label, tok, *_ in FIRES:
        for split, codec in SPLITS:
            for stack, pat in STACKS:
                name = pat.format(c=codec, f=tok)
                reals = _complete(os.path.join(paths.SETS, name))
                if reals is None:
                    missing.append(name)
                    continue
                for r in reals:
                    v = _mt_row(r)
                    m1, m13, dl = sets.level_losses(r)
                    orc = fire_oracle.analyse(r)
                    rec = 100.0 * orc['rec'] / orc['sent'] if orc else float('nan')
                    rows.append((label, split, stack, os.path.basename(r), float(v[0]), float(v[4]), float(v[5]),
                                 m1, m13, dl, rec))
    out = paths.data('comparative.tsv')
    with open(out, 'w') as f:
        f.write(HEADER['comparative.tsv'] + '\n')
        f.write('fire\tsplit\tstack\trealisation\tpsnr\tloss\tmloss\tm1loss\tm1to3loss\tdloss\trecoverable\n')
        for row in rows:
            f.write('%s\t%s\t%s\t%s\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\n' % row)
    print('%d realisations written to %s; %d sets not complete' % (len(rows), os.path.relpath(out), len(missing)))
    for label, tok, ign, head, wind, wdir in FIRES:
        fire_map(label, tok, ign, head, wind, wdir)


def fire_map(label, tok, ign, head, wind, wdir):
    """fire-map-<label>.tsv: each node's position, front and death instants in
    the first simulation of the rule stack at GOP 9-3."""
    src = glob.glob(os.path.join(paths.SETS, 'set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-%s-rules' % tok, 'r01', '*', 'fire-nodes.dat'))
    if not src:
        return
    rows = [l.split() for l in open(src[0]) if not l.startswith('#') and l.strip()]
    simt = [l for l in open(src[0]) if l.startswith('# prop')][0].split('simt')[1].split()[0]
    path = paths.data('fire-map-%s.tsv' % label)
    with open(path, 'w') as f:
        f.write(HEADER['fire-map'] + '\n')
        f.write('# ignition %s t0 0 head_speed %s wind %s wind_dir %s zone_s 60 detection 60 simt %s camera 0 sink 99\n'
                % (ign, head, wind, wdir, simt))
        f.write('id\tx\ty\tfront\tdeath\n')
        for r in rows:
            f.write('%s\t%s\t%s\t%.3f\t%.3f\n' % (r[0], r[1], r[2], float(r[3]), float(r[4])))
    print('fire map written to %s' % os.path.relpath(path))


# -------------------------------------------------------------- revision.tsv

REVISION_COLS = ('arm', 'fire', 'split', 'period', 'dist', 'realisation', 'psnr', 'ssim', 'loss', 'm1loss', 'usable',
                 'delay_mean', 'delay_p95', 'late', 'declared', 'false_declared', 'rreq_all', 'rerr', 'rrep', 'hello',
                 'usable25', 'usable31')


def usable(rdir, floor=FLOOR_DB):
    """Images of the realisation whose PSNR at the sink reaches the floor."""
    n = 0
    for f in glob.glob(os.path.join(rdir, '*', 'sim', 'rt-frame.dat')):
        for line in open(f):
            if line.startswith('#') or not line.strip():
                continue
            if float(line.split('\t')[1]) >= floor:
                n += 1
    return n


def timing(rdir):
    """Mean and 95th percentile of the delay, and the share of the received
    packets that arrive after the next image was captured."""
    st = glob.glob(os.path.join(rdir, '*', 'ns2_st-packet.dat')) or glob.glob(os.path.join(rdir, '*', 'st-packet.dat'))
    rt = glob.glob(os.path.join(rdir, '*', 'sim', 'rt-packet.dat')) or glob.glob(os.path.join(rdir, '*', 'rt-packet.dat'))
    if not st or not rt:
        return '', '', ''
    sent = {k: v[:2] for k, v in sets.read_packets(st[0]).items()}
    got = {k: v[:2] for k, v in sets.read_packets(rt[0]).items()}
    first = {}
    for t, f in sent.values():
        first[f] = min(t, first.get(f, t))
    frames = sorted(first)
    period = (first[frames[-1]] - first[frames[0]]) / (len(frames) - 1) if len(frames) > 1 else 0.0
    delays, late = [], 0
    for seq, (t, _) in got.items():
        if seq not in sent:
            continue
        ts, f = sent[seq]
        delays.append(t - ts)
        if t > first.get(f + 1, first[f] + period):
            late += 1
    if not delays:
        return '', '', ''
    delays.sort()
    return (sum(delays) / len(delays), delays[int(0.95 * (len(delays) - 1))], 100.0 * late / len(delays))


# What a declaration of a dead neighbour hits, by the oracle's link budget,
# and the inputs of a realisation's oracle: code/metrics/fire_oracle.py.
link_case = fire_oracle.link_case
oracle_of = fire_oracle.oracle_of


def declarations(rdir):
    """Neighbours declared dead during the alarm, and among them those still
    alive with a link above the floor at that instant (the oracle's verdict)."""
    run = oracle_of(rdir)
    if run is None:
        return '', ''
    tr, _, nodes, orc = run
    cases = [link_case(orc, nodes, t, a, b) for t, a, b in sets.deaths(tr)]
    return len(cases), cases.count('budget')


def events(name):
    """The routing counters of a set, from its events.tsv or from study 09's
    results/routing.tsv."""
    for path in (os.path.join(paths.SETS, name, 'events.tsv'),
                 paths.results(paths.STUDY_E0, 'routing.tsv')):
        if os.path.exists(path):
            rows = [r for r in csv.DictReader((l for l in open(path) if not l.startswith('#')), delimiter='\t')
                    if r['set'] == name]
            if rows:
                return {r['realisation']: r for r in rows}
    return {}


def revision_rows(name):
    """The rows of revision.tsv (REVISION_COLS) of one set, as tuples."""
    arm, fire, split, period, dist = sets.keys(name)
    ev = events(name)
    rows = []
    for r in sets.realisations(os.path.join(paths.SETS, name)):
        real = os.path.basename(r)
        mt = sets.read_mt(r)
        if mt is None:
            continue
        dm, dp, late = timing(r)
        dec, fal = declarations(r)
        e = ev.get(real, {})
        rows.append((arm, fire, split, period, dist, real, mt['psnr'], mt['ssim'], mt['pktLoss'], mt['pktlossM1'],
                     usable(r), dm, dp, late, dec, fal, e.get('rreq_all', ''), e.get('rerr', ''),
                     e.get('rrep', ''), e.get('hello', ''), usable(r, 25.0), usable(r, 31.0)))
    return rows


def _line(row):
    return '\t'.join('%.4f' % x if isinstance(x, float) else str(x) for x in row)


def revision():
    """revision.tsv: one row per simulation of the arms of studies 09 and 10
    that the article reads; the sets of the quality coefficient 0.1
    (simulated for 168 s) follow the others. Frozen: see the module's
    docstring; the compilation below is how the deposited file was made, and
    it runs only into another file (SENSORS_RL_REVISION_OUT=<path>)."""
    out = os.environ.get('SENSORS_RL_REVISION_OUT')
    if not out:
        print('revision.tsv is frozen as the first round deposited it: not rewritten '
              '(SENSORS_RL_REVISION_OUT=<path> compiles it into another file; the second round: --only round2)')
        return
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(paths.SETS, 'set_*_p*-fire*')))
    names.sort(key=lambda n: sets.QUALITY.match(n) is not None)
    rows = []
    for name in names:
        k = sets.keys(name)
        if k is None or not sets.harvested(os.path.join(paths.SETS, name)):
            continue
        arm, fire, split, period, dist = k
        if period == 'p9' and dist == '40' and arm not in ('rules', 'agents', 'hybrid', 'pq') \
                and not name.endswith(('-s10', '-frozen')):
            continue
        if period != 'p9' and not name.endswith('-s10'):
            continue
        rows += revision_rows(name)
    # Written aside, then renamed: a reader never sees a half-written file.
    with open(out + '.tmp', 'w') as f:
        f.write(HEADER['revision.tsv'] + '\n')
        f.write('\t'.join(REVISION_COLS) + '\n')
        for row in rows:
            f.write(_line(row) + '\n')
    os.replace(out + '.tmp', out)
    print('%s: %d simulations' % (out, len(rows)))


def round2(only=None):
    """round2.tsv: the columns of revision.tsv, one row per simulation of the
    sets of study 11, in the order of its sets.txt. A set complete on disk
    whose rows the file does not hold yet is compiled; the rows the file
    already holds are kept, so that a set stored then purged keeps them
    (delete a set's rows to compile it again); a set neither stored nor
    complete is left out and named. With only (data --only round2 --sets),
    a set it does not name is not read: its stored rows are kept, or it
    stays out, so that storing one set never fails on another."""
    listed = [l.split()[0] for l in open(paths.study(paths.STUDY_R2, 'sets.txt')) if l.strip() and not l.startswith('#')]
    unknown = [s for s in only or () if s not in listed]
    if unknown:
        sys.exit('round2: not listed in data/sensors-rl/%s/sets.txt: %s' % (paths.STUDY_R2, ' '.join(unknown)))
    sims = sets.declared_sims(paths.CONF)
    out = paths.data('round2.tsv')
    stored = {}
    if os.path.exists(out):
        lines = [l.rstrip('\n') for l in open(out) if not l.startswith('#') and l.strip()]
        if lines and lines[0].split('\t') != list(REVISION_COLS):
            sys.exit('round2.tsv: its columns are not those of revision.tsv; not rewritten')
        for l in lines[1:]:
            stored.setdefault(tuple(l.split('\t')[:5]), []).append(l)
    body, new, absent, unread = [], [], [], []
    for name in listed:
        key = tuple(sets.keys(name))
        d = os.path.join(paths.SETS, name)
        if key in stored:
            body += stored.pop(key)
            continue
        if only and name not in only:
            unread.append(name)
            continue
        reals = _complete(d)
        if not sets.harvested(d) or reals is None or len(reals) < sims.get(name, 0):
            absent.append(name)
            continue
        body += [_line(r) for r in revision_rows(name)]
        new.append(name)
    if stored:
        sys.exit('round2.tsv holds rows of sets study 11 no longer lists (%s); not rewritten' % ' '.join('-'.join(k) for k in stored))
    body, filled = _routing_from_runs(body)
    n = len(listed) - len(absent) - len(unread)
    with open(out + '.tmp', 'w') as f:
        f.write(HEADER['round2.tsv'] % (n, len(listed)) + '\n')
        f.write('\t'.join(REVISION_COLS) + '\n')
        for l in body:
            f.write(l + '\n')
    os.replace(out + '.tmp', out)
    print('%s: %d simulations of %d sets of %d, %d compiled now; not yet run or not complete: %d%s; '
          'routing cells filled from the study\'s runs.tsv: %d'
          % (os.path.relpath(out), len(body), n, len(listed), len(new), len(absent),
             '; not stored and not named by --sets, unread: %d' % len(unread) if only else '', filled))


ROUTING_COLS = ('rreq_all', 'rerr', 'rrep', 'hello')


def _routing_from_runs(body):
    """The rows of round2.tsv with their empty routing cells (ROUTING_COLS)
    taken from study 11's results/runs.tsv, which the harvest of each set
    wrote with these counters; a cell that holds a value is never changed,
    and a row runs.tsv does not hold stays as it is. Returns the rows and the
    number of cells filled."""
    runs = paths.results(paths.STUDY_R2, 'runs.tsv')
    if not os.path.exists(runs):
        return body, 0
    key = REVISION_COLS[:6]
    by = {tuple(r[k] for k in key): r
          for r in csv.DictReader((l for l in open(runs) if not l.startswith('#')), delimiter='\t')}
    at = [REVISION_COLS.index(c) for c in ROUTING_COLS]
    out, filled = [], 0
    for line in body:
        v = line.split('\t')
        r = by.get(tuple(v[:6]))
        if r is not None:
            for i, c in zip(at, ROUTING_COLS):
                if v[i] == '' and r.get(c, ''):
                    v[i] = r[c]
                    filled += 1
        out.append('\t'.join(v))
    return out, filled


# ---------------------------------------------------------------- frames.tsv

# The access-only stack in frames.tsv: study 10's arm at GOP 9-3
# (analysis/round2.access_only), at T = 9 s only, its rows after the four
# stacks' rows of that period (the gallery's panel (d)).
ACCESS_FRAMES = ('rules-onlyA', 'set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-%s-rules-onlyA-s10')


def frames():
    """frames.tsv: type, PSNR, SSIM, loss and first-level loss of each image,
    at GOP 9-3 and alarm periods of 7, 9 and 12 s, the four stacks; at 9 s,
    the access-only stack too."""
    out = [HEADER['frames.tsv'],
           '\t'.join(('arm', 'fire', 'period', 'realisation', 'image', 'type', 'psnr', 'ssim', 'loss', 'l1loss'))]
    missing = 0
    for period in ('p7', 'p9', 'p12'):
        arms = [(stack, 'set_%s_GC-PN-0p03-13_%s-n100-d40-%%s-%s%s' % (
                    'AOMDV' if stack == 'pq' else 'AOMDV_QPV', period, stack, '' if period == 'p9' else '-s10'))
                for stack in ('pq', 'rules', 'hybrid', 'agents')] + ([ACCESS_FRAMES] if period == 'p9' else [])
        for stack, name in arms:
            for fk, fv in (('fire', 'F1'), ('fire2', 'F2'), ('fire3', 'F3')):
                d = os.path.join(paths.SETS, name % fk)
                st = glob.glob(d + '/encoding/*/st-frame.dat')
                if not st:
                    print('missing set or encoding:', d, file=sys.stderr)
                    missing += 20
                    continue
                types = {int(r[0]): r[1] for r in (l.rstrip('\n').split('\t') for l in open(st[0])
                                                    if not l.startswith('#') and l.strip())}
                for r in range(1, 21):
                    g = glob.glob('%s/r%02d/*/sim/rt-frame.dat' % (d, r))
                    if not g:
                        print('missing realisation:', d, r, file=sys.stderr)
                        missing += 1
                        continue
                    for line in open(g[0]):
                        if line.startswith('#') or not line.strip():
                            continue
                        x = line.rstrip('\n').split('\t')
                        img = int(x[0])
                        out.append('\t'.join((stack, fv, period, 'r%02d' % r, str(img), types[img], x[1], x[2], x[3], x[4])))
    path = paths.data('frames.tsv')
    with open(path, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print('%s: %d images, %d realisations missing' % (os.path.relpath(path), len(out) - 2, missing))


def frames_access():
    """The access-only stack's rows of frames.tsv once its sets are purged
    (21 November 2026): read from study 10's results/images.tsv, which
    code/metrics/compile_runs.py wrote from the same sim/rt-frame.dat files
    (image, type, PSNR, SSIM, loss, loss of level 1, as written), and put
    where frames() puts them, after the last row at T = 9 s; the other rows
    are kept. Realisation r01 under F1, replayed on 26 November 2026 for the
    gallery, wrote the same rt-frame.dat (data/sensors-rl/article/galerie/README.md)."""
    arm, name = ACCESS_FRAMES
    fires = {name % fk: fv for fk, fv in (('fire', 'F1'), ('fire2', 'F2'), ('fire3', 'F3'))}
    src = paths.results(paths.STUDY_R1, 'images.tsv')
    new = ['\t'.join((arm, fires[r['set']], 'p9', r['realisation'], r['image'], r['type'], r['psnr'], r['ssim'], r['loss'], r['loss1']))
           for r in csv.DictReader((l for l in open(src) if not l.startswith('#')), delimiter='\t') if r['set'] in fires]
    if len(new) != 3 * 20 * 12:
        sys.exit('frames-access: %d image rows of the access-only stack in %s, 720 expected' % (len(new), src))
    path = paths.data('frames.tsv')
    lines = [l.rstrip('\n') for l in open(path)]
    head, rows = lines[:2], [l for l in lines[2:] if l and l.split('\t')[0] != arm]
    at = max(i for i, l in enumerate(rows) if l.split('\t')[2] == 'p9') + 1
    with open(path, 'w') as f:
        f.write('\n'.join(head + rows[:at] + new + rows[at:]) + '\n')
    print('%s: %d images of the access-only stack from %s' % (os.path.relpath(path), len(new), os.path.relpath(src)))


# ------------------------------------------------------------ oracle-s10.tsv

ORACLE_SETS = ('set_*_p7-n100-d40-*-s10', 'set_*_p12-n100-d40-*-s10', 'set_*_p18-n100-d40-*-s10', 'set_*_p30-n100-d40-*-s10',
               'set_*_p9-n100-d40-*-az*-s10', 'set_*_p9-n100-d40-*-pf*-s10', 'set_*_p9-n100-d40-*-fd1-s10',
               'set_*_p9-n100-d40-*-forest-s10', 'set_*_p9-n100-d40-*-smoke-s10', 'set_*_p9-n100-d30-*-j8-s10',
               'set_*_p9-n100-d40-*-swap-s10', 'set_*_p9-n100-d40-*-v15-s10')


def oracle():
    """oracle-s10.tsv: per simulation of the load, fire and scenario series,
    the packets lost and, among them, those that left the camera while no
    path of live nodes joined it to the sink."""
    names = sorted({os.path.basename(d) for p in ORACLE_SETS for d in glob.glob(os.path.join(paths.SETS, p))})
    rows = [HEADER['oracle-s10.tsv'],
            '\t'.join(('arm', 'fire', 'split', 'period', 'dist', 'realisation', 'lost', 'unreachable'))]
    for name in names:
        m = sets.NAME.match(name)
        d = os.path.join(paths.SETS, name)
        if not m or not sets.harvested(d):
            print('skipped:', name, file=sys.stderr)
            continue
        arm, fire, split, period, dist = sets.keys(name)
        for r in sets.realisations(d):
            x = fire_oracle.analyse(r)
            if x is None:
                print('no oracle input:', r, file=sys.stderr)
                continue
            rows.append('\t'.join((arm, fire, split, period, dist, os.path.basename(r), str(x['lost']), str(x['unrec']))))
    out = paths.data('oracle-s10.tsv')
    with open(out, 'w') as f:
        f.write('\n'.join(rows) + '\n')
    print('%s: %d realisations' % (os.path.relpath(out), len(rows) - 2))
