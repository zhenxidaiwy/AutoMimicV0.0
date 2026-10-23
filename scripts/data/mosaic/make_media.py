"""Side-by-side human->robot GIFs + backflip strip. Reads only MOSAICKED human video.
make_media.py <mode: gif|strip|preview> ..."""
import sys, os, subprocess, shutil, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

P = '/home/user/dance_win'
W_ = '/tmp/mosaic_work'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
FONTB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
LBL_H = 30
L_HUMAN = 'internet video (faces mosaicked)'
L_ROBOT = 'Unitree G1, learned policy'

CLIPS = {
    # name: human mosaic, human crop (x0,y0,x1,y1), robot video, robot crop
    'backflip': dict(h=f'{P}/data/source_clips_mosaic/backflip_3.mp4', hc=(300, 100, 780, 758),
                     r=f'{P}/docs/media/backflip_r14_fidelity.mp4', rc=(180, 80, 740, 720)),
    'sss': dict(h=f'{P}/data/source_clips_mosaic/bda_zhao_sss.mp4', hc=(280, 150, 760, 720),
                r=f'{P}/policies/sss_bda_v1/eval/policy.mp4', rc=(70, 60, 270, 240)),
    'gxdsm': dict(h=f'{P}/data/source_clips_mosaic/bda2_gxdsm_full.mp4', hc=(110, 60, 610, 576),
                  r=f'{P}/policies/gxdsm_full_v1/eval/policy.mp4', rc=(50, 50, 290, 240)),
}


def read(path):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return fr, fps


def crop(f, c):
    x0, y0, x1, y1 = c
    return f[y0:y1, x0:x1]


def to_pil(bgr):
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def label(draw, x, w, text, y=7):
    tw = draw.textlength(text, font=FONT)
    draw.text((x + (w - tw) / 2, y), text, font=FONT, fill=(235, 235, 235))


def compose(cfg, hf, rf, max_w=960, max_ph=450):
    ha = (cfg['hc'][2] - cfg['hc'][0]) / (cfg['hc'][3] - cfg['hc'][1])
    ra = (cfg['rc'][2] - cfg['rc'][0]) / (cfg['rc'][3] - cfg['rc'][1])
    ph = int(min(max_ph, (max_w - 4) / (ha + ra))) // 2 * 2
    hw, rw = int(round(ph * ha)) // 2 * 2, int(round(ph * ra)) // 2 * 2
    return ph, hw, rw


def frame_img(cfg, h, r, ph, hw, rw, t_text=None):
    W = hw + 4 + rw
    img = Image.new('RGB', (W, LBL_H + ph), (24, 24, 24))
    hi = to_pil(cv2.resize(crop(h, cfg['hc']), (hw, ph), interpolation=cv2.INTER_AREA))
    rr = crop(r, cfg['rc'])
    ri = to_pil(cv2.resize(rr, (rw, ph), interpolation=cv2.INTER_AREA if rr.shape[0] > ph else cv2.INTER_CUBIC))
    img.paste(hi, (0, LBL_H)); img.paste(ri, (hw + 4, LBL_H))
    d = ImageDraw.Draw(img)
    label(d, 0, hw, L_HUMAN); label(d, hw + 4, rw, L_ROBOT)
    if t_text:
        d.text((6, LBL_H + 4), t_text, font=FONT, fill=(255, 255, 255))
    return img


def make_gif(name, fps, colors, out, max_ph=450, max_w=960, bayer=4):
    cfg = CLIPS[name]
    hfr, hfps = read(cfg['h']); rfr, rfps = read(cfg['r'])
    ph, hw, rw = compose(cfg, hfr, rfr, max_w=max_w, max_ph=max_ph)
    T = max(len(hfr) / hfps, len(rfr) / rfps)
    tmp = f'{W_}/gif_{name}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    n = int(T * fps)
    for k in range(n):
        t = k / fps
        hi = min(int(round(t * hfps)), len(hfr) - 1)
        ri = min(int(round(t * rfps)), len(rfr) - 1)
        frame_img(cfg, hfr[hi], rfr[ri], ph, hw, rw).save(f'{tmp}/{k:04d}.png')
    pal = f'{tmp}/pal.png'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(fps), '-i', f'{tmp}/%04d.png',
                    '-vf', f'palettegen=max_colors={colors}:stats_mode=diff', pal], check=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(fps), '-i', f'{tmp}/%04d.png', '-i', pal,
                    '-lavfi', f'paletteuse=dither=bayer:bayer_scale={bayer}:diff_mode=rectangle', '-loop', '0', out], check=True)
    print(name, 'size', hw + 4 + rw, 'x', LBL_H + ph, 'frames', n, 'fps', fps, 'dur %.2f' % T,
          'human %.2fs robot %.2fs' % (len(hfr) / hfps, len(rfr) / rfps), 'MB %.2f' % (os.path.getsize(out) / 1e6))


def make_strip(out, times):
    cfg = dict(CLIPS['backflip'])
    cfg['hc'] = (278, 140, 801, 758)   # 523x618, same aspect as the robot crop
    cfg['rc'] = (200, 105, 720, 720)   # 520x615
    hfr, hfps = read(cfg['h']); rfr, rfps = read(cfg['r'])
    tw, th = 220, 260
    gap, rowlbl = 4, 26
    n = len(times)
    W = n * tw + (n - 1) * gap
    img = Image.new('RGB', (W, 2 * (rowlbl + th) + gap), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for row, (fr, fps, c, txt) in enumerate([(hfr, hfps, cfg['hc'], 'Internet video (faces mosaicked)'),
                                             (rfr, rfps, cfg['rc'], 'Unitree G1, learned policy (simulation)')]):
        y = row * (rowlbl + th + gap)
        d.text((4, y + 4), txt, font=FONTB, fill=(20, 20, 20))
        for i, t in enumerate(times):
            k = min(int(round(t * fps)), len(fr) - 1)
            tile = to_pil(cv2.resize(crop(fr[k], c), (tw, th), interpolation=cv2.INTER_AREA))
            x = i * (tw + gap)
            img.paste(tile, (x, y + rowlbl))
            if row == 0:
                s = f't = {t:.2f} s'
                d.rectangle([x, y + rowlbl, x + 78, y + rowlbl + 20], fill=(0, 0, 0))
                d.text((x + 4, y + rowlbl + 2), s, font=FONT, fill=(255, 255, 255))
    img.save(out, optimize=True)
    print('strip', img.size, os.path.getsize(out))


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'gif':
        make_gif(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5],
                 *[int(v) for v in sys.argv[6:9]])
    elif mode == 'strip':
        make_strip(sys.argv[2], [float(x) for x in sys.argv[3].split(',')])
