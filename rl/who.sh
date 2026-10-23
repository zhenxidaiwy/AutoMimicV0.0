#!/usr/bin/env bash
for p in $(pgrep -f "train_getup|chain_getup"); do
  echo "== pid $p ppid $(ps -o ppid= -p $p) start $(ps -o lstart= -p $p)"
  tr '\0' ' ' < /proc/$p/cmdline; echo
  echo "   env RESUME=$(tr '\0' '\n' < /proc/$p/environ | grep ^RESUME= )"
done
echo "== parent chain of the python process:"
py=$(pgrep -f "train_getup.py" | head -1); x=$py
while [ -n "$x" ] && [ "$x" != 1 ]; do ps -o pid=,args= -p $x | cut -c1-140; x=$(ps -o ppid= -p $x | tr -d ' '); done
