"""Download the authorized Wan 2.1 test model stack through a local proxy."""
import argparse
import concurrent.futures
import hashlib
import json
import shutil
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REPO = 'Comfy-Org/Wan_2.1_ComfyUI_repackaged'
FILES = [
    ('diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors', 2838303560, 'be531024cd9018cb5b48c40cfbb6a6191645b1c792eb8bf4f8c1c6e10f924dc5'),
    ('text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors', 6735906897, 'c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68'),
    ('vae/wan_2.1_vae.safetensors', 253815318, '2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b'),
]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def remove_download_parts(target):
    """Remove only this verified model's known temporary download files."""
    partial = target.with_suffix(target.suffix + '.part')
    partial.unlink(missing_ok=True)
    segment_dir = target.parent / (target.name + '.segments')
    plan = segment_dir / 'plan.json'
    if plan.exists():
        ranges = json.loads(plan.read_text())
        for i in range(len(ranges)):
            (segment_dir / f'{i:04}.part').unlink(missing_ok=True)
        plan.unlink()
        segment_dir.rmdir()


def download(item, proxy, *, model_root=None, repo=REPO, workers=6):
    relative, size, expected = item
    target = (model_root or (ROOT / '.runtime/wan21/models')) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.stat().st_size == size and sha256(target) == expected:
            remove_download_parts(target)
            print(f'Already verified: {target.name}', flush=True)
            return {'path': str(target), 'sha256': expected, 'bytes': size}
        raise RuntimeError(f'Existing file failed verification: {target}')
    partial = target.with_suffix(target.suffix + '.part')
    url = f'https://huggingface.co/{repo}/resolve/main/split_files/{relative}'
    segment_dir = target.parent / (target.name + '.segments')
    segment_dir.mkdir(exist_ok=True)
    plan_path = segment_dir / 'plan.json'
    if plan_path.exists():
        ranges = json.loads(plan_path.read_text())
    else:
        offset = partial.stat().st_size if partial.exists() else 0
        chunk_size = 128 * 1024 * 1024
        ranges = [[start, min(start + chunk_size, size) - 1] for start in range(offset, size, chunk_size)]
        plan_path.write_text(json.dumps(ranges))

    def fetch_range(index_range):
        index, (start, end) = index_range
        segment = segment_dir / f'{index:04}.part'
        expected_size = end - start + 1
        session = requests.Session()
        session.trust_env = False
        session.proxies = {'http': proxy, 'https': proxy}
        for attempt in range(4):
            offset = segment.stat().st_size if segment.exists() else 0
            if offset == expected_size:
                return segment
            try:
                first = start + offset
                with session.get(url, params={'download': 'true', 't': int(time.time())}, headers={'Range': f'bytes={first}-{end}'}, stream=True, timeout=(20, 60)) as response:
                    response.raise_for_status()
                    if response.status_code != 206 or not response.headers.get('Content-Range', '').startswith(f'bytes {first}-'):
                        raise RuntimeError('Server did not honor the requested byte range')
                    with segment.open('ab') as f:
                        for chunk in response.iter_content(1024 * 1024):
                            f.write(chunk)
                if segment.stat().st_size != expected_size:
                    raise RuntimeError('Incomplete range response')
                return segment
            except requests.RequestException as exc:
                print(f'{target.name} segment {index}: retry {attempt + 1}/4: {type(exc).__name__}', flush=True)
                if attempt == 3:
                    raise
                time.sleep(2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_range, item) for item in enumerate(ranges)]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            future.result()
            print(f'{target.name}: downloaded segment {i}/{len(ranges)}', flush=True)
    # Rebuild into a separate file so an interrupted assembly can be retried.
    assembled = target.with_suffix(target.suffix + '.assembled')
    with assembled.open('wb') as out:
        prefix_bytes = ranges[0][0] if ranges else size
        if prefix_bytes:
            with partial.open('rb') as source:
                remaining = prefix_bytes
                while remaining:
                    block = source.read(min(8 * 1024 * 1024, remaining))
                    if not block:
                        raise RuntimeError('Downloaded prefix is incomplete')
                    out.write(block)
                    remaining -= len(block)
        for i in range(len(ranges)):
            with (segment_dir / f'{i:04}.part').open('rb') as source:
                shutil.copyfileobj(source, out, 8 * 1024 * 1024)
    if assembled.stat().st_size != size or sha256(assembled) != expected:
        raise RuntimeError(f'File size or SHA256 mismatch: {assembled}')
    assembled.replace(target)
    remove_download_parts(target)
    print(f'Verified SHA256: {target.name}', flush=True)
    return {'path': str(target), 'sha256': expected, 'bytes': size, 'source': url}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--proxy', default='http://127.0.0.1:7890')
    args = parser.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda item: download(item, args.proxy), FILES))
    (ROOT / '.runtime/wan21/download-manifest.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
