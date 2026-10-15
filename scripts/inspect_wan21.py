"""Decode the generated test clip and save metadata, motion statistics and QA frames."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / '.runtime/ffmpeg/bin'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', default='wan21-amd-validation')
    args = parser.parse_args()
    project = ROOT / 'projects' / args.project
    video = project / 'assets/video/wan21-lowres.mp4'
    artifacts = project / 'artifacts'
    probe = json.loads(subprocess.check_output([
        str(BIN / 'ffprobe.exe'), '-v', 'error', '-count_frames',
        '-show_streams', '-show_format', '-of', 'json', str(video)
    ], text=True, encoding='utf-8'))
    stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    width, height = stream['width'], stream['height']
    decoded = subprocess.check_output([
        str(BIN / 'ffmpeg.exe'), '-v', 'error', '-i', str(video),
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-vsync', '0', '-'
    ])
    frames = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, height, width, 3)
    differences = np.abs(np.diff(frames.astype(np.int16), axis=0)).mean(axis=(1, 2, 3))
    report = {
        'path': str(video), 'sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
        'probe': probe, 'decoded_frames': len(frames),
        'mean_rgb': frames.mean(axis=(0, 1, 2)).tolist(),
        'per_frame_mean_absolute_difference': differences.tolist(),
        'nonidentical_frame_pairs': int((differences > 0).sum()),
        'visual_review': 'pending agent inspection of contact sheet and playback',
    }
    inputs = json.loads((artifacts / 'generation-input.json').read_text(encoding='utf-8'))
    assert (width, height, len(frames), stream['codec_name']) == (inputs['width'], inputs['height'], inputs['num_frames'], 'h264'), 'Unexpected output format'
    assert len(frames) > 1 and np.all(differences > 0), 'Repeated/static frames detected'
    indices = [0, 9, 19, 29, 39, len(frames) - 1]
    sheet = Image.new('RGB', (width * 3, (height + 24) * 2), '#151b24')
    draw = ImageDraw.Draw(sheet)
    for i, index in enumerate(indices):
        x, y = (i % 3) * width, (i // 3) * (height + 24)
        sheet.paste(Image.fromarray(frames[index]), (x, y + 24))
        draw.text((x + 8, y + 5), f'Frame {index + 1:02d} / {index / 16:.2f}s', fill='white')
    sheet.save(artifacts / 'contact-sheet.jpg', quality=95)
    (artifacts / 'media-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'resolution': f'{width}x{height}', 'decoded_frames': len(frames),
                      'duration': probe['format']['duration'], 'nonidentical_pairs': report['nonidentical_frame_pairs'],
                      'mean_frame_difference': float(differences.mean())}, indent=2))
