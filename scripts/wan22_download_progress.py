"""Report unique downloaded bytes, including open Windows download handles."""
import json
from download_wan22 import FILES, ROOT

rows = []
for relative, size, _ in FILES:
    target = ROOT / '.runtime/wan22/models' / relative
    if target.exists():
        received = size
    else:
        parts = list((target.parent / (target.name + '.segments')).glob('*.part'))
        prefix = target.with_suffix(target.suffix + '.part')
        if prefix.exists():
            parts.append(prefix)
        received = 0
        for part in parts:
            try:
                with part.open('rb') as handle:
                    received += handle.seek(0, 2)
            except FileNotFoundError:
                pass
    rows.append({'name': target.name, 'received': received, 'size': size, 'verified': target.exists()})
total, received = sum(r['size'] for r in rows), sum(r['received'] for r in rows)
print(json.dumps({'percent': round(received / total * 100, 1), 'GB': round(received / 1e9, 3), 'files': rows}))
