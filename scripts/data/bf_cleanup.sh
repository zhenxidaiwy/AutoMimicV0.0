#!/usr/bin/env bash
# Keep only the 6 used backflip sources; delete other raws (incl .part) and their sheets.
RAW=~/projects/dance/data/raw_backflip; SH=~/dance_win/scripts/data/tmp_sheets_bf
KEEP="av75680591 av116460269603942 av117438112863924 av116641228784719 av115505847472177 av233376646"
echo "downloaded: $(ls $RAW/*.mp4 | wc -l)"
for f in $RAW/av*; do id=$(basename $f); id=${id%%.*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
for f in $SH/*.png; do b=$(basename $f .png); case "$b" in clip_*) continue;; esac
  id=$(echo $b | grep -o 'av[0-9]*'); case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
ls $RAW; ls ~/projects/dance/data/clips | grep -i backflip
