# 2-round2 — the sets of the second review round

This study (study 11 in the comments of the code) holds the sets added in the
second review round: exploration
without learning and learning without exploration on the hybrid stack; the
configurations of the channel access learned in development runs, then
frozen; the access-only stack, the rule stack with the channel-access agent
alone, at GOPs 6-6 and 3-9, then in the series of E4
and E5; the link-break agent's exploration nil or decaying alone; and fixed
settings of the channel access, outside the article's plan. `sets.txt`
lists the 143 sets, 2708 simulations: 20 realisations per set, one
for each of the 8 development runs. Set names end in `-s11`
(`-bgreedy-s10` for the link-break agent without exploration, declared in the
first round and run in this one). The knobs behind each suffix are in the
last column of `code/campaign/sets.conf`, and the simulator's switches in
`code/ns2/README.md` (paths from the root of the repository).

**Seeds.** Every set takes the seeds of the main study, `0-comparative`
(`run_sets.sh --seed-name=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-<fire>`):
it pairs, realisation by realisation, with every set of the main study and of
the first round under the same fire, on the 60 seeds (fire, realisation).
The development runs take realisations 21 and 22 of the same series, outside
those seeds.

**The agents' trace.** Every set but those of tranche T7 carries
`rl_trace=1`, the agents' counts and values every 20 s, which leaves the
simulation unchanged; the 57 sets of T7 carry no trace, as the sets of E4
and E5 they join.

| Tranche | Experiment | Series | Suffix | Stacks | GOP | Sets (simulations) | What it controls |
|---|---|---|---|---|---|---|---|
| T1 | E3 | exploration only or learning only | `-hybrid-explore-s11` | hybrid | 9-3 | 3 (60) | every learning rate at 0 (`rl_alpha=0`, `rl_mac_alpha=0`): exploration without learning |
| T1 | E3 | exploration only or learning only | `-hybrid-learn-s11` | hybrid | 9-3 | 3 (60) | every exploration rate at 0 (`rl_epsilon=0`, `rl_mac_epsilon=0`): learning without exploration |
| T2 | – |  | `-hybrid-be<BE>nb<NB>-s11`, `-rules-be<BE>nb<NB>-s11` | access only, hybrid | 9-3 | 24 (480) | the channel-access agent held on one action (`rl_access_fixed=<a>`); outside the plan |
| T3 | E2 | access only | `-rules-onlyA-s11` | access only | 3-9, 6-6 | 6 (120) | the access-only stack at the two other GOPs |
| T4 | E3 | link break | `-agents-bgreedy-s10` | agents | 3-9, 6-6, 9-3 | 9 (180) | the link-break agent without exploration (`rl_break_eps=0`) |
| T4 | E3 | link break | `-agents-bdec-s11` | agents | 3-9, 6-6, 9-3 | 9 (180) | the link-break agent's exploration decaying alone, from 0.1 at 60 s to 0 at 114 s (`rl_break_eps_start=60`, `rl_break_eps_end=114`), the six other agents keeping 0.1 |
| T5 | E2 | learned configurations | `-rules-onlyA-dev<k>-s11`, `-hybrid-dev<k>-s11` | access only, hybrid | 9-3 | 8 (8) | the development runs, one simulation each, which write the configuration the agent has learned (`rl_access_dump=rl-access.tsv`, `realisation=K`) |
| T6 | E2 | learned configurations | `-rules-onlyA-cfg<k>-s11`, `-hybrid-cfg<k>-s11` | access only, hybrid | 9-3 | 24 (480) | configuration k frozen on the stack that learned it (`rl_access_policy=sensors-rl/2-round2/policies/<stack>-k<k>.tsv`) |
| T7 | E5 | load | `_p7`, `_p12`, `_p18`, `_p30`, `-rules-onlyA-s11` | access only | 9-3 | 12 (240) | alarm periods of 7, 12, 18 and 30 s instead of 9 s |
| T7 | E5 | scenario | `-rules-onlyA-forest-s11`, `-smoke`, `-j8`, `-swap`, `-v15` | access only | 9-3 | 15 (300) | the two other videos, the 30 m grid, camera and sink swapped, head speed times 1.5 |
| T7 | E5 | fire | `-rules-onlyA-az015-s11`, `-az05`, `-az165`, `-pf0`, `-pf025`, `-pf075`, `-fd1` | access only | 9-3 | 21 (420) | the seven variants of the fire parameters |
| T7 | E4 | equal rate | `_p9r65`, `_p9r32`, `-rules-onlyA-s11` | access only | 3-9, 6-6 | 6 (120) | GOPs 3-9 and 6-6 at the mean packet rate of GOP 9-3 |
| T7 | E4 | coefficient 0.1 | `_GC-QC-0p1_`, `-rules-onlyA-t168-s11` | access only | 9-3 | 3 (60) | the quality coefficient 0.1, simulated for 168 s |

In "Stacks", "access only" is the rule stack with the channel-access agent
(`rule_discard=1`, `rl_access=1`). The sets were run in tranches, which some
tools name: T1, exploration only and learning only; T2, the fixed settings of
the channel access; T3, the access-only stack at GOPs 6-6 and 3-9; T4, the
link-break agent's exploration; T5, the development runs; T6, the replays of
the learned configurations; T7, the access-only stack in E4 and E5. The
comparisons are computed by `code/analysis/sensors_rl/analysis/round2.py`
(`python3 -m sensors_rl report --only round2`, run from `code/analysis/`) and,
for T7, by `access_robustness.py` (`report --only access-robustness`).

## Learned configurations (T5 and T6)

**A configuration.** Per node, the channel-access agent holds a value for
each of its nine actions in each of nine states: 3 classes of packet
(critical, normal, low) × 3 ranges of the link's mean quality indicator
(under 120, under 180, above). Its configuration at the end of a run is, per
node and state, its greedy action by its own rule, the first action of
highest value, so that a state never visited keeps the standard's action a4,
its initial choice. The end of the run is the last event of the simulation
(`finish`, in `code/campaign/evalvsn.tcl`).

**Development runs** (T5): 8 sets of one simulation, at GOP 9-3, 4 per
stack, where the agent learns and explores as in the main study, on the seeds
below, none of the 60 of the evaluation. `rl_access_dump=rl-access.tsv`
writes the configuration at the end of the run, in the simulation's folder
(`r01/fire_qcif-0.03-13/`); `realisation=K`, read by `run_sets.sh`, gives the
simulation the seed of realisation K of its fire. The runs, their seeds and
the instant of the reading were fixed before any result of the series.

| k | Fire | Realisation | Seed | Set, access-only stack | Set, hybrid stack |
|---|---|---|---|---|---|
| 1 | F1 (`fire`) | 21 | 162459 | `…-fire-rules-onlyA-dev1-s11` | `…-fire-hybrid-dev1-s11` |
| 2 | F2 (`fire2`) | 21 | 646597 | `…-fire2-rules-onlyA-dev2-s11` | `…-fire2-hybrid-dev2-s11` |
| 3 | F3 (`fire3`) | 21 | 402314 | `…-fire3-rules-onlyA-dev3-s11` | `…-fire3-hybrid-dev3-s11` |
| 4 | F1 (`fire`) | 22 | 738890 | `…-fire-rules-onlyA-dev4-s11` | `…-fire-hybrid-dev4-s11` |

(`…` is `set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40`.)

**The frozen policies** (`policies/`). Each file is the `rl-access.tsv` its
development run left, copied unchanged: `policies/rules-onlyA-k1.tsv` to
`policies/rules-onlyA-k4.tsv` for the access-only stack,
`policies/hybrid-k1.tsv` to `policies/hybrid-k4.tsv` for the hybrid stack.
After two comment lines and the line of the column names, one line per node
and state (900 lines for the 100 nodes), tab-separated:

    node  class  link  action  be  nb  frames  q

class 0 critical, 1 normal, 2 low; link 0, 1, 2 the three ranges; action
a = 3 i + j, the minimum backoff exponent be = 2 + i and the maximum number of
backoffs nb = 3 + j; frames, the unicast frames the agent configured in that
state during the run; q, the value of the action. The replay reads the first
four columns and refuses a file that misses or repeats a node's state.

**Replays** (T6). Each configuration, frozen on the stack that learned it, on
the 60 seeds at GOP 9-3: `rl_access_policy` names the file, a path under
`data/`. Every unicast frame takes the action of its node and state, with no
random draw and no learning; broadcasts keep the standard's setting, and in
the hybrid stack the five other agents keep learning. Each is compared, by
seed, with its stack where the agent learns (the access-only stack of
`1-round1`, the hybrid stack of `0-comparative`) and with that stack at the
standard's setting (the rule stack, the hybrid stack without the agent): the
PSNR with Holm's correction over the 4 configurations of a stack and a
reference, the other measures as single tests.

This repository holds the 8 files: the replays run from them, in any
order. A reader who reruns the development runs finds the files again, from
the root of the repository (`sets/` is where `run_sets.sh` writes, unless
`SETS_DIR` is set):

```bash
B=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40
for s in rules-onlyA hybrid; do
  for kf in 1:fire 2:fire2 3:fire3 4:fire; do
    k=${kf%%:*} f=${kf#*:}
    cmp sets/$B-$f-$s-dev$k-s11/r01/fire_qcif-0.03-13/rl-access.tsv \
      data/sensors-rl/2-round2/policies/$s-k$k.tsv
  done
done
```

## Robustness of the access-only stack (T7, 23 November 2026)

The 57 sets of tranche T7 (1140 simulations) measure the access-only stack
in every series of E4 and E5 (the 9 s alarm period at GOP 9-3 is
`-rules-onlyA-s10` of `1-round1`). Each is the declaration of the hybrid set
of `1-round1` of the same variant, its six agents replaced by the
channel-access agent alone (`rule_discard=1`, `rl_access=1`), so that it pairs
with the rule and hybrid sets of that variant; the three fires everywhere.

The comparisons and the families of Holm's correction were fixed on
23 November 2026, before any result of these sets. The PSNR of the access-only
stack minus the rule stack, and of the hybrid stack minus the access-only
stack, at each level of each series, paired on the 60 seeds (two-sided
Student test, 95 % interval uncorrected); one Holm family per series and
comparison:

| Series | Experiment | Levels | Tests of the Holm family, per comparison |
|---|---|---|---|
| load | E5 | alarm periods of 7, 9, 12, 18 and 30 s (9 s from the main study and the first round) | 5 |
| fire | E5 | the 7 variants of the fire parameters | 7 |
| scenario | E5 | the 5 variants of the scenario | 5 |
| equal rate | E4 | GOPs 3-9 and 6-6 | 2 |
| coefficient 0.1 | E4 | GOP 9-3, one level | none (single test) |

The other measures (loss, loss of level M1, images at or above 28 dB,
declarations of dead neighbors, mean delay) are single tests, uncorrected,
outside the families; the article gives none of them. No variation of a gap
with the variant and no other comparison is tested, and the results are
reported whatever their sign, no series dropped.

## Fixed settings (T2)

The 24 sets `-hybrid-be<BE>nb<NB>-s11` and `-rules-be<BE>nb<NB>-s11` hold the
channel-access agent on one action for every unicast frame
(`rl_access_fixed=<a>`), the minimum backoff exponent BE = 2 + i and the
maximum number of backoffs NB = 3 + j of a = 3 i + j. The 4 settings were
chosen before the sets were run, by the decisions the agent takes most often
in the traced simulations of the first round (`agent-trace.tsv`), the standard
left out. The learned configurations replaced them in the article, whose plan,
tables and families leave them out; `report --only round2` prints their
comparisons apart, and their results are published as run.

## Results

`results/runs.tsv` holds one row per simulation, with its seed,
its routing counters and its energy (`code/metrics/compile_runs.py`, from
each set's `events.tsv`, `code/metrics/routing_events.py`);
`results/images.tsv`, `results/oracle.tsv` and `results/declarations.tsv`
hold, per simulation, the loss of each priority level of each image, the
lost packets the connectivity oracle finds recoverable or not, and what each
declaration of a dead neighbor hits. `data/sensors-rl/article/round2.tsv`
holds the columns of `revision.tsv` for these sets (`data --only round2`).
