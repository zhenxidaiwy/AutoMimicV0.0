#!/usr/bin/env bash
# Clone the MIT-licensed mjlab G1 curriculum that contains a get-up (fall recovery) task.
cd ~/projects
[ -d g1-humanoid-rl ] || git clone -q https://github.com/chaoticcuriosity-io/g1-humanoid-rl.git
cd g1-humanoid-rl && git log -1 --format='%h %cd' --date=short
ls recovery-task recovery-task/config/g1 recovery-task/mdp
grep -rn "mjlab" --include=*.toml --include=*.txt --include=*.md . | grep -iE "version|==|>=" | head -5
