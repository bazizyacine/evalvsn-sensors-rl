"""Numbers as the article writes them. The text and most tables round half
up, as a reader would (0.125 prints 0.13); the tables of the main study and
of quality and costs keep Python's fixed-point rounding. French writes the
decimal comma ({,} in LaTeX) and sets thousands off by a thin space from four
digits; English (MDPI) writes the decimal point and a comma from five digits.
"""
from decimal import ROUND_HALF_UP, Decimal


def half_up(x, nd):
    return Decimal(repr(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def fixed(x, nd, lang, half=False, thousands=False, minus=False):
    """A LaTeX cell: x to nd decimals in the edition's notation, '--' for
    None; minus writes a negative sign as the math minus."""
    if x is None:
        return '--'
    s = str(half_up(x, nd)) if half else '%.*f' % (nd, x)
    if thousands:
        i, dot, d = s.partition('.')
        digits = len(i.lstrip('-'))
        if lang == 'fr' and digits >= 4:
            i = i[:-3] + '\\,' + i[-3:]
        elif lang != 'fr' and digits >= 5:
            i = '{:,}'.format(int(i))
        s = i + dot + d
    if lang == 'fr':
        s = s.replace('.', '{,}')
    return s.replace('-', '$-$') if minus else s


def plain(x, nd, lang, thousands=False):
    """Rounded half up."""
    return fixed(x, nd, lang, half=True, thousands=thousands)


def signed(x, nd, lang):
    """Rounded half up, with an explicit sign unless the rounded value is 0."""
    if x is None:
        return '--'
    d = half_up(x, nd)
    s = str(abs(d))
    s = s.replace('.', '{,}') if lang == 'fr' else s
    if d == 0:
        return s
    return ('+' if d > 0 else '$-$') + s


def pval(p, lang, half=True):
    """A p value: three decimals, '< 0.001' below."""
    if p is None:
        return '--'
    if p < 0.001:
        return '$< 0{,}001$' if lang == 'fr' else '$< 0.001$'
    return fixed(p, 3, lang, half=half, minus=not half)


def ptext(p, lang):
    """A p value as the text writes it, with its symbol:
    '< 0.001' below that threshold, else three decimals below 0.1 and two
    above; rounded half up."""
    if p < 0.001:
        return '$p < 0{,}001$' if lang == 'fr' else '$p < 0.001$'
    return '$p = %s$' % plain(p, 3 if half_up(p, 3) < Decimal('0.1') else 2, lang)


def text(x, nd):
    """A number of the French text: half up, decimal comma, minus sign."""
    return str(half_up(x, nd)).replace('.', ',').replace('-', '−')
