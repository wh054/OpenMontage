"""Local Wan runtime safeguards, independent of model packages and ComfyUI source."""
import atexit
import json
import msvcrt
import time

import requests


class SingleGPURun:
    """An OS file lock releases automatically if the runner crashes."""

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = path.open('a+b')
        self.handle.seek(0, 2)
        if self.handle.tell() == 0:
            self.handle.write(b'0')
            self.handle.flush()
        self.handle.seek(0)
        try:
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            self.handle.close()
            raise RuntimeError('Another OpenMontage Wan run owns the GPU reservation') from None
        atexit.register(self.close)

    def close(self):
        if not self.handle.closed:
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            self.handle.close()


def local_session():
    session = requests.Session()
    session.trust_env = False
    return session


def require_idle(session, base_url):
    response = session.get(base_url + '/queue', timeout=10)
    response.raise_for_status()
    queue = response.json()
    if queue.get('queue_running') or queue.get('queue_pending'):
        raise RuntimeError('ComfyUI already has work; wait for its queue to become idle')


def release_idle_models(session, base_url, report_path):
    """Never interrupt or unload another queued job; record actual cleanup state."""
    report = {}
    try:
        require_idle(session, base_url)
        report['before'] = session.get(base_url + '/system_stats', timeout=10).json()
        response = session.post(base_url + '/free', json={'unload_models': True, 'free_memory': True}, timeout=10)
        response.raise_for_status()
        deadline = time.monotonic() + 10
        while True:
            report['after'] = session.get(base_url + '/system_stats', timeout=10).json()
            reserved = sum(d.get('torch_vram_total', 0) for d in report['after']['devices'])
            if reserved < 256 * 1024**2 or time.monotonic() >= deadline:
                break
            time.sleep(.5)
        report['status'] = 'released' if reserved < 256 * 1024**2 else 'requested_pending'
    except Exception as exc:
        report['status'] = 'skipped_or_failed'
        report['reason'] = str(exc)
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
