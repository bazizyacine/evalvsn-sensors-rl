# Gallery of the comparative study

Frame 8 of simulation r01 under the F1 fire at the 9-3 split of study 09,
decoded at the sink by `code/evalvsn/bin/evalvsn -decode` from the set's
encoding and the r01 traces (`st-packet.dat`, `rt-packet.dat`,
`ns2_st-packet.dat`, `st-frame.dat`). `python3 -m sensors_rl figures`
(`code/analysis/sensors_rl/figures/results.py`) lays the six images out as the
gallery figure, two columns and three rows.

| file | what it shows | decoded from |
|---|---|---|
| `reference.png` | the frame coded without network loss | the encoding (11 October 2026) |
| `aomdv.png` | classic AOMDV | `set_AOMDV_GC-PN-0p03-13_p9-n100-d40-fire-pq` |
| `rules.png` | the rule stack | `set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-fire-rules` |
| `access.png` | the access-only stack | `set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-fire-rules-onlyA-s10` (study 10), replayed |
| `agents.png` | the agents stack | `set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-fire-agents` |
| `hybrid.png` | the hybrid stack | `set_AOMDV_QPV_GC-PN-0p03-13_p9-n100-d40-fire-hybrid` |

The four frames of study 09 were decoded on 16 October 2026 from the rerun of study 09
on the packets that decode alone and the corrected salvage: the decoder
reads only the packets that reached the sink. The reference frame is
unchanged, the coding itself being the same. The decoding procedure
reproduces a stored frame pixel for pixel.

`access.png` is `sim/decodedImages/frame_8.png` of a replay of r01 of the
access-only set (26 November 2026), its sets being purged: `bash run_sets.sh
--sims=1 --seed=45026 <set>` in a private copy of `code/campaign`, on the
ns-2.35 build of 22 November 2026, seed 45026 being the one of r01 in
`data/sensors-rl/1-round1/results/runs.tsv`. The replay's `sim/mt.dat` equals
that row of `runs.tsv` in all 33 columns (PSNR 30.4223 dB, loss 49.8505 %,
M1 loss 6.36792 %), and its `sim/rt-frame.dat` equals the twelve rows of r01
in `results/images.tsv`, every level's loss included; frame 8 is at
32.8952 dB, M1 loss 0 %. The replay's reference image of frame 8 equals
`reference.png` pixel for pixel. The access-only stack's rows of
`frames.tsv` come from `results/images.tsv` (`python3 -m sensors_rl data
--only frames-access`).
