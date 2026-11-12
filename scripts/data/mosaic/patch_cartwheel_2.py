"""Extra face boxes for data/source_clips_mosaic/cartwheel_2.mp4 where mosaic.py lost the head (fast, blurred
inverted-to-upright phase, frames 44-58), set by hand from gridded frames; pixelated like mosaic.py (block = side / 7).
  python patch_cartwheel_2.py <mosaic.py output> <out.mp4>
Pipeline: crop rows 150-573 of data/clips/cartwheel_2.mp4 (no app UI) -> safe_run.py mosaic.py -> this script."""
import subprocess, sys, cv2
src, dst = sys.argv[1], sys.argv[2]
BOX = {}
for t in range(44, 51): BOX[t] = (15, 215, 145, 335)
for t in range(51, 54): BOX[t] = (15, 195, 145, 305)
BOX[54] = (55, 150, 175, 260); BOX[55] = (75, 130, 190, 240); BOX[56] = (105, 110, 225, 215)
BOX[57] = (115, 105, 240, 210); BOX[58] = (135, 110, 255, 215)
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS); fr = []
while True:
  ok, f = cap.read()
  if not ok: break
  fr.append(f)
H, W = fr[0].shape[:2]


def pixelate(img, box):
  x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3])
  blk = max(4, round(max(x2 - x1, y2 - y1) / 7))
  roi = img[y1:y2, x1:x2]
  small = cv2.resize(roi, (max(1, (x2 - x1) // blk), max(1, (y2 - y1) // blk)), interpolation=cv2.INTER_AREA)
  img[y1:y2, x1:x2] = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)


p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                      '-r', f'{fps}', '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                      '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], stdin=subprocess.PIPE)
for t, f in enumerate(fr):
  if t in BOX:
    pixelate(f, BOX[t])
  p.stdin.write(f.tobytes())
p.stdin.close(); p.wait()
print('patched', sorted(BOX), '->', dst)
