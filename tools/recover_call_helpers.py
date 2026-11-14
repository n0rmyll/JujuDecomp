#!/usr/bin/env python3
"""Reproduce compositional caller models from verified original disassembly."""
import argparse
import csv
import json
from pathlib import Path
import re

from integer_recovery import translate, render
from ppc_leaf import load_functions

ROOT=Path(__file__).resolve().parents[1]
SPECS=ROOT/'analysis/call-helper-specs.json'
SOURCE=ROOT/'src/recovered/call_leaf_helpers.c'


def main():
    global SPECS,SOURCE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--batch',type=int,choices=(3,4,5,6),default=3)
    args=parser.parse_args()
    if args.batch==4:
        SPECS=ROOT/'analysis/fourth-call-helper-specs.json'
        SOURCE=ROOT/'src/recovered/fourth_call_leaf_helpers.c'
    if args.batch==5:
        SPECS=ROOT/'analysis/fifth-sixth-call-helper-specs.json'
        SOURCE=ROOT/'src/recovered/fifth_sixth_call_leaf_helpers.c'
    if args.batch==6:
        SPECS=ROOT/'analysis/remaining-integer-helper-specs.json'
        SOURCE=ROOT/'src/recovered/remaining_integer_helpers.c'
    saved=json.loads(SPECS.read_text());addresses=[s['address'][2:] for s in saved['routines']]
    words=load_functions(addresses)
    rows={r['address'][2:]:r for r in csv.DictReader((ROOT/'analysis/functions.csv').open())}
    files={};recovered=[]
    for address in addresses:
        row=dict(rows[address]);path=row['assembly']
        if path not in files:files[path]=(ROOT/path).read_text()
        name=re.escape(row['name'])
        body=re.search(r'^\.fn '+name+r',.*?^\.endfn '+name+r'\s*$',files[path],re.M|re.S)
        if not body:raise ValueError('Missing original routine '+address)
        row['ins']=re.findall(r'/\*.*?\*/\s*([^\n]+)',body[0]);row['words']=list(words[address].values())
        recovered.append(translate(row,full_context=True,allow_calls=True))
    source=render(recovered,full_context=True,allow_calls=True)
    if args.write:
        saved['routines']=recovered;SPECS.write_text(json.dumps(saved,indent=2)+'\n');SOURCE.write_text(source)
    elif recovered!=saved['routines'] or source!=SOURCE.read_text():raise ValueError('Caller source/spec differs from verified original disassembly')
    print(f'PASS: {len(recovered)} integer-context models reproduce; callees remain opaque')


if __name__=='__main__':main()
