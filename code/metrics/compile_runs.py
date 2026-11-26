#!/usr/bin/env python3
"""compile_runs.py - one row per simulation of a study: the raw results that
the article's compiled tables are drawn from.

The sets under sets/ (or SETS_DIR) are machine-local and unversioned (traces,
images, hundreds of gigabytes), and they are purged once their study is
delivered. This keeps, for every realisation of every set a study lists in
data/<study>/sets.txt, what the simulation measured on it and the seed it ran
on, small enough to be versioned and published:

  - sim/mt.dat: the PSNR, the SSIM and their loss-free references, the packet
    loss overall, of the M and D frames and of each priority level;
  - sim/rt-frame.dat: the PSNR, SSIM and packet loss of each image at the sink;
  - the routing counters and the energy of metrics/routing_events.py, from
    the set's events.tsv or from the study's results/routing.tsv, where they
    exist.

The seed is recomputed with run_sets.sh's law (cksum of "<name>-<index>",
modulo 900000, plus 1; seed 0 for a single-realisation set, but that of
realisation K for one that declares realisation=K), from the set's
own name or, with --seed-base, from the name the study pairs its sets on
(BASE-<fire token>, as run_sets.sh --seed-name=BASE-<fire> runs them). It is
checked against the seed the set's PROGRESS.txt recorded; a mismatch fails.

    python3 compile_runs.py --seed-base=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40 sensors-rl/0-comparative
    python3 compile_runs.py --seed-base=... -o out.tsv sensors-rl/1-round1
    python3 compile_runs.py --allow-partial ... sensors-rl/2-round2     # leave out the sets still running
    python3 compile_runs.py --tables runs,images,oracle,declarations --jobs 4 ... sensors-rl/2-round2
    python3 compile_runs.py --keep --sets set_A ... sensors-rl/2-round2  # set_A's rows, the others kept

The default output is data/<study>/results/<table>.tsv. A set is complete
when graphs/PSNR/PSNR.dat exists and its realisations number the sims of its
declaration; without --allow-partial, an incomplete or missing set fails the
compilation, so that a published table never silently lacks a set.

--keep keeps, from the existing output, the rows of the sets this compilation
does not write: a set purged after its rows were stored, or no longer listed
in sets.txt; the file keeps its order, a new set's rows come after. A purged
set is then complete through its stored rows, and --keep with --sets
compiles one set into a study's files (the campaign's watcher, at the end of
each set).

The tables (--tables, runs by default):

runs.tsv. Columns: set, realisation, seed; arm, fire, split, period, dist, the
keys of the article's revision.tsv (empty for a set revision.tsv does not
hold, such as the sets of the quality coefficient 0.1 that stopped at 165 s);
then the mt.dat columns as the tools wrote them (psnr refPSNR ssim refSSIM
pktLoss pktLossM pktLossD pktlossM1..13 pktlossD1..13; dB, SSIM in [0, 1],
losses in %); then psnr_i<k>, ssim_i<k>, loss_i<k> for each image k at the
sink; then rreq_camera rreq_all rerr mac_drop rq_overflow cbk rrep hello
(messages or packets per simulation) and e_total e_node lifetime (J consumed
by all the nodes, J per node, lowest residual energy in % of the initial one;
routing_events.py). A value the set does not provide stays empty: the
routing counters of a set slimmed before events.tsv existed, the energy of a
set whose events.tsv has no energy columns.

images.tsv: one row per image at the sink: set, realisation, image, type (M
or D, from st-frame.dat), psnr, ssim, loss (%), then loss1 to loss13, the
packet loss (%) of each priority level of the image (sim/rt-frame.dat).

oracle.tsv: one row per simulation of a fire scenario (metrics/fire_oracle.py):
set, realisation, sent, lost, recoverable (lost while a path of live nodes
joined camera and sink), unreachable (lost while no such path existed), then
sent_m, lost_m, recoverable_m, the same for the M frames (video packets).

declarations.tsv: one row per simulation of the cross-layer stack
(fire_oracle.declaration_cases): set, realisation, n (neighbours declared dead
during the alarm), dead, zone, range, budget (what each declaration hits by
the oracle's link budget: the neighbour out of service, a link the heated
zone puts below the floor, a link out of range, a living neighbour within the
budget), declarer_dead, purge and purge_dead (HELLO purges of the alarm, and
those of a neighbour already out of service), out_of_service (nodes out of
service before the end of the run).
"""
import argparse
import csv
import glob
import multiprocessing
import os
import sys

import fire_oracle
from sets import FIRE_TOKEN, Unreadable, declared_realisations, declared_sims, first, keys, read_frames, read_mt, recorded_seeds, seed_for

HERE = os.path.dirname(os.path.abspath(__file__))

ROUTING = ('rreq_camera', 'rreq_all', 'rerr', 'mac_drop', 'rq_overflow', 'cbk', 'rrep', 'hello')
ENERGY = ('e_total', 'e_node', 'lifetime')
IMAGES = 12  # the twelve frames of the alarm video; more are added if a set has them
LEVELS = 13  # the priority levels of GC-PN-*-13
TABLES = ('runs', 'images', 'oracle', 'declarations')
ORACLE = ('sent', 'lost', 'recoverable', 'unreachable', 'sent_m', 'lost_m', 'recoverable_m')
DECLARATIONS = ('n',) + fire_oracle.CASES + ('declarer_dead', 'purge', 'purge_dead', 'out_of_service')


def read_routing(path, name):
    if not os.path.exists(path):
        return {}
    rows = csv.DictReader((l for l in open(path) if not l.startswith('#')), delimiter='\t')
    return {r['realisation']: r for r in rows if r['set'] == name}


def frame_types(rdir, setdir):
    """image -> M or D, from the realisation's st-frame.dat or the set's encoding."""
    f = first(rdir, 'st-frame.dat') or next(iter(glob.glob(os.path.join(setdir, 'encoding', '*', 'st-frame.dat'))), None)
    out = {}
    if f:
        for line in open(f):
            if line.startswith('#') or not line.strip():
                continue
            v = line.split('\t')
            out[int(v[0])] = v[1]
    return out


def image_rows(rdir, setdir):
    """[(image, type, psnr, ssim, loss, [loss of each level])] of sim/rt-frame.dat."""
    f = first(rdir, 'sim', 'rt-frame.dat')
    if not f:
        return []
    types = frame_types(rdir, setdir)
    out = []
    for line in open(f):
        if line.startswith('#') or not line.strip():
            continue
        v = line.rstrip('\n').rstrip('\t').split('\t')
        out.append((int(v[0]), types.get(int(v[0]), ''), v[1], v[2], v[3], v[4:]))
    return out


def one_set(job):
    """Every requested table's rows of one complete set."""
    name, d, sims, realisation, seed_name, routing_paths, tables = job
    logged = recorded_seeds(d)
    routing = {}
    for p in routing_paths:
        routing = read_routing(p, name)
        if routing:
            break
    out = {t: [] for t in tables}
    bad_seed = []
    reals = [r for r in sorted(glob.glob(os.path.join(d, 'r[0-9][0-9]'))) if glob.glob(os.path.join(r, '*', 'sim', 'mt.dat'))]
    for r in reals:
        real = os.path.basename(r)
        if 'runs' in tables:
            seed = seed_for(seed_name, int(real[1:]), sims, realisation)
            if real in logged and logged[real] != seed:
                bad_seed.append('%s %s: computed %d, recorded %d' % (name, real, seed, logged[real]))
            out['runs'].append((name, real, seed, keys(name) or ('',) * 5, read_mt(r), read_frames(r), routing.get(real, {})))
        if 'images' in tables:
            out['images'] += [(name, real) + x for x in image_rows(r, d)]
        if 'oracle' in tables:
            x = fire_oracle.analyse(r)
            if x is not None:
                out['oracle'].append((name, real, x['sent'], x['lost'], x['rec'], x['unrec'], x['sentM'], x['lostM'], x['recM']))
        if 'declarations' in tables:
            x = fire_oracle.declaration_cases(r)
            if x is not None:
                out['declarations'].append((name, real) + tuple(x[0][c] for c in DECLARATIONS))
    return name, out, bad_seed


def read_table(path):
    """(header, {set: [rows as dicts]}, set order) of an existing table; (None, {}, []) without one."""
    if not os.path.exists(path):
        return None, {}, []
    rows, order, head = {}, [], None
    for line in open(path):
        if line.startswith('#'):
            continue
        v = line.rstrip('\n').split('\t')
        if head is None:
            head = v
            continue
        if v[0] not in rows:
            rows[v[0]] = []
            order.append(v[0])
        rows[v[0]].append(dict(zip(head, v)))
    return head, rows, order


def write_table(path, comment, head, new, keep, listed):
    """Writes the rows of `new` ({set: [dicts]}) under `head`, with, under
    --keep, the rows the existing file holds for the other sets: its order
    and its columns first, the new sets and columns after. The comment's
    %(n)d and %(kept)s take the count of sets and of those kept. Returns
    (rows, sets, sets kept)."""
    old_head, old, old_order = read_table(path) if keep else (None, {}, [])
    if old_head:
        head = old_head + [c for c in head if c not in old_head]
    rows = dict(new)
    kept = [s for s in old if s not in new]
    for s in kept:
        rows[s] = old[s]
    order = [s for s in old_order if s in rows] + [s for s in listed if s in rows and s not in old_order]
    order += [s for s in rows if s not in order]
    total = len(set(listed) | set(order))
    note = ', %d kept from the previous compilation' % len(kept) if kept else ''
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = 0
    # Written aside, then renamed: a reader never sees a half-written file.
    with open(path + '.tmp', 'w') as f:
        f.write(comment % {'n': len(order), 'total': total, 'kept': note} + '\n')
        f.write('\t'.join(head) + '\n')
        for s in order:
            for r in rows[s]:
                f.write('\t'.join(r.get(c, '') for c in head) + '\n')
                n += 1
    os.replace(path + '.tmp', path)
    return n, len(order), kept


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('study', help='a folder of data/, e.g. sensors-rl/1-round1')
    ap.add_argument('-o', '--out', help='the runs table, default: data/<study>/results/runs.tsv')
    ap.add_argument('--outdir', help='the folder of the tables, default: data/<study>/results')
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(HERE)),
                    help='the root of the repository (default: two levels above this file); the sets are under '
                         '$SETS_DIR, by default ROOT/sets')
    ap.add_argument('--seed-base', default='', help='pairing name: each set takes the seeds of BASE-<fire token>')
    ap.add_argument('--allow-partial', action='store_true', help='leave out, with a warning, the sets not complete')
    ap.add_argument('--keep', action='store_true', help='keep the stored rows of the sets not compiled here')
    ap.add_argument('--sets', nargs='+', metavar='SET', help='compile these sets of the study only')
    ap.add_argument('--tables', default='runs', help='comma-separated, among %s (default runs)' % ', '.join(TABLES))
    ap.add_argument('--jobs', type=int, default=1, help='sets read in parallel (default 1)')
    a = ap.parse_args()

    tables = [t for t in a.tables.split(',') if t]
    if not tables or any(t not in TABLES for t in tables):
        ap.error('--tables: among %s' % ', '.join(TABLES))
    root = os.path.abspath(a.root)
    sets_dir = os.environ.get('SETS_DIR') or os.path.join(root, 'sets')
    study = os.path.join(root, 'data', a.study)
    outdir = a.outdir or os.path.join(study, 'results')
    outs = {t: os.path.join(outdir, t + '.tsv') for t in tables}
    if a.out:
        outs['runs'] = a.out
    listed = [l.split()[0] for l in open(os.path.join(study, 'sets.txt')) if l.strip() and not l.startswith('#')]
    names = listed
    if a.sets:
        unknown = [s for s in a.sets if s not in listed]
        if unknown:
            sys.exit('compile_runs.py: not listed in data/%s/sets.txt: %s' % (a.study, ' '.join(unknown)))
        names = a.sets
    sims_of = declared_sims(os.path.join(root, 'code', 'campaign', 'sets.conf'))
    real_of = declared_realisations(os.path.join(root, 'code', 'campaign', 'sets.conf'))
    study_routing = os.path.join(study, 'results', 'routing.tsv')
    # under --keep, a set whose rows runs.tsv holds is complete even once purged
    stored = set(read_table(a.out or os.path.join(outdir, 'runs.tsv'))[1]) if a.keep else set()

    jobs, missing = [], []
    for name in names:
        d = os.path.join(sets_dir, name)
        sims = sims_of.get(name)
        if sims is None:
            sys.exit('compile_runs.py: %s is not declared in sets.conf' % name)
        reals = sorted(glob.glob(os.path.join(d, 'r[0-9][0-9]')))
        done = [r for r in reals if glob.glob(os.path.join(r, '*', 'sim', 'mt.dat'))]
        if not os.path.exists(os.path.join(d, 'graphs', 'PSNR', 'PSNR.dat')) or len(done) < sims:
            if name not in stored:
                missing.append('%s (%d / %d)' % (name, len(done), sims))
            continue
        if a.seed_base:
            fire = FIRE_TOKEN.search(name)
            if not fire:
                sys.exit('compile_runs.py: %s has no fire token for --seed-base' % name)
            seed_name = '%s-%s' % (a.seed_base, fire[1])
        else:
            seed_name = name
        jobs.append((name, d, sims, real_of.get(name, 0), seed_name, (os.path.join(d, 'events.tsv'), study_routing), tables))

    if missing:
        print('compile_runs.py: %d set(s) of %s not complete%s:\n  %s'
              % (len(missing), a.study, ', left out' if a.allow_partial else '', '\n  '.join(missing)), file=sys.stderr)
        if not a.allow_partial:
            sys.exit(1)

    try:
        if a.jobs > 1:
            with multiprocessing.Pool(a.jobs) as pool:
                results = pool.map(one_set, jobs, chunksize=1)
        else:
            results = [one_set(j) for j in jobs]
    except Unreadable as e:
        sys.exit('compile_runs.py: %s; nothing is written' % e)
    bad_seed = [b for _, _, bs in results for b in bs]
    if bad_seed:
        print('compile_runs.py: %d seed(s) differ from PROGRESS.txt; check --seed-base:\n  %s'
              % (len(bad_seed), '\n  '.join(bad_seed[:10])), file=sys.stderr)
        sys.exit(1)

    seeds = ', seeds of %s-<fire>' % a.seed_base if a.seed_base else ''
    for t in tables:
        new = {}
        if t == 'runs':
            rows = [row for _, out, _ in results for row in out['runs']]
            mt_cols, images = [], IMAGES
            for row in rows:
                for c in row[4]:
                    if c not in mt_cols:
                        mt_cols.append(c)
                images = max([images] + list(row[5]))
            head = ['set', 'realisation', 'seed', 'arm', 'fire', 'split', 'period', 'dist'] + mt_cols
            for k in range(1, images + 1):
                head += ['psnr_i%d' % k, 'ssim_i%d' % k, 'loss_i%d' % k]
            head += list(ROUTING) + list(ENERGY)
            for name, real, seed, k, mt, frames, ev in rows:
                v = [name, real, str(seed)] + list(k) + [mt.get(c, '') for c in mt_cols]
                for i in range(1, images + 1):
                    v += list(frames.get(i, ('', '', '')))
                v += [ev.get(c, '') for c in ROUTING + ENERGY]
                new.setdefault(name, []).append(dict(zip(head, v)))
            what = 'one row per simulation'
        elif t == 'images':
            levels = max([LEVELS] + [len(x[7]) for _, out, _ in results for x in out['images']])
            head = ['set', 'realisation', 'image', 'type', 'psnr', 'ssim', 'loss'] + ['loss%d' % k for k in range(1, levels + 1)]
            for _, out, _ in results:
                for name, real, img, typ, psnr, ssim, loss, lv in out['images']:
                    new.setdefault(name, []).append(dict(zip(head, [name, real, str(img), typ, psnr, ssim, loss] + list(lv))))
            what = 'one row per image at the sink, with the loss of each priority level'
        elif t == 'oracle':
            head = ['set', 'realisation'] + list(ORACLE)
            for _, out, _ in results:
                for x in out['oracle']:
                    new.setdefault(x[0], []).append(dict(zip(head, [str(v) for v in x])))
            what = 'the video packets lost, recoverable or not (code/metrics/fire_oracle.py), one row per simulation'
        else:
            head = ['set', 'realisation'] + list(DECLARATIONS)
            for _, out, _ in results:
                for x in out['declarations']:
                    new.setdefault(x[0], []).append(dict(zip(head, list(x[:2]) + ['%g' % v for v in x[2:]])))
            what = 'the declarations of a dead neighbour by the oracle\'s case (code/metrics/fire_oracle.py), one row per simulation'
        comment = ('# compiled by code/metrics/compile_runs.py from sets/ (study %s): %s, %%(n)d of %%(total)d sets%%(kept)s%s'
                   % (a.study, what, seeds if t == 'runs' else ''))
        n, nsets, kept = write_table(outs[t], comment, head, new, a.keep, listed)
        print('%s: %d rows of %d sets%s' % (outs[t], n, nsets, ', %d kept' % len(kept) if kept else ''))


if __name__ == '__main__':
    main()
