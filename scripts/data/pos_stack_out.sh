#!/usr/bin/env bash
SH=~/dance_win/scripts/data/tmp_sheets_pos
P=~/miniforge3/envs/gmr/bin/python
$P -I ~/dance_win/scripts/data/pos_stack.py $SH/stack_out_g.png $SH/out_gxdsm_1.png $SH/out_gxdsm_2.png $SH/out_gxdsm_3.png $SH/out_gxdsm_4.png $SH/out_gxdsm_5.png $SH/out_gxdsm_6.png $SH/out_gxdsm_7.png
$P -I ~/dance_win/scripts/data/pos_stack.py $SH/stack_out_s.png $SH/out_sss_1.png $SH/out_sss_2.png $SH/out_sss_3.png $SH/out_sss_4.png $SH/out_sss_5.png
