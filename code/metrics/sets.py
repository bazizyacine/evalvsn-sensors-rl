"""sets.py - reading the sets under SETS (SETS_DIR, by default the folder
sets/ at the root of the repository): the declarations of sets.conf, the
grammar of the names of the Sensors RL article's sets, the seed of a
realisation, and the files a realisation leaves. Shared by compile_runs.py
and by the compilation of the article (the compile/ stage of its sensors_rl
package)."""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SETS = os.environ.get('SETS_DIR') or os.path.join(ROOT, 'sets')

# The article's sets at a GOP coefficient (13 levels), and those of the
# quality coefficient 0.1 simulated for 168 s; the arm of the latter is its
# stack with the suffix -q01, at GOP 9-3.
NAME = re.compile(r'set_(AOMDV_QPV|AOMDV)_GC-PN-(0p\d+)-13_(p[0-9r]+)-n100-d(\d+)-(fire[23]?)-(.+?)(?:-s10)?$')
QUALITY = re.compile(r'set_(AOMDV_QPV|AOMDV)_GC-QC-0p1_(p9)-n100-d(40)-(fire[23]?)-(rules-onlyA|rules|hybrid|agents|pq)-t168-(s10|s11)$')
SPLIT = {'0p03': '9M3D', '0p02525': '6M6D', '0p01597': '3M9D'}
FIRE = {'fire': 'F1', 'fire2': 'F2', 'fire3': 'F3'}
FIRE_TOKEN = re.compile(r'-d\d+-(fire[23]?)(?:-|$)')
PROGRESS = re.compile(r'realisation (\d+)/(\d+) \((r\d+), seed (\d+)\)')
# A neighbour declared dead in the routing trace (aomdv_qpv.tr).
DEATH = re.compile(r'^A (\d+\.\d+) _(\d+)_ deleting LL hop to (\d+)')


def keys(name):
    """(arm, fire, split, period, dist) of an article's set, or None."""
    q = QUALITY.match(name)
    if q:
        _, period, dist, fire, stack, study = q.groups()
        # study 11's sets keep their suffix in the arm, as NAME does below
        return stack + '-q01' + ('-s11' if study == 's11' else ''), FIRE[fire], '9M3D', period, dist
    m = NAME.match(name)
    if not m:
        return None
    _, gc, period, dist, fire, arm = m.groups()
    # the two other videos have their own GOP coefficient, both giving nine M frames
    split = '9M3D' if ('-forest' in arm or '-smoke' in arm) else SPLIT.get(gc, '')
    return arm, FIRE[fire], split, period, dist


def declared_sims(conf):
    """name -> sims, from sets.conf (the 13th column)."""
    out = {}
    for line in open(conf, encoding='utf8'):
        if not line.strip() or line.startswith('#'):
            continue
        f = line.split()
        if len(f) >= 13:
            out[f[0]] = int(f[12])
    return out


def declared_realisations(conf):
    """name -> K for the sets of one simulation whose knobs column (the 14th)
    declares realisation=K: that simulation is realisation K of the seed
    series (run_sets.sh), the development runs of study 11."""
    out = {}
    for line in open(conf, encoding='utf8'):
        if not line.strip() or line.startswith('#'):
            continue
        f = line.split()
        for kv in (f[13].split(',') if len(f) >= 14 else ()):
            if kv.startswith('realisation='):
                out[f[0]] = int(kv.split('=', 1)[1])
    return out


def _crc_table():
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) if c & 0x80000000 else (c << 1)
        table.append(c & 0xFFFFFFFF)
    return table


CRC = _crc_table()


def cksum(data):
    """POSIX cksum: CRC-32 of the bytes, then of their length, complemented."""
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ CRC[((crc >> 24) ^ b) & 0xFF]
    n = len(data)
    while n:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ CRC[((crc >> 24) ^ (n & 0xFF)) & 0xFF]
        n >>= 8
    return ~crc & 0xFFFFFFFF


def seed_for(name, i, sims, realisation=0):
    """run_sets.sh's seed_for(): a single-realisation set runs ns-2's own
    sequence, unless it declares realisation=K (declared_realisations): its
    one simulation, r01, then takes the seed of realisation K."""
    if realisation:
        i = realisation
    elif sims == 1:
        return 0
    return cksum(('%s-%d' % (name, i)).encode()) % 900000 + 1


def recorded_seeds(setdir):
    """realisation -> seed, as the set's PROGRESS.txt recorded them."""
    path = os.path.join(setdir, 'PROGRESS.txt')
    if not os.path.exists(path):
        return {}
    return {m[3]: int(m[4]) for m in PROGRESS.finditer(open(path, errors='ignore').read())}


def harvested(setdir):
    """True once the set's metrics are written: graphs/PSNR/PSNR.dat exists."""
    return os.path.exists(os.path.join(setdir, 'graphs', 'PSNR', 'PSNR.dat'))


def realisations(setdir):
    """The realisation directories rNN of a set, in order."""
    return sorted(glob.glob(os.path.join(setdir, 'r[0-9][0-9]')))


def first(rdir, *parts):
    """The path of a file of a realisation (under its <video>-<simId>/), or None."""
    g = glob.glob(os.path.join(rdir, '*', *parts))
    return g[0] if g else None


class Unreadable(ValueError):
    """A file of a realisation that exists but does not read as the chain
    writes it; the message names the file."""


def read_mt(rdir):
    """The realisation's sim/mt.dat as {column: string}, or None without one.
    An empty or truncated file (no row under the header, or a row shorter
    than it) raises Unreadable."""
    mt = first(rdir, 'sim', 'mt.dat')
    if not mt:
        return None
    lines = [l for l in open(mt) if l.strip()]
    head = lines[0].lstrip('#').split() if lines else []
    row = lines[1].split() if len(lines) > 1 else []
    if not row or len(row) < len(head):
        raise Unreadable('%s: empty or truncated (%d bytes, %d lines, %d values for %d columns); run the realisation again'
                         % (mt, os.path.getsize(mt), len(lines), len(row), len(head)))
    return dict(zip(head, row))


def read_frames(rdir):
    """image -> (psnr, ssim, loss), as sim/rt-frame.dat wrote them."""
    f = first(rdir, 'sim', 'rt-frame.dat')
    out = {}
    if f:
        for line in open(f):
            if line.startswith('#') or not line.strip():
                continue
            v = line.split('\t')
            out[int(v[0])] = (v[1], v[2], v[3])
    return out


def read_packets(path):
    """seq -> (send or receive time, frame, frame type, priority level) of a
    packet trace (st-packet.dat, rt-packet.dat)."""
    out = {}
    for line in open(path, errors='ignore'):
        if line.startswith('#') or not line.strip():
            continue
        v = line.split('\t')
        out[int(v[1])] = (float(v[0]), int(v[3]), v[4], int(v[5]))
    return out


def level_losses(rdir):
    """Packet loss (%) of level M1, of levels M1 to M3, and of the D frames."""
    s = read_packets(first(rdir, 'st-packet.dat'))
    g = read_packets(first(rdir, 'sim', 'rt-packet.dat'))

    def loss(pred):
        ks = [q for q, (_, _, ft, pr) in s.items() if pred(ft, pr)]
        return 100.0 * sum(1 for q in ks if q not in g) / len(ks)
    return (loss(lambda ft, pr: ft == 'M' and pr == 1),
            loss(lambda ft, pr: ft == 'M' and pr <= 3),
            loss(lambda ft, pr: ft == 'D'))


def deaths(path):
    """(t, node, neighbour) of each neighbour declared dead in a routing trace,
    leaving out the periodic neighbour purge, which fires on whole seconds,
    and the declarations before the alarm (t < 60 s)."""
    for line in open(path, errors='ignore'):
        m = DEATH.match(line)
        if not m:
            continue
        t = float(m[1])
        if t < 60 or abs(t - round(t)) < 1e-6:
            continue
        yield t, int(m[2]), int(m[3])


def purges(path):
    """(t, node, neighbour) of each periodic neighbour purge during the
    alarm: the deletions on whole seconds after 60 s, which deaths leaves
    out."""
    for line in open(path, errors='ignore'):
        m = DEATH.match(line)
        if m and float(m[1]) >= 60 and abs(float(m[1]) - round(float(m[1]))) < 1e-6:
            yield float(m[1]), int(m[2]), int(m[3])
