"""What the routing traces (aomdv_qpv.tr) of studies 09 and 10 say about the
agents: agent-trace.tsv, each agent's decisions every 20 s in the traced
simulations (the trajectories figure, the decisions table); break-agent.tsv, the counts the link-break
agent chose and declared with, the declarations per 18 s of the alarm and the
PSNR of the twelve images; and break-cases.tsv, what each declaration of a
dead neighbour hits by the oracle's link budget (the neighbour out of
service, a link below the floor, a link within the budget), with, for the
traced agents stack, the failure count it was declared with."""
import collections
import glob
import os
import statistics

import fire_oracle
import sets

from ..common import data, paths

BASE = 'set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-'
FIRES = (('fire', 'F1'), ('fire2', 'F2'), ('fire3', 'F3'))

# ------------------------------------------------------------ agent-trace.tsv

TRACED = (('hybrid-tr-s10', 'hybrid'), ('agents-tr-s10', 'agents'))
# (states, actions) of each agent's line Q; A0 to A2 are the classes of the access agent
SHAPE = {'P': (3, 5), 'C': (3, 4), 'B': (2, 4), 'D': (2, 3), 'E': (1, 5), 'A0': (3, 9), 'A1': (3, 9), 'A2': (3, 9)}
AGENT = {'P': 'path', 'C': 'congestion', 'B': 'break', 'D': 'discovery', 'E': 'discard', 'A': 'access', 'T': 'power'}
ACTIONS = 9
END = 999  # the row of each node's last snapshot


def snapshots(path):
    """(t, node, line kind, [(counts of a state, values of a state)])."""
    for line in open(path, errors='ignore'):
        if not line.startswith('Q '):
            continue
        p = line.split()
        if p[3] == 'T':
            yield float(p[1]), p[2], 'T', [([int(x) for x in p[4:10]], None)]
            continue
        states, actions = SHAPE[p[3]]
        cells = [c.split(':') for c in p[4:4 + states * actions]]
        yield float(p[1]), p[2], p[3], [([int(c[0]) for c in cells[s * actions:(s + 1) * actions]],
                                         [float(c[1]) for c in cells[s * actions:(s + 1) * actions]])
                                        for s in range(states)]


def best(values):
    return values.index(max(values))


def agent_trace():
    """agent-trace.tsv: per arm, agent and 20 s bin (and each node's last
    snapshot, t = 999), the nodes that decided and the decisions per
    simulation, the median per deciding node, the share of node-states whose
    best action left the initial one, and the decisions per action."""
    rows = []
    for suffix, arm in TRACED:
        runs = 0
        decisions = collections.Counter()
        per_action = collections.defaultdict(lambda: [0] * ACTIONS)
        per_node = collections.defaultdict(list)
        changed = collections.Counter()
        seen = collections.Counter()
        for fire, _ in FIRES:
            for tr in sorted(glob.glob(os.path.join(paths.SETS, BASE + fire + '-' + suffix, 'r[0-9][0-9]', '*', 'aomdv_qpv.tr'))):
                runs += 1
                initial = {}
                total = collections.Counter()
                last = {}

                def tally(key, node, kind, states):
                    for s, (n, q) in enumerate(states):
                        decisions[key] += sum(n)
                        for a, c in enumerate(n):
                            per_action[key][a] += c
                        total[key + (node,)] += sum(n)
                        if q is None:
                            continue
                        first = initial.setdefault((node, kind, s), best(q))
                        if sum(n):
                            seen[key] += 1
                            changed[key] += best(q) != first

                for t, node, kind, states in snapshots(tr):
                    tally((AGENT[kind[0]], int(t // 20) * 20), node, kind, states)
                    last[(node, kind)] = states
                # A burnt node stops writing: its last line is its total.
                for (node, kind), states in last.items():
                    tally((AGENT[kind[0]], END), node, kind, states)
                for (agent, t, node), n in total.items():
                    if n:
                        per_node[(agent, t)].append(n)
        for key in sorted(decisions):
            nodes = per_node[key]
            rows.append([arm, key[0], key[1], '%.1f' % (len(nodes) / runs), '%.1f' % (decisions[key] / runs),
                         '%g' % statistics.median(nodes) if nodes else 0,
                         '%.1f' % (100.0 * changed[key] / seen[key]) if seen[key] else '']
                        + ['%.1f' % (c / runs) for c in per_action[key]])
    out = paths.data('agent-trace.tsv')
    with open(out, 'w') as f:
        f.write('# compiled by code/analysis/sensors_rl/compile/agents.py from the traced sets of study 10 (GOP 9-3, 60 simulations an arm)\n')
        f.write('\t'.join(('arm', 'agent', 't', 'nodes', 'decisions', 'median', 'changed') + tuple('a%d' % a for a in range(ACTIONS))) + '\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')
    print('%s: %d rows' % (os.path.relpath(out), len(rows)))


# ----------------------------------------------------------- break-agent.tsv

BREAK_ARMS = (('rules', 'rules'), ('agents-frozen', 'agents-frozen'), ('hybrid-tr-s10', 'hybrid'), ('agents-tr-s10', 'agents'),
              ('hybrid-edec-s10', 'hybrid-edec'), ('agents-edec-s10', 'agents-edec'))
COUNTS = (1, 2, 3, 5)
EDGES = (60, 78, 96, 114, 132, 150, 169)
BREAK_COLS = (('arm', 'fire', 'realisation') + tuple('pick%d' % k for k in COUNTS) + tuple('decl%d' % k for k in COUNTS)
              + ('alive', 'silent') + tuple('best%d' % k for k in COUNTS) + tuple('t%d' % t for t in EDGES[:-1])
              + tuple('img%d' % i for i in range(1, 13)))


def b_lines(path):
    """The link-break agent's lines of a trace, split, one per node every
    20 s; their counters are cumulative."""
    for line in open(path, errors='ignore'):
        if line.startswith('Q ') and line.split(None, 3)[2:3] and ' B ' in line[:24]:
            yield line.split()


def break_lines(path):
    """The last B line of each node: picks and values per state, declarations
    per count, frames that proved a declared neighbour alive, silent neighbours."""
    return {p[2]: p for p in b_lines(path)}.values()


def break_counts(path):
    pick, decl, top = [0] * 4, [0] * 4, [0] * 4
    alive = silent = 0
    lines = list(break_lines(path))
    if not lines:
        return [''] * 14
    for p in lines:
        cells = [c.split(':') for c in p[4:12]]
        for s in (0, 1):
            n = [int(c[0]) for c in cells[4 * s:4 * s + 4]]
            q = [float(c[1]) for c in cells[4 * s:4 * s + 4]]
            for k in range(4):
                pick[k] += n[k]
            if sum(n):
                top[q.index(max(q))] += 1
        i = p.index('decl')
        for k in range(4):
            decl[k] += int(p[i + 1 + k])
        alive += int(p[p.index('alive') + 1])
        silent += int(p[p.index('silent') + 1])
    return pick + decl + [alive, silent] + top


def declarations_over_time(path):
    bins = [0] * (len(EDGES) - 1)
    for t, _, _ in sets.deaths(path):
        bins[max(i for i, e in enumerate(EDGES[:-1]) if t >= e)] += 1
    return bins


def images(rdir):
    f = sets.first(rdir, 'sim', 'rt-frame.dat')
    v = [line.split('\t')[1] for line in open(f) if line.strip() and not line.startswith('#')]
    return v[:12] + [''] * (12 - len(v))


def break_agent():
    """break-agent.tsv: one row per traced simulation at GOP 9-3."""
    rows = []
    for suffix, arm in BREAK_ARMS:
        for fire, label in FIRES:
            for r in sets.realisations(os.path.join(paths.SETS, BASE + fire + '-' + suffix)):
                tr = sets.first(r, 'aomdv_qpv.tr')
                if tr:
                    rows.append([arm, label, os.path.basename(r)] + break_counts(tr) + declarations_over_time(tr) + images(r))
    out = paths.data('break-agent.tsv')
    with open(out, 'w') as f:
        f.write('# compiled by code/analysis/sensors_rl/compile/agents.py from the traces of sets/ (GOP 9-3)\n')
        f.write('\t'.join(BREAK_COLS) + '\n')
        for row in rows:
            f.write('\t'.join(str(x) for x in row) + '\n')
    print('%s: %d simulations' % (os.path.relpath(out), len(rows)))


# ----------------------------------------------------------- break-cases.tsv

# The arms of studies 09 and 10 at GOP 9-3 and T = 9 s whose declarations the
# oracle classifies; the traced agents stack alone writes the counters that
# attribute each declaration to a failure count.
CASE_ARMS = ((('rules', 'rules'), ('hybrid', 'hybrid'), ('agents', 'agents'), ('hybrid-tr-s10', 'hybrid-tr'),
              ('agents-tr-s10', 'agents-tr'), ('hybrid-frozen', 'hybrid-frozen'), ('agents-frozen', 'agents-frozen'),
              ('hybrid-edec-s10', 'hybrid-edec'), ('agents-edec-s10', 'agents-edec'))
             + tuple(('rules-only%s-s10' % x, 'rules-only' + x) for x in 'ABPCDET')
             + tuple(('hybrid-no%s-s10' % x, 'hybrid-no' + x) for x in 'APCDET'))
ATTRIBUTED = 'agents-tr'
ATTRIBUTION_COLS = (tuple('k%d_%s' % (k, c) for k in COUNTS for c in data.CASES)
                    + tuple('p%d_%s' % (k, c) for k in COUNTS for c in data.CASES)
                    + ('unattributed',) + tuple('un_' + c for c in data.CASES) + ('mixed', 'mismatch'))
CASE_COLS = (('arm', 'fire', 'realisation', 'n') + data.CASES + ('declarer_dead', 'purge', 'purge_dead', 'out_of_service')
             + ATTRIBUTION_COLS)


purges = sets.purges


def attribute(row, declared, path):
    """Gives each declaration of the traced agents stack to the failure count
    the link-break agent declared with, through the cumulative counters of
    the declaring node's B lines: the declarations of a node up to one of its
    lines take the counts whose counters moved since its previous line,
    shared in proportion when several moved (kK_case); those of an interval
    where one count alone moved are also counted apart (pK_case). A
    declaration after the node's last line, or in an interval where no
    counter moved, stays unattributed; mismatch counts the declarations of
    the intervals whose counters moved by another number."""
    for c in ATTRIBUTION_COLS:
        row[c] = 0.0
    counters = {}
    for p in b_lines(path):
        i = p.index('decl')
        counters.setdefault(int(p[2].strip('_')), []).append((float(p[1]), [int(x) for x in p[i + 1:i + 1 + len(COUNTS)]]))
    by_node = {}
    for d in declared:
        by_node.setdefault(d[1], []).append(d)
    for node, ds in by_node.items():
        lines = sorted(counters.get(node, []))
        groups = {}
        for d in ds:
            groups.setdefault(next((j for j, (t, _) in enumerate(lines) if t >= d[0]), None), []).append(d)
        for j, g in groups.items():
            delta = None
            if j is not None:
                prev = lines[j - 1][1] if j > 0 else [0] * len(COUNTS)
                delta = [x - y for x, y in zip(lines[j][1], prev)]
                if sum(delta) != len(g):
                    row['mismatch'] += len(g)
            if delta is None or sum(delta) <= 0:
                row['unattributed'] += len(g)
                for d in g:
                    row['un_' + d[3]] += 1
                continue
            moved = [k for k, x in zip(COUNTS, delta) if x]
            if len(moved) > 1:
                row['mixed'] += len(g)
            else:
                for d in g:
                    row['p%d_%s' % (moved[0], d[3])] += 1
            for d in g:
                for k, x in zip(COUNTS, delta):
                    row['k%d_%s' % (k, d[3])] += x / sum(delta)


def case_counts(rdir, attributed):
    """One row of break-cases.tsv: the declarations of a dead neighbour during
    the alarm by the case the oracle finds, the HELLO purges and those that
    remove a neighbour already out of service, and the nodes out of service
    before the end of the run (fire_oracle.declaration_cases); None without
    the trace."""
    run = fire_oracle.declaration_cases(rdir)
    if run is None:
        return None
    row, declared, tr = run
    if attributed:
        attribute(row, declared, tr)
    return row


def break_cases():
    """break-cases.tsv: one row per simulation of CASE_ARMS, what its
    declarations of a dead neighbour hit."""
    rows = []
    for suffix, arm in CASE_ARMS:
        for fire, label in FIRES:
            for r in sets.realisations(os.path.join(paths.SETS, BASE + fire + '-' + suffix)):
                row = case_counts(r, arm == ATTRIBUTED)
                if row is not None:
                    row.update(arm=arm, fire=label, realisation=os.path.basename(r))
                    rows.append('\t'.join(row[c] if c in ('arm', 'fire', 'realisation') else '%g' % row[c] if c in row else ''
                                          for c in CASE_COLS))
    path = data.write_tsv('break-cases.tsv', '# compiled by code/analysis/sensors_rl/compile/agents.py from the traces of sets/'
                          ' (GOP 9-3, T = 9 s) with code/metrics/fire_oracle.py', CASE_COLS, rows)
    print('%s: %d simulations' % (os.path.relpath(path), len(rows)))
