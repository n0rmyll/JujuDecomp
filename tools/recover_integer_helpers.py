#!/usr/bin/env python3
"""Reproduce selected integer recovery specs from verified local disassembly.

Without --write, check the saved specifications and C without modifying them.
This is low-level C recovery, not original source/prototype reconstruction.
"""
import argparse
import csv
import json
from pathlib import Path
import re

from integer_recovery import translate, render
from ppc_leaf import load_functions

ROOT=Path(__file__).resolve().parents[1]
SPECS=ROOT/'analysis/integer-helper-specs.json'
SOURCE=ROOT/'src/recovered/integer_leaf_helpers.c'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    saved=json.loads(SPECS.read_text())
    addresses=[r['address'][2:] for r in saved['routines']]
    words=load_functions(addresses)
    rows={r['address'][2:]:r for r in csv.DictReader((ROOT/'analysis/functions.csv').open())}
    files={}
    recovered=[]
    for address in addresses:
        row=dict(rows[address])
        path=row['assembly']
        if path not in files:files[path]=(ROOT/path).read_text()
        name=re.escape(row['name'])
        match=re.search(r'^\.fn '+name+r',.*?^\.endfn '+name+r'\s*$', files[path],re.M|re.S)
        if not match:raise ValueError('Missing disassembly for '+address)
        row['ins']=re.findall(r'/\*.*?\*/\s*([^\n]+)',match[0])
        row['words']=list(words[address].values())
        recovered.append(translate(row))
    source=render(recovered)
    if args.write:
        saved['routines']=recovered
        SPECS.write_text(json.dumps(saved,indent=2)+'\n')
        SOURCE.write_text(source)
    elif recovered!=saved['routines'] or source!=SOURCE.read_text():
        raise ValueError('Recovered specs/source differ from verified local disassembly')
    print(f'PASS: {len(recovered)} complete integer C models reproduce from verified original disassembly')


if __name__=='__main__':main()
