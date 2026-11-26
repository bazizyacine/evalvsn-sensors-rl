# evalvsn-sensors-rl — EvalVSN: Reinforcement Learning Agents in a Cross-Layer Stack for Forest Fire Video Surveillance over Wireless Sensor Networks

Supporting material for the article *Reinforcement Learning Agents in a Cross-Layer Stack for Forest Fire Video Surveillance over Wireless Sensor Networks* (M. Y. Baziz, L. Sekhri
and B. Kechar), in the second round of review at *Sensors* (MDPI). This
release, v2.1.4, is the version of the manuscript revised for that round:
the code that ran the simulations, the results of every simulation and the
commands that reproduce them.

| Directory | Contents |
|---|---|
| `code/evalvsn/` | the EvalVSN tool, which codes the video of the camera and evaluates it at the sink (C++11 with GNU extensions, gnu++0x, OpenCV 4.6), with its `CMakeLists.txt` |
| `code/ns2/` | `modules/ns-2.35/`, every file added to or modified in ns-2.35, at its path under `ns-2.35/`: the cross-layer routing agent `aomdv_qpv/` (AOMDV Quality Prioritized Video, AOMDV_QPV) with its learning agents, the derived 802.15.4 MAC and PHY, the power monitor and the fire propagation model under `mac/`, the priority interface queue under `queue/`, the video source and sink under `evalvsn/`, and the release files they touch, `aomdv/` among them; `build.sh`, which builds ns-2.35 with them; a `README.md` that lists them, with the switches of the revision's experiments |
| `code/campaign/` | the simulation scripts: `run_sets.sh` runs the simulations of a set, `sets.conf` declares the sets of the three studies, `ipFiles/` holds their encoder files |
| `code/metrics/` | the measurement scripts: the measurements of each simulation, the connectivity oracle, the routing counters (`routing_events.py`) and one row per simulation (`compile_runs.py`) |
| `code/analysis/` | `sensors_rl`, the article's package, one entry point (`python3 -m sensors_rl`, run from `code/analysis/`): the compilation of the simulations and of the codec (`compile/`), the paired tests with Holm correction, the analyses of variance and the checks of their assumptions (`analysis/`), the tables (`tables/`), the figures (`figures/`) and the check of every number of the text (`claims/`) |
| `data/sensors-rl/` | the three studies, each with its `sets.txt`, a `README.md` and `results/`, whose `runs.tsv` holds one row per simulation: `0-comparative/` (the 36 sets of the main study, experiment E0), `1-round1/` (the 261 sets of the other experiments, run for the first review round) and `2-round2/` (the 143 sets of the second round: its controls, the learned configurations of the channel access, whose frozen policies are in `policies/`, and the access-only stack in E4 and E5); and `article/`, the measurements behind every number of the article: `comparative.tsv`, `revision.tsv` and `round2.tsv`, one row per simulation, and the files listed below |
| `article/figures-src/icons/` | the Twemoji pictograms of Figure 2 (Twitter, Inc and other contributors, CC BY 4.0, license beside them); the package writes the article's tables and figures under `article/tables/` and `article/figures/` |
| `LICENSE`, `LICENSE-data`, `code/ns2/LICENSE-GPL-2.0` | the licenses: GPL-3.0 for the EvalVSN tool and the scripts, GPL-2.0 or later for the files of the ns-2 modules written by the authors, CC BY 4.0 for the data (see License) |
| `CITATION.cff`, `.zenodo.json` | the reference of this release, and its record at Zenodo |

The paths below are given from the root of the repository. The comments of
the code call the three studies 09, 10 and 11.

## The experimental plan

The article's plan (its Table 6) holds six experiments, E0 to E5. An
experiment holds one or several series of its factor; the families of Holm's
correction are those of the article's table of families (`FAMILIES` in
`code/analysis/sensors_rl/tables/plan.py`, printed by
`report --only plan`). A configuration is one set: one
stack, one fire, one GOP and one level of the factor, simulated as many times
as `code/campaign/sets.conf` declares;
`code/analysis/sensors_rl/tables/plan.py` counts them from the three
`sets.txt` and writes the table. 24 sets of `2-round2`, the fixed settings of
the channel access (480 simulations), stay outside the plan: the learned
configurations replaced them, and the article reports them as the first
version of that series.

| Experiment | Question | Configurations (simulations) | Sets |
|---|---|---|---|
| E0 | Effect of the stack, the fire and the GOP | 36 (720) | `data/sensors-rl/0-comparative/` |
| E1 | Implementation of AOMDV (series: control AOMDV, AOMDV with cross-layer timers) | 18 (360) | `data/sensors-rl/1-round1/` |
| E2 | Contribution of each decision (series: access only, learned configurations) | 77 (1388) | `data/sensors-rl/1-round1/`, `data/sensors-rl/2-round2/` |
| E3 | Adaptation of the agents (series: frozen, exploration only or learning only, decaying ε, link break) | 48 (960) | `data/sensors-rl/1-round1/`, `data/sensors-rl/2-round2/` |
| E4 | Video coding, GOP volume and quality coefficient (series: equal rate, coefficient 0.1) | 33 (660) | `data/sensors-rl/1-round1/`, `data/sensors-rl/2-round2/` |
| E5 | Scope of the differences between the stacks (series: load, fire, scenario) | 198 (3960) | `data/sensors-rl/1-round1/`, `data/sensors-rl/2-round2/` |

Two measurements without a code complete the plan (Section 2.7 of the
article). The agents' traces rerun 120 simulations of E0, those of
the agents and hybrid stacks at GOP 9-3 (6 sets of
`1-round1`), with a trace of the agents' choices and values every 20 s. The
costs for a sensor node have no simulation of their own: they are measured on
the simulations of E0 to E2 and the traces.

## Building

The build and the replays below were checked on Ubuntu 24.04 (4 cores),
with gcc-4.8 and g++-4.8 4.8.5 for ns-2.35, gcc 13.3, CMake 3.28 and OpenCV
4.6.0 for EvalVSN, FFmpeg 6.1.1, Python 3.12 with NumPy 2.5, Matplotlib 3.11
and Pillow 12.3.

1. ns-2.35, from the release `ns-allinone-2.35.tar.gz` (the ns-2 project,
   nsnam on SourceForge,
   https://sourceforge.net/projects/nsnam/files/allinone/ns-allinone-2.35/),
   which this repository does not redistribute. `code/ns2/build.sh`
   downloads it, checks its SHA-256, unpacks it under `NS2_HOME`, copies
   `code/ns2/modules/ns-2.35/` over its `ns-2.35/`, then runs the release's
   `install` script, which builds Tcl 8.5.10, Tk 8.5.10, OTcl 1.14, TclCL 1.20
   and then ns-2.35 (about 5 minutes):

   ```bash
   NS2_HOME=$PWD/ns-allinone-2.35 bash code/ns2/build.sh
   export PATH=$PWD/ns-allinone-2.35/ns-2.35:$PATH
   ```

   `./configure && make` in `ns-2.35/` alone stops at configure, which
   needs the Tcl, OTcl and TclCL that `install` builds first. The copied
   `Makefile.in` compiles ns-2.35 with `gcc-4.8` and `g++-4.8`, which must
   be on the `PATH` (Ubuntu 18.04 packages them): g++ 13 stops on a file of
   the release, `ns-2.35/tcp/tcp-linux.cc`. Tk needs the X11 development headers
   (`libx11-dev`). The optional `dei80211mr` library may fail to build;
   ns-2.35 does not use it. The `ns` binary needs no other variable than the
   `PATH`. The release's 802.15.4 classes are left untouched; the stack lives
   in derived classes.
2. The EvalVSN tool: `cmake . && make` under `code/evalvsn/`, which builds
   `bin/evalvsn` (CMake 3.5 or later, the OpenCV 4.6 development files; the
   default build type, Debug, is the one `sensors_rl/compile/codec.py` reproduces).
3. The videos: each content is a 12 s cut of a video of the FLAME 2 dataset
   (Hopkins et al., IEEE DataPort, 2022, https://doi.org/10.21227/swyw-6j78), which
   this repository does not redistribute: in the YUV file, 300 frames at 25 frames per second,
   QCIF (176 × 144 pixels), YUV 4:2:0, under `code/campaign/videos/`; the
   encoder reads the AVI file and codes twelve frames of each in grayscale
   (Table 2 of the article).

   | Content | FLAME 2 video | From | Read by |
   |---|---|---|---|
   | `fire_qcif` | `#6) RGB Video 6.MP4` | 27.0 s | every experiment |
   | `forest_qcif` | `#18) RGB Preburn Video 2.MP4` | 60.0 s | E5 (scenario) |
   | `smoke_qcif` | `#7) RGB Video 7.MP4` | 170.0 s | E5 (scenario) |

   With FFmpeg 6.1.1, these two commands, run from the root of the
   repository with the FLAME 2 video copied there, write the `fire_qcif`
   files the simulations read, byte for byte (their SHA-256 sums are given
   below):

   ```bash
   ffmpeg -ss 27.0 -t 12 -i "#6) RGB Video 6.MP4" -vf "fps=25,scale=176:144" \
     -frames:v 300 -pix_fmt yuv420p -f rawvideo code/campaign/videos/fire_qcif.yuv
   ffmpeg -ss 27.0 -t 12 -i "#6) RGB Video 6.MP4" -vf "fps=25,scale=176:144" \
     -pix_fmt yuv420p -q:v 2 code/campaign/videos/fire_qcif.avi
   ```

   The AVI of `fire_qcif` is cut from the FLAME 2 video itself, at the
   quantizer 2 (`-q:v 2`). Its header declares 301 frames
   (12.04 s): 300 coded frames and an empty entry after the
   first one. EvalVSN takes the frame count from the header
   (`CAP_PROP_FRAME_COUNT`, `code/evalvsn/src/evalvsn.cc`) and codes one
   frame in 26 (Table 2 of the article). An AVI converted
   from `fire_qcif.yuv` declares 300 frames: EvalVSN would code one
   frame in 25, other images. The other contents are cut with the
   first command, from their video and instant in the table above, then
   converted with `ffmpeg -s qcif -i code/campaign/videos/<content>.yuv code/campaign/videos/<content>.avi`, which writes their AVI byte for byte.
   `code/campaign/run_sets.sh` converts the YUV file only when the AVI is
   missing or `--regen-avi` is passed: write `fire_qcif.avi` with the command
   above before running a set. The start of `fire_qcif` was found afterwards,
   by matching its first frame (mean squared error of 4.4).

## Configuration of the main study

As Tables 1 and 2 of the article write it.

Table 1. Simulation parameters and factors of the main study E0.

| Category | Parameter | Value |
|---|---|---|
| Common configuration | Simulator | ns-2.35, IEEE 802.15.4 at 2.4 GHz, 250 kbit/s |
|  | Topology | 10 × 10 grid of nodes spaced 40 m apart, camera and sink at opposite corners |
|  | Radio | AT86RF231, transmission at +3 dBm, sensitivity of -101 dBm |
|  | Clear channel assessment (CCA) | threshold of -91 dBm |
|  | Propagation | log-distance with exponent 3.2, range of 48.6 m |
|  | Interface queue | 16 packets |
|  | Traffic | one reading of 32 bytes every 60 s throughout the mission; from detection at 60 s onward, one image every 9 s, in packets sent 15 ms apart |
|  | Simulated duration | 168 or 169 s depending on the Group of Pictures (GOP) structure |
|  | Agents | learning rate of 0.3 (routing) and 0.2 (access), exploration rate of 0.1 |
| Studied factors | Stack | Ad hoc On-demand Multipath Distance Vector (AOMDV), rules, agents, hybrid |
|  | Fire | F1, F2, F3 (Table 3) |
|  | GOP structure | 3-9, 6-6, 9-3 (Table 2) |
| Repetitions | Simulations | 20 per stack, fire and GOP, 720 in all |

Table 2. Parameters of the EvalVSN tool.

| Parameter | Value |
|---|---|
| Videos | FLAME 2 (fire, forest before the burn, smoke), cut with FFmpeg 6.1.1; 176 × 144 grayscale pixels, 12 frames |
| Encoder | Modified Moving Picture Experts Group (MMPEG), as implemented in EvalVSN |
| Frame rate | 1 image per second, hence 12 of the 301 images extracted from the source, which runs at 25 images per second and whose first two images are identical, that is, one in 26, every 1.04 s after a first interval of 1.00 s (one in 25, every 1.00 s, for the 300 images of the forest and smoke videos of the scenario variants, Section 2.7) |
| Skip threshold | zero, no image skipped |
| GOP coefficient GC | 0.01597, 0.02525 or 0.03, for GOP 3-9, 6-6 or 9-3, respectively; studied factor of E0; 0.01597 and 0.15671 give GOP 9-3 for the forest and smoke videos of the scenario variants |
| Quality coefficient | 0.01, applied to the luminance table of the Joint Photographic Experts Group (JPEG) |
| Priority levels | 13, one per diagonal of the zigzag scan of a block, with the first two diagonals merged, as well as the last two |
| Transform | classical discrete cosine transform on blocks of 8 × 8 pixels |
| Coefficient coding | run-length coding at all levels, then order-0 Exp-Golomb binary coding |
| Payload | at most 74 bytes, including the header |

## Reproducing the main study (E0)

```bash
cd code/campaign
for s in $(cat ../../data/sensors-rl/0-comparative/sets.txt); do
  fire=$(sed -E 's/.*-d[0-9]+-(fire[23]?)(-.*)?$/\1/' <<<"$s")   # fire, fire2 or fire3
  bash run_sets.sh --seed-name=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-$fire "$s"
done
cd ../analysis
python3 -m sensors_rl data --only comparative     # -> data/sensors-rl/article/comparative.tsv
python3 -m sensors_rl report --only comparative   # paired tests, Holm, ANOVA
python3 -m sensors_rl tables                      # the tables, both editions
```

The other experiments run the same way, from the `sets.txt` of `1-round1` and
`2-round2`: "The exact commands, in order", below.

The stacks (AOMDV, the rule stack, the agents stack, the hybrid stack), the
fires (F1, F2, F3) and the GOP structures (3-9, 6-6 and 9-3, set by the GOP
coefficient `gopCoef` of the encoder files `code/campaign/ipFiles/GC-PN-*.dat`)
cross into 36 sets of 20 simulations. The seed of a simulation
derives from the name of the fire and its index (`--seed-name` above), not
from the stack or the GOP, so the stacks and the GOPs of a fire undergo the
same failures and the comparisons are paired. A set keeps its traces and
decoded frames, several gigabytes per set, under `sets/` (or `SETS_DIR` when
it is set); do not pass `--prune`, which deletes the routing trace
(`aomdv_qpv.tr`) the compilation of the revision reads.

## Reading the measurements

`comparative.tsv` holds one row per simulation of E0: the fire, the GOP
structure (`split`: `3M9D`, `6M6D` or `9M3D`), the stack, the simulation
index, the PSNR at the sink averaged over the twelve frames (dB), the overall
packet loss, the loss of the M frames, of priority level M1, of levels M1 to
M3 and of the D frames (%), and, in the column `recoverable`, the packets
lost while a path of live nodes linked the camera to the sink, in % of the
packets sent (the instantaneous-path losses of the article), given by the
connectivity oracle. Every mean, confidence interval and test of E0 is
computed from it by `sensors_rl/analysis/comparative.py`, so each reported
number can be checked without rerunning a simulation.

## The raw results

This release archives the raw result of every simulation of the three
studies, 720, 5220 and 2708 simulations: those the article
reads and, in `2-round2`, the 480 of the fixed settings its plan leaves
out. The per-packet traces are not included.

### What each file of the measurements is

A writer named `data --only NAME` is the command
`python3 -m sensors_rl data --only NAME`, run from `code/analysis/`.

| File | Contents | Written by |
|---|---|---|
| `data/sensors-rl/0-comparative/results/runs.tsv` | the 720 simulations of the main study (E0), one row each | `code/metrics/compile_runs.py` |
| `data/sensors-rl/1-round1/results/runs.tsv` | the 5220 simulations of the 261 sets of the first round, one row each | `code/metrics/compile_runs.py` |
| `data/sensors-rl/2-round2/results/runs.tsv` | the 2708 simulations of the 143 sets of the second round, one row each | `code/metrics/compile_runs.py` |
| `data/sensors-rl/0-comparative/results/routing.tsv` | route requests, route errors, MAC drops, route-queue refusals, route replies, hellos and energy per simulation of the main study | `code/metrics/routing_events.py` |
| `data/sensors-rl/*/results/images.tsv`, `oracle.tsv`, `declarations.tsv` | per simulation: the PSNR, SSIM and loss of each priority level of each image at the sink; the lost packets recoverable or not by the connectivity oracle; what each declaration of a dead neighbor hits | `code/metrics/compile_runs.py --tables` |
| `data/sensors-rl/1-round1/results/sets.tsv` | the moments of each set's graphs (mean, standard deviation and count of each metric: energy per node and per network, lifetime among them) for the nine sets of the tuned AOMDV series of E1, one row each; no tool reads it | `code/metrics/setGraphs.pl`, per set |
| `data/sensors-rl/1-round1/sets.txt`, `README.md` | the 261 sets of the first round, by experiment and series | |
| `data/sensors-rl/2-round2/sets.txt`, `README.md` | the 143 sets of the second round, by control, and the protocols of the learned configurations and of the access-only stack in E4 and E5 | |
| `data/sensors-rl/2-round2/policies/` | the 8 frozen configurations of the channel access, per node and state, which the replays of E2 read: 4 for the access-only stack, 4 for the hybrid stack | the development runs (`rl_access_dump`) |
| `data/sensors-rl/article/comparative.tsv` | one row per simulation of E0 (see above) | `data --only comparative` |
| `data/sensors-rl/article/fire-map-F1.tsv` to `fire-map-F3.tsv` | the state of each node at the instant the scenario figure draws, per fire | `data --only comparative` |
| `data/sensors-rl/article/galerie/` | the frames of the gallery figure, decoded at the sink, and their `README.md` | `code/evalvsn/bin/evalvsn -decode` |
| `data/sensors-rl/article/revision.tsv` | one row per simulation of the main study and of the first round that the article reads: PSNR, SSIM, loss, M1 loss, usable images (PSNR ≥ 28 dB, and 25 and 31 dB), mean and 95th-percentile delay, late packets, neighbor-death declarations and the false ones, control messages; frozen as the first round deposited it | `data --only revision` |
| `data/sensors-rl/article/round2.tsv` | the same columns, one row per simulation of the second round (the controls, the learned configurations and their development runs, the fixed settings, the access-only stack in E4 and E5) | `data --only round2` |
| `data/sensors-rl/article/agent-trace.tsv` | the agents' decisions every 20 s in the 120 simulations of the agents' traces: deciding nodes, decisions, median per node, share away from the initial choice, decisions per action | `data --only agent-trace` |
| `data/sensors-rl/article/break-agent.tsv` | per simulation at GOP 9-3: the failure counts the link-break agent chose, the declarations per 18 s of the alarm, the PSNR of each image | `data --only break-agent` |
| `data/sensors-rl/article/break-cases.tsv` | per simulation at GOP 9-3: what each declaration of a dead neighbor hits by the oracle's link budget (the neighbor out of service, a link the heated zone puts below the floor, a link within the budget), the HELLO purges, and, for the traced agents stack, the failure count of each declaration | `data --only break-cases` |
| `data/sensors-rl/article/frames.tsv` | per image, at alarm periods of 7, 9 and 12 s: type, PSNR, SSIM, packet loss and loss of the first priority level; the access-only stack at 9 s, from the images of `1-round1/results/images.tsv` | `data --only frames`, then `data --only frames-access` |
| `data/sensors-rl/article/oracle-s10.tsv` | per simulation of the load, fire and scenario series of E5: packets lost, and those lost while no path of live nodes joined camera and sink | `data --only oracle` |
| `data/sensors-rl/article/overhead.tsv` | radio energy per node and per network, and lifetime, per set: the four stacks and the control AOMDV at the three GOPs, AOMDV with cross-layer timers and the access-only stack at GOP 9-3 | `data --only overhead` |
| `data/sensors-rl/article/methode-mesures.tsv` | the numbers the methods quote from the sets: simulated time and nodes out of service per alarm period, the worst-case connectivity, the correlation of each loss class with the PSNR, the frame sizes and reference PSNR per GOP, the calibration losses, the packets of the other videos | `data --only methods` |
| `data/sensors-rl/article/codec-frames.tsv` | why a D frame of the fire video holds more bytes than an M frame: frames, bytes and packets per type and GOP, the same image coded as M and as D, the correlation and the energy of the DCT coefficients per band, the non-zero coefficients, the Exp-Golomb bits, the quality coefficient swept at GOP 9-3, the steps of the source video | `data --only codec` |
| `code/metrics/compile_runs.py`, `routing_events.py` | the raw-results compiler and the routing-event counter | |

`runs.tsv` keys each row by `set` and `realisation`, gives the `seed` the
simulation ran on, the keys of `revision.tsv` (`arm`, `fire`, `split`,
`period`, `dist`), then what the
simulation measured, as the tools wrote it: the `sim/mt.dat` columns (PSNR,
SSIM and their loss-free references in dB and [0, 1], packet loss overall, of the M
and D frames and of each priority level M1 to M13 and D1 to D13, in %), the
PSNR, SSIM and loss of each image at the sink (`psnr_i1` … `loss_i12`), and
the routing counters where they were counted. A row of `revision.tsv` or
`comparative.tsv` joins its row in `runs.tsv` on these keys; its PSNR and
losses are the same numbers.

### The seeds

Every set of the three studies takes the seeds of
`set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-<fire>`, `<fire>` being `fire`,
`fire2` or `fire3`: the seed of realisation k is
`cksum("<that name>-<k>") mod 900000 + 1` (`seed_for` in
`code/campaign/run_sets.sh`), the column `seed` of `runs.tsv`, checked
against the seed each set's log recorded. The one simulation of a development
run of `2-round2` is one of realisations 21 and 22 of that series (`realisation=K` in
its knobs), and runs as `r01`.

### Replaying one simulation

One realisation replays from its seed, the column `seed` of `runs.tsv`
(`--sims=1` alone would run ns-2's own sequence, seed 0, which is no
realisation of the campaigns). For the first realisation of the hybrid stack
under F1 at GOP 9-3, about two minutes:

```bash
cd code/campaign
bash run_sets.sh --sims=1 --seed=45026 set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-fire-hybrid
```

The run writes the realisation under `sets/<set>/r01/` (under `SETS_DIR`
when it is set), whatever its index in the campaign; its `sim/mt.dat` holds,
as written, the PSNR, SSIM and losses of the row (`set`, `r01`) of
`data/sensors-rl/0-comparative/results/runs.tsv`. Built as above, the
simulator and EvalVSN replay the campaigns bit for bit: on 14 November 2026,
the 20 realisations of this set and one realisation of nine other sets of
the main study and of the first round wrote reception traces, packet traces
and decoded images identical, byte for byte, to those of the campaigns. The
simulator has since gained the switches of the second round, off by default:
built from this release's modules on 22 November 2026, it replayed the same way
the first realisation of eighteen sets of the three studies.

### The exact commands, in order

Prerequisites: ns-2.35 built with `code/ns2/build.sh` (see Building) and on
the `PATH`, `code/evalvsn/bin/evalvsn`, perl, ffmpeg (ffprobe included),
gnuplot and pdftoppm (poppler-utils) for the plots of `setGraphs.pl`, Python
3.12 with NumPy, Matplotlib and Pillow, the Liberation Sans font
(fonts-liberation), with which the figures are drawn, and the videos under
`code/campaign/videos/`. The files the simulations read have these SHA-256
sums:

| File | SHA-256 |
|---|---|
| `fire_qcif.yuv` | `b660fdd2d63d42095168fb4a3fa273d92fe6250f05244bb4c3ef05471e9dc31d` |
| `fire_qcif.avi` | `79613269d72d46e506f1b391868b41509efc6c6323712b7865e8cc7fa7edaf9a` |
| `forest_qcif.yuv` | `3a29ba244832a083c638c744813ef4b7c2e04f038b35e2142309f5b10c693b15` |
| `forest_qcif.avi` | `0ec5f187b31270d3c97b15cd36b54d70ca6e94b65ea018012ea3b934bdeb407e` |
| `smoke_qcif.yuv` | `aa4daeb4bb3bec1a42c058e0e77950b598d08c6660111cc817215187b1b3dc60` |
| `smoke_qcif.avi` | `c53d4bf76a485b734d5daec719a0bc14a5fa25fda715ea5e9c02a369f5f697ab` |

1. The simulations, the commands the campaigns ran (each set ran with the
   options above; a set interrupted by a restart was completed with
   `--resume`, which keeps the realisations already harvested). A
   simulation takes 1.5 to 3.5 minutes on one core, a set of 20
   simulations 30 to 70 minutes, and a set keeps about 3.8 GB of traces,
   decoded frames and log: the 440 sets, 8648 simulations, take about
   370 hours of one core and 1.7 TB of
   disk. `code/campaign/` holds one campaign at a time (`run_sets.sh`
   takes a lock there): run sets in parallel from separate copies of the
   repository. The replays of `2-round2` read the frozen policies of
   `data/sensors-rl/2-round2/policies/`, which this repository holds.

   ```bash
   cd code/campaign
   BASE=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40
   for study in 0-comparative 1-round1 2-round2; do
     for s in $(cat ../../data/sensors-rl/$study/sets.txt); do
       fire=$(sed -E 's/.*-d[0-9]+-(fire[23]?)(-.*)?$/\1/' <<<"$s")
       bash run_sets.sh --seed-name=$BASE-$fire "$s"
     done
   done
   ```

2. The routing counters, read from the packet traces (`st-packet.tr`); once
   they are counted, `st-packet.tr` and `st-packet.nam` may be deleted, no
   other tool reads them:

   ```bash
   cd ../metrics
   python3 routing_events.py -o ../../data/sensors-rl/0-comparative/results/routing.tsv \
     $(cat ../../data/sensors-rl/0-comparative/sets.txt)
   for s in $(cat ../../data/sensors-rl/1-round1/sets.txt ../../data/sensors-rl/2-round2/sets.txt); do
     python3 routing_events.py -o ../../sets/$s/events.tsv "$s"
   done
   ```

3. The raw results, one row per simulation:

   ```bash
   python3 compile_runs.py --seed-base=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40 sensors-rl/0-comparative
   python3 compile_runs.py --seed-base=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40 sensors-rl/1-round1
   python3 compile_runs.py --seed-base=set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40 sensors-rl/2-round2
   ```

   and, per simulation, the images, the oracle and the declarations: the same
   commands with `--tables images,oracle,declarations`.

4. The measurements of the article, from the sets (`code/analysis/`):

   ```bash
   cd ../analysis
   python3 -m sensors_rl data     # every file of data/sensors-rl/article/ in turn
   ```

   `--only NAME` compiles one file: `comparative` (with `fire-map-F1.tsv` to
   `F3`), `revision`, `round2`, `frames`, `oracle` (`oracle-s10.tsv`),
   `agent-trace`, `break-agent`, `break-cases`, `methods`
   (`methode-mesures.tsv`), `codec` (`codec-frames.tsv`, re-encoding the
   video) and `overhead`. Without all the sets of `0-comparative` and
   `1-round1` on disk, every step but `revision` and `round2` refuses, and the
   stored file stays.

5. The tables and figures, from `data/sensors-rl/article/` and the results
   of the three studies alone: no simulation is needed from here on. The
   `tables` step writes, under `article/tables/`, the article's tables and
   their French counterparts, their names starting with `en_` and `fr_`; the
   `figures` step writes `article/figures/`.

   ```bash
   mkdir -p ../../article/tables ../../article/figures
   python3 -m sensors_rl tables
   python3 -m sensors_rl figures --lang en
   ```

6. The statistics behind them and behind the text, printed, all or one by one
   (`--only NAME`), then every number of the text, recomputed:

   ```bash
   python3 -m sensors_rl report
   python3 -m sensors_rl claims
   ```

   | `--only` | What it prints | Module |
   |---|---|---|
   | `comparative` | the main study (E0): the means of each cell, the paired gaps, the analyses of variance | `sensors_rl/analysis/comparative.py` |
   | `quality` | the images, the delay and the deadlines of the main study | `sensors_rl/analysis/quality.py` |
   | `controls` | E1 and E3, the implementation of AOMDV and the adaptation of the agents | `sensors_rl/analysis/controls.py` |
   | `ablation` | E2, the agents one by one | `sensors_rl/analysis/ablation.py` |
   | `coding` | E4, the equal rate and the coefficient 0.1 | `sensors_rl/analysis/coding.py` |
   | `robustness` | E5, the load, the fire and the scenario | `sensors_rl/analysis/robustness.py` |
   | `overhead` | the costs for a sensor node | `sensors_rl/analysis/overhead.py` |
   | `plan` | the plan and the families of Holm's correction | `sensors_rl/tables/plan.py` |
   | `round2` | the controls of the second round, the learned configurations and the fixed settings | `sensors_rl/analysis/round2.py` |
   | `assumptions` | the assumptions of the tests: normality, sphericity, rank tests | `sensors_rl/analysis/assumptions.py` |
   | `access-robustness` | the access-only stack in the series of E4 and E5 | `sensors_rl/analysis/access_robustness.py` |

### Each table of the revised article

| Table | Generated by | Statistics printed by (`python3 -m sensors_rl`) |
|---|---|---|
| 1, Simulation parameters and factors of the main study E0 | written in the article | |
| 2, Parameters of the EvalVSN tool | written in the article | |
| 3, Three fires; camera at (0, 0) m, sink at (360, 360) m | written in the article | |
| 4, Agents and the rules they replace | written in the article | |
| 5, Metrics of the results | written in the article | |
| 6, Experimental plan: 20 simulations per configuration, one per development run | `sensors_rl/tables/plan.py` | `report --only plan` |
| 7, Families of the Holm correction | `sensors_rl/tables/plan.py` | `report --only plan` |
| 8, PSNR at the sink, mean ± half-width of the 95% confidence interval | `sensors_rl/tables/comparative.py` | `report --only comparative` |
| 9, Ablations at GOP 9-3, means over 60 seeds: agent minus its rule, 95% confidence interval in brackets; link-break detection in the hybrid stack: agents stack minus hybrid stack, p of its E0 family | `sensors_rl/tables/ablation.py` | `report --only ablation` |
| 10, Agent decisions at GOP 9-3, means per simulation | `sensors_rl/tables/controls.py` |  |
| 11, Controls at GOP 9-3, means over 60 seeds; learned, then frozen: mean of the four configurations (240 simulations) | `sensors_rl/tables/controls.py` | `report --only controls` |
| 12, PSNR differences by cell, 95% confidence interval in brackets, corrected p for E0; the access-only stack is tested by GOP | `sensors_rl/tables/comparative.py` | `report --only comparative` |
| 13, Image quality and packet delay, means over 60 seeds | `sensors_rl/tables/quality.py` | `report --only quality` |
| 14, Repeated-measures analysis of the PSNR, 540 simulations over 60 seeds, 95% confidence interval in brackets; dash: between-seed term, not corrected | `sensors_rl/tables/comparative.py` | `report --only comparative` |
| 15, GOP at T = 9 s and at equal rate, means over 60 seeds; T: alarm period | `sensors_rl/tables/coding.py` | `claims`, rows P26, the tests at equal rate |
| 16, Quality coefficient at GOP 9-3, means over 60 seeds | `sensors_rl/tables/coding.py` | `report --only coding`, the tests of the coefficient 0.1 |
| 17, Alarm period T at GOP 9-3, means over 60 seeds, 95% confidence interval in brackets | `sensors_rl/tables/robustness.py` | `report --only robustness`, `report --only access-robustness` |
| 18, Fire parameters at GOP 9-3, means over 60 seeds, 95% confidence interval in brackets | `sensors_rl/tables/robustness.py` | `report --only robustness`, `report --only access-robustness` |
| 19, Scenario variants at GOP 9-3, means over 60 seeds, 95% confidence interval in brackets; reference: fire video, 40 m grid | `sensors_rl/tables/robustness.py` | `report --only robustness`, `report --only access-robustness` |
| 20, Costs of the stacks at GOP 9-3, means over 60 seeds | `sensors_rl/tables/overhead.py` | `report --only overhead` |

### Each figure of the revised article

| Figure | Drawn by |
|---|---|
| 1, Video surveillance of a forest fire by a wireless sensor network | a drawing (TikZ or UML), not part of this release |
| 2, The three fires 150 s after ignition, that is, 90 s after detection, in the first simulation with the rule stack | `sensors_rl/figures/methods.py` |
| 3, Admission region of the early discard versus the congestion index IC and the normalized rank, for the rule's threshold IC_0 and the agent's other finite thresholds | `sensors_rl/figures/methods.py` |
| 4, AOMDV Quality Prioritized Video (AOMDV_QPV) cross-layer stack | a drawing (TikZ or UML), not part of this release |
| 5, Unified Modeling Language (UML) class diagram of the agents | a drawing (TikZ or UML), not part of this release |
| 6, Learning trajectories of the agents at GOP 9-3 | `sensors_rl/figures/results.py` |
| 7, PSNR at the sink for the four stacks of E0 and the access-only stack (E2), by GOP and fire | `sensors_rl/figures/results.py` |
| 8, Loss of the M1 level for the four stacks of E0 and the access-only stack (E2), by GOP and fire | `sensors_rl/figures/results.py` |
| 9, Image 8 of the first simulation under F1 at GOP 9-3, with the PSNR of the image decoded at the sink and the loss of its M1 level | `sensors_rl/figures/results.py` |

`python3 -m sensors_rl claims` recomputes every other number the text
quotes, from `data/sensors-rl/`, and prints for each the value the
text writes, the value computed and whether they agree: the results
(`claims/results.py`), then the scenario series of E5 (`claims/scenario.py`),
the tuned AOMDV series of E1 (`claims/aomdv.py`) and what the second review
round adds (`claims/review.py`, with the controls in `claims/round2.py`, the
forms the abstract, the introduction, the discussion and the conclusions give
in `claims/synthesis.py` and the access-only stack in E4 and E5 in
`claims/access_robustness.py`). Their labels
are in French, and their numbers carry a decimal comma; the numbers are those
of the article. The same step also looks for each written value in the
article's French text, which this repository does not hold: it says so
("sources absentes, non lues") and checks the values alone.

`sensors_rl/analysis/overhead.py` reads the size of the agents' tables from
the simulator's headers, under `code/ns2/modules/ns-2.35/`.

## License

The licenses go by directory:

| Directory | License |
|---|---|
| `code/` (the EvalVSN tool, the scripts, `code/ns2/build.sh` and the article's package) but `code/ns2/modules/`; the `sets.txt` and `README.md` of each study under `data/sensors-rl/` | GNU General Public License, version 3 (`LICENSE`) |
| `code/ns2/modules/`, the 9 files written by the authors (`SPDX-License-Identifier: GPL-2.0-or-later` in their header) | GNU General Public License, version 2 or any later version (`code/ns2/LICENSE-GPL-2.0`), so that they combine with the GPL version 2 of AOMDV, with which they are compiled |
| `code/ns2/modules/`, the 31 files that come from ns-2.35 or derive from it, AOMDV and AOMDV_QPV among them | their original license, as the notices of their headers state it; `code/ns2/README.md` lists each file by license |
| `data/sensors-rl/*/results/`, `data/sensors-rl/2-round2/policies/`, `data/sensors-rl/article/` and the tables the tools generate from them | Creative Commons Attribution 4.0 International (`LICENSE-data`), except the frames of `data/sensors-rl/article/galerie/`, decoded from a FLAME 2 video, which keep the dataset's terms |
| `article/figures-src/icons/` | the Twemoji pictograms, by Twitter, Inc and other contributors, under CC BY 4.0 (`LICENSE-GRAPHICS` beside them) |

## Citation

This release, v2.1.4, is archived at Zenodo. All its versions share the
concept DOI [10.5281/zenodo.24147853](https://doi.org/10.5281/zenodo.24147853), which
leads to the latest one; the Zenodo record of each version gives the DOI of
that version.
`CITATION.cff` gives the reference of this release in a form citation
managers read; the article's reference will join it once the article is
published.
