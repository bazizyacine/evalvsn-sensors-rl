#!/usr/bin/env python3
"""routing_events.py - the routing events and the energy of each realisation, read from its ns-2 trace.

The routing measures rest on counts the harvest does not keep: how many
route requests the camera
and the whole network sent, how many route errors, how many video packets the
MAC gave up on, how many the camera's routing queue refused while it waited
for a route, how many went to a neighbour already dead. setGraphs.pl never
reads them, so they are counted here from sets/<set>/r*/*/st-packet.tr, which
only a set run without --prune still holds (the campaign's watcher writes
each set's events.tsv before it slims the set). The same pass reads the
energy of each simulation, which setGraphs.pl only keeps as the mean of the
set: slimming deletes the trace, so events.tsv is its only per-simulation
record.

    python3 routing_events.py -o ../../data/sensors-rl/0-comparative/results/routing.tsv set_A set_B ...
    python3 routing_events.py -o ../../sets/set_A/events.tsv set_A

One row per realisation: set, realisation, the camera's node, then
rreq_camera (RREQ the camera originated), rreq_all (RREQ sent by every node,
originated or forwarded), rerr (RERR sent), mac_drop (video packets dropped at
the MAC), rq_overflow (video packets the camera's routing queue refused,
reason IFQ at the RTR layer), cbk (video packets dropped on a MAC failure
callback, reason CBK), rrep and hello (RREP and HELLO sent), and pkt_loss (% of
video packets lost, from sim/mt.dat); then the energy, as setGraphs.pl's
calculate_Consumption computes it from the same trace (each node's last
reported energy, from the N lines and the -Ne field of the s, r, d and f
lines; the highest energy seen is the initial one): e_total (J consumed by
all the nodes, the set's 'Power Consumption'), e_node (J consumed per node,
their mean, 'Energy Consumption') and lifetime (the lowest residual energy,
% of the initial one, 'Life Time'). The mean of each over a set's
realisations is the value of its graphs/<metric>/<metric>.dat.
"""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SETS = os.environ.get('SETS_DIR') or os.path.join(ROOT, 'sets')

# One awk pass per trace: a 150 MB trace is read in seconds, a Python loop
# would take minutes.
AWK = r'''
{
  ev = $1; node = ""; layer = ""; why = ""; type = ""; pc = ""; ps = ""; ph = ""; t = ""; ne = ""
  if (ev == "N") {
    # N -t <time> -n <node> -e <energy>: a node's energy, logged by the PHY
    energy($3 + 0, $5, $7 + 0)
    next
  }
  for (i = 2; i < NF; i++) {
    if ($i == "-Ni") node = $(i + 1)
    else if ($i == "-Nl") layer = $(i + 1)
    else if ($i == "-Nw") why = $(i + 1)
    else if ($i == "-It") type = $(i + 1)
    else if ($i == "-Pc") pc = $(i + 1)
    else if ($i == "-Ps") ps = $(i + 1)
    else if ($i == "-Ph") ph = $(i + 1)
    else if ($i == "-t") t = $(i + 1)
    else if ($i == "-Ne") ne = $(i + 1)
  }
  if ((ev == "s" || ev == "r" || ev == "d" || ev == "f") && t != "" && ne != "" && node ~ /^[0-9]+$/)
    energy(t + 0, node, ne + 0)
  if (ev == "s" && layer == "AGT" && type == "video") cam[node]++
  if (ev == "s" && layer == "RTR" && pc == "REQUEST") {
    rreq_all++
    # originated here: the request's source is this node, at hop count 0
    if (ps == node && ph == "0") rreq_from[node]++
  }
  if (ev == "s" && layer == "RTR" && pc == "ERROR") rerr++
  if (ev == "s" && layer == "RTR" && pc == "REPLY") rrep++
  if (ev == "s" && layer == "RTR" && pc == "HELLO") hello++
  if (ev == "d" && type == "video") {
    if (layer == "MAC") mac_drop++
    if (layer == "RTR" && why == "IFQ") rq[node]++
    if (layer == "RTR" && why == "CBK") cbk++
  }
}
# setGraphs.pl's rule: the highest energy seen is the initial one, and a
# node's latest report (a tie going to the later line) its residual energy.
function energy(when, n, e) {
  if (e > e0) e0 = e
  if (!(n in etime) || when >= etime[n]) { eres[n] = e; etime[n] = when }
}
END {
  best = ""; for (n in cam) if (best == "" || cam[n] > cam[best]) best = n
  total = 0; nn = 0; low = ""
  for (n in eres) { total += e0 - eres[n]; nn++; if (low == "" || eres[n] < low) low = eres[n] }
  printf "%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d", best, rreq_from[best], rreq_all, rerr, mac_drop, rq[best], cbk, rrep, hello
  printf "\t%.6f\t%.6f\t%.6f\n", total, (nn ? total / nn : 0), (e0 > 0 ? 100 * low / e0 : 0)
}
'''

COLS = ['camera', 'rreq_camera', 'rreq_all', 'rerr', 'mac_drop', 'rq_overflow', 'cbk', 'rrep', 'hello']
ENERGY = ['e_total', 'e_node', 'lifetime']
HEADER = ['set', 'realisation'] + COLS + ['pkt_loss'] + ENERGY


def pkt_loss(rdir):
    for mt in glob.glob(os.path.join(rdir, '*', 'sim', 'mt.dat')):
        with open(mt) as fh:
            head = fh.readline().split()
            row = fh.readline().split()
        if 'pktLoss' in head and row:
            return row[head.index('pktLoss')]
    return ''


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('-o', '--output', required=True)
    ap.add_argument('sets', nargs='+')
    args = ap.parse_args()

    rows = []
    for name in args.sets:
        rdirs = sorted(glob.glob(os.path.join(SETS, name, 'r[0-9]*')))
        if not rdirs:
            sys.exit('routing_events.py: no realisation under sets/%s' % name)
        for rdir in rdirs:
            traces = glob.glob(os.path.join(rdir, '*', 'st-packet.tr'))
            if not traces:
                sys.exit('routing_events.py: %s has no st-packet.tr (pruned?)' % rdir)
            out = subprocess.run(['awk', AWK, traces[0]], capture_output=True, text=True, check=True)
            v = out.stdout.split()
            if len(v) != len(COLS) + len(ENERGY):
                sys.exit('routing_events.py: %s: unreadable trace' % traces[0])
            rows.append([name, os.path.basename(rdir)] + v[:len(COLS)] + [pkt_loss(rdir)] + v[len(COLS):])
            print('%s %s' % (name, os.path.basename(rdir)), file=sys.stderr)

    # Written aside, then renamed: a reader never sees a half-written file.
    with open(args.output + '.tmp', 'w') as fh:
        fh.write('# routing events and energy per realisation, from the ns-2 traces (code/metrics/routing_events.py)\n')
        fh.write('\t'.join(HEADER) + '\n')
        for r in rows:
            fh.write('\t'.join(r) + '\n')
    os.replace(args.output + '.tmp', args.output)
    print('wrote %s: %d realisation(s)' % (args.output, len(rows)))


if __name__ == '__main__':
    main()
