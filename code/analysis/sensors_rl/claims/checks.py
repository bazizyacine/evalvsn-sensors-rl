"""The frame of the checks of the text's numbers: one line per number, the
block, what is computed, the value as the text writes it, the value computed
here, and OK, DIFFERS or MISSING (a source file missing). Pairs share their
seeds (fire, realisation): mean difference, 95 % Student interval, p, Holm
within the family the text names. Rounding is half up, as everywhere in the
package. A p of the text is checked in the form this package gives it
(p_text): its value and its decimals both come from the computed p.

The written form of a line is the text itself: each of its fragments
(separated by ' … ') is found in the French sources, sensors-fr.tex and
sections/fr_*.tex, once their LaTeX is read as plain text (plain); a line
that checks a generated table or another file names it (source). A fragment
the source no longer holds makes the line MISSING-IN-TEXT, and every number
a line checks appears in its written form: a number changed in the text
breaks its line, it does not slip by."""
import glob
import os
import re
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

from ..common import data, paths, stats
from ..common.notation import half_up, text as fr

FRAGMENT = ' … '
PREFIX = {'kilo': 'k', 'milli': 'm', 'giga': 'G', 'deci': 'd'}
UNIT = {'bel': 'B', 'metre': 'm', 'second': 's', 'hertz': 'Hz', 'watt': 'W', 'bit': 'bit', 'hour': 'h',
        'percent': '%', 'celsius': '°C', 'degree': '°'}
PLAIN = (('$+$', '+'), ('$-$', '−'), ('\\textminus', '−'), ('{,}', ','), ('~;', ' ;'), ('~', ' '), ('\\,', ' '),
         ('\\%', '%'), ('\\newline', ' '), ('\\geq', '≥'), ('\\leq', '≤'), ('$', ''))


def _unit(u):
    """A siunitx unit as the PDF prints it: \\deci\\bel\\per\\metre, dB/m."""
    out = ''
    for m in re.finditer(r'\\(\w+)|([^\\]+)', u):
        name, literal = m.groups()
        out += literal if literal else '/' if name == 'per' else PREFIX.get(name, UNIT.get(name, name))
    return out


def _first_argument(s, macro):
    """s with every macro{a}{b} replaced by a (\\texorpdfstring)."""
    out, i, key = [], 0, macro + '{'
    while True:
        j = s.find(key, i)
        if j < 0:
            return ''.join(out) + s[i:]
        out.append(s[i:j])
        args, k = [], j + len(key) - 1
        for _ in range(2):
            depth, a = 0, k
            while True:
                depth += {'{': 1, '}': -1}.get(s[k], 0)
                k += 1
                if depth == 0:
                    break
            args.append(s[a + 1:k - 1])
        out.append(args[0])
        i = k


def _cell(x):
    """A \\tablenum of the tables as siunitx prints it: decimal comma, minus
    sign, thousands set off from four digits (group-minimum-digits = 4)."""
    sign, x = (x[0], x[1:]) if x[:1] in '+-' else ('', x)
    i, dot, d = x.partition('.')
    if len(i) >= 4:
        i = re.sub(r'(?<=\d)(?=(\d{3})+$)', ' ', i)
    return sign.replace('-', '−') + i + (',' + d if dot else '')


def plain(tex):
    """The LaTeX of the text as the reader reads it, the forms the claims
    write: comments dropped, \\texorpdfstring{a}{b} as a, \\SI{x}{unit} as
    'x unit', $-$ and $+$ as − and +, {,} as a comma, ~ and \\, as spaces,
    \\geq and \\leq as ≥ and ≤, spaces collapsed."""
    s = re.sub(r'(?<!\\)%.*', '', tex)
    s = _first_argument(s, '\\texorpdfstring')
    s = re.sub(r'\\SI\{([^}]*)\}\{([^}]*)\}', lambda m: (m[1] + ' ' + _unit(m[2])).strip(), s)
    s = re.sub(r'\\tablenum(?:\[[^\]]*\])?\{([^}]*)\}', lambda m: _cell(m[1]), s)
    # a gap cell of the tables of E5 (tables/cells.intervals):
    # the gap and its interval on one line, in an \mbox, the room a shorter
    # bound leaves written as phantoms; read as the text writes them, without
    # the box and the phantoms ('+2,02 [1,50 ; 2,53]')
    s = re.sub(r'\\num\{([^}]*)\}', lambda m: _cell(m[1]), s).replace('{[}', '[').replace('{]}', ']')
    s = re.sub(r'\\phantom\{(?:\$-\$|0)\}', '', s)
    s = re.sub(r'\\mbox\{([^{}\[\]]* \[[^{}\[\]]*\])\}', r'\1', s)
    # a p the text keeps on one line, \mbox{$p < 0{,}001$}, read as text; the
    # p cells of the tables, \mbox{$<$\;...}, stay as they are
    s = re.sub(r'\\mbox\{(\$[^$]*\$)\}', r'\1', s)
    for a, b in PLAIN:
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s)


_SOURCES = {}
# The French replies of the first round, delivered: the lines that read them
# name them as their source.
LETTER_1 = 'submission-fr/round1/reponse-relecteur-1-fr.md'
LETTER_2 = 'submission-fr/round1/reponse-relecteur-2-fr.md'


def table(name):
    """The source of a line that reads a generated table, fr_NAME.tex."""
    return 'src/tables/fr_%s.tex' % name


def source_text(source):
    """The plain text of a source: 'text' the French sources of the article,
    else a file under writing/sensors-rl (a generated table, a letter in
    Markdown, read as it is); None when it is not there (an export without
    the text)."""
    if source not in _SOURCES:
        if source == 'text':
            main = os.path.join(paths.SRC, 'sensors-fr.tex')
            files = [main] + sorted(glob.glob(os.path.join(paths.SRC, 'sections', 'fr_*.tex'))) if os.path.isfile(main) else []
        else:
            files = [f for f in [os.path.join(paths.WRITING, source)] if os.path.isfile(f)]
        read = lambda f: plain(open(f, encoding='utf-8').read()) if f.endswith('.tex') else re.sub(r'\s+', ' ', open(f, encoding='utf-8').read())
        _SOURCES[source] = ' '.join(read(f) for f in files) if files else None
    return _SOURCES[source]


def _joined(s):
    """s with its thousands set off by a space joined ('2 195' as '2195')
    and without signs, to find a number in it."""
    return re.sub(r'(?<=\d) (?=\d{3}(?!\d))', '', s).replace('−', '').replace('+', '')


def unwritten(written, checks):
    """The expected values of checks that the written form does not hold:
    a number checked to nd decimals ('=', 'b', '<=', '>='), as the text
    prints it without its sign, or a p in its written form."""
    flat = _joined(written)
    out = []
    for computed, op, expected, nd in checks:
        if isinstance(computed, bool) or isinstance(expected, bool):
            continue
        if op == 'p':
            value = expected.split(' ', 1)[1]
            if not re.search(r'(?<![\d,])%s(?!\d|,\d)' % re.escape(value), written) or (expected[0] != '=' and expected not in written):
                out.append(expected)
        elif op in ('=', 'b', '<=', '>='):
            token = fr(abs(expected), nd).replace('−', '')
            if not re.search(r'(?<![\d,])%s(?!\d|,\d)' % re.escape(token), flat):
                out.append(token)
    return out

mean = stats.mean
holm = stats.holm
pearson = stats.pearson
slope = stats.slope


def p_text(p, op='='):
    """p as the text writes it: '< 0,001'
    below that threshold, else op and p, with three decimals below 0,1 and
    two above ('= 0,015', '= 0,35'), half up. A bound over several
    comparisons stays strictly true: op '≥' writes their smallest p rounded
    down, op '≤' their largest rounded up, at the decimals of that form
    (a minimum of 0,136 gives '≥ 0,13', a maximum of 0,0031 '≤ 0,004')."""
    if p < 0.001:
        return '< 0,001'
    if op == '=':
        return '= ' + fr(p, 3 if half_up(p, 3) < Decimal('0.1') else 2)
    nd = 3 if p < 0.1 else 2
    rounding = ROUND_FLOOR if op == '≥' else ROUND_CEILING
    b = Decimal(repr(p)).quantize(Decimal(1).scaleb(-nd), rounding=rounding)
    if nd == 3 and b >= Decimal('0.1'):
        b = Decimal(repr(p)).quantize(Decimal('0.01'), rounding=rounding)
    return '%s %s' % (op, str(b).replace('.', ','))


def flips(p, op='='):
    """A p under 0,05 that prints 0,050 (half up, or rounded up for a bound
    '≤'): its rounding would read as no significance, so the text cannot
    print it by the rule."""
    return (0.049 if op == '≤' else 0.0495) <= p < 0.05 and op != '≥'


def pv(p, written):
    """The check of a p as the text writes it: '= 0,35', '< 0,001', or a
    bound over several comparisons, '≥ 0,84' (the smallest p rounded down)
    or '≤ 0,004' (the largest rounded up). It is OK when p_text gives
    exactly the written form."""
    return (p, 'p', written, 0)


class Claims:
    """The lines of one block of checks, printed with columns of the widths given."""

    def __init__(self, written_width, computed_width):
        self.lines = []
        self.widths = (written_width, computed_width)

    def claim(self, block, label, written, checks, source='text'):
        """checks: (computed, op, expected, nd); op '=' compares the half-up
        rounding to nd decimals, '<' and '>' compare the raw value, '<=' and
        '>=' the rounded one; op 'b' (bound_check) is '=' for an interval
        bound, which prints 0 only when it is 0; op 'p' (pv) compares the
        form of a p, expected being the written form. A computed None means
        the source file is missing. written: the fragments of the source
        (the French text, or a file under writing/sensors-rl) that hold the
        numbers, joined by FRAGMENT; one it does not hold, or a number
        checked that written does not hold, makes the line MISSING-IN-TEXT."""
        if source == 'text':
            _READ.extend(written.split(FRAGMENT))
        if any(c[0] is None for c in checks):
            self.lines.append((block, label, written, 'MISSING', 'MISSING', source))
            return
        ok, shown = True, []
        for computed, op, expected, nd in checks:
            if isinstance(computed, bool):
                good = computed == expected
                shown.append(str(computed))
            elif op == 'p':
                computed = float(computed)
                rel = expected[0] if expected[0] in '≥≤' else '='
                form = p_text(computed, rel)
                good = form == expected and not flips(computed, rel)
                shown.append(form + (' (0,050 : à signaler)' if flips(computed, rel) else ''))
            else:
                computed = float(computed)
                r = float(Decimal(repr(computed)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))
                good = {'=': r == expected, '<': computed < expected, '>': computed > expected,
                        '<=': r <= expected, '>=': r >= expected,
                        'b': r == expected and (expected != 0 or computed == 0)}[op]
                shown.append(fr(computed, nd + 2) if op in ('<', '>') or (op == 'b' and not good) else fr(computed, nd))
            ok = ok and good
        verdict = 'OK' if ok else 'DIFFERS'
        text = source_text(source)
        if text is not None:
            absent = [f for f in written.split(FRAGMENT) if f not in text] + ['%s (non écrit)' % v for v in unwritten(written, checks)]
            if absent:
                verdict = 'MISSING-IN-TEXT'
                shown.append('absent : ' + ' | '.join(absent))
        self.lines.append((block, label, written, ' ; '.join(shown), verdict, source))

    def report(self):
        """Prints the lines and their counts, then where their written forms
        were found; 1 if a line DIFFERS or is MISSING-IN-TEXT, else 0."""
        w, c = self.widths
        width = max(len(l[1]) for l in self.lines)
        for block, label, written, computed, verdict, _ in self.lines:
            print('%-4s  %-*s  texte : %-*s  calcul : %-*s  %s' % (block, width, label, w, written, c, computed, verdict))
        ok = sum(1 for l in self.lines if l[4] == 'OK')
        bad = [l for l in self.lines if l[4] == 'DIFFERS']
        miss = [l for l in self.lines if l[4] == 'MISSING']
        gone = [l for l in self.lines if l[4] == 'MISSING-IN-TEXT']
        print('\n%d lignes : %d OK, %d DIFFERS, %d MISSING' % (len(self.lines), ok, len(bad), len(miss)))
        read = {}
        for l in self.lines:
            key = 'le texte français' if l[5] == 'text' else l[5]
            read[key] = read.get(key, 0) + 1
        unread = sorted({l[5] for l in self.lines if source_text(l[5]) is None})
        print('  formes écrites lues dans %s ; %d MISSING-IN-TEXT%s' % (
            ', '.join('%s : %d' % (k, n) for k, n in sorted(read.items(), key=lambda kv: kv[0] != 'le texte français')),
            len(gone), ' ; sources absentes, non lues : ' + ', '.join(unread) if unread else ''))
        for l in bad + miss + gone:
            print('  %s %s : %s' % (l[4], l[0], l[1]))
        _BLOCKS.update(l[0][0] for l in self.lines)
        return 1 if bad or gone else 0


def pair_checks(r, d, lo, hi, nd=2, sign=1):
    """The difference and its interval as the text writes them (sign=-1: the
    text writes the magnitude of a negative difference and its bounds swapped);
    a bound printing 0 must be 0, as in bound_check."""
    if sign > 0:
        return [(r['d'], '=', d, nd), (r['lo'], 'b', lo, nd), (r['hi'], 'b', hi, nd)]
    return [(-r['d'], '=', d, nd), (-r['hi'], 'b', lo, nd), (-r['lo'], 'b', hi, nd)]


# A gap as the text writes it: the signed difference, its unit, the interval
# in brackets, then its p, e.g. '+1,52 dB [1,12 ; 1,92], p < 0,001',
# '+1 161 [1 046 ; 1 276], p < 0,001' or, the p given apart, '+1,06 dB
# [0,37 ; 1,75] au GOP 3-9 (p = 0,003'; without p when the text gives none
# there ('−1,28 dB [−1,81 ; −0,76]').
NUMBER = r'[+−]?\d[\d ]*(?:,\d+)?'
WRITTEN_GAP = re.compile(r'(?<![\d,])(?P<d>%s)(?: [^\[\]\d+−…]{0,30}?)? ?\[(?P<lo>%s) ; (?P<hi>%s)\]' % (NUMBER, NUMBER, NUMBER))
WRITTEN_P = re.compile(r'p (?P<op>[<=≥≤]) (?P<v>\d,\d+)')


def written(s):
    """(value, decimals) of a number as the French text writes it."""
    s = s.strip().replace(' ', '').replace('−', '-').replace(',', '.')
    return float(s), len(s.partition('.')[2])


# The other way round: each interval and each p of the French text lies in an
# occurrence of a fragment some line reads, so that a number changed in one
# place of the text, even where a line still finds the others, breaks.
_READ = []
_BLOCKS = set()
TEXT_NUMBER = re.compile(r'\[%s ; %s\]|p [<=≥≤] \d,\d+' % (NUMBER, NUMBER))


def unread():
    """(position, number, context) of every interval '[lo ; hi]' and every
    p of the French text that no line reads, but the threshold p < 0,05."""
    text = source_text('text')
    held = bytearray(len(text))
    for f in set(_READ):
        i = text.find(f)
        while i >= 0:
            held[i:i + len(f)] = b'\x01' * len(f)
            i = text.find(f, i + 1)
    return [(m.start(), m[0], text[max(0, m.start() - 80):m.end() + 20]) for m in TEXT_NUMBER.finditer(text)
            if m[0] != 'p < 0,05' and not all(held[m.start():m.end()])]


def report_unread():
    """After the four blocks of the claims step (P, G, A and S): prints the
    intervals and the p of the French text no line reads, NON LU each; 1 if
    one is, else 0. Without the text, or run without the other blocks, it
    says so and checks nothing."""
    if source_text('text') is None:
        print('\n  texte français absent : la lecture du texte par les lignes n\'est pas vérifiée')
        return 0
    if not set('PGAS') <= _BLOCKS:
        print('\n  blocs %s seulement : la lecture du texte par les lignes n\'est vérifiée que par python3 -m sensors_rl claims'
              % ''.join(sorted(_BLOCKS)))
        return 0
    left = unread()
    text = source_text('text')
    print('\n--- le texte relu : intervalles et valeurs de p du texte français, chacun lu par une ligne ---')
    for _, number, context in left:
        print('  %-18s ...%s...  NON LU' % (number, context))
    print('%d intervalles et valeurs de p dans le texte : %d lus, %d NON LU'
          % (len([m for m in TEXT_NUMBER.finditer(text) if m[0] != 'p < 0,05']),
             len([m for m in TEXT_NUMBER.finditer(text) if m[0] != 'p < 0,05']) - len(left), len(left)))
    return 1 if left else 0


def bound_check(x, text):
    """A bound of an interval to the decimals written (op 'b'): a bound that
    prints 0 while it is not 0 DIFFERS, the text then writes the gap and its
    interval with one more decimal (−1,90 [−3,82 ; 0,01])."""
    v, nd = written(text)
    return (x, 'b', v, nd)


def interval_checks(e, text):
    """An Estimate's interval alone, '[0,07 ; 0,95]' as the text writes it."""
    m = re.match(r'^\[(%s) ; (%s)\]$' % (NUMBER, NUMBER), text)
    if m is None:
        raise ValueError('not an interval as the text writes it: %r' % text)
    return [bound_check(e.lo, m[1]), bound_check(e.hi, m[2])]


def gap_checks(e, text, sign=1):
    """The checks of an Estimate against a gap as the text writes it: the
    difference and its bounds to the decimals written, and p when the text
    gives it there, Holm's when the estimate belongs to a family, else its
    single test, in the form of p_text. sign=-1: the text writes the gap the
    other way round, b - a. None (the source missing) gives a MISSING line."""
    if e is None:
        return [(None, '=', 0, 0)]
    m = WRITTEN_GAP.search(text)
    if m is None:
        raise ValueError('not a gap as the text writes it: %r' % text)
    d, nd = written(m['d'])
    mean_, low, high = (e.mean, e.lo, e.hi) if sign > 0 else (-e.mean, -e.hi, -e.lo)
    checks = [(mean_, '=', d, nd), bound_check(low, m['lo']), bound_check(high, m['hi'])]
    q = WRITTEN_P.search(text, m.end()) or ([None] + list(WRITTEN_P.finditer(text, 0, m.start())))[-1]
    if q is not None:
        checks.append(pv(e.p if e.holm is None else e.holm, '%s %s' % (q['op'], q['v'])))
    return checks


SPAN = re.compile(r'(?<![\d,])(?P<a>%s)(?: [^\s\[\]…\d]+)?(?: \[[^\]]*\])? (?:à|et) (?P<b>%s)' % (NUMBER, NUMBER))


def span_checks(xs, text, ps=(), ordered=False):
    """A range as the text writes it, 'a à b' in either order, each end
    possibly followed by its unit and its interval ('de −14,3 [−15,6 ; −13,0]
    à −15,6 [−16,8 ; −14,4]'), the first of written: its ends, the
    smallest and the largest of xs, to the decimals written; ordered, 'a et
    b', xs[0] and xs[1] in that order. Then the p the text gives the
    comparisons it covers, ps, one each: 'p ≥ x' is their smallest, 'p ≤ x'
    and 'p < 0,001' their largest, 'p = x' each of them."""
    m = SPAN.search(text)
    if m is None:
        raise ValueError('not a range as the text writes it: %r' % text)
    (a, na), (b, nb) = written(m['a']), written(m['b'])
    if ordered:
        checks = [(xs[0], '=', a, na), (xs[1], '=', b, nb)]
    else:
        (lo, nlo), (hi, nhi) = sorted(((a, na), (b, nb)))
        checks = [(min(xs), '=', lo, nlo), (max(xs), '=', hi, nhi)]
    q = WRITTEN_P.search(text)
    if q is not None:
        if q['op'] == '≥':
            checks.append(pv(min(ps), '≥ ' + q['v']))
        elif q['op'] == '=':
            checks += [pv(p, '= ' + q['v']) for p in ps]
        else:
            checks.append(pv(max(ps), '%s %s' % (q['op'], q['v'])))
    return checks


BOUNDS = re.compile(r'[Ii]ntervalles (?:vont )?de (?P<lo>%s) à (?P<hi>%s)' % (NUMBER, NUMBER))


def holm_or_p(e):
    """The p of an Estimate as the text gives it: Holm's within its family,
    else its single test's."""
    return e.p if e.holm is None else e.holm


def range_checks(es, text, ordered=False):
    """The checks of a range of gaps with that of their intervals, as the text
    writes them in one passage, '+1,06 à +2,00 dB, intervalles de 0,37 à
    2,62 dB, p ≤ 0,004': the ends of the gaps of es (ordered, 'a et b', the
    gaps of es in that order) and the p the text gives them, Holm's within
    the family, else the single test's (span_checks); then the lowest and the
    highest bound of their intervals. The text may set them apart ('1,84 dB
    au GOP 3-9 à 6,06 dB'): the caller then passes the numbers as they would
    stand together, and the written form of its line holds them all."""
    m = BOUNDS.search(text)
    if m is None:
        raise ValueError('no range of intervals as the text writes it: %r' % text)
    return (span_checks([e.mean for e in es], text, [holm_or_p(e) for e in es], ordered=ordered)
            + [bound_check(min(e.lo for e in es), m['lo']), bound_check(max(e.hi for e in es), m['hi'])])


def gap(e):
    """An Estimate as the dict the checks read: n, d, lo, hi, p and, within a
    family, holm."""
    out = dict(n=e.n, d=e.mean, lo=e.lo, hi=e.hi, p=e.p)
    if e.holm is not None:
        out['holm'] = e.holm
    return out


def paired(a, b):
    """Mean of a - b over the shared seeds, its 95 % interval and p, as a dict."""
    return gap(stats.paired(a, b))


def ci_mean(v):
    e = stats.estimate(v)
    return e.lo, e.hi


def revision():
    """The rows of revision.tsv, read once; None when it is missing."""
    return data.table('revision.tsv')


def rev(arm, split='9M3D', period='p9', m='psnr', fire=None):
    """{seed: value} of an arm of revision.tsv on the 40 m grid."""
    return data.select(revision(), arm, m, split, period, '40', fire)


def pooled(arm, m='psnr'):
    """Per seed, the mean over the three GOPs."""
    return data.pooled_over_gops([rev(arm, s, m=m) for s in data.SPLITS])
