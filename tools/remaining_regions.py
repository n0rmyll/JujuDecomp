"""Read distinct not-yet-counted indexed regions and verify original words."""
import csv
import json
from pathlib import Path
import re
from ppc_leaf import load_functions

ROOT=Path(__file__).resolve().parents[1]


def remaining_rows():
    used={r['address'] for r in json.loads((ROOT/'analysis/semantic-functions.json').read_text())['routines']}
    rows=[dict(r) for r in csv.DictReader((ROOT/'analysis/functions.csv').open()) if r['address'] not in used]
    words=load_functions([r['address'][2:] for r in rows]);bodies={}
    for path in {r['assembly'] for r in rows}:
        for match in re.finditer(r'^\.fn (\w+),.*?^\.endfn \1\s*$',(ROOT/path).read_text(),re.M|re.S):bodies[match[1]]=match[0]
    for row in sorted(rows,key=lambda r:(int(r['size']),r['address'])):
        row['ins']=re.findall(r'/\*.*?\*/\s*([^\n]+)',bodies[row['name']])
        row['words']=list(words[row['address'][2:]].values())
        yield row
