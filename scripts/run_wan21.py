"""Execute one prepared Wan workflow through the OpenMontage video selector.

Production planning, review and checkpoints remain the calling agent's duty.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', default='wan21-amd-validation')
    parser.add_argument('--workflow', type=Path, default=ROOT / 'workflows/wan21-1.3b-lowres-api.json')
    parser.add_argument('--resume-prompt-id')
    args = parser.parse_args()
    if not args.project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.project):
        parser.error('project must be a lowercase kebab-case name')
    os.chdir(ROOT)
    os.environ.setdefault('NO_PROXY', 'localhost,127.0.0.1,::1')
    from tools.tool_registry import registry

    project = ROOT / 'projects' / args.project
    if not (project / 'checkpoint_assets.json').exists():
        parser.error('Initialize the project and its assets checkpoint before generation')
    workflow = json.loads(args.workflow.read_text(encoding='utf-8'))
    registry.discover()
    selector = registry.get('video_selector')
    inputs = {
        'preferred_tool': 'comfyui_video',
        'allowed_providers': ['comfyui'],
        'operation': 'text_to_video',
        'prompt': workflow['6']['inputs']['text'],
        'workflow_path': str(args.workflow.resolve()),
        'output_node': '50',
        'workflow_name': 'Wan 2.1 1.3B native T2V, low-resolution local AMD test',
        'workflow_model': 'Wan2.1-T2V-1.3B FP16',
        'workflow_model_stack': [
            {'role': 'diffusion_model', 'name': workflow['37']['inputs']['unet_name'], 'precision': 'FP16'},
            {'role': 'text_encoder', 'name': workflow['38']['inputs']['clip_name'], 'precision': 'scaled FP8'},
            {'role': 'vae', 'name': workflow['39']['inputs']['vae_name']},
        ],
        'benchmark_configuration': {
            'sampler': 'uni_pc', 'scheduler': 'simple', 'steps': 30, 'cfg': 6.0, 'shift': 8.0,
            'source': 'Comfy-Org native text_to_video_wan template',
        },
        'seed': workflow['3']['inputs']['seed'],
        'width': workflow['40']['inputs']['width'],
        'height': workflow['40']['inputs']['height'],
        'num_frames': workflow['40']['inputs']['length'],
        'timeout_seconds': 1800,
        'output_path': str(project / 'assets/video/wan21-lowres.mp4'),
    }
    if args.resume_prompt_id:
        inputs['resume_prompt_id'] = args.resume_prompt_id
    (project / 'artifacts/generation-input.json').write_text(json.dumps(inputs, indent=2, ensure_ascii=False), encoding='utf-8')
    result = selector.execute(inputs)
    payload = {'success': result.success, 'data': result.data, 'error': result.error,
               'artifacts': result.artifacts, 'duration_seconds': result.duration_seconds,
               'cost_usd': result.cost_usd, 'model': result.model}
    (project / 'artifacts/generation-result.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str), flush=True)
    raise SystemExit(0 if result.success else 1)
