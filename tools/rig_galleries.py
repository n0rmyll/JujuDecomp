#!/usr/bin/env python3
"""Regenerate local skeleton and animation viewers from export manifests."""
import json
from pathlib import Path
from model_gallery import write_gallery

ROOT=Path(__file__).resolve().parents[1]/'assets'


def main():
    rigs=json.loads((ROOT/'rigs/manifest.json').read_text())['entries']
    write_gallery(ROOT/'rigs',rigs)
    bypath={r['glb']:r for r in rigs}
    rows=[]
    for bank in json.loads((ROOT/'animations/manifest.json').read_text())['entries']:
        if 'glb' not in bank:continue
        rig=bypath[bank['rig']]
        rows.append(dict(**{k:v for k,v in rig.items() if k not in ('name','archive','glb','path_hint')},
                         name=bank['path_hint'].split('\\')[-1]+f' ({bank["animated_clips"]} clips)',
                         archive=bank['archive'],glb=bank['glb'],path_hint=bank['path_hint']))
    write_gallery(ROOT/'animations',rows)


if __name__=='__main__':main()
