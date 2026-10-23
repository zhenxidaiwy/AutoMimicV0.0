#!/usr/bin/env bash
# Keep only the 12 used batch-2 negative sources in ~/projects/dance/data/raw_neg2; drop unused raws, sheets, trials.
RAW=~/projects/dance/data/raw_neg2; SH=~/dance_win/scripts/data/tmp_sheets_neg2
KEEP="av929113809 av980445915 av115655483332578 av847448728 av949268496 av221839081 av449913934 av116168832584860 av117443699737792 av114574862844188 av838244221 av784695080"
echo "downloaded: $(ls $RAW/*.mp4 | wc -l)"
rm -f $RAW/*.part
for f in $RAW/av*; do id=$(basename $f); id=${id%%.*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
for f in $SH/av*.png; do id=$(basename $f .png); id=${id%%_*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
rm -rf ~/dance_win/scripts/data/tmp_trial_neg2 ~/dance_win/scripts/data/tmp_neg2_fetch.py
ls $RAW | wc -l; ls ~/projects/dance/live_tests
# overlap check against the exclusion list
for k in $KEEP; do grep -qx "${k#av}" ~/projects/dance/data/search/neg2_exclude.txt && echo "OVERLAP $k"; done
for k in $KEEP; do python3 -c "import json,sys;d=json.load(open('$RAW/$k.meta.json'));print('$k',d.get('owner'),d.get('w'),d.get('h'),'|',d.get('title'))"; done
ls ~/projects/dance/data/raw_backflip >/dev/null && echo "raw_backflip untouched"
