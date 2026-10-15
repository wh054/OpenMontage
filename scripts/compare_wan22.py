"""Compare completed, equally configured Wan trials using observed execution data."""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def summarize(name):
    project = ROOT / 'projects' / name
    artifacts = project / 'artifacts'
    result = json.loads((artifacts / 'generation-result.json').read_text(encoding='utf-8'))
    assert result['success'], name
    events = read_rows(artifacts / 'execution-events.jsonl')
    nodes = [(e['data']['node'], e['elapsed_s']) for e in events if e.get('type') == 'executing' and e['data'].get('node')]
    durations = {node: nodes[i+1][1] - elapsed for i, (node, elapsed) in enumerate(nodes[:-1])}
    observations = [r for r in read_rows(artifacts / 'gpu-observation.jsonl') if 'devices' in r]
    logs = read_rows(artifacts / 'timed-server-log.jsonl')
    execution = next(float(m.group(1)) for row in logs if (m := re.search(r'Prompt executed in ([\d.]+) seconds', row['text'])))
    releases = [json.loads(row['text'].split('OpenMontage stage release: ', 1)[1]) for row in logs if 'OpenMontage stage release: ' in row['text']]
    cached = [e['data'].get('nodes', []) for e in events if e.get('type') == 'execution_cached']
    return {
        'project': name, 'server_execution_seconds': execution,
        'roundtrip_seconds': result['observed_wall_seconds'],
        'text_encoding_seconds': durations['2'] + durations['3'],
        'node_wall_seconds': durations,
        'sampled_peak_torch_reserved_GiB': max(r['devices'][0]['torch_vram_total'] for r in observations) / 2**30,
        'initial_available_ram_GiB': observations[0]['ram_free'] / 2**30,
        'minimum_available_ram_MiB': min(r['ram_free'] for r in observations) / 2**20,
        'stage_releases': releases, 'cached_nodes': cached,
    }


def frames(name):
    path = ROOT / 'projects' / name / 'renders/wan22-amd-5s.mp4'
    data = subprocess.check_output([str(ROOT / '.runtime/ffmpeg/bin/ffmpeg.exe'), '-v', 'error', '-i', str(path), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-vsync', '0', '-'])
    result = np.frombuffer(data, dtype=np.uint8).reshape(-1, 480, 832, 3)
    assert len(result) == 80
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default='wan22-amd-14b-benchmark')
    parser.add_argument('--candidate', default='wan22-amd-14b-staged')
    parser.add_argument('--intermediate', default='wan22-amd-14b-optimized')
    args = parser.parse_args()
    baseline = summarize(args.baseline)
    candidate = summarize(args.candidate)
    artifacts = ROOT / 'projects' / args.candidate / 'artifacts'
    # Only resource order and output naming may differ from the reference graph.
    reference = json.loads((ROOT / 'workflows/wan22-14b-480p-5s-api.json').read_text())
    candidate_input = json.loads((artifacts / 'generation-input.json').read_text())
    graph = json.loads(Path(candidate_input['workflow_path']).read_text())
    normalized = json.loads(json.dumps(graph))
    normalized['5']['class_type'] = 'UNETLoader'
    normalized['5']['inputs'].pop('positive', None)
    normalized['5']['inputs'].pop('negative', None)
    normalized['6']['class_type'] = 'UNETLoader'
    normalized['6']['inputs'].pop('samples', None)
    normalized['16']['inputs']['filename_prefix'] = reference['16']['inputs']['filename_prefix']
    assert normalized == reference, 'Generation parameters differ from baseline'
    old, new = frames(args.baseline), frames(args.candidate)
    report = {
        'baseline': baseline, 'candidate': candidate,
        'generation_parameters_equal': True,
        'roundtrip_reduction_percent': (1 - candidate['roundtrip_seconds'] / baseline['roundtrip_seconds']) * 100,
        'text_encoding_speedup': baseline['text_encoding_seconds'] / candidate['text_encoding_seconds'],
        'decoded_pixel_identity_with_baseline': bool(np.array_equal(old, new)),
        'limitations': ['Single observed run per configuration, not a repeated statistical benchmark',
                       'Initial system RAM availability differs; global RAM minima are observations, not a controlled peak-memory reduction',
                       'CPU and GPU text encoding can introduce numerical differences despite identical generation parameters',
                       'Pixel equality or frame differences alone do not establish visual quality'],
    }
    if args.intermediate:
        report['intermediate'] = summarize(args.intermediate)
        interim_frames = frames(args.intermediate)
        report['decoded_pixel_identity_with_gpu_text_trial'] = bool(np.array_equal(interim_frames, new))
    sheet = Image.new('RGB', (832 * 3, 504 * 2), '#151b24')
    draw = ImageDraw.Draw(sheet)
    for row, (label, clip) in enumerate([('BEFORE', old), ('AFTER', new)]):
        for column, index in enumerate([0, 39, 79]):
            x, y = column * 832, row * 504
            draw.text((x + 8, y + 5), f'{label} / {index / 16:.2f}s', fill='white')
            sheet.paste(Image.fromarray(clip[index]), (x, y + 24))
    sheet.save(artifacts / 'before-after.jpg', quality=95)
    (artifacts / 'comparison-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
