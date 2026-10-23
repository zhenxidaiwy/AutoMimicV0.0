# Source-video candidates for G1 dynamic skills (2026-10-23)

Scope: real-human monocular clips for the GVHMR → retarget → RL tracking pipeline. Nothing was downloaded.
Every URL below was opened and checked through the platform API: Bilibili search API plus `x/player/videoshot` storyboard sprites, and YouTube search plus storyboard sprites.
I judged camera, view, floor, framing and number of people from those storyboard thumbnails. The thumbnails are sampled only every ~1–25 s, so **each timestamp is approximate (±2–5 s)**. Watch each clip once before cutting.

## 1. Motions shown by the reference works

| Work | Motions listed on project page / paper |
|---|---|
| OmniXtreme (extreme-humanoid.github.io) | B-boying with rapid back handsprings; skip back → hand-to-headstand pivot → drop → flip → bounce back; 2 long breaking routines; 5× consecutive Webster flips; alternating pistol squats; back handspring, cartwheels, **aerial cartwheel**, bicycle-kick flips; **spin kicks & butterfly kicks**; forward/backward roll, crawl; **Thomas flare, backspin**, backflip; attack combos, handstand walk, knocked-out, push-ups, roll-flip combos |
| MimicX (nebulis-lab.com/MimicX, redirected from github.io) | football juggling, tennis swing, dance sequence, kung-fu sequence, parkour, track running, stair ascent/descent, platform jump (take-off + landing), forest traversal. The pipeline is also GVHMR → G1 |
| KungfuBot / PBHC (kungfubot.github.io, arXiv 2506.12851) | jump kick, roundhouse kick, side kick, front kick, back kick, horse-stance punch, hook/jab punches, fighting combo, Bruce Lee pose, horse-stance pose, stretch leg, 360° spin, dance, Tai Chi |
| VideoMimic (videomimic.net) | stair up/down, sit/stand on chairs, terrain traversal, stepping over obstacles, crawling down stairs, vaulting a block. These are terrain/scene skills, not acrobatics |
| SONIC (nvlabs.github.io/SONIC, arXiv 2511.07820) | The page renders by JS and was empty to the fetcher. The paper names no specific skills; it is a mocap-scale general tracker (VR teleop, video, VLA) |

## 2. Criteria legend

- **C1**: one performer, whole body in frame from take-off to landing, no cut during the move
- **C2**: static or slow camera, side or 3/4 view (for cartwheel, aerial and side flip a *front* view sees the rotation plane, which is also fine)
- **C3**: flat ground: no trampoline, air-track, foam pit or mat edge (thin mat or sprung gym floor noted)
- **C4**: move ~1–4 s, clear lighting, real-time available (not slow-motion only)
- **C5**: tutorial or training style with repeated reps
- **C6**: body and skill plausible for a 1.3 m G1 (child performers are a plus)

"Fails" lists only the criteria that fail or are uncertain (?). Pv = portrait (vertical) video. GVHMR works on it, but the subject is smaller.

---

## 3. Candidates by motion (ranked)

### 3.1 Backflip (standing back tuck)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=MYaPb8E2sGM&t=120s | How To BACK FLIP Super Slow Motion Analysis (Ronnie Street Stunts, 6:18) | ~1 s per rep, many reps 1:30–5:30 | landscape, static, side view | concrete plaza, single performer, full body, strong reps | C4? mostly slow-mo; check for a real-time rep (timing can be rescaled) |
| 2 | YouTube | https://www.youtube.com/watch?v=5c1cNMnvTsw&t=26s | slow motion back flip (0:48) | ~1 s (slow-mo ~8 s) | landscape, static, clean side view | gym sprung carpet, full body, single take | C4 slow-motion only; C3 sprung floor |
| 3 | Bilibili | https://www.bilibili.com/video/BV1ys411N771/?t=86 | 慢动作演示后空翻教学 (2:14) | ~1 s | landscape; full-frame slow-mo flip ~1:28, picture-in-picture demos 0:46/1:18 | hard floor, white wall | C4 slow-mo; C1 PiP insets and talking-head cuts |
| 4 | YouTube | https://www.youtube.com/watch?v=ltho8_PzC2U&t=300s | Learn How to Backflip in 5 Minutes (pigmie) | ~1 s | landscape, static tripod, mostly front/3-4 view, wide | flat grass field, single performer | C2 front-ish view; C3 grass; performer small in frame |
| 5 | Bilibili | https://www.bilibili.com/video/BV1mm4y1A7wR/ | 后空翻两周全过程 (0:31) | ~1.2 s | landscape, side view, outdoor grass | flip is a **double** backflip; bystanders in frame | C1 several people; C6 double too hard |
| 6 | Bilibili | https://www.bilibili.com/video/BV1vQ4y167us/?t=50 | 原地后空翻教程 (武术阿杵, 1:00) | ~1 s | Pv, 3/4 view | gym carpet, box drills before final flip | Pv; C3 drills onto box/mats |

### 3.2 Aerial cartwheel / side flip (侧空翻)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV1s3411a75d/?t=1 | 2-4.干拔侧空翻 (舞蹈云/乐舂塑形, 0:30) | ~1.5 s | landscape, static, front view (sees the rotation plane) | **child dancer (~1.3 m)**, bare white studio, hard floor, single person; ideal G1 proportions | C5? probably 1–2 reps only |
| 2 | Bilibili | https://www.bilibili.com/video/BV1zxWUeXE7r/ | 侧空翻教学 (超亻毕, 1:34) | ~1.5 s | landscape, static tripod, front/3-4 view | dance studio hard floor, single adult, progressions 0:06–1:18 plus full aerial | C1? confirm a full unassisted aerial is in frame |
| 3 | YouTube | https://www.youtube.com/watch?v=d39xLrtOtFQ&t=160s | Aerial Tutorial (No Handed Cartwheel) – Ginger Ninja Trickster | ~1.5 s, reps 2:40, 3:40, 4:00 | landscape, static, side/front | blue sprung floor, single performer | C1 some reps cropped at frame edge (3:00), edited cuts; C3 sprung floor |
| 4 | YouTube | https://www.youtube.com/watch?v=LWTpnU3AvkI&t=275s | Learn How to Side Flip On Ground in 5 Minutes (pigmie) | ~1 s (two-foot side flip) | landscape, static, front view (rotation plane) | flat grass, single performer, many attempts | C3 grass; wide shot, performer small |
| 5 | YouTube | https://www.youtube.com/watch?v=LUF8tQR_Plo&t=240s | How to do an Aerial in One Day! (Anna McNulty) | ~1.5 s | landscape, static, front | home room, hardwood floor, final attempt ~4:00 | C5 mostly drills; C1? final aerial may be cut |
| 6 | Bilibili | https://www.bilibili.com/video/BV1ot4y1A7pN/ | 招儿丨侧空翻的小妙招 (3:12) | ~1.5 s | landscape, static, white cyclorama | very clean background | C5 mostly talking; demo rep short or unverified |

### 3.3 Front flip (standing)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV1bc41137Bm/ | 原地前空翻，不加助跑 (0:31) | ~1 s, reps at 0:00 and ~0:10 | landscape, static, **clean side view** | single performer, full body, outdoor flat grass | C3 grass (flat) |
| 2 | YouTube | https://www.youtube.com/watch?v=_Z7ekwI7oMI&t=50s | How to Front Flip Tutorial (pigmie) | ~1 s, also ~3:45 | landscape, static, side view | grass field, many reps | C3 grass; performer small |
| 3 | YouTube | https://www.youtube.com/watch?v=iENtDEeocLQ&t=22s | Standing Frontflip Tutorial (Bob Reese, 0:51) | ~1 s | landscape, static, side | gym sprung floor; some reps onto mats or box (0:00–0:20, 0:40) | C3 mats in some reps |
| 4 | Bilibili | https://www.bilibili.com/video/BV14W41197vS/?t=175 | 原地前空翻教学 (3:13) | ~1 s | landscape, side | gym; final flips onto mat/box | C3 mat/box; C1 cuts |

### 3.4 Cartwheel (侧手翻)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV16q4y1y7vY/?t=10 | 7.侧手翻串连训练 (舞蹈云, 0:31) | ~1.5 s each, chained | landscape, static, front view | **child (~1.3 m)**, white studio, hard floor, repeated cartwheels | C2 slight pan possible |
| 2 | Bilibili | https://www.bilibili.com/video/BV1ka411q7pL/ | 10-2.趋步侧手翻 (舞蹈云, 0:12) | ~1.5 s | landscape, front; camera pans to follow | same child and studio, hop-step entry | C2 pan |
| 3 | Bilibili | https://www.bilibili.com/video/BV1iF411v7r5/ | 10-1.蹦跳趋步侧手翻 (舞蹈云, 0:14) | ~1.5 s | landscape, front | same setting | C2 pan? |
| 4 | YouTube | https://www.youtube.com/watch?v=wDCVnVpcWAs&t=60s | Learn How to Cartwheel in Only 5 Minutes (pigmie) | ~1.5 s, also ~1:36 | landscape, static, front view | turf field, single adult | C3 turf (flat) |
| 5 | Bilibili | https://www.bilibili.com/video/BV1V541127ib/ | 零基础侧手翻分步教学 (浅笑祥子-特技, 1:45) | ~1.5 s at 0:00, ~1:35 | landscape, 3/4 | night sports field, edited | C1 cuts; C4 night lighting |

### 3.5 Round-off (踺子)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV1zaSBYuE6D/?t=14 | 今天带来的是踺子教学 (i正牌阿飞, 1:48) | ~1.2 s, reps around 0:14–0:20 | landscape, side view, plain wall | single performer, clean side profile | C1 heavy frame overlay graphics and jump cuts; C3 grey mat floor |
| 2 | YouTube | https://www.youtube.com/watch?v=A7iUSgc4rH0&t=33s | How to do a Roundoff (TC2) | ~1.2 s, 0:35–1:10 | landscape, static, side/3-4 | backyard grass, thin mat; three girls take turns | C1 several people in some shots; C3 thin mat |
| 3 | YouTube | https://www.youtube.com/watch?v=nM4K2MfHkFQ&t=60s | Beginner Gymnastics: Round Off Tutorial | ~1.2 s | landscape, static | backyard, blue folding mat | C3 mat; C5 mostly drills |
| 4 | Bilibili | https://www.bilibili.com/video/BV1HS4y1K7Fv/ | 第5集《踺子系统教学》 | ~1.2 s | Pv, front view | blue carpet | Pv; front view hides round-off depth |

**Weak**: no clean flat-ground side-view round-off was found.

### 3.6 Back handspring / front handspring
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=VP5UPUSDC4M&t=105s | Learn How to BACKHANDSPRING IN ONLY 5 MINUTES (pigmie) | ~1 s, also ~3:18 | landscape, static, side view | flat grass field, single performer | C3 grass |
| 2 | Bilibili | https://www.bilibili.com/video/BV1d6421c7V3/ | 全舞种通用技巧-后手翻教学 (bboy阿求, 1:05) | ~1 s at 0:00 and ~1:00 | Pv, static, side view | plain studio, hard floor, single performer | Pv; C1 spotter in drill section only |
| 3 | Bilibili | https://www.bilibili.com/video/BV1A84y1k7Fu/?t=78 | 后手翻教学，按步骤来练习 (1:22) | ~1 s | Pv, side | outdoor grass | Pv; C3 grass |
| 4 | Bilibili | https://www.bilibili.com/video/BV1qnnE6PEta/ | 后手翻教学 (Dz泽辉, 0:27) | ~1 s | Pv, side/3-4 | dance studio floor | Pv |
| 5 | Bilibili (front handspring) | https://www.bilibili.com/video/BV1bT411V7F8/ | 前手翻教学 (bboy阿求, 0:44) | ~1 s at 0:00 | Pv, side | outdoor flat concrete | Pv |

### 3.7 Webster (单腿前空翻)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=YLPW1E1ChZw&t=175s | Webster tutorial by Neguin (Red Bull) | ~1 s | landscape, static, side view, white cyclorama | elite b-boy, very clean background | C1 some split-screen segments (two copies of him at 2:20/3:00) |
| 2 | Bilibili | https://www.bilibili.com/video/BV1d44y177j5/ | 单腿前空翻教学视频 (空翻教学, 1:05) | ~1 s, 0:02–0:06 | landscape, side view | garden path/grass, single performer | C1 cuts to other footage after 0:07 |
| 3 | YouTube | https://www.youtube.com/watch?v=jnmIwqqYTF8&t=95s | Do A Webster In Only 5 Minutes (pigmie) | ~1 s | landscape, static, side/3-4 | flat grass field | C3 grass |
| 4 | Bilibili | https://www.bilibili.com/video/BV175411b7ZT/ | 半小时内练成韦伯斯特单腿前空翻 (1:20) | ~1 s | landscape, static, side | gym mats; includes falls | C3 mats; failed reps |

### 3.8 Butterfly kick (旋子)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=zPmukqlQnVM&t=26s | Butterfly Kick (B-Kick) Tutorial – Bob Reese (0:48) | ~1 s | landscape, static, front/3-4 | gym floor, single performer, repeated reps | C3 pit/mats in background only (OK) |
| 2 | Bilibili | https://www.bilibili.com/video/BV1QZ4y1X7ke/?t=2 | 简易【旋子教程】(zz宝宝酱, 1:00) | ~1 s at 0:03 and ~0:09 | landscape, static, front | wood dance floor | C1 mirror wall (reflection may be detected as a second person), second dancer at 0:10 |
| 3 | YouTube | https://www.youtube.com/watch?v=z3sTXIEsmCs&t=82s | Butterfly Kick Tutorial (B-Kick) – GNT | ~1 s, also ~1:48 | landscape, static, side | blue sprung floor | C1 edited cuts |
| 4 | YouTube | https://www.youtube.com/watch?v=vbefem-b8p8&t=118s | WUSHU TUTORIAL: Butterfly Kick (Jade Xu) | ~1 s | landscape, changes angle | wushu carpet, elite athlete | C2 multiple angles and cuts |
| 5 | Bilibili | https://www.bilibili.com/video/BV1Aj411V7mi/ | 自学旋子，看完会一半 (1:50) | ~1 s at 0:00 | landscape | outdoor stone yard | C3 uneven stone |

### 3.9 Tornado / 360 spin kick (旋风踢/旋风脚)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=Y1rmsLtq96Y&t=195s | How to Do a Tornado Kick – Taekwondo Tutorial **(One Take)** | ~1 s, reps ~3:20–4:00 | landscape, static, single uncut take, 3/4 | TKD gym floor, full body | heavy bag at frame edge (may occlude) |
| 2 | Bilibili | https://www.bilibili.com/video/BV1ZA4y1Q7rH/ | 跆拳道旋风踢 (0:58) | ~1 s; labelled "侧面示范" at 0:00 and ~0:18 | landscape, static, **side view** | studio, single performer | C1 close-up foot cuts mid-video |
| 3 | YouTube | https://www.youtube.com/watch?v=dJcLrZRc1Bc&t=135s | Learn the Tornado Kick in 2 Minutes (pdbtkd) | ~1 s | landscape, static, front/3-4 | blue mat gym | C1 cutaway at 2:34 |
| 4 | Bilibili | https://www.bilibili.com/video/BV1Ue4y1M7BM/ | 旋风腿完整版教学 (功夫-老杨, 0:52) | ~1 s | landscape, low static camera | indoor hard floor | C1 text overlays and cuts every few s |

### 3.10 540 kick (540后旋/540横踢)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=o70u-0og-A0&t=170s | How to 540 Kick In Only 5 Minutes (pigmie) | ~1.2 s, reps 2:55–3:45 | landscape, static, front/3-4 | flat grass | C3 grass; performer small |
| 2 | YouTube | https://www.youtube.com/watch?v=vcmEKRPenZ4&t=150s | Learn 540 Kick Fast by Turning a 360… (pigmie) | ~1.2 s | landscape, static | grass, text captions | C3 grass |
| 3 | YouTube | https://www.youtube.com/watch?v=HV4UYZVUS4s&t=245s | Taekwondo 540 Kick Tutorial – GNT | ~1.2 s | landscape, static, front | blue floor, target stand in frame | C1 cuts |
| 4 | Bilibili | https://www.bilibili.com/video/BV15p7a6bEjb/ | 入门腿法之540后旋教学 (0:21) | ~1.2 s | Pv | tricking gym floor | Pv; C5 very short |

### 3.11 Other KungfuBot kicks (jump front kick, side kick, spinning hook kick)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 (side kick) | Bilibili | https://www.bilibili.com/video/BV1R5411s7ZH/?t=38 | 简单的四步学侧踢 (0:50) | ~1 s; combination at 0:40, slow-mo at 0:45 | landscape, static, **side view** | single performer, TKD dobok | early steps use a barre |
| 2 (jump front kick 腾空飞脚) | Bilibili | https://www.bilibili.com/video/BV1uS4y187Sj/ | 从零开始学武术第十八期，腾空飞脚教学 (2:08) | ~1 s | landscape, static, side/3-4 | wushu hall carpet, single coach | C5 mostly explanation; confirm full-speed rep |
| 3 (spin hook kick) | YouTube | https://www.youtube.com/watch?v=tjO5BiG1mTE&t=62s | Master the Taekwondo Spinning Hook Kick | ~1 s, 1:04–1:36 | landscape, static | TKD mat | C1 cartoon overlays later (1:52+), heavy bags in background |
| 4 (spin hook kick) | YouTube | https://www.youtube.com/watch?v=rw7EvAo-0Og&t=200s | Scott Adkins Spinning Hook Kick Tutorial | ~1 s (also ~7:20) | landscape, static | gym, kicking dummy beside him | dummy occludes; C5 long talk |

### 3.12 Windmill (风车)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV1dK411G7fs/?t=100 | 入门级街舞推手风车教学 (肖青天, 2:24) | ~1 s/rev, 1:46–2:06 | landscape, static, 3/4 | bare grey studio, very clean | C1 step cards between segments |
| 2 | YouTube | https://www.youtube.com/watch?v=0dB7JjpBMtI&t=495s | Learn How to Windmill – Complete Step by Step (pigmie) | continuous windmills 8:15–9:45 | landscape, static | plain studio, glossy floor | — (best continuous reps) |
| 3 | Bilibili | https://www.bilibili.com/video/BV1fb411y7T9/ | breaking 并腿风车教学 (肖青天, 1:02) | ~1 s/rev at 0:05, 0:22–0:39 | landscape, static, front | studio wood floor | C1 talking cuts |
| 4 | YouTube | https://www.youtube.com/watch?v=xE80Bh_aOvY&t=180s | Learn How to Windmill – Kaio | revs at ~3:00, 7:30 | landscape, static | studio, red floor, clutter | background clutter |

### 3.13 Thomas flare (托马斯全旋)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV1Zt411X7Ni/?t=220 | 如何在4分钟学会托马斯回旋 (B-Boy Hironaga, 4:06) | ~0.8 s/circle, 1:20 and 3:40–4:00 | landscape, static, front | studio, curtain background | C1 hand close-up inserts (0:40, 2:40) |
| 2 | YouTube | https://www.youtube.com/watch?v=8w2OAzzwl84&t=435s | Learn How to do Flares – Step-By-Step (pigmie) | flares ~7:20, 8:40 | landscape, static | studio wood floor | — |
| 3 | YouTube | https://www.youtube.com/watch?v=cpImjWHoc8U&t=155s | How To Flare – B-Boy Lil G (Red Bull BC One) | ~0.8 s/circle at 0:16, 2:40 | landscape, static | dark studio floor | lower contrast |
| 4 | Bilibili | https://www.bilibili.com/video/BV1rv4y1E7bR/ | 霹雳舞国家队队员于子昂示范托马斯动作要领 (1:19) | 0:10, 1:04 | landscape | stage lighting, cuts and close-ups | C1 cuts |
| 5 | Bilibili | https://www.bilibili.com/video/BV1NZ4y1V7YN/ | 托马斯全旋从1到10 (0:30) | consecutive 1→10 circles | Pv, static | gym floor | Pv |

### 3.14 Freezes (定格) / toprock
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=4Z1tQowkLVQ | 25 Basic BBoy freeze you need to learn (Bimal Rana, 1:43) | ~3–4 s each, labelled | landscape, static | bright studio, single performer | — |
| 2 | Bilibili | https://www.bilibili.com/video/BV1pb4y1o7Um/ | Breaking里七个最常用的freeze定格动作 (木悉浪, 1:39) | ~5 s each (chair, turtle, shoulder, headstand, elbow, air freeze) | landscape, static, 3/4 | studio | — |
| 3 (toprock) | Bilibili | https://www.bilibili.com/video/BV1Md7k62E29/ | 10个toprock舞步元素 (bboy阿求, 0:51) | ~4 s per element | Pv, front | outdoor, single dancer | Pv; jump cut per element |
| 4 (toprock) | Bilibili | https://www.bilibili.com/video/BV1yg411U7Zx/ | Breaking中常用TopRock的9种舞步原型动作 (1:19) | ~5 s each | landscape, static | studio | C1 **two dancers** in frame |

### 3.15 Kip-up (鲤鱼打挺), useful for get-up
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | YouTube | https://www.youtube.com/watch?v=G0lNYjtBUeE | Learn the KICK UP / KIP UP in 3 Steps (Vitality) | ~1 s | landscape, static, side | indoor wood floor | C5 mostly drills; confirm a full rep |
| 2 | Bilibili | https://www.bilibili.com/video/BV1XJ411573f/ | 通俗易懂的教学方式…鲤鱼打挺 (街健呆木头, 3:28) | ~1 s | landscape, static, side | outdoor, thin mat | C3 thin mat |
| 3 | Bilibili | https://www.bilibili.com/video/BV1Qv4y1g79C/ | 鲤鱼打挺教学 (bboy阿求, 0:49) | ~1 s | Pv, side | plain studio | Pv |

### 3.16 Kung-fu forms (长拳 etc.)
| # | Platform | URL (@move) | Title | Move | Camera / view | Notes | Fails |
|---|---|---|---|---|---|---|---|
| 1 | Bilibili | https://www.bilibili.com/video/BV1zAo3BuEyk/ | 初级一路长拳完整版 (承武者, 2:26) | full routine ~0:00–0:50, then single moves | landscape, static, front | wushu carpet, single performer | long sequence (segment it) |
| 2 | Bilibili | https://www.bilibili.com/video/BV1rR9dBhEiX/ | 初级二路长拳｜全套完整示范 (承武者, 2:19) | full routine plus breakdown | landscape, static, front | same setting; includes kicks | — |
| 3 | Bilibili | https://www.bilibili.com/video/BV1b541137Qn/ | 国际武术第二套竞赛套路长拳 (1:31) | continuous routine with jumps | landscape, static, front | plain curtain background | older, lower resolution |
| 4 | YouTube | https://www.youtube.com/watch?v=hABx8NqETz0&t=80s | Wushu Elementary Changquan Routine 3 (Wushu Vision) | 1:20–3:28 | landscape, static | green screen, wushu carpet | — |
| 5 | Bilibili | https://www.bilibili.com/video/BV1uQ1YBdEqW/?t=180 | 国一长拳 (4:29) | full set 3:00+ | landscape, static, very wide | competition carpet | performer small |
| 6 (Tai Chi) | Bilibili | https://www.bilibili.com/video/BV1vV411P7KB/ | 一分钟教会你太极拳 (1:03) | ~1 min sequence | Pv, front | outdoor grass | Pv |

---

## 4. Gaps and notes
- **Not found or not searched**: backspin/headspin, handstand walk, pistol squat, bicycle-kick flip (OmniXtreme); scene skills from MimicX/VideoMimic (stairs, vault, parkour). Those last ones break the flat-ground rule.
- **Weakest categories**: round-off (no clean flat-ground side view) and toprock (only portrait or two-dancer clips).
- Bilibili tutorial clips are mostly portrait gym shorts with air-tracks or mats. The **舞蹈云 / 乐舂塑形 child-dancer series** (landscape, static, white studio, ~1.3 m performer) is the best Bilibili source for G1 proportions. Its 侧手翻, 前软翻 and 后软翻 lessons are BV1T7vVeaEei, BV1t7vVeaEyt, BV147vVeaESx, BV1T7vVeYERy and BV1T7vVeaEku; they were found but not storyboard-checked.
- pigmie (YouTube) "learn in 5 minutes" videos are consistently landscape, static tripod and flat grass, with many reps. The performer is small in frame, so they are good for GVHMR but low resolution.
- Slow-motion clips (backflip #1–#3) need time rescaling. Prefer a real-time rep if one exists in the same video.
- Excluded on purpose: wikiHow animation (tkugpC33ZVI is not a real human), air-track and trampoline clips, and Howcast two-person clips.
