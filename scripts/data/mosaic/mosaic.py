"""Face-mosaic a clip. Usage: mosaic.py <in_cut.mp4> <out.mp4> <dets.json> [imgsz]
Reads every frame, runs yolov8n-pose (+ a 180-deg-rotated pass for inverted bodies),
builds a head box per person, unions boxes over +-2 frames (never misses a frame),
pixelates each box, writes H.264 (no audio) at the input fps/resolution."""
import sys, json, subprocess, numpy as np, cv2
from ultralytics import YOLO

src, dst, detp = sys.argv[1], sys.argv[2], sys.argv[3]
imgsz = int(sys.argv[4]) if len(sys.argv) > 4 else 960
MODEL = '/home/user/dance_win/live/yolov8n-pose.pt'
KC = 0.3      # keypoint confidence
WIN = 3       # temporal union half-window (frames)
HC_ROT = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5   # run the rotated pass below this mean head-kp conf

cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
cap.release()
H, W = frames[0].shape[:2]
print(f'{src}: {len(frames)} frames {W}x{H} @ {fps}')
model = YOLO(MODEL)
import torch
dev = 0 if torch.cuda.is_available() else 'cpu'


def run(img):
    r = model.predict(img, imgsz=imgsz, conf=0.15, device=dev, verbose=False, half=False)[0]
    out = []
    if r.boxes is None or len(r.boxes) == 0:
        return out
    b = r.boxes.xyxy.cpu().numpy(); c = r.boxes.conf.cpu().numpy()
    k = r.keypoints.data.cpu().numpy()  # n,17,3
    for i in range(len(b)):
        out.append((b[i], float(c[i]), k[i]))
    return out


def head_box(bb, kp):
    x1, y1, x2, y2 = bb
    bw, bh = x2 - x1, y2 - y1
    # a keypoint counts only if confident, not the (0,0) placeholder, and inside the person box (+15%)
    mx, my = 0.15 * bw, 0.15 * bh
    good = ((kp[:, 2] > KC) & ~((kp[:, 0] < 1) & (kp[:, 1] < 1))
            & (kp[:, 0] > x1 - mx) & (kp[:, 0] < x2 + mx) & (kp[:, 1] > y1 - my) & (kp[:, 1] < y2 + my))
    hp = kp[:5]
    vis = hp[good[:5]][:, :2]
    sh = kp[5:7]; hi = kp[11:13]
    sh_ok = good[5:7].all(); hi_ok = good[11:13].all()
    torso = None
    if sh_ok and hi_ok:
        torso = np.linalg.norm(sh[:, :2].mean(0) - hi[:, :2].mean(0))
    priors = [0.06 * H, 0.2 * max(bw, bh)]
    if torso is not None:
        priors.append(0.7 * torso)
    src_kind = 'kp'
    if len(vis) >= 2:
        cen = vis.mean(0)
        span = max(np.linalg.norm(a - b) for a in vis for b in vis)
        side = max(min(1.6 * span, 0.5 * max(bw, bh)), *priors)
    elif len(vis) == 1:
        cen = vis[0]; side = max(priors)
    elif sh_ok:
        smid = sh[:, :2].mean(0)
        if hi_ok:
            up = smid - hi[:, :2].mean(0)
            cen = smid + 0.45 * up
        else:
            cen = smid - np.array([0, 0.12 * bh])
        side = max(priors) * 1.2; src_kind = 'shoulder'
    else:
        cen = np.array([(x1 + x2) / 2, y1 + 0.12 * bh])
        side = max(max(priors), 0.35 * bw) * 1.2; src_kind = 'boxtop'
    side *= 1.15
    cx, cy = cen
    return [float(cx - side / 2), float(cy - side / 2), float(cx + side / 2), float(cy + side / 2)], src_kind, float(np.mean(hp[:, 2] * good[:5]))


raw = []   # per frame: list of head boxes
dets = []
stats = {'kp': 0, 'shoulder': 0, 'boxtop': 0, 'rot': 0, 'empty': 0}
# pass 1: detections (normal + 180-deg rotated pass when head keypoints are weak)
allp = []
for t, f in enumerate(frames):
    people = run(f)
    hcs = [head_box(bb, kp)[2] for bb, c, kp in people]
    weak = len(people) == 0 or any(h < HC_ROT for h in hcs)
    print(t, 'head conf', [round(h, 2) for h in hcs], 'rot' if weak else '')
    rotp = []
    if weak:
        rot = cv2.rotate(f, cv2.ROTATE_180)
        for bb, c, kp in run(rot):
            bb2 = np.array([W - bb[2], H - bb[3], W - bb[0], H - bb[1]])
            kp2 = kp.copy(); kp2[:, 0] = W - kp[:, 0]; kp2[:, 1] = H - kp[:, 1]
            rotp.append((bb2, c, kp2))
    allp.append((people, rotp))
# person scale per clip: a head is ~1/7.5 of standing height -> face box >= 0.2 x the
# 75th-percentile person-box size of the confident detections (keeps boxes big during a tuck)
sizes = [max(bb[2] - bb[0], bb[3] - bb[1]) for people, _ in allp for bb, c, kp in people if c > 0.5]
PSCALE = float(np.percentile(sizes, 75)) if sizes else 0.0
print('person scale', PSCALE)


def grow(hb, side_min):
    cx, cy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
    s = max(hb[2] - hb[0], side_min) / 2
    return [cx - s, cy - s, cx + s, cy + s]


for t, (people, rotp) in enumerate(allp):
    boxes, pb = [], []
    for bb, c, kp in people:
        hb, kind, hc = head_box(bb, kp)
        # full scale prior only for confident (main) people; small/far people keep their own scale
        if c > 0.5:
            hb = grow(hb, 0.2 * PSCALE * 1.15)
        boxes.append(hb); pb.append([float(v) for v in bb] + [c]); stats[kind] += 1
    for bb2, c, kp2 in rotp:
        hb, kind, hc = head_box(bb2, kp2)
        if kind == 'kp':
            boxes.append(grow(hb, 0.2 * PSCALE * 1.15)); stats['rot'] += 1
    if not boxes:
        stats['empty'] += 1
    raw.append(boxes); dets.append(pb)

final, last = [], []
for t in range(len(frames)):
    s = []
    for u in range(max(0, t - WIN), min(len(frames), t + WIN + 1)):
        s += raw[u]
    if not s:
        s = last
    final.append(s)
    if s:
        last = s
# leading frames with nothing: borrow the first non-empty set
first = next((s for s in final if s), [])
final = [s if s else first for s in final]
assert all(final), 'some frame has no face box'


def pixelate(img, box):
    x1, y1, x2, y2 = [int(round(v)) for v in box]
    x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(W, x2), min(H, y2)
    if x2 - x1 < 2 or y2 - y1 < 2:
        return
    side = max(x2 - x1, y2 - y1)
    blk = max(4, int(round(side / 7)))
    roi = img[y1:y2, x1:x2]
    sw, shh = max(1, (x2 - x1) // blk), max(1, (y2 - y1) // blk)
    small = cv2.resize(roi, (sw, shh), interpolation=cv2.INTER_AREA)
    img[y1:y2, x1:x2] = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)


p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                      '-s', f'{W}x{H}', '-r', f'{fps}', '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'slow',
                      '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], stdin=subprocess.PIPE)
for t, f in enumerate(frames):
    g = f.copy()
    for b in final[t]:
        pixelate(g, b)
    p.stdin.write(g.tobytes())
p.stdin.close(); p.wait()
json.dump({'W': W, 'H': H, 'fps': fps, 'n': len(frames), 'person_boxes': dets, 'face_boxes': final,
           'raw_face_boxes': raw, 'stats': stats}, open(detp, 'w'))
print('stats', stats, '-> ', dst)
