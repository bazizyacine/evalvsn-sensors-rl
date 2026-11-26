"""The statistics of the article: Student's t and Fisher's F computed from the
regularized incomplete beta function (no dependency beyond the standard
library), the paired comparison of two arms over their shared seeds, Holm's
correction within a family of tests, correlation, and the repeated-measures
ANOVA of the main study with Mauchly's test and the Greenhouse-Geisser and
Huynh-Feldt corrections of its within-seed terms, and the interval of each
partial eta squared by the noncentral F distribution. The checks of their
assumptions come last: the sample skewness
and excess kurtosis, the Shapiro-Wilk test, Wilcoxon's signed-rank test,
Mardia's multivariate skewness and kurtosis, and Box's M test."""
import math
from statistics import NormalDist

import numpy as np


# ---------------------------------------------------------------- distributions

def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / (c if abs(c) > tiny else tiny)
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / (c if abs(c) > tiny else tiny)
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """Two-sided p-value of Student's t."""
    x = df / (df + t * t)
    return betainc(df / 2.0, 0.5, x)


def t_quantile(p, df):
    """Two-sided quantile: t such that P(|T| > t) = 1 - p; 0.95 gives the
    half-width factor of a 95 % interval."""
    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_sf2(mid, df) > 1.0 - p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def f_sf(f, d1, d2):
    """Upper tail of the F distribution; d1 and d2 may be fractional (the
    degrees of freedom of a sphericity correction)."""
    if f <= 0.0:
        return 1.0
    return betainc(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * f))


def ncf_cdf(f, d1, d2, nc):
    """Lower tail of the noncentral F distribution of noncentrality nc, the
    Poisson mixture of central tails: the sum over j of Poisson(j; nc / 2)
    I_x(d1 / 2 + j, d2 / 2), x = d1 f / (d1 f + d2), over the j within ten
    standard deviations of the mean nc / 2. I_x is computed at the largest j
    and the others follow from I_x(a, b) = I_x(a + 1, b) + x^a (1 - x)^b /
    (a B(a, b)), a sum of positive terms. Checked against
    scipy.stats.ncf.cdf: d1 = 2 to 8, d2 = 57 to 228, nc = 0 to 2000, within
    1e-12."""
    if f <= 0.0:
        return 0.0
    if nc <= 0.0:
        return 1.0 - f_sf(f, d1, d2)
    half, b, x = nc / 2.0, d2 / 2.0, d1 * f / (d1 * f + d2)
    spread = 10.0 * math.sqrt(half) + 40.0
    first, last = max(0, int(half - spread)), int(half + spread)
    tail = betainc(d1 / 2.0 + last, b, x)
    total = 0.0
    for j in range(last, first - 1, -1):
        total += math.exp(j * math.log(half) - half - math.lgamma(j + 1.0)) * tail
        a = d1 / 2.0 + j - 1.0
        if j > first:
            tail += math.exp(a * math.log(x) + b * math.log(1.0 - x) + math.lgamma(a + b) - math.lgamma(a + 1.0)
                             - math.lgamma(b))
    return min(1.0, total)


def gammaq(a, x):
    """Regularized upper incomplete gamma Q(a, x): the series below a + 1,
    the continued fraction (Lentz) above."""
    if x <= 0.0:
        return 1.0
    lg = math.lgamma(a)
    if x < a + 1.0:
        term = total = 1.0 / a
        n = a
        for _ in range(1000):
            n += 1.0
            term *= x / n
            total += term
            if abs(term) < abs(total) * 3e-16:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - lg)
    tiny = 1e-300
    b = x + 1.0 - a
    c, d = 1.0 / tiny, 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-16:
            break
    return math.exp(-x + a * math.log(x) - lg) * h


def chi2_sf(x, df):
    """Upper tail of the chi-square distribution."""
    return gammaq(df / 2.0, x / 2.0)


# ------------------------------------------------------------------ estimates

def mean(x):
    x = list(x)
    return sum(x) / len(x)


def complete_mean(x, n):
    """The mean of the values x when there are n of them (every seed of the
    comparison), else None."""
    x = list(x)
    return mean(x) if len(x) == n else None


def spread(x):
    """n, mean, standard deviation and half-width of the two-sided 95 %
    Student interval of the mean of the values x."""
    x = list(x)
    n, m = len(x), mean(x)
    s = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
    return n, m, s, t_quantile(0.95, n - 1) * s / math.sqrt(n)


class Estimate:
    """A mean with its two-sided 95 % Student interval and p; holm is Holm's
    p once the estimate has been corrected within its family; values, the
    values it was computed from (the per-seed differences of a paired test),
    for the checks of its assumptions (analysis/assumptions.py)."""
    __slots__ = ('n', 'mean', 'lo', 'hi', 'p', 'holm', 'values')

    def __init__(self, n, mean, lo, hi, p, holm=None, values=None):
        self.n, self.mean, self.lo, self.hi, self.p, self.holm = n, mean, lo, hi, p, holm
        self.values = values


def estimate(d):
    """The mean of a list of values (per-seed differences, usually), its 95 %
    interval and the p of the test of a zero mean."""
    d = tuple(d)
    n, m, s, h = spread(d)
    if s == 0:
        return Estimate(n, m, m, m, 1.0 if m == 0 else 0.0, values=d)
    return Estimate(n, m, m - h, m + h, t_sf2(m / (s / math.sqrt(n)), n - 1), values=d)


def paired(a, b):
    """a - b over the seeds both hold (dicts seed: value), seed by seed."""
    return estimate(a[k] - b[k] for k in a if k in b)


def holm(ps):
    """Holm's step-down correction of a list of p."""
    m = len(ps)
    order = sorted(range(m), key=lambda q: ps[q])
    adj, running = [None] * m, 0.0
    for rank, q in enumerate(order):
        running = max(running, (m - rank) * ps[q])
        adj[q] = min(1.0, running)
    return adj


def family(estimates):
    """Holm's correction within a family: {label: Estimate} with their holm
    set; a None (a contrast the seeds do not all back) stays out of it."""
    full = [k for k, e in estimates.items() if e is not None]
    for k, p in zip(full, holm([estimates[k].p for k in full])):
        estimates[k].holm = p
    return estimates


def detected(e, alpha=0.05):
    """A difference is detected: its p, Holm's within its family when there
    is one, the single test's otherwise, is under alpha."""
    return (e.p if e.holm is None else e.holm) < alpha


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def pearson_p(r, n):
    """Two-sided p of a Pearson correlation r over n pairs: Student's t with
    n - 2 degrees of freedom."""
    return t_sf2(r * math.sqrt((n - 2) / (1 - r * r)), n - 2)


def slope(x, y):
    mx, my = mean(x), mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)


# ------------------------------------------------------------------- ANOVA

def rm_anova(rows, metric):
    """Split-plot ANOVA of the main study: the subjects are the seeds (fire,
    realisation), the fire varies between subjects, the stack and the GOP
    within; each term is tested against its own error stratum (the design is
    balanced). Returns (term, df, error df, F, p, partial eta2) per term."""
    data = [(r['fire'], r['realisation'], r['stack'], r['split'], float(r[metric])) for r in rows]
    y = np.array([d[4] for d in data])
    gm = y.mean()

    def ss(*cols):
        groups = {}
        for d in data:
            groups.setdefault(tuple(d[c] for c in cols), []).append(d[4])
        return sum(len(v) * (sum(v) / len(v) - gm) ** 2 for v in groups.values())

    F_, R_, S_, G_ = 0, 1, 2, 3
    a = len({d[F_] for d in data})
    b = len({d[S_] for d in data})
    c = len({d[G_] for d in data})
    n = len({(d[F_], d[R_]) for d in data})
    fire, stack, split = ss(F_), ss(S_), ss(G_)
    subj = ss(F_, R_)
    fs = ss(F_, S_) - fire - stack
    fg = ss(F_, G_) - fire - split
    sg = ss(S_, G_) - stack - split
    fsg = ss(F_, S_, G_) - fire - stack - split - fs - fg - sg
    e0, d0 = subj - fire, n - a
    e1, d1 = ss(F_, R_, S_) - subj - stack - fs, d0 * (b - 1)
    e2, d2 = ss(F_, R_, G_) - subj - split - fg, d0 * (c - 1)
    e3 = float(((y - gm) ** 2).sum()) - subj - stack - split - fs - fg - sg - fsg - e1 - e2
    d3 = d0 * (b - 1) * (c - 1)
    terms = (('stack', stack, b - 1, e1, d1), ('fire', fire, a - 1, e0, d0), ('split', split, c - 1, e2, d2),
             ('stack x fire', fs, (a - 1) * (b - 1), e1, d1), ('stack x split', sg, (b - 1) * (c - 1), e3, d3),
             ('fire x split', fg, (a - 1) * (c - 1), e2, d2),
             ('stack x fire x split', fsg, (a - 1) * (b - 1) * (c - 1), e3, d3))
    out = []
    for name, s, df, e, de in terms:
        f = (s / df) / (e / de)
        out.append((name, df, de, f, f_sf(f, df, de), s / (s + e)))
    return out


def eta_interval(f, d1, d2, level=0.95):
    """(lower, upper) bounds of the two-sided interval of the partial eta
    squared of an F test, by the noncentral F distribution with the degrees
    of freedom of the test, uncorrected for sphericity (the method of
    Smithson, Educational and Psychological Measurement 61, 2001, 605-632, to
    which Lakens, Frontiers in Psychology 4:863, 2013, points): the
    noncentralities nc that put the observed f at the quantile (1 + level) / 2
    (lower bound) and (1 - level) / 2 (upper bound), each nc / (nc + d1 + d2
    + 1). A bound is 0 when f is under that quantile of the central
    distribution. Checked against Lakens's two examples, at the level of
    0.90: F(1, 18) = 6.34 gives [0.02, 0.48], F(1, 9) = 22.50 gives
    [0.31, 0.82]; and against scipy.stats.ncf on the seven terms of the
    ANOVA table, at 1e-9."""
    def noncentrality(q):
        if 1.0 - f_sf(f, d1, d2) <= q:
            return 0.0
        lo, hi = 0.0, 1.0
        while ncf_cdf(f, d1, d2, hi) > q:
            lo, hi = hi, 2.0 * hi
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if ncf_cdf(f, d1, d2, mid) > q:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0
    return tuple(nc / (nc + d1 + d2 + 1.0)
                 for nc in (noncentrality((1.0 + level) / 2.0), noncentrality((1.0 - level) / 2.0)))


# ------------------------------------------------------------- sphericity

# The error stratum each term of rm_anova is tested in, hence the sphericity
# correction it takes; the fire, between the seeds, takes none.
STRATUM = {'stack': 'stack', 'stack x fire': 'stack', 'split': 'split', 'fire x split': 'split',
           'stack x split': 'stack x split', 'stack x fire x split': 'stack x split'}


def helmert(k):
    """k x (k - 1) orthonormal contrasts."""
    c = np.zeros((k, k - 1))
    for j in range(1, k):
        c[:j, j - 1] = 1.0
        c[j, j - 1] = -j
        c[:, j - 1] /= np.linalg.norm(c[:, j - 1])
    return c


def within_design(rows, metric):
    """The design of rm_anova as arrays: y[seed, stack, split] (the seeds
    (fire, realisation), the stacks and the splits sorted), the fire of each
    seed, the stacks and the splits."""
    seeds = sorted({(r['fire'], r['realisation']) for r in rows})
    stacks = sorted({r['stack'] for r in rows})
    splits = sorted({r['split'] for r in rows})
    index = {k: n for n, k in enumerate(seeds)}
    y = np.zeros((len(seeds), len(stacks), len(splits)))
    for r in rows:
        y[index[(r['fire'], r['realisation'])], stacks.index(r['stack']), splits.index(r['split'])] = float(r[metric])
    return y, np.array([k[0] for k in seeds]), stacks, splits


def contrast_scores(y):
    """{stratum: the scores of the seeds on the orthonormal (Helmert)
    contrasts of the term}, the three within-seed strata of rm_anova: for a
    main effect, the contrasts of the seed's means over the other within
    factor; for the interaction, the products of the two."""
    n, a, b = y.shape
    cs, cg = helmert(a), helmert(b)
    return {'stack': y.mean(axis=2) @ cs, 'split': y.mean(axis=1) @ cg,
            'stack x split': np.einsum('sij,ia,jb->sab', y, cs, cg).reshape(n, -1)}


def within_fires(z, fire):
    """The rows of z centered on the mean of their fire, the fires in
    order: the residuals of the between-seed factor."""
    return np.vstack([z[fire == f] - z[fire == f].mean(axis=0) for f in sorted(set(fire))])


def sphericity(rows, metric):
    """Mauchly's test and the Greenhouse-Geisser and Huynh-Feldt factors of
    the three within-seed strata of rm_anova (stack, split, stack x split).
    The orthonormal contrasts of a term are applied to each seed's cell means
    (for a main effect, the mean over the other within factor); S is their
    covariance pooled within the fires, the fire varying between the seeds;
    Mauchly's W = det S / (tr S / q)^q with its chi-square, the
    Greenhouse-Geisser factor (tr S)^2 / (q tr S^2), and the Huynh-Feldt
    factor with Lecoutre's correction, capped at 1. Neither factor depends on
    the orthonormal basis. Returns {stratum: dict(q, W, chi2, df, p, gg, hf)}."""
    y, fire, _, _ = within_design(rows, metric)
    n, g = len(fire), len(set(fire))
    dfe = n - g
    out = {}
    for name, z in contrast_scores(y).items():
        q = z.shape[1]
        resid = within_fires(z, fire)
        s = resid.T @ resid / dfe
        w = float(np.linalg.det(s) / (np.trace(s) / q) ** q)
        chi = -(dfe - (2 * q * q + q + 2) / (6.0 * q)) * math.log(w)
        df = q * (q + 1) // 2 - 1
        gg = float(np.trace(s) ** 2 / (q * np.trace(s @ s)))
        hf = min(1.0, ((n - g + 1) * q * gg - 2) / (q * (n - g - q * gg)))
        out[name] = dict(q=q, W=w, chi2=chi, df=df, p=chi2_sf(chi, df), gg=gg, hf=hf)
    return out


def corrected(terms, sph):
    """The terms of rm_anova with the corrections of their stratum and the
    95 % interval of their partial eta2 (eta_interval): (term, df, error df,
    F, p, partial eta2, gg, p_gg, hf, p_hf, eta2 lower, eta2 upper); gg to
    p_hf are None for the fire, tested between the seeds."""
    out = []
    for name, df, de, f, p, eta in terms:
        s = sph.get(STRATUM.get(name))
        corr = ((None,) * 4 if s is None else
                (s['gg'], f_sf(f, df * s['gg'], de * s['gg']), s['hf'], f_sf(f, df * s['hf'], de * s['hf'])))
        out.append((name, df, de, f, p, eta) + corr + eta_interval(f, df, de))
    return out


# ------------------------------------------------------------- assumptions

def normal_sf2(z):
    """Two-sided p of a standard normal deviate."""
    return math.erfc(abs(z) / math.sqrt(2.0))


def shape(x):
    """The sample skewness g1 = m3 / m2^(3/2) and excess kurtosis
    g2 = m4 / m2^2 - 3 of the values x, from their central moments with
    divisor n (D'Agostino, Belanger and D'Agostino, The American
    Statistician 44, 1990, 316-321); (None, None) when the values are all
    equal."""
    x = np.asarray(x, float)
    c = x - x.mean()
    m2 = float((c ** 2).mean())
    if m2 == 0.0:
        return None, None
    return float((c ** 3).mean()) / m2 ** 1.5, float((c ** 4).mean()) / m2 ** 2 - 3.0


def _poly(c, x):
    return sum(ci * x ** i for i, ci in enumerate(c))


# The coefficients of Royston's algorithm AS R94 (Royston, Statistics and
# Computing 2, 1992, 117-119; Applied Statistics 44, 1995, 547-551).
_SW_C1 = (0.0, 0.221157, -0.147981, -2.071190, 4.434685, -2.706056)
_SW_C2 = (0.0, 0.042981, -0.293762, -1.752461, 5.682633, -3.582633)
_SW_C3 = (0.5440, -0.39978, 0.025054, -6.714e-4)
_SW_C4 = (1.3822, -0.77857, 0.062767, -0.0020322)
_SW_C5 = (-1.5861, -0.31082, -0.083751, 0.0038915)
_SW_C6 = (-0.4803, -0.082676, 0.0030302)
_SW_G = (-2.273, 0.459)


def shapiro_wilk(x):
    """The Shapiro-Wilk test of normality by Royston's algorithm AS R94
    (Royston 1992 and 1995, the coefficients above; the algorithm of R's
    shapiro.test), for 3 <= n <= 5000: the coefficients from the normal
    scores m_i = Phi^-1((i - 3/8) / (n + 1/4)), the two largest by Royston's
    polynomials in 1 / sqrt(n); W the squared correlation of the ordered
    values with the coefficients; p the upper tail of the normal law fitted
    to log(1 - W) (to -log(gamma - log(1 - W)) for n <= 11), exact for
    n = 3. Returns (W, p), (None, None) when the values are all equal.
    Checked against R's shapiro.test: mtcars$mpg, W = 0.94756, p = 0.1229;
    ToothGrowth$len, W = 0.96743, p = 0.1091."""
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if not 3 <= n <= 5000:
        raise ValueError('Shapiro-Wilk: 3 <= n <= 5000, not %d' % n)
    if x[-1] - x[0] == 0.0:
        return None, None
    half = n // 2
    if n == 3:
        a = np.array([math.sqrt(0.5)])
    else:
        q = NormalDist()
        m = np.array([-q.inv_cdf((i - 0.375) / (n + 0.25)) for i in range(1, half + 1)])
        summ2 = 2.0 * float((m ** 2).sum())
        ssumm2 = math.sqrt(summ2)
        rsn = 1.0 / math.sqrt(n)
        a1 = _poly(_SW_C1, rsn) + m[0] / ssumm2
        if n > 5:
            a2 = m[1] / ssumm2 + _poly(_SW_C2, rsn)
            fac = math.sqrt((summ2 - 2.0 * m[0] ** 2 - 2.0 * m[1] ** 2) / (1.0 - 2.0 * a1 ** 2 - 2.0 * a2 ** 2))
            a = np.concatenate(([a1, a2], m[2:] / fac))
        else:
            fac = math.sqrt((summ2 - 2.0 * m[0] ** 2) / (1.0 - 2.0 * a1 ** 2))
            a = np.concatenate(([a1], m[1:] / fac))
    coef = np.zeros(n)
    coef[:half] = -a
    coef[n - half:] = a[::-1]
    xs = x / (x[-1] - x[0]) - (x / (x[-1] - x[0])).mean()
    ca = coef - coef.mean()
    ssa, ssx, sax = float((ca ** 2).sum()), float((xs ** 2).sum()), float((ca * xs).sum())
    root = math.sqrt(ssa * ssx)
    w1 = (root - sax) * (root + sax) / (ssa * ssx)   # 1 - W, without the rounding of W near 1
    w = 1.0 - w1
    if n == 3:
        return w, max(0.0, 6.0 / math.pi * (math.asin(math.sqrt(w)) - math.pi / 3.0))
    y = math.log(w1)
    if n <= 11:
        gamma = _poly(_SW_G, n)
        if y >= gamma:
            return w, 1e-99
        y = -math.log(gamma - y)
        mu, sigma = _poly(_SW_C3, n), math.exp(_poly(_SW_C4, n))
    else:
        mu, sigma = _poly(_SW_C5, math.log(n)), math.exp(_poly(_SW_C6, math.log(n)))
    return w, 0.5 * math.erfc((y - mu) / sigma / math.sqrt(2.0))


def midranks(x):
    """The ranks of the values x, 1 to n, ties sharing the mean of their
    ranks; and the size of each group of ties."""
    x = np.asarray(x, float)
    values, inverse, counts = np.unique(x, return_inverse=True, return_counts=True)
    first = np.concatenate(([0], np.cumsum(counts)[:-1]))
    return (first + (counts + 1) / 2.0)[inverse], counts


def wilcoxon(d, decimals=9):
    """Wilcoxon's signed-rank test of a zero median of the differences d, by
    the normal approximation without continuity correction (Hollander,
    Wolfe and Chicken, Nonparametric Statistical Methods, 3rd ed., Wiley,
    2014, section 3.1): the zero differences are dropped (Wilcoxon's
    treatment of zeros), the absolute differences ranked, ties taking their
    midrank; W+ is the sum of the ranks of the positive differences, of mean
    n(n + 1) / 4 and variance n(n + 1)(2n + 1) / 24 - sum(t^3 - t) / 48 over
    the n differences left and the groups of t ties. The differences are
    rounded to decimals first, so that the rounding of a float neither makes
    a difference of 0 nor breaks a tie. Returns dict(n, zeros, w, z, p); p
    is 1 when every difference is 0. Checked against scipy.stats.wilcoxon
    (method 'asymptotic') on Darwin's maize differences, p = 0.040888, and
    its tie correction against the exact variance of W+ given the midranks."""
    d = np.round(np.asarray(d, float), decimals)
    nz = d[d != 0.0]
    n = len(nz)
    if n == 0:
        return dict(n=0, zeros=len(d), w=0.0, z=0.0, p=1.0)
    r, ties = midranks(np.abs(nz))
    w = float(r[nz > 0].sum())
    var = n * (n + 1) * (2 * n + 1) / 24.0 - float((ties ** 3 - ties).sum()) / 48.0
    z = (w - n * (n + 1) / 4.0) / math.sqrt(var)
    return dict(n=n, zeros=len(d) - n, w=w, z=z, p=normal_sf2(z))


def mardia(z):
    """Mardia's multivariate skewness b1,p and kurtosis b2,p of the rows of
    z, n observations of p variables (Mardia, Biometrika 57, 1970, 519-530),
    from the covariance with divisor n: the skewness test n b1,p / 6, a
    chi-square with p(p + 1)(p + 2) / 6 degrees of freedom; the kurtosis
    test (b2,p - p(p + 2)) / sqrt(8 p(p + 2) / n), a standard normal deviate.
    Returns dict(n, p, b1, chi2, df, p_skew, b2, z, p_kurt). Checked against
    R's MVN::mvn on iris[1:50, 1:4]: skewness 25.66, p = 0.177; kurtosis
    1.295, p = 0.195."""
    z = np.asarray(z, float)
    n, q = z.shape
    c = z - z.mean(axis=0)
    g = c @ np.linalg.inv(c.T @ c / n) @ c.T
    b1, b2 = float((g ** 3).sum()) / n ** 2, float((np.diag(g) ** 2).sum()) / n
    chi, df = n * b1 / 6.0, q * (q + 1) * (q + 2) // 6
    zk = (b2 - q * (q + 2)) / math.sqrt(8.0 * q * (q + 2) / n)
    return dict(n=n, p=q, b1=b1, chi2=chi, df=df, p_skew=chi2_sf(chi, df), b2=b2, z=zk, p_kurt=normal_sf2(zk))


def box_m(groups):
    """Box's M test of the equality of the covariance matrices of g groups,
    with its chi-square approximation (Box, Biometrika 36, 1949, 317-346):
    M = (N - g) ln|S| - sum (n_i - 1) ln|S_i|, S_i the covariance of group i
    (divisor n_i - 1) and S their pooled covariance; chi2 = (1 - u) M with
    u = (sum 1 / (n_i - 1) - 1 / (N - g)) (2p^2 + 3p - 1) / (6 (p + 1)(g - 1)),
    on p(p + 1)(g - 1) / 2 degrees of freedom. groups: one array of n_i rows
    and p columns per group. Returns dict(g, p, M, chi2, df, p_value).
    Checked against R's heplots::boxM on iris by species: chi2 = 140.943,
    20 degrees of freedom."""
    groups = [np.asarray(x, float) for x in groups]
    g, q = len(groups), groups[0].shape[1]
    ns = [len(x) for x in groups]
    total = sum(ns)
    covs = [np.cov(x, rowvar=False, ddof=1) for x in groups]
    pooled = sum((k - 1) * s for k, s in zip(ns, covs)) / (total - g)
    logdet = lambda s: np.linalg.slogdet(s)[1]  # noqa: E731
    m = (total - g) * logdet(pooled) - sum((k - 1) * logdet(s) for k, s in zip(ns, covs))
    u = (sum(1.0 / (k - 1) for k in ns) - 1.0 / (total - g)) * (2 * q * q + 3 * q - 1) / (6.0 * (q + 1) * (g - 1))
    chi, df = float((1.0 - u) * m), q * (q + 1) * (g - 1) // 2
    return dict(g=g, p=q, M=float(m), chi2=chi, df=df, p_value=chi2_sf(chi, df))
