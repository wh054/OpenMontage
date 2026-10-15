"""Trim and inspect the real Wan 2.2 benchmark; visual review remains manual."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / '.runtime/ffmpeg/bin'


def probe(path):
    return json.loads(subprocess.check_output([
        str(BIN / 'ffprobe.exe'), '-v', 'error', '-count_frames',
        '-show_streams', '-show_format', '-of', 'json', str(path)
    ], text=True, encoding='utf-8'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', default='wan22-amd-14b-staged')
    args = parser.parse_args()
    project = ROOT / 'projects' / args.project
    artifacts = project / 'artifacts'
    source = project / 'assets/video/wan22-generated.mp4'
    output = project / 'renders/wan22-amd-5s.mp4'
    output.parent.mkdir(exist_ok=True)
    original = probe(source)
    stream = next(s for s in original['streams'] if s['codec_type'] == 'video')
    assert (stream['width'], stream['height'], int(stream['nb_read_frames'])) == (832, 480, 81)
    subprocess.run([
        str(BIN / 'ffmpeg.exe'), '-y', '-v', 'error', '-i', str(source),
        '-frames:v', '80', '-an', '-c:v', 'copy',
        '-movflags', '+faststart', str(output)
    ], check=True)
    final = probe(output)
    stream = next(s for s in final['streams'] if s['codec_type'] == 'video')
    width, height = stream['width'], stream['height']
    decoded = subprocess.check_output([
        str(BIN / 'ffmpeg.exe'), '-v', 'error', '-i', str(output),
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-vsync', '0', '-'
    ])
    frames = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, height, width, 3)
    differences = np.abs(np.diff(frames.astype(np.int16), axis=0)).mean(axis=(1, 2, 3))
    assert (len(frames), stream['codec_name'], stream['avg_frame_rate']) == (80, 'h264', '16/1')
    assert abs(float(final['format']['duration']) - 5) < .01
    report = {
        'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'original_probe': original, 'probe': final, 'decoded_frames': len(frames),
        'per_frame_mean_absolute_difference': differences.tolist(),
        'nonidentical_frame_pairs': int((differences > 0).sum()),
        'mean_frame_difference': float(differences.mean()),
        'visual_review': 'pending contact sheet inspection and video playback',
    }
    indices = np.linspace(0, len(frames) - 1, 6).astype(int)
    sheet = Image.new('RGB', (width * 3, (height + 24) * 2), '#151b24')
    draw = ImageDraw.Draw(sheet)
    for i, index in enumerate(indices):
        x, y = (i % 3) * width, (i // 3) * (height + 24)
        sheet.paste(Image.fromarray(frames[index]), (x, y + 24))
        draw.text((x + 8, y + 5), f'Frame {index + 1:02d} / {index / 16:.2f}s', fill='white')
    sheet.save(artifacts / 'contact-sheet.jpg', quality=95)
    (artifacts / 'media-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('path', 'decoded_frames', 'nonidentical_frame_pairs', 'mean_frame_difference')}, indent=2))
