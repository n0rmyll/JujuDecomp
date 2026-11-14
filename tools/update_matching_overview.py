#!/usr/bin/env python3
"""Combine distinct verified function-code matching reports without double count."""
import hashlib
import json
from pathlib import Path

from check_application_flag import EXPECTED_HASH

ROOT=Path(__file__).resolve().parents[1]


def main():
    inventory=json.loads((ROOT/'analysis/semantic-functions.json').read_text())
    regions={r['address']:r for r in inventory['routines']}
    old=json.loads((ROOT/'analysis/all-matching-summary.json').read_text())
    small=json.loads((ROOT/'analysis/small-matching-summary.json').read_text())
    if hashlib.sha256((ROOT/'analysis/main.dol').read_bytes()).hexdigest()!=EXPECTED_HASH:raise ValueError('DOL identity')
    for path,expected in old['source_hashes'].items():
        if path.startswith('src/') and hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('Matching source changed since survey: '+path)
    if small.get('dol_sha256')!=EXPECTED_HASH or old['dol_sha256']!=EXPECTED_HASH:raise ValueError('Report DOL identity')
    if hashlib.sha256((ROOT/'src/matching/small_helpers.cpp').read_bytes()).hexdigest()!=small['source_sha256']:
        raise ValueError('Small matching source changed')
    checked={};matched={}
    for report in (old,small):
        for r in report['results']:
            address=r['address']
            if address not in regions or r['original_bytes']!=regions[address]['original_bytes']:raise ValueError('Region mismatch')
            checked[address]=r
            if r['status']=='match':matched[address]=r
    result={'revision':'GJUE78 rev 0','dol_sha256':EXPECTED_HASH,
            'modeled_functions':len(regions),'checked_distinct_functions':len(checked),
            'matched':len(matched),'matched_bytes':sum(r['original_bytes'] for r in matched.values()),
            'not_yet_surveyed':len(regions)-len(checked),
            'reports':['analysis/all-matching-summary.json','analysis/small-matching-summary.json'],
            'scope':'Exact individual function code; no linked game executable',
            'matched_addresses':sorted(matched)}
    (ROOT/'analysis/matching-overview.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: {result["matched"]} exact matches, {result["matched_bytes"]} bytes; '
          f'{len(checked)} surveyed, {result["not_yet_surveyed"]} not yet surveyed')


if __name__=='__main__':main()
