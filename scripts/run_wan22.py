"""Run one prepared local Wan 2.2 benchmark and observe its real execution.

The calling agent owns planning, checkpoints, visual review and final delivery.
"""
import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests
from websockets.sync.client import connect
from wan22_runtime import SingleGPURun, local_session, require_idle, release_idle_models

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', default='wan22-amd-14b-staged')
    parser.add_argument('--workflow', type=Path, default=ROOT / 'workflows/wan22-14b-480p-5s-staged-api.json')
    parser.add_argument('--server-log', type=Path, default=ROOT / '.runtime/wan22/staged-server.stderr.log')
    args = parser.parse_args()
    if not args.project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.project):
        parser.error('Use a lowercase kebab-case project name')
    os.chdir(ROOT)
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'
    from tools.tool_registry import registry

    project = ROOT / 'projects' / args.project
    artifacts = project / 'artifacts'
    if not (project / 'checkpoint_assets.json').is_file():
        parser.error('The agent must initialize the assets checkpoint before generation')
    registry.discover()
    provider = registry.get('comfyui_video')
    selector = registry.get('video_selector')
    base_url = provider._client.server_url
    gpu_reservation = SingleGPURun(ROOT / '.runtime/wan22/generation.lock')
    runtime_session = local_session()
    require_idle(runtime_session, base_url)
    stats_response = runtime_session.get(base_url + '/system_stats', timeout=10)
    stats_response.raise_for_status()
    server_stats = stats_response.json()
    (artifacts / 'system-before.json').write_text(json.dumps(server_stats, indent=2), encoding='utf-8')
    wf = json.loads(args.workflow.read_text(encoding='utf-8'))
    inputs = {
        'preferred_tool': 'comfyui_video', 'allowed_providers': ['comfyui'],
        'operation': 'text_to_video', 'model_family': 'wan2.2',
        'prompt': wf['2']['inputs']['text'],
        'workflow_path': str(args.workflow.resolve()), 'output_node': '16',
        'workflow_name': 'Native Wan 2.2 14B FP8 T2V with LightX2V 4-step LoRAs',
        'workflow_model': 'Wan2.2-T2V-A14B FP8 + LightX2V 4-step',
        'workflow_model_stack': [
            {'role': 'high_noise_diffusion', 'name': wf['5']['inputs']['unet_name'], 'precision': 'scaled FP8'},
            {'role': 'low_noise_diffusion', 'name': wf['6']['inputs']['unet_name'], 'precision': 'scaled FP8'},
            {'role': 'high_noise_lora', 'name': wf['7']['inputs']['lora_name'], 'strength_model': 1.0},
            {'role': 'low_noise_lora', 'name': wf['8']['inputs']['lora_name'], 'strength_model': 1.0},
            {'role': 'text_encoder', 'name': wf['1']['inputs']['clip_name']},
            {'role': 'vae', 'name': wf['4']['inputs']['vae_name']},
        ],
        'benchmark_configuration': {
            'sampler': 'euler', 'scheduler': 'simple', 'steps': 4, 'cfg': 1.0, 'shift': 5.0,
            'server_argv': server_stats['system']['argv'],
        },
        'seed': wf['12']['inputs']['noise_seed'], 'width': wf['11']['inputs']['width'],
        'height': wf['11']['inputs']['height'], 'num_frames': wf['11']['inputs']['length'],
        'timeout_seconds': 7200, 'output_path': str(project / 'assets/video/wan22-generated.mp4'),
    }
    (artifacts / 'generation-input.json').write_text(json.dumps(inputs, indent=2, ensure_ascii=False), encoding='utf-8')
    stopped = threading.Event()
    ws_ready = threading.Event()
    origin = time.monotonic()

    def observe_ws():
        url = base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        with (artifacts / 'execution-events.jsonl').open('w', encoding='utf-8') as log:
            try:
                with connect(f'{url}/ws?clientId={provider._client.client_id}', proxy=None, open_timeout=10, close_timeout=2, max_size=None) as ws:
                    ws_ready.set()
                    while not stopped.is_set():
                        try:
                            raw = ws.recv(timeout=1)
                        except TimeoutError:
                            continue
                        if not isinstance(raw, str):
                            continue
                        event = json.loads(raw)
                        log.write(json.dumps({'elapsed_s': time.monotonic() - origin, 'epoch_s': time.time(), **event}) + '\n')
                        log.flush()
                        if event.get('type') == 'executing':
                            node = event.get('data', {}).get('node')
                            print(f'Executing node {node}: {wf.get(str(node), {}).get("class_type", "finished")}', flush=True)
                        elif event.get('type') == 'progress':
                            data = event.get('data', {})
                            print(f'Sampling progress: {data.get("value")}/{data.get("max")}', flush=True)
            except Exception as exc:
                log.write(json.dumps({'elapsed_s': time.monotonic() - origin, 'observer_error': str(exc)}) + '\n')
            finally:
                ws_ready.set()

    def observe_stats():
        session = requests.Session(); session.trust_env = False
        with (artifacts / 'gpu-observation.jsonl').open('w', encoding='utf-8') as log:
            while not stopped.is_set():
                try:
                    data = session.get(base_url + '/system_stats', timeout=10).json()
                    log.write(json.dumps({'elapsed_s': time.monotonic() - origin, 'epoch_s': time.time(), 'devices': data['devices'], 'ram_free': data['system']['ram_free']}) + '\n')
                    log.flush()
                except Exception as exc:
                    log.write(json.dumps({'elapsed_s': time.monotonic() - origin, 'observer_error': str(exc)}) + '\n'); log.flush()
                stopped.wait(3)

    def observe_log():
        source = args.server_log
        if not source.is_file():
            (artifacts / 'timed-server-log.jsonl').write_text(
                json.dumps({'elapsed_s': time.monotonic() - origin, 'observer_error': f'Server log unavailable: {source}'}) + '\n', encoding='utf-8')
            return
        with source.open('r', encoding='utf-8', errors='replace') as incoming, (artifacts / 'timed-server-log.jsonl').open('w', encoding='utf-8') as log:
            incoming.seek(0, 2)
            while not stopped.is_set():
                line = incoming.readline()
                if line:
                    log.write(json.dumps({'elapsed_s': time.monotonic() - origin, 'text': line.rstrip()}) + '\n'); log.flush()
                else:
                    stopped.wait(0.2)

    threads = [threading.Thread(target=f, daemon=True) for f in (observe_ws, observe_stats, observe_log)]
    for thread in threads:
        thread.start()
    ws_ready.wait(12)
    started = time.monotonic()
    try:
        result = selector.execute(inputs)
        wall = time.monotonic() - started
        payload = {'success': result.success, 'error': result.error, 'data': result.data,
                   'artifacts': result.artifacts, 'duration_seconds': result.duration_seconds,
                   'observed_wall_seconds': wall, 'cost_usd': result.cost_usd, 'model': result.model}
        (artifacts / 'generation-result.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
        print(json.dumps({'success': result.success, 'wall_seconds': wall, 'error': result.error, 'artifacts': result.artifacts}, ensure_ascii=False), flush=True)
    finally:
        stopped.set()
        for thread in threads:
            thread.join(timeout=3)
        cleanup = release_idle_models(runtime_session, base_url, artifacts / 'cleanup-result.json')
        print(f'Idle model cleanup: {cleanup["status"]}', flush=True)
        gpu_reservation.close()
    raise SystemExit(0 if result.success else 1)
