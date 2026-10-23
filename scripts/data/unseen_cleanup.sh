#!/usr/bin/env bash
# Remove held-out candidates that were not used (raw videos + their tmp sheets) and probe leftovers.
# Keeps the 4 used sources (mp4 + meta.json) in ~/projects/dance/data/raw_unseen.
RAW=~/projects/dance/data/raw_unseen; SH=~/dance_win/scripts/data/tmp_sheets
KEEP="av117459487038205 av117341190885645 av117381422713290 av117428046534506"
echo "downloaded: $(ls $RAW/*.mp4 | wc -l) videos"
n=0
for f in $RAW/av*; do
  b=$(basename $f); id=${b%%.*}
  case " $KEEP " in *" $id "*) continue;; esac
  rm -f "$f"; n=$((n+1))
done
echo "removed $n raw files"
m=0
for f in $SH/*.png; do
  b=$(basename $f .png); id=${b%%_*}
  case "$b" in out_unseen_*) continue;; esac
  case " $KEEP " in *" $id "*) continue;; esac
  rm -f "$f"; m=$((m+1))
done
echo "removed $m sheets"
rm -f ~/projects/dance/data/search/bili_cookies.txt /tmp/unseen_page.html /tmp/unseen_api.html /tmp/unseen_m.html
rm -f ~/dance_win/scripts/data/unseen_explore.sh ~/dance_win/scripts/data/unseen_list.py ~/dance_win/scripts/data/unseen_list.sh \
      ~/dance_win/scripts/data/unseen_probe.sh ~/dance_win/scripts/data/unseen_status.sh
echo "== raw_unseen"; ls -la $RAW
echo "== tmp_sheets"; ls $SH
echo "== live_tests"; ls -la ~/projects/dance/live_tests
