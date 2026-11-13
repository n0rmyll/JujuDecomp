#!/usr/bin/env python3
"""Build an offline GLB preview and searchable export list from model manifest."""
import base64
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_gallery(root):
    report = json.loads((root/'manifest.json').read_text())
    entries = report['entries']
    default = next((e for e in entries if e['archive'] == 'Preload.dbu' and e['path_hint'] == 'weapons\\coconut.dbl'),
                   entries[0] if entries else None)
    encoded = base64.b64encode((root/default['glb']).read_bytes()).decode() if default else ''
    links = ''.join(f'<li><a href="{html.escape(e["glb"], quote=True)}">{html.escape(e["archive"]+" / "+e["name"])}</a>'
                    f' · {e["triangles"]:,} triangles</li>' for e in entries)
    viewer = (ROOT/'tools/model_viewer.html').read_text()
    viewer = viewer.replace('__DEFAULT_GLB__', encoded).replace('__EXPORT_LINKS__', links)
    (root/'index.html').write_text(viewer)


if __name__ == '__main__':
    write_gallery(ROOT/'assets/models')
