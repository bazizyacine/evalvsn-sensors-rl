"""The one style of the article's figures: a sans-serif type (Liberation
Sans, Arial's metrics, the Helvetica of the TikZ diagrams), the Okabe-Ito
palette, readable under every colour-vision deficiency, one colour per stack
in every figure (grey AOMDV, blue rule stack, orange agents stack, green
hybrid stack; the architecture's TikZ uses the same), means only, legend
colours equal to the marks', the edition's decimal marker on the axes.

The panels follow Figure 2 of the MDPI template: two at most
a row, each with its letter alone under it, (a) with the letter bold, and
with its own y-axis title; what a panel shows is in the caption. The legend
of the series is one framed box at the top right, or in the free cell of the
second row when a third panel leaves one.

Each figure is drawn at the width it prints at (PRINT, the width of its
\\includegraphics in sections/fr_*.tex), so that its type prints at the size
set here: 8 pt for ticks, legends and labels, 9 pt for axis titles. The PNG
is 8-bit RGB without alpha at 600 dpi, as MDPI asks. LANG is the edition
being drawn; use(lang) sets it."""
import io
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
from PIL import Image  # noqa: E402

from ..common import paths  # noqa: E402
from .palette import (BLUE, GREEN, GREY, GRID, INK, MUTED, ORANGE, PURPLE, RULE_CORE, RULE_FILL,  # noqa: E402,F401
                      SKY, VERMIL, YELLOW)

plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Liberation Sans', 'DejaVu Sans'],
    'font.size': 9, 'axes.titlesize': 9.5,
    'axes.labelsize': 9, 'legend.fontsize': 8, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.spines.top': False, 'axes.spines.right': False,
    'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.grid': True, 'axes.axisbelow': True,
    'lines.linewidth': 1.6, 'lines.markersize': 5,
    # the symbols in the sans-serif of the labels
    'mathtext.fontset': 'custom', 'mathtext.rm': 'Liberation Sans', 'mathtext.it': 'Liberation Sans:italic',
    'mathtext.bf': 'Liberation Sans:bold', 'mathtext.sf': 'Liberation Sans', 'mathtext.fallback': 'stixsans',
})
# The print widths, in inches: the MDPI class's \textwidth (394.355 pt) or its
# full width under adjustwidth (525.522 pt), times the factor of the figure's
# \includegraphics in sections/fr_*.tex. When the .tex changes a factor,
# change it here and regenerate.
TEXT_W, FULL_W = 394.35522 / 72.27, 525.52245 / 72.27
PRINT = {'scenario-carte': 0.8 * TEXT_W, 'rejet-anticipe': 0.72 * TEXT_W,
         'comparatif-psnr': 0.82 * FULL_W, 'comparatif-m1': 0.82 * FULL_W,
         'galerie': 0.85 * TEXT_W, 'trajectoires': 0.85 * TEXT_W}
PAD = 0.04  # white margin around the drawing, inches
LANG = 'fr'
T = {
    'fr': {'psnr': 'PSNR au puits (dB)',
           'floor': 'seuil de 28 dB',
           'x': '$x$ (m)', 'y': '$y$ (m)', 'alive': 'relais en service', 'zone': 'zone chauffée, TZ = 60 s',
           'burnt': 'surface brûlée', 'front': 'détruit par le front', 'early': 'en panne avant le front',
           'heated': 'relais dans la zone chauffée', 'camera': 'caméra (0, 0), mode alarme', 'sink': 'puits (360, 360)', 'ignition': 'allumage du feu',
           'forest': 'forêt instrumentée',
           'wind': 'vent $U$', 't': '$t$ = %d s', 'ic': 'IC', 'rank': '$(\\rho - 1)/(2L)$',
           'admitted': 'admis, IC$_0$ = 0,2', 'other': 'limite pour IC$_0$ = 0,1, 0,3 ou 0,5',
           'mframes': 'frames M', 'dframes': 'frames D', 'always': '$\\rho \\leq 3$ toujours admis',
           'ref': 'codée,\nsans perte réseau',
           # the stacks' short names, those of the tables
           'stack': {'aomdv': 'AOMDV', 'rules': 'Règles', 'access': 'Accès seul', 'agents': 'Agents', 'hybrid': 'Hybride'},
           'md': 'GOP (M-D)', 'm1loss': 'perte du niveau M1 (%)'},
    'en': {'psnr': 'PSNR at the sink (dB)',
           'floor': '28 dB threshold',
           'x': '$x$ (m)', 'y': '$y$ (m)', 'alive': 'relay in service', 'zone': 'heated zone, TZ = 60 s',
           'burnt': 'burned area', 'front': 'destroyed by the front', 'early': 'failed before the front',
           'heated': 'relay in the heated zone', 'camera': 'camera (0, 0), alarm mode', 'sink': 'sink (360, 360)', 'ignition': 'fire ignition',
           'forest': 'instrumented forest',
           'wind': 'wind $U$', 't': '$t$ = %d s', 'ic': 'IC', 'rank': '$(\\rho - 1)/(2L)$',
           'admitted': 'admitted, IC$_0$ = 0.2', 'other': 'limit for IC$_0$ = 0.1, 0.3 or 0.5',
           'mframes': 'M frames', 'dframes': 'D frames', 'always': '$\\rho \\leq 3$ always admitted',
           'ref': 'coded,\nno network loss',
           'stack': {'aomdv': 'AOMDV', 'rules': 'Rules', 'access': 'Access only', 'agents': 'Agents', 'hybrid': 'Hybrid'},
           'md': 'GOP (M-D)', 'm1loss': 'M1 level loss (%)'},
}


def num(v, nd=1):
    s = f'{v:.{nd}f}'
    return s.replace('.', ',') if LANG == 'fr' else s


def decimal_axes(*axes):
    f = FuncFormatter(lambda v, _: (('%g' % v).replace('.', ',') if LANG == 'fr' else '%g' % v).replace('-', '−'))
    for a in axes:
        a.xaxis.set_major_formatter(f)
        a.yaxis.set_major_formatter(f)


def letter(i):
    """The letter of panel i as the MDPI template prints it: (a), the letter bold."""
    return '($\\mathbf{%s}$)' % chr(97 + i)


def letter_panels(axes):
    """Each panel's letter alone, under it, a blank line under its x-axis
    title; the caption describes the panel."""
    for i, a in enumerate(axes):
        xl = a.get_xlabel()
        a.set_xlabel((xl + '\n\n' if xl else '') + letter(i))


def top_legend(fig, handles, labels, ncol=1, **kw):
    style = dict(loc='upper right', bbox_to_anchor=(1.0, 1.0), ncol=ncol, frameon=True, fancybox=False,
                 edgecolor='#9a9a92', framealpha=1.0, borderpad=0.5, handlelength=1.8, labelspacing=0.35,
                 borderaxespad=0.1)
    style.update(kw)
    return fig.legend(handles, labels, **style)


def below(fig, artist, gap=0.06):
    """The figure fraction left under a legend at the top, less a gap (inches)."""
    bb = artist.get_window_extent(fig.canvas.get_renderer())
    return bb.y0 / fig.dpi / fig.get_figheight() - gap / fig.get_figheight()


def fit_width(fig, name, layout=None, keep_aspect=False):
    """Set the figure's width so that the saved PNG (its tight box plus PAD)
    is the print width of `name`; `layout` redoes the layout at each try, and
    `keep_aspect` scales the height with the width."""
    target = PRINT[name]
    for _ in range(8):
        if layout:
            layout()
        w = fig.get_tightbbox(fig.canvas.get_renderer()).width + 2 * PAD
        if abs(w - target) < 0.002:
            return
        W, H = fig.get_size_inches()
        fig.set_size_inches(W + target - w, H * (W + target - w) / W if keep_aspect else H)
    if layout:
        layout()


def save(fig, name, fill_print=False):
    """600 dpi, 8-bit RGB: matplotlib writes RGBA, MDPI asks for RGB.
    `fill_print`: the drawing is narrower than its print width, which the
    \\includegraphics enlarges; the dpi rises so that the PNG still prints at
    600 ppi or more (one more dot per inch for pdfTeX's rounding of the scale)."""
    os.makedirs(paths.FIGURES, exist_ok=True)
    path = os.path.join(paths.FIGURES, f'{LANG}_{name}.png')
    dpi = 600
    if fill_print:
        w = fig.get_tightbbox(fig.canvas.get_renderer()).width + 2 * PAD
        dpi = max(600, math.ceil(600 * PRINT[name] / w) + 1)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', pad_inches=PAD, facecolor='white')
    plt.close(fig)
    buf.seek(0)
    Image.open(buf).convert('RGB').save(path, dpi=(dpi, dpi))
    return os.path.basename(path)


def use(lang):
    """Draw the figures of the edition lang ('fr' or 'en') from now on."""
    global LANG
    LANG = lang
