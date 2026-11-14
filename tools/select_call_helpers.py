#!/usr/bin/env python3
"""Collect supported, previously uncounted caller candidates for verification.

This only proposes candidates. check_call_helpers.py must validate them before
anything is added to the inventory.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import re

from integer_recovery import translate
from ppc_leaf import load_functions

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--include-call-free',action='store_true')
    args=parser.parse_args()
    used={r['address'] for r in json.loads((ROOT/'analysis/semantic-functions.json').read_text())['routines']}
    rows=[r for r in csv.DictReader((ROOT/'analysis/functions.csv').open()) if r['address'] not in used]
    words=load_functions([r['address'][2:] for r in rows]);bodies={};out=[];errors=collections.Counter()
    for path in {r['assembly'] for r in rows}:
        for match in re.finditer(r'^\.fn (\w+),.*?^\.endfn \1\s*$',(ROOT/path).read_text(),re.M|re.S):
            bodies[match[1]]=match[0]
    for row in sorted(rows,key=lambda r:(int(r['size']),int(r['address'],16))):
        row=dict(row)
        row['ins']=re.findall(r'/\*.*?\*/\s*([^\n]+)',bodies[row['name']])
        row['words']=list(words[row['address'][2:]].values())
        try:
            spec=translate(row,full_context=True,allow_calls=True)
            if spec['external_call_sites'] or args.include_call_free:out.append(spec)
        except ValueError as error:errors[str(error).split(':')[0]]+=1
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(f'{len(out)} uncounted integer-context candidates; none accepted yet')
    print(errors.most_common(15))


if __name__=='__main__':main()
