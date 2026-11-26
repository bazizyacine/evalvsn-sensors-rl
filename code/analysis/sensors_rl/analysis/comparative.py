"""The main study (experiment E0, study 09) from comparative.tsv: the mean of
each cell (fire x GOP x stack) and the half-width of its 95 % interval, the
paired differences between stacks in each cell with Holm's correction over
the nine cells of a comparison, the differences per GOP over the 60 seeds
with Holm's correction over the three GOPs, the same differences per seed
over the three GOPs, and the repeated-measures ANOVA of the three
cross-layer stacks with Mauchly's test, the Greenhouse-Geisser and
Huynh-Feldt corrections and the 95 % interval of each partial eta squared."""
from ..common import data, stats

STACKS = ('aomdv', 'rules', 'agents', 'hybrid')
PAIRS = (('hybrid', 'rules'), ('agents', 'rules'), ('hybrid', 'agents'), ('rules', 'aomdv'))


def rows():
    return data.read_tsv('comparative.tsv')


def cells(rs, metric):
    """{(fire, split, stack): {realisation: value}}."""
    out = {}
    for r in rs:
        out.setdefault((r['fire'], r['split'], r['stack']), {})[r['realisation']] = float(r[metric])
    return out


def half_width(values):
    """Half-width of the 95 % Student interval of a mean."""
    return stats.spread(values)[3]


def paired_cells(cell, a, b, fires=data.FIRES, splits=data.SPLITS):
    """{(fire, split): Estimate of a - b}, Holm-corrected over the cells."""
    tests = {(f, s): stats.paired(cell[(f, s, a)], cell[(f, s, b)])
             for f in fires for s in splits if (f, s, a) in cell and (f, s, b) in cell}
    return stats.family(tests)


def per_seed(cell, a, b):
    """Each seed's difference a - b averaged over the GOPs, and every
    difference (fire, split, realisation) for the share of positive pairs."""
    seeds, pairs = {}, []
    for (f, s, st), _ in sorted(cell.items()):
        if st != a or (f, s, b) not in cell:
            continue
        for k in sorted(set(cell[(f, s, a)]) & set(cell[(f, s, b)])):
            x = cell[(f, s, a)][k] - cell[(f, s, b)][k]
            seeds.setdefault((f, k), []).append(x)
            pairs.append(x)
    return stats.estimate(sum(v) / len(v) for v in seeds.values()), pairs


def anova(rs, metric='psnr'):
    """The repeated-measures ANOVA of the three cross-layer stacks, each
    within-seed term with the Greenhouse-Geisser and Huynh-Feldt corrections
    of its stratum: (term, df, error df, F, p, partial eta2, gg, p_gg, hf,
    p_hf, eta2 lower, eta2 upper), gg to p_hf None for the fire, the last two
    the 95 % interval of the partial eta2 (stats.eta_interval)."""
    cross = [r for r in rs if r['stack'] != 'aomdv']
    return stats.corrected(stats.rm_anova(cross, metric), stats.sphericity(cross, metric))


def effect_sizes(rs, metric='psnr'):
    """{term: Estimate} of the partial eta squared of each term of the ANOVA,
    its 95 % interval and the p of the term's F test, uncorrected."""
    return {t[0]: stats.Estimate(None, float(t[5]), float(t[10]), float(t[11]), float(t[4])) for t in anova(rs, metric)}


def sphericity(rs, metric='psnr'):
    """Mauchly's test of each within-seed stratum of the ANOVA."""
    return stats.sphericity([r for r in rs if r['stack'] != 'aomdv'], metric)


def paired_gops(cell, a, b, splits=data.SPLITS):
    """{split: Estimate of a - b over the 60 seeds of the three fires},
    Holm-corrected over the GOPs (a family of the method, section 2.7)."""
    pooled = {}
    for s in splits:
        x = {(f, k): v for f in data.FIRES for k, v in cell.get((f, s, a), {}).items()}
        y = {(f, k): v for f in data.FIRES for k, v in cell.get((f, s, b), {}).items()}
        pooled[s] = stats.paired(x, y)
    return stats.family(pooled)


def means(cell, stack, split, fire):
    """(mean, half-width of its 95 % interval) of a cell, None when absent."""
    v = cell.get((fire, split, stack))
    if not v:
        return None
    _, m, _, h = stats.spread(v.values())
    return m, h


def report(metric='psnr'):
    rs = rows()
    cell = cells(rs, metric)
    fires = sorted({r['fire'] for r in rs})
    splits = sorted({r['split'] for r in rs})
    print('%s, mean over the realisations' % metric)
    print('%-4s %-5s ' % ('fire', 'split') + ' '.join('%9s' % s for s in STACKS))
    for f in fires:
        for s in splits:
            vals = [cell.get((f, s, st)) for st in STACKS]
            print('%-4s %-5s ' % (f, s) + ' '.join('%9.2f' % (sum(v.values()) / len(v)) if v else '%9s' % '-' for v in vals))
    print('\npaired differences (Holm over the cells of each comparison)')
    for a, b in PAIRS:
        tests = paired_cells(cell, a, b, fires, splits)
        if not tests:
            continue
        print('  %s - %s' % (a, b))
        for (f, s), e in tests.items():
            print('    %s %s  %+7.2f  p = %.4f  p_Holm = %.4f  (n = %d)' % (f, s, e.mean, e.p, e.holm, e.n))
        e, pairs = per_seed(cell, a, b)
        print('    per seed %+7.2f  95%% CI [%+.2f, %+.2f]  p = %.3g  (n = %d seeds); positive in %.1f%% of the %d pairs'
              % (e.mean, e.lo, e.hi, e.p, e.n, 100 * sum(x > 0 for x in pairs) / len(pairs), len(pairs)))
    if all((f, s, st) in cell for f in fires for s in splits for st in STACKS):
        print('\nrepeated-measures ANOVA %s, the three cross-layer stacks' % metric)
        for t, df, de, F, p, eta, gg, pgg, hf, phf, lo, hi in anova(rs, metric):
            corr = ('  GG %.4f: df %.2f, %.2f  p %.4g  HF %.4f: p %.4g' % (gg, df * gg, de * gg, pgg, hf, phf)
                    if gg is not None else '')
            print('  %-22s df %2d, %3d  F %9.2f  p %.4g  partial eta2 %.3f [%.3f, %.3f]%s' % (t, df, de, F, p, eta, lo, hi, corr))
        print('  sum of the partial eta2: %.3f (each term has its own denominator)'
              % sum(x[5] for x in anova(rs, metric)))
        print('\nsphericity: covariance of the contrasts pooled within the fires')
        for name, s in sphericity(rs, metric).items():
            print('  %-14s q %d  Mauchly W %.4f  chi2(%d) %.2f  p %.4g  Greenhouse-Geisser %.4f  Huynh-Feldt %.4f'
                  % (name, s['q'], s['W'], s['df'], s['chi2'], s['p'], s['gg'], s['hf']))
    else:
        print('\nANOVA waits for the complete design')
