# 1-round1 — the other experiments of the revised article

The main study, `0-comparative`, is experiment E0 of the article's plan; this
study holds the sets of the others, E1 to E5, and of the agents' traces, run
for the first review round (study 10 in the comments of the code). Every set
takes the seeds of the main study
(`run_sets.sh --seed-name=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-<fire>`),
20 realisations per set: the 60 seeds (fire, realisation) each give
one failure schedule, identical across stacks and GOPs, so that every
comparison with the main study is paired. Set names end in `-s10` (`-frozen`
for the frozen policy), so that no set of the main study is overwritten.
`sets.txt` lists the 261 sets, 5220 simulations; the knobs behind each
suffix are in the last column of `code/campaign/sets.conf`, and the
simulator's switches in `code/ns2/README.md` (paths from the root of the
repository).

| Experiment | Series | Suffix | Stacks | GOP | Sets (simulations) | What it controls |
|---|---|---|---|---|---|---|
| E1 | control AOMDV | `-pq-ctl-s10` | AOMDV | 3-9, 6-6, 9-3 | 9 (180) | classic AOMDV on the derived PHY and MAC, transmission watchdog included (`aomdv_derived=1`); a control, never the reference |
| E1 | AOMDV with cross-layer timers | `-pq-tuned-s10` | AOMDV | 3-9, 6-6, 9-3 | 9 (180) | the control AOMDV with the cross-layer stacks' routing timers and route queue (`aomdv_tuned=1`); a control, never the reference |
| E2 | one agent alone | `-only<X>-s10` | rules | 9-3 | 21 (420) | one agent alone: agent X in place of its rule on the rule stack |
| E2 | one agent out | `-no<X>-s10` | hybrid | 9-3 | 18 (360) | one agent out: agent X taken out of the hybrid stack |
| E3 | frozen | `-frozen` | agents, hybrid | 3-9, 6-6, 9-3 | 18 (360) | every learning and exploration rate at 0: each agent stays on its initial choice |
| E3 | decaying ε | `-edec-s10` | agents, hybrid | 9-3 | 6 (120) | exploration falling linearly to 0 between 60 and 114 s |
| E4 | equal rate | `_p9r65`, `_p9r32` | rules, hybrid | 3-9, 6-6 | 12 (240) | GOPs 3-9 and 6-6 at the mean packet rate of GOP 9-3 (T = 9.65 and 9.32 s) |
| E4 | coefficient 0.1 | `_GC-QC-0p1_`, `-t168-s10` | all four | 9-3 | 12 (240) | the quality coefficient 0.1 instead of 0.01 (`code/campaign/ipFiles/GC-QC-0p1.dat`), simulated for the 168 s of their counterparts of the main study (`simtime=168`) |
| E5 | load | `_p7`, `_p12`, `_p18`, `_p30` | all four | 9-3 | 48 (960) | alarm periods of 7, 12, 18 and 30 s instead of 9 s |
| E5 | fire | `-az015`, `-az05`, `-az165`, `-pf0`, `-pf025`, `-pf075`, `-fd1` | rules, hybrid | 9-3 | 42 (840) | heated-zone attenuation of 0.15, 0.5 and 1.65 dB/m instead of 1; failure probability of 0, 0.25 and 0.75 instead of 0.5; failures closer to the front |
| E5 | scenario | `-forest`, `-smoke`, `-j8`, `-swap`, `-v15` | all four | 9-3 | 60 (1200) | two other videos, at their own GOP 9-3 coefficients; a 30 m grid with an irregular deployment of ±8 m and scaled ignitions; camera and sink swapped; head speed times 1.5 |
| the agents' traces |  | `-tr-s10` | agents, hybrid | 9-3 | 6 (120) | `rl_trace=1`: each agent's action counts and values every 20 s; the runs replay those of the main study exactly |

The agents' letters: P (path), C (congestion threshold), B (link-break
detection), D (discovery), A (channel access), T (transmit power), E (early
discard). The knob `simtime=S` sets a floor of S seconds on the simulated time;
`code/campaign/set.sh` reads it and never passes it to ns-2, so that a set
without it simulates up to its last packet plus 3 s, as before.

The sets were run in tranches, which some tools name: T0, the frozen policy;
T1, the traces, the control AOMDV and the decaying exploration; T2, the agents
one by one; T3, the load and the equal rate; T4, the fire; T5, the scenario;
T8, the tuned AOMDV; T10, the quality coefficient 0.1. T6, T7 and T9 name no
set of this study (`2-round2` has tranches of its own).

**Results.** `results/runs.tsv` holds one row per simulation, with its seed
(`code/metrics/compile_runs.py`): the 5220 simulations of the sets of
`sets.txt`. The routing counters come from each set's `events.tsv`
(`code/metrics/routing_events.py`), written before the packet traces were
deleted; the energy of each simulation, from the same traces, only for the
sets that still held them on 21 November 2026 (the others give the mean of
the set). `results/images.tsv`, `results/oracle.tsv` and
`results/declarations.tsv` hold, per simulation, the loss of each priority
level of each image, the lost packets the connectivity oracle finds
recoverable or not, and what each declaration of a dead neighbor hits
(`code/metrics/compile_runs.py --tables`). `results/sets.tsv` holds the
moments of each set's graphs (`code/metrics/setGraphs.pl`) for the nine sets
of the tuned AOMDV series of E1, their energy at the three GOPs among them;
no tool reads it, and `data/sensors-rl/article/overhead.tsv` gives that
energy at GOP 9-3.
