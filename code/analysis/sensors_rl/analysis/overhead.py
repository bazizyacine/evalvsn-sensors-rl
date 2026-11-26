"""The costs of the four stacks and of the access-only stack for a sensor
node (the costs table): energy, control traffic and memory, and the
processing figures the text quotes.

Energy. The simulator's energy model counts the radio's states only (transmit,
receive, idle listening, sleep; ns-2 EnergyModel, rates in
code/campaign/radio-params.tcl): overhead.tsv holds, per set, the mean over
its realisations of the energy consumed per node and by the whole network and
the lowest residual energy as a share of the initial one; the busiest node's
consumption is (1 - life time) x the initial energy. The access-only stack
has its rows at GOP 9-3 only (study 10).

Control traffic. Messages sent by every node in a simulation (HELLO, RREQ
originated or forwarded, RERR, RREP), from revision.tsv for the traced arms
(agents-tr and hybrid-tr, identical runs to the agents and hybrid stacks at
GOP 9-3), the control AOMDV (pq-ctl) and the access-only stack (rules-onlyA,
study 10), and for the rules and AOMDV of study
09 from data/sensors-rl/0-comparative/results/routing.tsv when that file
exists; a dash otherwise.

Memory. What the agents add to a node: their value tables, sized from their
declarations in the simulator's headers, and the context of the decisions that
await an outcome, in a node's formats (the assumptions are the constants below).
The counters that only feed the trace (RL_TRACE_) are left out.

Processing. Printed only: the operations per packet read from the code, and the
decisions per node from agent-trace.tsv over the alarm."""
import os
import re
import sys

from ..common import data, paths
from ..compile import measures

ROUTING = paths.results(paths.STUDY_E0, 'routing.tsv')
# the simulator's modules, at their path under ns-2.35/, in both repositories
NS = paths.NS2
RT_H = os.path.join(NS, 'aomdv_qpv', 'aomdv_qpv.h')
MAC_H = os.path.join(NS, 'mac', 'mac-802_15_4EvalVSN.h')
MAC_CC = os.path.join(NS, 'mac', 'mac-802_15_4EvalVSN.cc')

# Memory on a node (assumptions, stated in the text):
# a value 4 bytes (single-precision float), an action, a state or a flag 1 byte,
# a neighbour's short address or a packet id 2 bytes, an instant 4 bytes, a
# per-interval packet count 2 bytes; per-neighbour and per-packet records sit in
# arrays indexed by the neighbour's slot or the packet's buffer, without a key,
# and a decision's context is freed with its packet. The simulator stores values
# as 8-byte doubles.
FLOAT, BYTE, ADDR, TIME, COUNT, DOUBLE = 4, 1, 2, 4, 2, 8
NEIGHBOURS = 4   # 40 m grid, range 48.6 m, diagonal 56.6 m out of reach
HELD = 16 + 1    # packets a node holds: its interface queue (16) and the frame in the MAC
DESTINATIONS = 1  # the discovery agent decides at the camera, for the sink alone
ALARM = (60.0, 168.0)  # detection to the end of a GOP 9-3 simulation (s)
EMIT = 0.015     # interval between two video packets of an image (s)
# A sensor-node microcontroller for scale: the ATmega128L's 4 Kbytes of
# internal SRAM (the bibliography's atmel_atmega128l_datasheet).
SRAM_REF = 4 * 1024

# Fields the simulator keeps per decision awaiting its outcome, in node formats.
CONTEXT = {
    # RlCtx (class, threshold, profile, occupancy, instant) and the early-discard
    # value of an admitted packet (discard_val_), per held packet
    'path': HELD * (3 * BYTE + FLOAT + TIME),
    'discard': HELD * FLOAT + BYTE + 3 * FLOAT + COUNT,  # + rle_a_, rle_ack_/fail_/disc_, rle_n_
    # the frame in the MAC: state (class, link), actions (access, power), pending
    # and failed flags, destination, packet id, start instant
    'access': 6 * BYTE + ADDR + ADDR + TIME,
    # per neighbour: the run's count and state, then the declaration awaiting its
    # verdict (instant, count, state)
    'break': NEIGHBOURS * (2 * BYTE + TIME + 2 * BYTE),
    # per destination: the flood in flight (action, bucket, instant)
    'discovery': DESTINATIONS * (2 * BYTE + TIME),
}
CONTEXT['path'] += BYTE  # rlp_cur_, the profile in use
# The agent each table belongs to, and its declaration
TABLES = (('path', RT_H, 'rlp_q_'), ('congestion', RT_H, 'rlc_q_'), ('break', RT_H, 'rlb_q_'),
          ('discovery', RT_H, 'rld_q_'), ('discard', RT_H, 'rle_q_'), ('access', MAC_H, 'rlmQ_'))
# The agents of each stack; the access-only stack's one agent is the
# channel-access agent (the main comparison between the stacks)
AGENTS = {'agents': ('path', 'congestion', 'break', 'discovery', 'discard', 'access', 'power'),
          'hybrid': ('path', 'congestion', 'discovery', 'discard', 'access', 'power'),
          'access': ('access',)}


def dims(path, name):
    """Product of the array dimensions of `double name[a][b]...;` in a header."""
    m = re.search(r'double\s+%s((?:\[\d+\])+)\s*;' % re.escape(name), open(path).read())
    if not m:
        sys.exit('%s: no declaration of %s' % (path, name))
    n = 1
    for d in re.findall(r'\[(\d+)\]', m.group(1)):
        n *= int(d)
    return n


def power_steps():
    m = re.search(r'kRlpStepsNb\s*=\s*(\d+)', open(MAC_CC).read())
    return int(m.group(1))


def trace_counters():
    """Counters that only feed the trace: the long arrays and scalars named *_cnt_."""
    n = 0
    for path in (RT_H, MAC_H):
        for m in re.finditer(r'^\s*long\s+(\w+_cnt_)((?:\[\d+\])*)\s*;', open(path).read(), re.M):
            k = 1
            for d in re.findall(r'\[(\d+)\]', m.group(2)):
                k *= int(d)
            n += k
    return n


def memory():
    values = {a: dims(p, n) for a, p, n in TABLES}
    values['power'] = power_steps() * NEIGHBOURS
    out = {}
    for stack, agents in AGENTS.items():
        v = sum(values[a] for a in agents)
        ctx = sum(CONTEXT.get(a, 0) for a in agents)
        out[stack] = {'values': v, 'tables': v * FLOAT, 'context': ctx, 'node': v * FLOAT + ctx, 'sim': v * DOUBLE}
    return values, out


def energy(rows, stack, split='9M3D'):
    """Means over the simulations of the three fires, weighted by realisations."""
    sel = [r for r in rows if r['stack'] == stack and r['split'] == split]
    if not sel:
        return None
    n = sum(int(r['n']) for r in sel)
    return {k: sum(float(r[k]) * int(r['n']) for r in sel) / n for k in ('e_total', 'e_node', 'e_max')}


def control(stack, traced, rev, routing):
    out = {}
    for m in ('hello', 'rreq_all', 'rerr', 'rrep'):
        v = []
        if traced:
            v = [float(r[m]) for r in rev if r['arm'] == traced and r['split'] == '9M3D' and r['period'] == 'p9'
                 and r[m] != '']
        if not v and routing:
            name = dict((s, p) for s, p, _ in measures.ENERGY_STACKS)[stack]
            names = {name.format(gc='0p03', fire=f) for f in measures.ENERGY_FIRE}
            v = [float(r[m]) for r in routing if r.get('set') in names and r.get(m, '') != '']
        out[m] = sum(v) / len(v) if v else None
    return out


def _report(en_rows, values, mem, r):
    print('\nEnergy (radio only; overhead.tsv):')
    cross = ('rules', 'agents', 'hybrid')
    spread, gap = [], []
    for split in measures.ENERGY_SPLIT.values():
        for f in measures.ENERGY_FIRE.values():
            e = {x['stack']: float(x['e_node']) for x in en_rows if x['split'] == split and x['fire'] == f}
            if all(s in e for s in cross):
                v = [e[s] for s in cross]
                spread.append(100 * (max(v) - min(v)) / min(v))
            if 'pq' in e and 'rules' in e:
                gap.append(100 * (e['pq'] - e['rules']) / e['rules'])
    print('  three cross-layer stacks, largest spread of the per-node energy in a cell: %.3f %% (%d cells)'
          % (max(spread), len(spread)))
    four = cross + ('access',)
    spread4 = []
    for f in measures.ENERGY_FIRE.values():
        e = {x['stack']: float(x['e_node']) for x in en_rows if x['split'] == '9M3D' and x['fire'] == f}
        if all(s in e for s in four):
            v = [e[s] for s in four]
            spread4.append(100 * (max(v) - min(v)) / min(v))
    if spread4:
        print('  with the access-only stack, GOP 9-3: largest spread of the per-node energy in a cell: %.3f %% (%d cells)'
              % (max(spread4), len(spread4)))
    print('  AOMDV against the rules, per node: %.2f to %.2f %%' % (min(gap), max(gap)))
    for s, _, _ in measures.ENERGY_STACKS:
        e = energy(en_rows, s)
        if e:
            print('  %-7s GOP 9-3: network %.1f J, per node %.3f J, busiest node %.3f J' % (s, e['e_total'], e['e_node'], e['e_max']))
    e = energy(en_rows, 'hybrid')
    print('  radio rates: tx %.3f W, rx %.3f W, idle %.3f W; tx over listening +%.1f %%'
          % (r['tx'], r['rx'], r['idle'], 100 * (r['tx'] - r['idle']) / r['idle']))
    print('  per node and simulation, %.2f J of the %g J battery: %.3f %%' % (e['e_node'], r['initeng'], 100 * e['e_node'] / r['initeng']))
    print('  listening alone empties the battery in %.1f h' % (r['initeng'] / r['idle'] / 3600))
    print('\nMemory (node formats; values %d bytes, simulator %d):' % (FLOAT, DOUBLE))
    print('  values per agent: %s' % ', '.join('%s %d' % kv for kv in values.items()))
    for s, m in mem.items():
        print('  %-7s %d values = %d bytes of tables + %d bytes of context = %d bytes; %d bytes as doubles'
              % (s, m['values'], m['tables'], m['context'], m['node'], m['sim']))
    print('  context per agent (bytes): %s' % ', '.join('%s %d' % kv for kv in CONTEXT.items()))
    print('  left out: %d trace counters (long), RL_TRACE_ only' % trace_counters())
    print('  interface queue for comparison: 16 packets of 74 bytes of payload = %d bytes' % (16 * 74))
    print('  share of the ATmega128L\'s %d bytes of SRAM: %s' % (SRAM_REF, ', '.join(
        '%s %.1f %%' % (s, 100.0 * m['node'] / SRAM_REF) for s, m in mem.items())))
    trace = data.read_tsv('agent-trace.tsv')
    alarm = ALARM[1] - ALARM[0]
    print('\nProcessing (alarm %g s):' % alarm)
    for x in trace:
        if x['t'] == '999':
            print('  %-7s %-11s median %6s per node -> %.1f per s; mean per deciding node %.1f per s'
                  % (x['arm'], x['agent'], x['median'], float(x['median']) / alarm,
                     float(x['decisions']) / float(x['nodes']) / alarm))
    per_packet = 4
    print('  per packet: %d decisions (path, congestion, access, power); argmax over 5 + 4 + 9 + <=6 values: '
          '<= %d comparisons; <= %d uniform draws if not critical, none if critical; %d updates of 3 operations'
          % (per_packet, 4 + 3 + 8 + (power_steps() - 1), 2 * per_packet, per_packet))
    print('  camera: one packet every %g s = %.1f per s -> <= %.0f decisions per s'
          % (EMIT, 1 / EMIT, per_packet / EMIT))


def inputs():
    """The rows of overhead.tsv, revision.tsv and the routing counters of study 09 (None when absent)."""
    routing = data.read_tsv(ROUTING)
    return data.read_tsv('overhead.tsv'), data.read_tsv('revision.tsv'), routing


def report():
    en_rows, _, _ = inputs()
    values, mem = memory()
    _report(en_rows, values, mem, data.radio())
