"""The one generator of the cells of the article's tables: the numbers of a
column aligned on the decimal marker inside siunitx's \\tablenum, the local
siunitx settings of a table file, the rules between rows, the order of the
compared items and the tabularx preamble. The tables format their numbers
with common/notation.py; align() rewrites each formatted number inside a
\\tablenum with the same digits, so that no value changes. Inside a centered
X column every \\tablenum of the column gets the same box (its table-format),
hence the numbers line up on the decimal marker and the column stays centered
under its header. A comparator ("< 0,001") hangs before the box, and the
other cells of its column take a phantom of the same width. A cell that is
not a number (a dash, a level, a label) is left as it is."""
import re

import os

from ..common import paths
from ..common.notation import half_up

# The compared items, in the order of every table and every list of the
# article, the order of the first round (decision of 24 November 2026): the
# stacks (AOMDV with cross-layer timers and the access-only stack, where a
# table has them, after AOMDV and after the rule stack), the gaps between
# them, the GOPs and the fires.
STACKS = ('pq', 'rules', 'agents', 'hybrid')
GAPS = (('hybrid', 'rules'), ('agents', 'rules'), ('hybrid', 'agents'))
GOPS = ('3-9', '6-6', '9-3')
FIRES = ('F1', 'F2', 'F3')
# The header of every count of images whose PSNR at the sink reaches the
# threshold (the data's column usable), in both editions: the threshold is in
# the header, never broken from its comparator.
IMAGES = 'Images \\mbox{$\\geq$ 28~dB}'


def setup(lang):
    """Local siunitx settings, written at the head of a table file (the table
    float is a group, so they stop at its end): an explicit plus kept on the
    gaps; digit groups as each edition writes them, a thin space from four
    digits in French, a comma from five in English (MDPI)."""
    if lang == 'fr':
        return '\\sisetup{retain-explicit-plus, group-minimum-digits = 4}'
    return '\\sisetup{retain-explicit-plus, group-separator = {,}, group-minimum-digits = 5}'


def rules(groups):
    """The rule written after each row of a table body, from the group of
    each row (the label a \\multirow writes once, vertically centered, over
    the rows of its group; a table without groups gives each row a group of
    its own): no rule between the rows of a group, a \\midrule between two
    groups, the \\bottomrule after the last row. No partial rule
    (\\cmidrule) runs between two rows, hence none beside a group's label; a
    \\cmidrule(lr) is drawn only under a header that spans several columns.
    Returns one string per row, '' within a group."""
    groups = list(groups)
    out = []
    for i, g in enumerate(groups):
        if i == len(groups) - 1:
            out.append('\\bottomrule')
        else:
            out.append('\\midrule' if groups[i + 1] != g else '')
    return out


def parse(cell, lang):
    """(comparator, sign, integer digits, decimal digits) of a formatted
    number, or None when the cell is not a number."""
    s = cell.strip()
    cmp = ''
    m = re.fullmatch(r'\$<\s*(.*)\$', s)
    if m:
        cmp, s = '<', m.group(1).strip()
    sign = ''
    if s.startswith('$-$'):
        sign, s = '-', s[3:]
    elif s[:1] in '+-' and s[:1]:
        sign, s = s[0], s[1:]
    if lang == 'fr':
        s = s.replace('{,}', '.').replace('\\,', '')
    else:
        s = re.sub(r'(?<=\d),(?=\d{3}(?!\d))', '', s)
    m = re.fullmatch(r'(\d+)(?:\.(\d+))?', s)
    if not m:
        return None
    return cmp, sign, m.group(1), m.group(2) or ''


def align(column, lang, pvalues=False):
    """The cells of one column, numbers rewritten as \\tablenum of a common
    format; returns the column unchanged when it holds no number. A column of
    p (pvalues) keeps the comparator's room even when no cell needs it, so
    that every p column of the article puts its digits at the same place."""
    parsed = [parse(c, lang) for c in column]
    nums = [p for p in parsed if p]
    if not nums:
        return list(column)
    signed = any(p[1] for p in nums)
    comparator = pvalues or any(p[0] for p in nums)
    whole = max(len(p[2]) for p in nums)
    frac = max(len(p[3]) for p in nums)
    fmt = '%s%d.%d' % ('+' if signed else '', whole, frac)
    # siunitx's input is the decimal point in both editions: it prints the
    # edition's marker (a comma in French, set in the preamble), and the
    # source never reads "1,000" as a thousand
    mark = '.'
    out = []
    for c, p in zip(column, parsed):
        if not p:
            out.append(c)
            continue
        cmp, sign, i, d = p
        num = '\\tablenum[table-format=%s]{%s%s%s}' % (fmt, sign, i, mark + d if d else '')
        if comparator:
            # the comparator, its space and the number in one box: no line
            # break inside a cell (an overfull box shows a column too narrow)
            num = '\\mbox{%s%s}' % ('$<$\\;' if cmp else '\\phantom{$<$\\;}', num)
        out.append(num)
    return out


def align_rows(rows, lang, columns=None, pcols=()):
    """Align, column by column, a list of rows (lists of cells of equal
    length). columns: the indices to align, every column by default; pcols:
    the indices of the columns of p."""
    if not rows:
        return rows
    n = len(rows[0])
    cols = range(n) if columns is None else columns
    out = [list(r) for r in rows]
    for j in cols:
        col = align([r[j] for r in rows], lang, j in pcols)
        for r, c in zip(out, col):
            r[j] = c
    return out


def intervals(column, nd, lang, lines=1, plus=True):
    """A column of gaps written as the text writes them, the gap then its 95 %
    interval in brackets ('+2,02 [1,50 ; 2,53]', in English '+2.02 [1.50,
    2.53]'), from Estimates (None prints a dash); rounded half up, as in the
    text. The gap sits in a \\tablenum whose format is common to the column,
    so that the gaps line up; each bound hugs its bracket, and the room a
    shorter bound leaves (a sign or a digit the column's widest has) goes
    after the closing bracket, that of the lower bound then that of the
    upper, so that every cell of the column has the same width and no blank
    opens between the gap and its interval: the opening
    brackets line up, the bounds do not. lines=2 sets the interval, centred, under the gap. A cell
    never breaks inside a line. A bound that would print 0 without being 0
    gets one more decimal, with its gap and the other bound, as the text
    writes it (−1,90 [−3,82 ; 0,01]): the reader then sees on which side of
    zero the interval ends (the tables of E5). plus=False: a
    column of sizes, not of gaps (the partial eta squared of the ANOVA
    table), without the explicit plus."""
    def rounded(e):
        for d in (nd, nd + 1):
            r = [half_up(x, d) for x in (e.mean, e.lo, e.hi)]
            if all(v != 0 or x == 0 for v, x in zip(r[1:], (e.lo, e.hi))):
                break
        # a value that rounds to zero prints without a sign, as signed() writes it
        return [abs(v) if v == 0 else v for v in r]
    parts = [None if e is None else rounded(e) for e in column]
    whole = lambda v: len(str(abs(v)).split('.')[0])   # noqa: E731
    vals = [[p[i] for p in parts if p] for i in range(3)]
    width = [max(whole(v) for v in vals[i]) for i in range(3)]
    signed = [any(v < 0 for v in vals[i]) for i in range(3)]
    gap_fmt = '%s%d.%d' % ('+' if plus else '', width[0], max(len(str(p[0]).partition('.')[2]) for p in parts if p))

    def pad(v, i):
        """The room bound v leaves against the column's widest bound i."""
        return '\\phantom{$-$}' * (signed[i] and v >= 0) + '\\phantom{0}' * (width[i] - whole(v))
    sep = '~; ' if lang == 'fr' else ', '
    out = []
    for p in parts:
        if p is None:
            out.append('--')
            continue
        gap = '\\tablenum[table-format=%s]{%s%s}' % (gap_fmt, '+' if plus and p[0] > 0 else '', p[0])
        bounds = '{[}\\num{%s}%s\\num{%s}{]}' % (p[1], sep, p[2])
        if lines == 2:
            out.append('\\begin{tabular}[c]{@{}c@{}}%s\\\\ %s\\end{tabular}' % (gap, bounds))
        else:
            out.append('\\mbox{%s %s%s%s}' % (gap, bounds, pad(p[1], 1), pad(p[2], 2)))
    return out


# Inside the float's adjustwidth, tabularx may leave a row a few hundredths
# of a point short of \linewidth, which TeX reports as an underfull row: a
# stretch of the space between columns (0.5 pt at most) absorbs it, the left
# padding of the first column kept.
FILL = '@{\\extracolsep{0pt plus 0.5pt}\\hspace{\\tabcolsep}}'


def xcols(widths, stub='', fill=False):
    """A tabularx preamble: an optional stub column, then centered X columns
    of the relative widths given (strings, summing to their count). Each X
    column holds its widest header line or cell plus an equal share of the
    free width, so that the gaps between columns are equal. fill: the
    columns may stretch by FILL, against an underfull row."""
    return (FILL if fill else '') + stub + ''.join('>{\\hsize=%s\\hsize\\centering\\arraybackslash}X' % w for w in widths)


def write(lang, name, lines):
    """<lang>_<name>.tex of paths.TABLES from its lines; returns the path."""
    os.makedirs(paths.TABLES, exist_ok=True)
    path = os.path.join(paths.TABLES, '%s_%s.tex' % (lang, name))
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return path
