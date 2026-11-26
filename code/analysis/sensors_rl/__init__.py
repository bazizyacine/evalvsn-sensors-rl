"""The package of the Sensors RL article: the raw sets of the simulations
(sets/) compiled into data/sensors-rl/article, the analyses of those tables,
the tables and figures drawn from them, and the numbers of the text
recomputed.

    python3 -m sensors_rl data | tables | figures | abstract | claims | report | all

common/    paths, the tables of data/sensors-rl/article, statistics, numbers
compile/   sets/ -> data/sensors-rl/article/*.tsv
analysis/  data/sensors-rl/article -> estimates (difference, 95 % interval, p, Holm's p)
tables/    estimates -> the article's tables, {fr,en}_*.tex
figures/   data/sensors-rl/article and estimates -> the article's figures,
           {fr,en}_*.png, and the graphical abstract
claims/    every number of the text recomputed: OK, DIFFERS or MISSING

common/paths.py gives where the article's tables and figures are written.
"""

# code/metrics (the readers of the raw sets) on the module path
from .common import paths  # noqa: E402,F401
