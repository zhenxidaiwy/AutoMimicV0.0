#!/usr/bin/env bash
# Keep only the 9 used negative sources in ~/projects/dance/data/raw_neg; drop unused raws and their sheets.
RAW=~/projects/dance/data/raw_neg; SH=~/dance_win/scripts/data/tmp_sheets_neg
KEEP="av325278019 av668029995 av47296669 av979956852 av114567749312109 av117455695450375 av951867735 av968635540 av117420933122710"
echo "downloaded: $(ls $RAW/*.mp4 | wc -l)"
for f in $RAW/av*; do id=$(basename $f); id=${id%%.*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
for f in $SH/av*.png; do id=$(basename $f .png); id=${id%%_*}; case " $KEEP " in *" $id "*) ;; *) rm -f "$f";; esac; done
ls -la $RAW; ls ~/projects/dance/live_tests
