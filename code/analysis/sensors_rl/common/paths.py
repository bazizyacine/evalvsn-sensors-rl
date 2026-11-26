"""Paths of the article and of the tree around it, relative to this package,
so that they hold in the working repository and in the companion repository
alike: the package sits at code/analysis/sensors_rl in both."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.normpath(os.path.join(_HERE, '..', '..'))
ROOT = os.path.dirname(os.path.dirname(ANALYSIS))
# The article's sources: writing/sensors-rl/src in the working repository,
# article/ in the companion repository.
WRITING = os.path.join(ROOT, 'writing', 'sensors-rl')
SRC = os.path.join(WRITING, 'src') if os.path.isdir(os.path.join(WRITING, 'src')) else os.path.join(ROOT, 'article')
DATA = os.path.join(ROOT, 'data', 'sensors-rl', 'article')
TABLES = os.path.join(SRC, 'tables')
FIGURES = os.path.join(SRC, 'figures')
FIGURES_SRC = os.path.join(SRC, 'figures-src')
# The raw sets, outside the repository: SETS_DIR, or else the folder sets/ at
# the root of the repository (run_sets.sh's default).
SETS = os.environ.get('SETS_DIR') or os.path.join(ROOT, 'sets')
STUDIES = os.path.join(ROOT, 'data', 'sensors-rl')
# The article's three studies, folders of STUDIES: the main study (E0), the
# controls of the first review round and those of the second. Every path to
# them goes through these names.
STUDY_E0 = '0-comparative'
STUDY_R1 = '1-round1'
STUDY_R2 = '2-round2'
CAMPAIGN = os.path.join(ROOT, 'code', 'campaign')
CONF = os.path.join(CAMPAIGN, 'sets.conf')
IPFILES = os.path.join(CAMPAIGN, 'ipFiles')
RADIO = os.path.join(CAMPAIGN, 'radio-params.tcl')
VIDEOS = os.path.join(CAMPAIGN, 'videos')
METRICS = os.path.join(ROOT, 'code', 'metrics')
EVALVSN = os.path.join(ROOT, 'code', 'evalvsn')
NS2 = os.path.join(ROOT, 'code', 'ns2', 'modules', 'ns-2.35')


def data(name):
    return os.path.join(DATA, name)


def study(name, *parts):
    """A file of a study's folder: study(STUDY_R2, 'sets.txt')."""
    return os.path.join(STUDIES, name, *parts)


def results(name, filename):
    """A versioned result of a study: results(STUDY_R1, 'runs.tsv')."""
    return study(name, 'results', filename)


def submission(lang, round_):
    """The folder of a review round: submission/roundN for the English files
    sent to the journal, submission-fr/roundN for the French editions."""
    return os.path.join(WRITING, 'submission' if lang == 'en' else 'submission-fr', 'round%d' % round_)


# The readers of the raw sets (code/metrics: sets.py, fire_oracle.py).
if METRICS not in sys.path:
    sys.path.insert(0, METRICS)
