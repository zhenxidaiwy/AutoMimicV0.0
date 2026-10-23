#!/usr/bin/env bash
SH=~/dance_win/scripts/data/tmp_sheets_pos; O=~/projects/dance/data/pos_train
P=~/miniforge3/envs/gmr/bin/python
for n in gxdsm_6 sss_3; do
  $P -I ~/dance_win/scripts/data/sheet.py $O/$n.mp4 $SH/big_$n.png --every 0.4 --cols 5 --w 192 --max_tiles 10
done
$P -I ~/dance_win/scripts/data/pos_stack.py $SH/stack_big.png $SH/big_gxdsm_6.png $SH/big_sss_3.png
