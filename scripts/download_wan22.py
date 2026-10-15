"""Proxy-only, SHA256-verified Wan 2.2 14B FP8 / LightX2V downloads."""
import argparse
import concurrent.futures
import json
from pathlib import Path

from download_wan21 import download

ROOT = Path(__file__).resolve().parents[1]
REPO = 'Comfy-Org/Wan_2.2_ComfyUI_Repackaged'
FILES = [
    ('diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors', 14293923632, 'cad711ae211c8b23455ec68cd6a190a33a3d874234a77eb57266d73f8f0e6c9f'),
    ('diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors', 14293923632, 'e71b96d7c82e638694c5e7fb98fac4bfb0e4ddc5fbbb4b1df40da8f0f1278a97'),
    ('loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors', 1226977424, '698321cb86bd30c4af06c9b84e656a1048c8cb54e06d50694536fb5de37fde41'),
    ('loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors', 1226977424, 'ec95216e614b3c132c11bfb387b11feedf62163150ccc9068bca8a189771e75a'),
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--proxy', default='http://127.0.0.1:7890')
    args = parser.parse_args()
    def fetch(item):
        return download(item, args.proxy, model_root=ROOT / '.runtime/wan22/models', repo=REPO, workers=16)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, FILES))
    (ROOT / '.runtime/wan22/download-manifest.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
