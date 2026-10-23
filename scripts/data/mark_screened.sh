#!/usr/bin/env bash
# Append every video listed in the current overview index to screened.txt (after the VLM has reviewed the mosaics).
awk '{print $2}' ~/dance_win/data/qa/overview/index.txt >> ~/dance_win/data/annotations/screened.txt
sort -u ~/dance_win/data/annotations/screened.txt -o ~/dance_win/data/annotations/screened.txt
echo "screened: $(wc -l < ~/dance_win/data/annotations/screened.txt)"
