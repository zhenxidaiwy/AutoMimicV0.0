#!/usr/bin/env bash
# Download GVHMR inference checkpoints from the HF mirror camenduru/GVHMR (non-commercial license, research use).
# sha256 values were cross-checked to be identical in two independent mirrors (camenduru/GVHMR, ryanrudes/gvhmr).
cd ~/projects/GVHMR/inputs/checkpoints || { mkdir -p ~/projects/GVHMR/inputs/checkpoints && cd ~/projects/GVHMR/inputs/checkpoints; }
BASE=https://huggingface.co/camenduru/GVHMR/resolve/main
while read -r sha path; do
  mkdir -p "$(dirname "$path")"
  if [ -f "$path" ] && echo "$sha  $path" | sha256sum -c --quiet 2>/dev/null; then echo "ok (cached) $path"; continue; fi
  for i in 1 2 3; do curl -fL --retry 3 -C - -o "$path" "$BASE/$path" && break; sleep 5; done
  echo "$sha  $path" | sha256sum -c || { echo "SHA MISMATCH $path"; exit 1; }
done <<'EOF'
4fae7da2de388d5da3514cb27a2d003f364dacb280e9cf88972b710e589c6b91 gvhmr/gvhmr_siga24_release.ckpt
2dcf79638109781d1ae5f5c44fee5f55bc83291c210653feead9b7f04fa6f20e hmr2/epoch=10-step=25000.ckpt
50e33f4077ef2a6bcfd7110c58742b24c5859b7798fb0eedd6d2215e0a8980bc vitpose/vitpose-h-multi-coco.pth
c4d5a3f000d771762f03fc8b57ebd0aae324aeaefdd6e68492a9c4470f2d1e8b yolo/yolov8x.pt
EOF
echo DONE_CKPTS
