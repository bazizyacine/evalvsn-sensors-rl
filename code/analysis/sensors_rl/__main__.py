"""The one entry point of the article's package:

    python3 -m sensors_rl STEP [STEP ...] [--lang fr|en|both] [--round N] [--only NAME]

data      sets/ -> data/sensors-rl/article/*.tsv (needs the raw sets); --only NAME
          compiles one file: comparative, revision, round2, frames, oracle,
          agent-trace, break-agent, break-cases, methods, codec, overhead.
          Every file but round2 reads the sets of studies 09 and 10: once
          one of them is missing (purged) the step refuses to write and
          the stored file stays; all then skips data. frames-access
          rewrites the access-only stack's rows of frames.tsv from study
          10's results/images.tsv, the other rows kept, sets or not.
          revision.tsv is frozen as the first round deposited it; round2
          (study 11) keeps the rows of a set once stored; --sets NAME ...
          with round2 or overhead reads those sets only and keeps the
          other rows as stored (overhead: SETS_DIR on an extraction of a
          light archive)
tables    data/sensors-rl/article -> the article's tables, {fr,en}_*.tex
figures   data/sensors-rl/article -> the article's figures, {fr,en}_*.png
abstract  the graphical abstract -> submission/roundN/, submission-fr/roundN/
claims    every number of the text recomputed; exits 1 when one DIFFERS,
          is MISSING-IN-TEXT or when an interval or a p of the text is read
          by no line
report    the statistics behind the tables and the text, printed; --only one
          of comparative, quality, controls, ablation, coding, robustness,
          overhead, plan, round2 (the controls of study 11), assumptions
          (the assumptions of the tests),
          access-robustness (the access-only stack in the series of E4 and
          E5, tranche T7 of study 11)
all       data (skipped once the raw sets are purged), tables, figures,
          abstract, claims, in that order

Run from code/analysis, the parent of this package; common/paths.py gives
where the article's tables and figures are written."""
import argparse
import sys

STEPS = ('data', 'tables', 'figures', 'abstract', 'claims', 'report', 'all')
DATA = ('comparative', 'revision', 'round2', 'frames', 'frames-access', 'oracle', 'agent-trace', 'break-agent', 'break-cases', 'methods',
        'codec', 'overhead')
REPORTS = ('comparative', 'quality', 'controls', 'ablation', 'coding', 'robustness', 'overhead', 'plan', 'round2',
           'assumptions', 'access-robustness')


def missing_sets():
    """The sets that studies 09 and 10 list (sets.txt) and that are not
    complete on disk: graphs/PSNR/PSNR.dat and the realisations their
    declaration gives."""
    import glob
    import os
    import sets
    from .common import paths
    sims = sets.declared_sims(paths.CONF)
    out = []
    for study in (paths.STUDY_E0, paths.STUDY_R1):
        for line in open(paths.study(study, 'sets.txt')):
            if not line.strip() or line.startswith('#'):
                continue
            name = line.split()[0]
            d = os.path.join(paths.SETS, name)
            if not sets.harvested(d) or len(glob.glob(os.path.join(d, 'r[0-9][0-9]', '*', 'sim', 'mt.dat'))) < sims.get(name, 1):
                out.append(name)
    return out


def data(only, skip_without_sets=False, names=None):
    """The data steps; 1 when a step refused to write. names (--sets): the
    only sets round2 reads."""
    from .compile import agents, codec, measures, simulations
    steps = {'comparative': simulations.comparative, 'revision': simulations.revision,
             'round2': lambda: simulations.round2(names), 'overhead': lambda: measures.overhead(names),
             'frames': simulations.frames, 'frames-access': simulations.frames_access,
             'oracle': simulations.oracle, 'agent-trace': agents.agent_trace,
             'break-agent': agents.break_agent, 'break-cases': agents.break_cases, 'methods': measures.methods,
             'codec': codec.codec}
    missing = missing_sets()
    if missing and skip_without_sets:
        print('data: %d sets of studies 09 and 10 are not on disk (purged on 21 November 2026?): data/sensors-rl/article stays as stored'
              % len(missing))
        return 0
    rc = 0
    for name in ([only] if only else DATA):
        # with --sets, overhead reads the sets named only: the others keep their rows
        if missing and name not in ('revision', 'round2', 'frames-access') and not (name == 'overhead' and names):
            print('data --only %s: refused, %d sets of studies 09 and 10 are not on disk (%s%s): data/sensors-rl/article keeps its stored file'
                  % (name, len(missing), missing[0], ', ...' if len(missing) > 1 else ''), file=sys.stderr)
            rc = 1
            continue
        steps[name]()
    return rc


def tables(langs):
    from .tables import ablation, coding, comparative, controls, overhead, plan, quality, robustness
    for module in (plan, comparative, controls, ablation, quality, coding, robustness, overhead):
        for path in module.tables(langs):
            print(path)


def figures(langs):
    from .figures import methods, results, style
    for lang in langs:
        style.use(lang)
        for path in methods.figures() + results.figures():
            print(path)


def abstract(langs, round_):
    from .figures import graphical_abstract
    for path in graphical_abstract.abstract(langs, round_):
        print(path)


def claims():
    from .claims import aomdv, results, review, scenario
    rc = results.main()
    print('\n--- E5, variantes du scénario (claims/scenario.py) ---')
    rc |= scenario.main()
    print('\n--- E1, AOMDV aux temporisations inter-couches (claims/aomdv.py) ---')
    rc |= aomdv.main()
    print('\n--- second tour, S01 à S14 : écarts et intervalles, sphéricité, échéances, déclarations, accès seul, contrôles de '
          'l\'étude 11 et sa tranche T7, puis le texte relu (claims/review.py, round2.py, synthesis.py, access_robustness.py) ---')
    rc |= review.main()
    return rc


def report(only, metric):
    from .analysis import (ablation, access_robustness, assumptions, coding, comparative, controls, overhead, quality,
                           robustness, round2)
    from .tables import plan
    for name in ([only] if only else REPORTS):
        print('\n=== %s' % name)
        if name == 'comparative':
            comparative.report(metric)
        elif name == 'plan':
            plan.report()
        else:
            {'quality': quality, 'controls': controls, 'ablation': ablation, 'coding': coding,
             'robustness': robustness, 'overhead': overhead, 'round2': round2, 'assumptions': assumptions,
             'access-robustness': access_robustness}[name].report()


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python3 -m sensors_rl', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('steps', nargs='+', choices=STEPS, metavar='STEP')
    ap.add_argument('--lang', choices=('fr', 'en', 'both'), default='both')
    ap.add_argument('--round', type=int, default=2, help='the review round of the graphical abstract (default 2)')
    ap.add_argument('--only', help='one data file (data) or one report (report)')
    ap.add_argument('--metric', default='psnr', help='the metric of the comparative report (default psnr)')
    ap.add_argument('--sets', nargs='+', metavar='SET',
                    help='with data --only round2 or overhead: read these sets only; the others keep their stored rows, or stay out')
    a = ap.parse_args(argv)
    if a.only and a.only not in DATA + REPORTS:
        ap.error('--only: one of %s' % ', '.join(sorted(set(DATA + REPORTS))))
    if a.sets and (a.only not in ('round2', 'overhead') or 'data' not in a.steps):
        ap.error('--sets: with data --only round2 or data --only overhead only')
    langs = ('fr', 'en') if a.lang == 'both' else (a.lang,)
    steps = ('data', 'tables', 'figures', 'abstract', 'claims') if 'all' in a.steps else a.steps
    rc = 0
    for step in steps:
        if step == 'data':
            rc |= data(a.only, skip_without_sets='all' in a.steps, names=a.sets)
        elif step == 'tables':
            tables(langs)
        elif step == 'figures':
            figures(langs)
        elif step == 'abstract':
            abstract(langs, a.round)
        elif step == 'claims':
            rc |= claims()
        elif step == 'report':
            report(a.only, a.metric)
    return rc


if __name__ == '__main__':
    sys.exit(main())
