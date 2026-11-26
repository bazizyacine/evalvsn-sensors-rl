"""The figures of the methods: the scenario, one map per fire
(fire-map-F1..F3.tsv), and the early discard's admission region. They are
drawn as the first round deposited them, the maps two a row as in the MDPI
template."""
import math
import os

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon

from ..common import paths
from . import style as sty
from .style import (BLUE, GREY, INK, MUTED, PAD, PRINT, RULE_CORE, RULE_FILL, T, below, decimal_axes, fit_width,
                    letter, plt, save, top_legend)

def read_map(name):
    meta, rows = {}, []
    for line in open(paths.data(name), encoding='utf8'):
        if line.startswith('# ignition'):
            v = line[2:].split()
            meta = {'ix': float(v[1]), 'iy': float(v[2])}
            meta.update({v[i]: float(v[i + 1]) for i in range(3, len(v), 2)})
        elif line.startswith('#') or line.startswith('id'):
            continue
        else:
            i, x, y, front, death = line.split()
            rows.append((int(i), float(x), float(y), float(front), float(death)))
    return meta, rows


def ellipse(meta, t):
    """FARSITE's ellipse at time t (evalvsn.tcl: rear focus at the ignition)."""
    U, R = meta['wind'], meta['head_speed']
    LB = min(8.0, 0.936 * math.exp(0.2566 * U) + 0.461 * math.exp(-0.1548 * U) - 0.397)
    HB = (LB + math.sqrt(LB * LB - 1)) / (LB - math.sqrt(LB * LB - 1))
    a, b = 0.5 * (R + R / HB) / LB, (R + R / HB) / 2
    c = b - R / HB
    th = math.radians(meta['wind_dir'])
    ph = np.linspace(0, 2 * math.pi, 240)
    xw, yw = c * t + b * t * np.cos(ph), a * t * np.sin(ph)
    return (meta['ix'] + xw * math.cos(th) - yw * math.sin(th),
            meta['iy'] + xw * math.sin(th) + yw * math.cos(th))


ICONS = os.path.join(paths.FIGURES_SRC, 'icons')
FOREST = '#e9f3e1'
S_FRONT, S_EARLY, S_ZONE, S_ALIVE = '#8e1b12', '#d94a2b', '#f2a65a', '#9a9a92'


def place(ax, name, x, y, zoom, z=5):
    """A Twemoji pictogram (CC BY 4.0)."""
    from matplotlib.image import imread
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    ab = AnnotationBbox(OffsetImage(imread(os.path.join(ICONS, f'icon-{name}.png')), zoom=zoom), (x, y),
                        frameon=False, pad=0)
    ab.set_zorder(z)
    ax.add_artist(ab)


def map_scale(mw):
    """The scale of the pictograms, discs and strokes of a map mw inches wide:
    1 for the map of the first round's drawing, 0.325 of its 7.14 in less the
    margins, so that they keep their size relative to the map."""
    return mw / (0.325 * (7.14 - 2 * PAD))


# The layout of the scenario figure, in inches: two maps a
# row, (a) F1 and (b) F2, then (c) F3 with the legend in the free cell beside
# it; the gap between the maps, the band of each panel's letter and the gap
# between the rows. The maps fill the print width.
MAP_GAP, LETTER_BAND, ROW_GAP = 0.08, 0.22, 0.08
MAP_W = (PRINT['scenario-carte'] - 2 * PAD - MAP_GAP) / 2


def scenario_figure():
    """The three fires of the main study, 90 s after the detection, in the
    illustrated style of a drawn map: the forest as a light ground, the
    relays as antenna pictograms on a disc whose shade gives their state at
    time t, the burnt ellipse and the heated zone ahead of it, the camera, the
    sink, the fire and its wind as pictograms.

    Two maps a row, each with its letter alone under it, (c) beside the
    legend; the pictograms, discs and strokes are scaled by
    g (map_scale), the type is not, so that it prints at 9 pt (letters), 8 pt
    (wind and legend). Each map's wind band, above it, is just tall enough
    for its arrow and label."""
    import random
    L = T[sty.LANG]
    t = 150
    W = PRINT['scenario-carte'] - 2 * PAD
    mw = MAP_W
    g = map_scale(mw)
    fires = [('F%d' % k,) + read_map('fire-map-F%d.tsv' % k) for k in (1, 2, 3)]
    # the maps' height: their width spans 430 m, their height 467 m with the wind band
    mh = mw * 467 / 430
    H = 2 * (LETTER_BAND + mh) + ROW_GAP + 0.01
    fig = plt.figure(figsize=(W, H))
    cells = [(0, LETTER_BAND + mh + ROW_GAP + LETTER_BAND), (mw + MAP_GAP, LETTER_BAND + mh + ROW_GAP + LETTER_BAND),
             (0, LETTER_BAND)]
    axes = [fig.add_axes((x / W, y / H, mw / W, mh / H)) for x, y in cells]
    for k, (ax, (label, meta, rows)) in enumerate(zip(axes, fires)):
        forest = ax.add_patch(plt.Rectangle((-32, -32), 424, 424, facecolor=FOREST, edgecolor='#7fae6a',
                                            lw=1.0 * g, zorder=0))
        rnd = random.Random(7)
        for _ in range(26):
            place(ax, 'tree' if rnd.random() < 0.6 else 'tree2', rnd.uniform(-15, 375), rnd.uniform(-15, 375),
                  0.028 * g, z=1)
        zx, zy = ellipse(meta, t + meta['zone_s'])
        ax.add_patch(Polygon(np.c_[zx, zy], closed=True, facecolor='#fbe3c4', alpha=0.85, edgecolor='#e0a060',
                             lw=0.8 * g, ls='--', zorder=1.5)).set_clip_path(forest)
        bx, by = ellipse(meta, t)
        ax.add_patch(Polygon(np.c_[bx, by], closed=True, facecolor='#f0b8a8', alpha=0.9, edgecolor='#b03a2e',
                             lw=1.2 * g, zorder=1.6)).set_clip_path(forest)
        for i, x, y, front, death in rows:
            if i in (0, 99):
                continue
            if front <= t:
                col = S_FRONT
            elif death <= t:
                col = S_EARLY
            elif front <= t + meta['zone_s']:
                col = S_ZONE
            else:
                col = S_ALIVE
            ax.plot(x, y, 'o', ms=8.5 * g, color=col, markeredgecolor='white', markeredgewidth=0.6 * g, zorder=3)
            place(ax, 'relay', x, y, 0.022 * g, z=4)
        place(ax, 'camera', 0, 0, 0.05 * g, z=6)
        place(ax, 'sink', 360, 360, 0.055 * g, z=6)
        place(ax, 'fire', meta['ix'], meta['iy'], 0.05 * g, z=6)
        # The wind, in a band above the map so that it hides no relay.
        th = math.radians(meta['wind_dir'])
        cx, cy, r = 150, 412, 20
        ax.annotate('', xy=(cx + r * math.cos(th), cy + r * math.sin(th)),
                    xytext=(cx - r * math.cos(th), cy - r * math.sin(th)),
                    arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.4 * g), zorder=8)
        ax.text(cx - 40, cy, L['wind'], fontsize=8, color=INK, ha='right', va='center', zorder=8)
        ax.set_xlim(-35, 395); ax.set_ylim(-35, 432); ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_xlabel(letter(k), labelpad=4)
    # The legend, framed, in the free cell beside (c) and centred on its map:
    # one column of three groups, the relays' four states, the three grounds
    # (burnt area, heated zone, the forest and its trees, which MDPI asks to
    # explain like every pictogram), the three pictograms of the camera, the
    # sink and the fire.
    groups = [[(('disc', S_ALIVE), L['alive']), (('disc', S_ZONE), L['heated']), (('disc', S_EARLY), L['early']),
               (('disc', S_FRONT), L['front'])],
              [(('patch', '#f0b8a8'), L['burnt']), (('patch', '#fbe3c4'), L['zone']), (('forest', None), L['forest'])],
              [(('icon', 'camera'), L['camera']), (('icon', 'sink'), L['sink']), (('icon', 'fire'), L['ignition'])]]
    rnd_ = fig.canvas.get_renderer()

    def width(s, fs):
        tx = fig.text(0, 0, s, fontsize=fs)
        w = tx.get_window_extent(rnd_).width / fig.dpi
        tx.remove()
        return w
    # inches: the key and its gap, the row pitch, the gap between groups, the margin inside the frame
    fs, key, row, sep, margin = 8, 0.24, 0.155, 0.07, 0.10
    lw_ = max(width(lab, fs) for grp in groups for _, lab in grp) + key + 2 * margin
    lh = sum(len(grp) for grp in groups) * row + (len(groups) - 1) * sep + 2 * margin - (row - 0.10)
    lx, ly = mw + MAP_GAP + (mw - lw_) / 2, LETTER_BAND + (mh - lh) / 2
    lax = fig.add_axes((lx / W, ly / H, lw_ / W, lh / H))
    lax.set_xlim(0, lw_); lax.set_ylim(0, lh)
    lax.set_xticks([]); lax.set_yticks([]); lax.grid(False)
    for sp in lax.spines.values():
        sp.set_visible(True); sp.set_edgecolor('#9a9a92'); sp.set_linewidth(0.8)
    cy = lh - margin - 0.05
    for grp in groups:
        for (kind, val), label in grp:
            draw_key(lax, kind, val, margin, cy, g)
            lax.text(margin + key, cy, label, va='center', ha='left', fontsize=fs, color=INK)
            cy -= row
        cy -= sep
    # the maps span the print width less the margins: the dpi rises only by pdfTeX's rounding
    return save(fig, 'scenario-carte', fill_print=True)


def draw_key(lax, kind, val, cx, cy, g):
    """One key of the scenario legend, left edge at cx, centred on cy (inches)."""
    if kind == 'disc':
        lax.plot(cx + 0.07, cy, 'o', ms=7 * g, color=val, markeredgecolor='white')
        place(lax, 'relay', cx + 0.07, cy, 0.018 * g)
    elif kind == 'icon':
        place(lax, val, cx + 0.07, cy, 0.032 * g)
    elif kind == 'forest':  # the map's ground and edge, with one of its trees
        lax.add_patch(plt.Rectangle((cx, cy - 0.05), 0.15, 0.10, facecolor=FOREST, edgecolor='#7fae6a', lw=0.8))
        place(lax, 'tree', cx + 0.075, cy, 0.028 * g)
    else:  # the edges of the map's ellipses: solid for the burnt area, dashed for the heated zone
        burnt = val == '#f0b8a8'
        lax.add_patch(plt.Rectangle((cx, cy - 0.05), 0.15, 0.10, facecolor=val, lw=0.8 if burnt else 0.7,
                                    edgecolor='#b03a2e' if burnt else '#e0a060', ls='-' if burnt else '--'))


# --- the early discard ------------------------------------------------------------

def discard_figure():
    L = T[sty.LANG]
    Lv = 13
    ic = np.linspace(0, 1, 401)

    def limit(ic0):
        return np.clip(np.where(ic <= ic0, 1.0, 1 - (ic - ic0) / 0.4), 0, 1)
    fig, ax = plt.subplots(figsize=(3.95, 2.72))
    # IC_0 = 0.2 is the rule stack's threshold: its region takes the rule
    # stack's blue, the agent's other thresholds stay grey
    ax.fill_between(ic, 0, limit(0.2), color=RULE_FILL, zorder=1)
    ax.fill_between(ic, 0, 3 / (2 * Lv), color=RULE_CORE, zorder=1)
    ax.plot(ic, limit(0.2), color=BLUE, lw=1.8, zorder=3)
    for ic0 in (0.1, 0.3, 0.5):
        ax.plot(ic, limit(ic0), color=GREY, lw=0.9, ls='--', zorder=2)
    ax.axhline(0.5, color=MUTED, lw=0.8, ls=':')
    ax.text(0.985, 0.25, L['mframes'], ha='right', va='center', fontsize=8, color=MUTED)
    ax.text(0.985, 0.75, L['dframes'], ha='right', va='center', fontsize=8, color=MUTED)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel(L['ic']); ax.set_ylabel(L['rank'])
    decimal_axes(ax)
    h = [Patch(facecolor=RULE_FILL, edgecolor=BLUE), Patch(facecolor=RULE_CORE),
         Line2D([], [], color=GREY, lw=0.9, ls='--')]
    leg = top_legend(fig, h, [L['admitted'], L['always'], L['other']])
    fit_width(fig, 'rejet-anticipe', lambda: fig.tight_layout(rect=(0, 0, 1, below(fig, leg, 0.01)), pad=0.3))
    return save(fig, 'rejet-anticipe')


def figures():
    return [scenario_figure(), discard_figure()]
