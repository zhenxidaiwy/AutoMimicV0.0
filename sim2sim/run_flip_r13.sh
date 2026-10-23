#!/usr/bin/env bash
# r13 pipeline (mjlab, delay check, native cross checks, scenarios incl. warp-clamp emulation)
S=~/dance_win/sim2sim/native_flip.sh
P=backflip_r13_fid1
bash $S mjlab $P
bash $S delay $P
bash $S native $P
bash $S scen $P 100
bash $S scenwc $P 100
