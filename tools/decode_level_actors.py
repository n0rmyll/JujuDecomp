#!/usr/bin/env python3
"""Resolve supported Hub actor prefixes to named instances and replacement assets.

This is a bounded prefix extractor, not a full .env or gameplay interpreter.
Only explicit model overrides on uniquely named box placements are eligible.
"""
import hashlib
import json
import struct
from pathlib import Path
from decode_rigs import ROOT
from inspect_dbu import inspect

SUPPORTED_CLASSES={'chicken','monkey','rhino','sheep','yorbel','tiki','rope','zipline'}


def cstring(data,offset,limit=256):
    if offset<0 or offset>=len(data):raise ValueError('String outside payload')
    end=data.find(b'\0',offset,min(len(data),offset+limit))
    if end<0:raise ValueError('Unterminated source string')
    raw=data[offset:end]
    if any(x<32 or x>126 for x in raw):raise ValueError('Non-ASCII source string')
    return raw.decode('ascii'),end


def padded_string(data,offset):
    if offset%4:raise ValueError('Unaligned environment string')
    value,end=cstring(data,offset)
    following=(end+4)&~3
    if following>len(data):raise ValueError('Truncated environment string padding')
    return value,following


def instance_names(payload,rows):
    names={}
    for row in rows:
        offset=row['auxiliary_offset']+0x20
        name,_=cstring(payload,offset)
        names.setdefault(name.lower(),[]).append(row['index'])
    return names


def actor_prefixes(payload,names,classes=SUPPORTED_CLASSES):
    """Anchor supported class/name/override prefixes to actual instance names.

    fn_8024269C/802425CC advance by (strlen+4)&~3; fn_80252EEC reads
    the instance name then model_name. Remainders are deliberately not parsed.
    """
    found=[]
    for cls in sorted(classes):
        needle=cls.encode('ascii')+b'\0';cursor=16
        while True:
            offset=payload.find(needle,cursor)
            if offset<0:break
            cursor=offset+len(needle)
            if offset%4 or (offset and 32<=payload[offset-1]<127):continue
            try:
                actor_class,start=padded_string(payload,offset)
                name,next_field=padded_string(payload,start)
                override,end=padded_string(payload,next_field)
            except ValueError:continue
            matches=names.get(name.lower())
            if matches:
                found.append(dict(actor_class=actor_class,instance_name=name,model_override=override,
                                  record_offset=offset,name_offset=start,override_offset=next_field,
                                  prefix_end=end,instance_indices=matches))
    return sorted(found,key=lambda row:row['record_offset'])


def replacement_path(override):
    # fn_801FCFF4 appends Replace\ + override + .dbl. Restrict this pass
    # to simple explicit stems; do not infer constructor-specific defaults.
    if not override or override.lower()=='none':return None
    if any(not (c.isalnum() or c in '_-') for c in override):return None
    return 'replace\\'+override.lower()+'.dbl'


def resolve_assets(prefixes,rows,exports,archive,asset_root=ROOT/'assets'):
    by_index={r['index']:r for r in rows};bindings={};unresolved=[]
    for prefix in prefixes:
        item=dict(prefix)
        if len(prefix['instance_indices'])!=1:
            unresolved.append(dict(**item,reason='Ambiguous world instance name'));continue
        index=prefix['instance_indices'][0];row=by_index[index]
        if not row['box_proxy_candidate']:continue
        path=replacement_path(prefix['model_override'])
        if path is None:
            unresolved.append(dict(**item,reason='No supported explicit model override'));continue
        candidates=[]
        for preferred in (archive,'Preload.dbu'):
            candidates=[r for r in exports if r['archive']==preferred and (r.get('path_hint') or '').replace('/','\\').lower()==path]
            if candidates:break
        if len(candidates)!=1:
            unresolved.append(dict(**item,reason='Replacement asset missing or ambiguous'));continue
        if index in bindings:raise ValueError('Multiple actor prefixes resolve to one instance')
        asset=candidates[0];source=asset_root/asset['category']/asset['glb']
        bindings[index]=dict(**item,instance_index=index,asset_category=asset['category'],asset_glb=asset['glb'],
                             asset_name=asset['name'],asset_path=path,asset_chunk=asset['chunk'],asset_index=asset['index'],
                             asset_archive=asset['archive'],asset_archive_sha256=asset['archive_sha256'],
                             asset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                             pose='bind' if asset['category']=='rigs' else 'static')
    return bindings,unresolved


def resolve_level_actors(data,chunks,instance_chunk,rows,archive):
    envs=[c for c in chunks if c['type']=='0x0402']
    if len(envs)!=1:raise ValueError('Expected one environment resource')
    env=envs[0];payload=data[env['payload_offset']:env['payload_offset']+env['payload_size']]
    instances=data[instance_chunk['payload_offset']:instance_chunk['payload_offset']+instance_chunk['payload_size']]
    names=instance_names(instances,rows);prefixes=actor_prefixes(payload,names)
    exports=[]
    for category in ('rigs','models'):
        for asset in json.loads((ROOT/f'assets/{category}/manifest.json').read_text())['entries']:
            # Prefer a validated rig when the static pass also exported this asset.
            if category=='models' and any(r['archive']==asset['archive'] and r['glb']==asset['glb'] for r in exports):continue
            exports.append(dict(asset,category=category))
    bindings,unresolved=resolve_assets(prefixes,rows,exports,archive)
    for binding in bindings.values():
        binding.update(environment_chunk=env['index'],environment_source_offset=env['payload_offset']+binding['record_offset'])
    report=dict(environment_chunk=env['index'],supported_classes=sorted(SUPPORTED_CLASSES),matched_prefixes=len(prefixes),
                replacements=len(bindings),unresolved=unresolved,
                remaining_box_markers=sum(r['box_proxy_candidate'] and r['index'] not in bindings for r in rows),
                limitations='Supported class/name/model-override prefixes only; no full environment parse, constructor defaults, spawn timing, state selection, or actor behavior. Rigs shown in static bind pose.')
    return bindings,report
