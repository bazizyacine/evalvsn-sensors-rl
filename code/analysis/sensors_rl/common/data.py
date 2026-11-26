"""The tables of data/sensors-rl/article and the plan they follow: reading a
TSV, the arms and seeds of a comparison, and the per-seed operations every
analysis uses.
A seed is (fire, realisation): the stacks of one fire share their seeds, so
two arms compare simulation by simulation."""
import os
import re

from . import paths
from fire_oracle import CASES  # noqa: E402 (paths puts code/metrics on sys.path)

FIRES = ('F1', 'F2', 'F3')
SPLITS = ('3M9D', '6M6D', '9M3D')
GOP = {'3M9D': '3-9', '6M6D': '6-6', '9M3D': '9-3'}
SEEDS = 60
STACKS = ('pq', 'rules', 'agents', 'hybrid')
# What a declaration of a dead neighbour hits, the columns of break-cases.tsv:
# CASES, imported above from code/metrics/fire_oracle.py, which
# classifies them.


def read_tsv(name):
    """The rows of data/sensors-rl/article/<name> (or of a path) as dicts of
    strings, the '#' lines and the empty ones left out; None when the file is
    missing."""
    path = name if os.sep in name else paths.data(name)
    if not os.path.exists(path):
        return None
    lines = [l for l in open(path) if not l.startswith('#')]
    cols = lines[0].rstrip('\n').split('\t')
    return [dict(zip(cols, l.rstrip('\n').split('\t'))) for l in lines[1:] if l.strip()]


_TABLES = {}


def table(name):
    """read_tsv(name), read once: every caller shares the rows and only reads
    them."""
    if name not in _TABLES:
        _TABLES[name] = read_tsv(name)
    return _TABLES[name]


def radio():
    """The radio constants of code/campaign/radio-params.tcl: the initial
    energy (J) and the transmit, receive and idle power (W)."""
    text = open(paths.RADIO).read()
    get = lambda k: float(re.search(r'set val\(%s\)\s+(\S+)' % k, text).group(1))  # noqa: E731
    return {'initeng': get('initeng'), 'tx': get('txPower'), 'rx': get('rxPower'), 'idle': get('idlePower')}


def write_tsv(name, comment, header, rows):
    """data/sensors-rl/article/<name>: the comment line, the header, then the
    rows, already formatted as strings."""
    path = paths.data(name)
    with open(path, 'w') as f:
        f.write(comment + '\n')
        f.write('\t'.join(header) + '\n')
        for r in rows:
            f.write(r + '\n')
    return path


def holding(arm):
    """The table that holds an arm: round2.tsv for the sets of study 11 (the
    arms ending in -s11, and agents-bgreedy, declared in study 10 and run in
    study 11), revision.tsv for those of studies 09 and 10. No arm name is in
    both."""
    return 'round2.tsv' if any(r['arm'] == arm for r in table('round2.tsv') or ()) else 'revision.tsv'


def select(rows, arm, metric, split='9M3D', period='p9', dist='40', fire=None):
    """{seed: value} of an arm of revision.tsv; a cell the sets left empty
    is not a seed."""
    return {(r['fire'], r['realisation']): float(r[metric]) for r in rows
            if r['arm'] == arm and r['split'] == split and r['period'] == period
            and (dist is None or r['dist'] == dist) and r[metric] != ''
            and (fire is None or r['fire'] == fire)}


def stack(rows, stack_, split, metric, fire=None):
    """{seed: value} of a stack of comparative.tsv at one GOP."""
    return {(r['fire'], r['realisation']): float(r[metric]) for r in rows
            if r['stack'] == stack_ and r['split'] == split and (fire is None or r['fire'] == fire)}


def difference(a, b):
    """a - b, seed by seed, over the seeds a holds and b too."""
    return {k: a[k] - b[k] for k in a if k in b}


def pooled_over_gops(per_gop):
    """Per seed, the mean of the dicts of the three GOPs (in that order), over
    the seeds all three hold."""
    return {k: sum(d[k] for d in per_gop) / len(per_gop) for k in per_gop[0] if all(k in d for d in per_gop)}
