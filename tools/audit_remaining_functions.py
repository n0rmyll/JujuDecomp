#!/usr/bin/env python3
"""Account for every not-yet-counted indexed region, without generating stubs."""
import collections
import json
from pathlib import Path

from integer_recovery import translate as integer_translate
from transfer_recovery import translate as transfer_translate,OPS
from remaining_regions import remaining_rows,ROOT

STATE_OPS={'mfmsr','mtmsr','mtspr','mfspr','mftb','mftbu','mfsr','mtsr','mfsprg','mtsprg','mffs','mtfsf','mtfsb0','mtfsb1',
           'sync','isync','eieio','dcbst','dcbf','dcbi','dcbz','icbi','tlbie','tlbsync','rfi','sc','wrteei'}


def main():
    rows=[];counts=collections.Counter();sizes=collections.Counter();primary=collections.Counter();operations=collections.Counter()
    integer_excluded=set();transfer_excluded=set()
    path=ROOT/'analysis/remaining-integer-selection-summary.json'
    if path.exists():integer_excluded.update(json.loads(path.read_text())['insufficient_addresses'])
    path=ROOT/'analysis/scalar-transfer-selection-summary.json'
    if path.exists():transfer_excluded.update(r['address'] for r in json.loads(path.read_text())['excluded'])
    for row in remaining_rows():
        ops=sorted({ins.split()[0] for ins in row['ins']});missing=[]
        for kind,translate in (('integer',integer_translate),('scalar-transfer',transfer_translate)):
            try:
                if kind=='integer':translate(row,full_context=True,allow_calls=True)
                else:translate(row)
            except ValueError as error:missing.append(str(error))
            else:
                supported=kind;break
        else:supported=None
        paired=[op for op in ops if op.startswith(('ps_','psq_'))]
        arithmetic=[op for op in ops if op.startswith('f') and op not in OPS]
        processor=[op for op in ops if op.rstrip('.') in STATE_OPS]
        if supported:
            bucket='insufficient-comparison-evidence' if row['address'] in (integer_excluded|transfer_excluded) else 'supported-not-yet-verified'
        elif paired:bucket='paired-single-or-quantized'
        elif arithmetic:bucket='scalar-floating-beyond-supported-transfers'
        elif processor:bucket='processor-state-or-hardware'
        else:bucket='unsupported-integer-or-control-flow'
        reason=missing[-1] if supported is None and missing else None
        counts[bucket]+=1;sizes[bucket]+=int(row['size']);operations.update(ops)
        if reason:primary[reason]+=1
        rows.append({'address':row['address'],'original_name':row['name'],'original_bytes':int(row['size']),'assembly':row['assembly'],
                     'status':'unresolved-not-counted','bucket':bucket,'supported_projection':supported,'translation_rejection':reason,
                     'paired_operations':paired,'floating_operations_beyond_transfers':arithmetic,'processor_operations':processor,'all_operations':ops})
    inventory=json.loads((ROOT/'analysis/semantic-functions.json').read_text())
    result={'revision':'GJUE78 rev 0','dol_sha256':inventory['dol_sha256'],'indexed_total':9667,'modeled':len(inventory['routines']),
            'remaining':len(rows),'remaining_original_bytes':sum(r['original_bytes'] for r in rows),'bucket_counts':dict(counts),'bucket_original_bytes':dict(sizes),
            'primary_rejections':dict(primary.most_common()),'operations_by_remaining_routine':dict(operations.most_common()),
            'scope':'Every remaining provisional indexed region; unsupported and insufficient-evidence bodies are excluded from the model inventory. Buckets are exclusive, operation lists may overlap.',
            'routines':rows}
    if result['modeled']+result['remaining']!=result['indexed_total']:raise ValueError('Index coverage gap')
    used={r['address'] for r in inventory['routines']}
    if used&{r['address'] for r in rows}:raise ValueError('Inventory overlap')
    (ROOT/'analysis/remaining-functions.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: {result["modeled"]} counted + {result["remaining"]} unresolved = {result["indexed_total"]} indexed regions')
    print(json.dumps(result['bucket_counts'],sort_keys=True))


if __name__=='__main__':main()
