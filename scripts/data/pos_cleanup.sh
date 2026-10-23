#!/usr/bin/env bash
# Keep only the 7 used positive-training sources in raw_pos_train; drop unused raws, candidate sheets, temp fetcher.
RAW=~/projects/dance/data/raw_pos_train; SH=~/dance_win/scripts/data/tmp_sheets_pos
KEEP="av117323675600986 av117344059853267 av117444957963125 av117424842148656 av117472506220761 av117421637633984 av117372161688659"
echo "downloaded: $(ls $RAW/*.mp4 | wc -l)"
rm -f $RAW/*.part
for f in $RAW/av*; do id=$(basename $f); id=${id%%.*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
for f in $SH/av*.png $SH/stack_s*.png $SH/probe_*.png $SH/big_*.png $SH/stack_big.png; do
  [ -e "$f" ] || continue; id=$(basename $f .png); id=${id%%_*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
rm -f ~/dance_win/scripts/data/tmp_pos_fetch.py
echo "kept: $(ls $RAW | tr '\n' ' ')"
for k in $KEEP; do grep -qx "${k#av}" ~/projects/dance/data/search/pos_exclude.txt && echo "OVERLAP $k"; done
for k in $KEEP; do python3 -c "import json;d=json.load(open('$RAW/$k.meta.json'));print('$k',d.get('owner'),d.get('w'),d.get('h'),d.get('duration'),'|',d.get('title'))"; done
ls -la ~/projects/dance/data/pos_train
