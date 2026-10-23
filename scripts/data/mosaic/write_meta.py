import json, subprocess, os
O = '/home/user/dance_win/data/source_clips_mosaic'
method = ('yolov8n-pose (ultralytics 8.2.42) per frame, plus a 180-degree-rotated pass when the head keypoints are '
          'missing (inverted bodies); face box from nose/eyes/ears (1.6x their span, >= 6% of frame height and '
          '>= 0.2 x the clip person size), shoulder/box-top fallback, union over +-3 frames, last box reused '
          'when nothing is detected; pixelated with block size = box/7. Every person detected (conf >= 0.15) is mosaicked.')
meta = {
    'backflip_3': dict(
        platform='bilibili', id='av75680591', url='https://www.bilibili.com/video/av75680591',
        title='武术基本功—原地直体后空翻', uploader='功夫者平台',
        start_s=35.2, end_s=round(35.2 + 79 / 30, 3), frames=79, fps=30,
        dataset_range_s=[35.2, 38.25],
        note='Source is a portrait collage (1080x1920); only the live-video band (rows 579-1336, native 1080x758) is kept, '
             'as in scripts/data/backflip_redo.sh. Frames 0-78 = the 79 frames labelled in dataset/backflip_3/annotation.json.',
        policies=['policies/backflip_r12_clean', 'policies/backflip_r13_fid1', 'policies/backflip_r14_fid2'],
        motion='dataset/backflip_3/g1_ballistic_50fps.npz'),
    'bda_zhao_sss': dict(
        platform='bilibili', id='av117312921404527', url='https://www.bilibili.com/video/av117312921404527',
        origin='北京舞蹈学院中国民族民间舞教材（1990年代），赵铁春示范，安徽花鼓灯·闪身步',
        start_s=2.5, end_s=9.6, frames=213, fps=30,
        policies=['policies/sss_bda_v1'], motion='dataset/bda_zhao_sss/g1_lock_vlm_50fps.npz'),
    'bda2_gxdsm_full': dict(
        platform='bilibili', id='av117381925963568', url='https://www.bilibili.com/video/av117381925963568',
        origin='北舞鼓子秧歌教材，狗熊哆嗦毛全身完整示范（白衣男舞者）',
        start_s=16.25, end_s=round(16.25 + 232 / 30, 3), frames=232, fps=30,
        dataset_range_s=[16.25, 24.0],
        note='Cut from data/clips/bda2_gxdsm_full.mp4 (the exact 232-frame clip GVHMR used; the raw download is no longer kept). '
             'Resolution 768x576 as in that clip.',
        policies=['policies/gxdsm_full_v1'], motion='dataset/bda2_gxdsm_full/g1_lock_vlm_50fps.npz'),
}
for c, m in meta.items():
    f = f'{O}/{c}.mp4'
    pr = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries',
                         'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames', '-of', 'json', f],
                        capture_output=True, text=True).stdout
    s = json.loads(pr)['streams']
    assert len(s) == 1 and s[0]['codec_type'] == 'video', s
    m['clip_id'] = c
    m['video'] = dict(file=f'{c}.mp4', codec=s[0]['codec_name'], width=s[0]['width'], height=s[0]['height'],
                      fps=s[0]['r_frame_rate'], frames=int(s[0]['nb_read_frames']), audio=False)
    m['face_mosaic'] = method
    m['license_note'] = 'Third-party internet video, faces mosaicked; for research illustration only.'
    json.dump(m, open(f'{O}/{c}.json', 'w'), ensure_ascii=False, indent=1)
    print(c, m['video'])
