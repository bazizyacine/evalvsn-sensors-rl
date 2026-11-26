"""The figures of the results: the agents' learning trajectories
(agent-trace.tsv), the PSNR and the M1 loss per fire and GOP of the four
stacks of the main study (comparative.tsv) and of the access-only stack (the
rule stack with the channel-access agent alone, experiment E2: study 10 at
GOP 9-3 in revision.tsv, study 11 at 6-6 and 3-9 in round2.tsv, the same 20
seeds a cell), and the gallery of a frame decoded at the sink
by each stack, access-only included (data/sensors-rl/article/galerie/,
frames.tsv). They are drawn as the first round deposited them (decision of
24 November 2026), the access-only stack added to the PSNR and M1-loss
figures; AOMDV with cross-layer timers is in the tables.

The trajectories, two panels against the simulated time, means of the 60
traced simulations at GOP 9-3: (a) the share of node-state pairs whose best action
has left the initial one, (b) the mean cumulative decisions per node that has
decided, on a log axis; one line per agent (path, congestion, channel access
and early discard from the hybrid stack, link-break detection from the agents
stack). It leaves out the 160 s bin, which is partial, and the t = 999 rows
(each node's last snapshot, in the decisions table); the discovery agent, which decides
about eleven times a simulation on one node, and the power agent, which
writes no values; and the bins where fewer than one node a simulation
decided. A node writes its snapshot at its first HELLO after each 20 s mark,
so each point is drawn at the bin's middle, t + 10 s."""
import os
import sys

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from PIL import Image

from ..analysis import quality, round2
from ..common import data, paths, stats
from . import style as sty
from .style import (BLUE, GREEN, GREY, INK, MUTED, ORANGE, PRINT, PURPLE, SKY, T, VERMIL, below, decimal_axes,
                    fit_width, letter_panels, num, plt, save, top_legend)

BINS = range(0, 160, 20)  # complete bins only: 0 to 140 s
DETECTION = 60  # t_d, the alarm (materials and methods)

# agent, stack, colour, marker, line style; the near-equal pairs (path and
# congestion, access and discard) differ by their line style. The hybrid
# stack's agents take colours that no stack takes in the comparative figures
# (grey AOMDV, blue rules, green hybrid); the link-break detection keeps the
# agents stack's orange, and a dash-dot line: its orange and the channel
# access's sky blue print the same grey (CIE L* 70.6 and 69.8).
AGENTS = [('path', 'hybrid', INK, 'o', '-'),
          ('congestion', 'hybrid', VERMIL, 's', '--'),
          ('access', 'hybrid', SKY, '^', '-'),
          ('discard', 'hybrid', PURPLE, 'D', '--'),
          ('break', 'agents', ORANGE, 'v', '-.')]
TRAJECTORY = {
    'fr': {'path': 'chemin', 'congestion': 'congestion', 'access': 'accès au canal', 'discard': 'rejet anticipé',
           'break': 'détection de rupture', 'hybrid': 'Hybride', 'agents': 'Agents',
           'x': '$t$ (s)', 'share': 'hors du choix initial (%)', 'count': 'décisions par nœud'},
    'en': {'path': 'path', 'congestion': 'congestion', 'access': 'channel access', 'discard': 'early discard',
           'break': 'link-break detection', 'hybrid': 'Hybrid', 'agents': 'Agents',
           'x': '$t$ (s)', 'share': 'away from the initial choice (%)', 'count': 'decisions per node'},
}


def trajectory_rows():
    return {(r['arm'], r['agent'], int(r['t'])): r for r in data.read_tsv('agent-trace.tsv')}


def log_tick(v, _):
    """A log tick as a plain number. French sets thousands off by a thin space
    as its tables do; English follows MDPI, a comma from five digits only."""
    s = '%d' % round(v) if v >= 1 else ('%g' % v)
    if sty.LANG == 'fr':
        if len(s) > 3:
            s = s[:-3] + '\u2009' + s[-3:]
        return s.replace('.', ',')
    return s[:-3] + ',' + s[-3:] if len(s) > 4 else s


def trajectory_figure(rows):
    L = TRAJECTORY[sty.LANG]
    fig, (a, b) = plt.subplots(1, 2, figsize=(PRINT['trajectoires'], 2.75))
    handles, labels = [], []
    for agent, arm, col, mk, ls in AGENTS:
        style = dict(color=col, marker=mk, ls=ls, lw=1.3, ms=3.6 if mk != 'D' else 3.0)
        kept = [(t + 10, rows[(arm, agent, t)]) for t in BINS if float(rows[(arm, agent, t)]['nodes']) >= 1.0]
        a.plot([x for x, r in kept if r['changed'] != ''], [float(r['changed']) for x, r in kept if r['changed'] != ''],
               **style)
        b.plot([x for x, r in kept], [float(r['decisions']) / float(r['nodes']) for x, r in kept], **style)
        handles.append(Line2D([], [], **style))
        labels.append('%s, %s' % (L[agent], L[arm]))
    for ax in (a, b):
        ax.axvline(DETECTION, color=MUTED, lw=0.8, ls=':', zorder=1)
        ax.text(DETECTION - 2, 0.97, '$t_d$', transform=ax.get_xaxis_transform(), ha='right', va='top',
                fontsize=8, color=MUTED)
        ax.set_xlim(0, 160)
        ax.set_xticks(range(0, 161, 40))
        ax.set_xlabel(L['x'])
    a.set_ylim(0, 22)
    a.set_yticks(range(0, 21, 5))
    a.set_ylabel(L['share'])
    b.set_yscale('log')
    b.set_ylim(0.8, 1000)
    b.set_yticks([k * 10 ** e for e in range(3) for k in (1, 2, 5)] + [1000])
    b.yaxis.set_minor_locator(plt.NullLocator())
    b.set_ylabel(L['count'])
    decimal_axes(a, b)
    b.yaxis.set_major_formatter(FuncFormatter(log_tick))
    letter_panels((a, b))
    leg = top_legend(fig, handles, labels, ncol=2, columnspacing=1.2)
    fit_width(fig, 'trajectoires', lambda: fig.tight_layout(rect=(0, 0, 1, below(fig, leg, 0.01)), pad=0.3,
                                                                  w_pad=1.6))
    return save(fig, 'trajectoires')


# stack, colour, mark, line style, in the order of the PSNR table's columns
# (tables/comparative.py, WORDS) less AOMDV with cross-layer timers. The
# access-only stack takes the channel-access agent's sky blue, as in the
# trajectories figure, a filled plus and a dash-dot-dot line: its sky and the
# agents' orange print nearly the same grey (CIE L* 69.8 and 70.6), and its
# marks often fall on the hybrid stack's, under which they would vanish, so
# it is drawn over the other stacks (ZORDER).
STACKS = [('aomdv', GREY, 'o', '-'), ('rules', BLUE, 's', '-'), ('access', SKY, 'P', (0, (4, 1.2, 1, 1.2, 1, 1.2))),
          ('agents', ORANGE, '^', '-'), ('hybrid', GREEN, 'v', '-')]
ZORDER = {'access': 2.1}  # the lines' default is 2
SPLITS = [('3M9D', '3-9'), ('6M6D', '6-6'), ('9M3D', '9-3')]


def comparative():
    out = {}
    for r in data.read_tsv('comparative.tsv'):
        out.setdefault((r['fire'], r['split'], r['stack']), []).append(r)
    return out


def cell_mean(c, fire, split, stack, metric):
    """The mean of a metric over the 20 seeds of a cell: the main study's
    four stacks from comparative.tsv, the access-only stack from its arm at
    that GOP (analysis/round2.py, access_only), which must hold the same
    seeds, as the PSNR table computes it (tables/comparative.py,
    cell_values); None when the cell is empty."""
    if stack != 'access':
        rows = c.get((fire, split, stack))
        return sum(float(r[metric]) for r in rows) / len(rows) if rows else None
    v = {k[1]: x for k, x in quality.values(round2.access_only(split), metric, split).items() if k[0] == fire}
    seeds = {r['realisation'] for r in c.get((fire, split, 'rules'), ())}
    if set(v) != seeds:
        sys.exit(f'{round2.access_only(split)}: the seeds of {fire} {split} differ from those of the main study')
    return stats.mean(v.values()) if v else None


def comp_figure(c, metric, ylabel, name, floor=False, ylim=None, yticks=None):
    """One panel per fire, the M-D split on the x axis, one line per stack;
    means only, the tables carry the deviations and the tests. Two panels a
    row: (a) F1 and (b) F2, then (c) F3 with the legend of
    the stacks in the free cell beside it, centred on (c)'s plot; each panel
    has its y-axis title and its ticks, on the scale the three share."""
    L = T[sty.LANG]
    fig = plt.figure(figsize=(PRINT[name], 4.45))
    gs = fig.add_gridspec(2, 2)
    first = fig.add_subplot(gs[0, 0])
    axes = [first, fig.add_subplot(gs[0, 1], sharey=first), fig.add_subplot(gs[1, 0], sharey=first)]
    for ax, fire in zip(axes, ('F1', 'F2', 'F3')):
        for st, col, mk, ls in STACKS:
            xs, ys = [], []
            for k, (sp, _) in enumerate(SPLITS):
                m = cell_mean(c, fire, sp, st, metric)
                if m is not None:
                    xs.append(k)
                    ys.append(m)
            ax.plot(xs, ys, color=col, marker=mk, ls=ls, zorder=ZORDER.get(st, 2), label=L['stack'][st])
        if floor:
            ax.axhline(28, color=VERMIL, lw=1.0, ls='--', label=L['floor'])
        ax.set_xticks(range(len(SPLITS)))
        ax.set_xticklabels([lab for _, lab in SPLITS])
        ax.set_xlabel(L['md'])
        ax.grid(False, axis='x')  # three categories: the ticks suffice
        if ylim:
            ax.set_ylim(*ylim)
        if yticks is not None:  # the ticks of the larger drawing, kept at print size
            ax.set_yticks(yticks)
        ax.set_ylabel(ylabel)
    letter_panels(axes)
    decimal_axes(*axes)
    for ax in axes:  # after decimal_axes, whose formatter would number the splits
        ax.set_xticks(range(len(SPLITS)))
        ax.set_xticklabels([lab for _, lab in SPLITS])
    h, lab = axes[0].get_legend_handles_labels()
    leg = top_legend(fig, h, lab, loc='center', bbox_to_anchor=(0.75, 0.25))

    def layout():
        fig.tight_layout(pad=0.3, w_pad=1.4, h_pad=0.8)
        b, f3 = axes[1].get_position(), axes[2].get_position()
        leg.set_bbox_to_anchor(((b.x0 + b.x1) / 2, (f3.y0 + f3.y1) / 2), transform=fig.transFigure)
    fit_width(fig, name, layout)
    return save(fig, name)


# The gallery's frame (data/sensors-rl/article/galerie/README.md): image 8 of r01, F1, GOP
# 9-3, T = 9 s (study 09; the access-only stack, study 10); the arms of
# frames.tsv, AOMDV being 'pq' and the access-only stack its arm at GOP 9-3.
GALLERY = {'fire': 'F1', 'period': 'p9', 'realisation': 'r01', 'image': '8'}
ARM = {'aomdv': 'pq', 'rules': 'rules', 'access': round2.access_only('9M3D'), 'agents': 'agents', 'hybrid': 'hybrid'}


def gallery_frame():
    """The gallery frame's PSNR at the sink (dB) and the loss of its first
    level (%), per stack, read in frames.tsv; the frame is a main one, so
    that level is M1. The caption prints them, checked by claims P19."""
    out = {}
    for r in data.read_tsv('frames.tsv'):
        if all(r[k] == x for k, x in GALLERY.items()):
            out[r['arm']] = r
    for st, arm in ARM.items():
        if out.get(arm, {}).get('type') != 'M':
            sys.exit(f'frames.tsv: no main frame {GALLERY} for {arm}')
    return {st: (float(out[arm]['psnr']), float(out[arm]['l1loss'])) for st, arm in ARM.items()}


def gallery_figure():
    """Frame 8 of the first simulation of F1 at GOP 9-3, coded without
    network loss then as the sink decodes it for each stack: six panels, two
    columns and three rows, in the caption's order; as in Figure 2 of the
    MDPI template, each panel carries its letter alone, and the caption
    gives the stack, the PSNR of the frame and the loss of its M1 level."""
    files = ['reference'] + list(ARM)
    gallery_frame()  # every stack's frame is in frames.tsv, and a main one
    fig, axes = plt.subplots(3, 2, figsize=(PRINT['galerie'], 1.2 * PRINT['galerie']))
    for i, (ax, f) in enumerate(zip(axes.flat, files)):
        img = np.array(Image.open(os.path.join(paths.DATA, 'galerie', f + '.png')).convert('L'))
        ax.imshow(img, cmap='gray', vmin=0, vmax=255)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xlabel('($\\mathbf{%s}$)' % chr(97 + i), fontsize=8, labelpad=3)
    fit_width(fig, 'galerie', lambda: fig.tight_layout(w_pad=0.8, h_pad=0.4), keep_aspect=True)
    return save(fig, 'galerie')


def figures():
    c = comparative()
    L = T[sty.LANG]
    return [trajectory_figure(trajectory_rows()),
            comp_figure(c, 'psnr', L['psnr'], 'comparatif-psnr', floor=True, ylim=(16, 31), yticks=range(16, 31, 2)),
            comp_figure(c, 'm1loss', L['m1loss'], 'comparatif-m1', ylim=(0, 80), yticks=range(0, 81, 10)),
            gallery_figure()]
