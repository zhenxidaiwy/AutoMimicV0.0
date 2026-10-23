#!/usr/bin/env bash
# Delete downloaded Bilibili videos that contributed no 闪身步 clip, their contact sheets, overview mosaics and the
# tennis smoke-test artefacts. Processed clips (clips/, gvhmr/, g1/, dataset/) are kept.
KEEP="av117312921404527 av117346945600980 av117332315867932 av117438683289595 av117285977068813 av117416621246346"
RAW=~/projects/dance/data/raw; SHEETS=~/dance_win/data/qa/sheets
before=$(du -sm $RAW ~/dance_win/data/qa | awk '{s+=$1} END {print s}')
n=0
for f in $RAW/*; do
  id=$(basename "$f"); id=${id%%.*}
  [[ " $KEEP " == *" $id "* ]] && continue
  rm -f "$f"; n=$((n+1))
done
for f in $SHEETS/*.png; do
  id=$(basename "$f" .png); id=${id%%_*}
  [[ " $KEEP " == *" $id "* ]] || rm -f "$f"
done
rm -rf ~/dance_win/data/qa/overview ~/dance_win/data/qa/test_tennis \
       ~/projects/dance/data/{clips/test_tennis.mp4,gvhmr/test_tennis,g1/test_tennis,gvhmr/test_tennis.gvhmr.log}
after=$(du -sm $RAW ~/dance_win/data/qa | awk '{s+=$1} END {print s}')
echo "deleted $n raw files; raw+qa ${before} MB -> ${after} MB"
echo "kept raw videos:"; ls -la $RAW | grep mp4
