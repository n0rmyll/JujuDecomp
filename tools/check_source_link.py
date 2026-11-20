#!/usr/bin/env python3
"""Link manifest-selected recovered sources with binary fallbacks; compare the full DOL."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct

from check_application_flag import EXPECTED_HASH
from check_rebuild_foundation import compare_dols, dol_layout, run_logged
from ppc_matching import function_code

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'analysis/source-link-manifest.json'
SPLITS = ROOT / 'analysis/source-link-splits.txt'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display(path):
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def relative_path(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_./-]+', value):
        raise ValueError('Invalid manifest path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('Manifest paths must be relative without traversal')
    return value


def validate_manifest(manifest):
    if manifest.get('revision') != 'GJUE78 rev 0' or manifest.get('dol_sha256') != EXPECTED_HASH:
        raise ValueError('Unsupported manifest DOL identity')
    entries = manifest.get('replacements')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Manifest requires source replacements')
    seen = {key: set() for key in ('id', 'unit', 'symbol', 'address')}
    ranges = []
    required = {'id', 'unit', 'address', 'size', 'symbol', 'source', 'language', 'defines', 'relocations'}
    for entry in entries:
        if not isinstance(entry, dict) or not required <= entry.keys() or entry.keys() - required - {'behavior_test', 'cpp_exceptions'}:
            raise ValueError('Unknown or missing replacement fields')
        if not isinstance(entry['id'], str) or not re.fullmatch(r'[a-z][a-z0-9_]*', entry['id']):
            raise ValueError('Invalid replacement id')
        if not isinstance(entry['address'], str) or not re.fullmatch(r'0x[0-9A-F]{8}', entry['address']):
            raise ValueError('Invalid replacement address')
        address, size = int(entry['address'], 0), entry['size']
        if type(size) is not int or size <= 0 or size % 4 or address % 4 or address + size > 0x100000000:
            raise ValueError('Invalid replacement range')
        if entry['symbol'] != f'fn_{address:08X}':
            raise ValueError('Replacement symbol disagrees with address')
        relative_path(entry['unit']); relative_path(entry['source'])
        if not entry['source'].startswith('src/') or entry['language'] not in ('c', 'c++'):
            raise ValueError('Unsupported replacement source/language')
        if 'cpp_exceptions' in entry and (entry['language'] != 'c++' or type(entry['cpp_exceptions']) is not bool):
            raise ValueError('Unsupported C++ exception setting')
        if 'behavior_test' in entry:
            relative_path(entry['behavior_test'])
            if not entry['behavior_test'].startswith('tests/') or entry['language'] != 'c':
                raise ValueError('Unsupported behavior test')
        if not isinstance(entry['defines'], dict) or any(
                not isinstance(key, str) or not re.fullmatch(r'[A-Za-z_]\w*', key) or not isinstance(value, str)
                or not re.fullmatch(r'[A-Za-z0-9_]+', value) for key, value in entry['defines'].items()):
            raise ValueError('Invalid replacement defines')
        if not isinstance(entry['relocations'], list):
            raise ValueError('Invalid relocation contract')
        for relocation in entry['relocations']:
            if (not isinstance(relocation, dict) or set(relocation) != {'offset', 'type', 'symbol', 'target', 'addend'}
                or type(relocation['offset']) is not int or not 0 <= relocation['offset'] < size
                or type(relocation['type']) is not int or relocation['type'] not in (1, 4, 5, 6, 10, 109)
                or relocation['offset'] + (2 if relocation['type'] in (4, 5, 6) else 4) > size
                or type(relocation['addend']) is not int
                or not isinstance(relocation['symbol'], str)
                or not re.fullmatch(r'(?:fn|lbl)_[0-9A-F]{8}', relocation['symbol'])
                or relocation['target'] != '0x' + relocation['symbol'][-8:]):
                raise ValueError('Invalid relocation contract')
        for key in seen:
            if entry[key] in seen[key]:
                raise ValueError('Duplicate manifest ' + key)
            seen[key].add(entry[key])
        ranges.append((address, address + size))
    ordered = sorted(ranges)
    if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError('Overlapping replacement ranges')
    return entries


def split_text(header, entries):
    # Ranges have one authority: the manifest, never hand-maintained duplicates.
    if re.findall(r'^([^\s/][^\n]*):\s*$', header, re.M) != ['Sections']:
        raise ValueError('Split template must contain only a section header')
    parts = [header.rstrip()]
    for entry in entries:
        start = int(entry['address'], 0)
        parts.append(f'\n{entry["unit"]}:\n\t.text start:0x{start:08X} end:0x{start+entry["size"]:08X} align:4')
    return '\n'.join(parts) + '\n'


def original_function(data, entry):
    address, size = int(entry['address'], 0), entry['size']
    for section in dol_layout(data)['sections']:
        start = int(section['address'], 0)
        if section['kind'] == 'text' and start <= address and address + size <= start + section['size']:
            offset = section['offset'] + address - start
            return data[offset:offset + size]
    raise ValueError('Source replacement is outside original text')


def replacement_plan(config, entries, compiled):
    """Substitute every manifest unit exactly once, preserving DTK link order."""
    if config.get('version') != '1.8.4' or config.get('modules') or config.get('links'):
        raise ValueError('Unsupported split configuration')
    units = config['units']
    by_name = {entry['unit']: entry for entry in entries}
    if set(compiled) != set(by_name) or len(set(compiled.values())) != len(compiled):
        raise ValueError('Compiled objects disagree with manifest')
    if len({u['name'] for u in units}) != len(units):
        raise ValueError('Duplicate split unit')
    if not set(by_name) <= {u['name'] for u in units}:
        raise ValueError('Missing recovered-source unit')
    objects = [Path(u['object']) if Path(u['object']).is_absolute() else ROOT / u['object'] for u in units]
    if len(set(objects)) != len(objects) or set(compiled.values()) & set(objects):
        raise ValueError('Duplicate split object or compiled-object collision')
    excluded = {}
    for index, unit in enumerate(units):
        if unit['name'] in by_name:
            entry = by_name[unit['name']]
            if unit.get('autogenerated') is not False or unit['code_size'] != entry['size'] or unit['data_size'] != 0:
                raise ValueError('Unexpected source-unit ownership or size')
            excluded[unit['name']] = objects[index]
            objects[index] = compiled[unit['name']]
        elif not unit.get('autogenerated'):
            raise ValueError('Unexpected additional source unit')
    if set(excluded.values()) & set(objects):
        raise ValueError('Original source target was not excluded')
    return objects, excluded


def global_definitions(path):
    """Read defined GLOBAL/WEAK names from strict ELF32 big-endian PPC inputs."""
    data = path.read_bytes()
    if len(data) < 52 or data[:7] != b'\x7fELF\x01\x02\x01' or struct.unpack_from('>HH', data, 16) != (1, 20):
        raise ValueError('Expected relocatable ELF32/PPC input')
    start = struct.unpack_from('>I', data, 32)[0]
    stride, count = struct.unpack_from('>HH', data, 46)
    if stride != 40 or not count or start + count * stride > len(data):
        raise ValueError('Invalid ELF section table')
    sections = [struct.unpack_from('>10I', data, start + i * stride) for i in range(count)]
    def contents(section):
        offset, size = section[4:6]
        if offset + size > len(data):
            raise ValueError('Truncated ELF section')
        return data[offset:offset + size]
    names = []
    for section in sections:
        if section[1] != 2:
            continue
        if section[9] != 16 or section[5] % 16 or section[6] >= len(sections):
            raise ValueError('Invalid ELF symbol table')
        strings = contents(sections[section[6]])
        symbols = contents(section)
        for offset in range(0, len(symbols), 16):
            name, _, _, info, _, index = struct.unpack_from('>IIIBBH', symbols, offset)
            if info >> 4 not in (1, 2) or index == 0:
                continue
            if name >= len(strings) or b'\0' not in strings[name:]:
                raise ValueError('Invalid ELF symbol name')
            names.append(strings[name:].split(b'\0', 1)[0].decode('ascii'))
    return names


def verify_owners(objects, entries, compiled):
    definitions = {}
    for path in objects:
        for name in global_definitions(path):
            definitions.setdefault(name, []).append(path)
    for entry in entries:
        if definitions.get(entry['symbol']) != [compiled[entry['unit']]]:
            raise ValueError('Target symbol must be defined exactly once by compiled source: ' + entry['symbol'])
        for relocation in entry['relocations']:
            if len(definitions.get(relocation['symbol'], [])) != 1:
                raise ValueError('Relocation dependency requires exactly one definition: ' + relocation['symbol'])
    return definitions


def verify_map_symbol(text, symbol, address, size=None, object_name=None):
    pattern = r'^\s*[0-9a-fA-F]{8}\s+([0-9a-fA-F]{6,8})\s+([0-9a-fA-F]{8})\s+\d+\s+' + re.escape(symbol) + r'\s+(\S+)\s*$'
    matches = re.findall(pattern, text, re.M)
    if len(matches) != 1:
        raise ValueError('Link map has missing or duplicate symbol placement: ' + symbol)
    actual_size, actual_address, actual_object = matches[0]
    if int(actual_address, 16) != address or (size is not None and int(actual_size, 16) != size) or (object_name is not None and actual_object != object_name):
        raise ValueError('Link map placement differs: ' + symbol)


def verify_relocations(actual, entry):
    if actual != entry['relocations']:
        raise ValueError('Compiled relocations differ from manifest contract: ' + entry['symbol'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/source-link')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / 'report.json'
    report_path.unlink(missing_ok=True)
    manifest_path = args.manifest.resolve()
    entries = validate_manifest(json.loads(manifest_path.read_text()))
    original = (ROOT / 'analysis/main.dol').read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED_HASH:
        raise ValueError('Unexpected DOL revision')
    inputs = {manifest_path, SPLITS, *[ROOT / e['source'] for e in entries],
              *[ROOT / e['behavior_test'] for e in entries if 'behavior_test' in e]}
    input_hashes = {display(p): digest(p) for p in inputs}
    commands = []
    def execute(command, log):
        commands.append(command)
        run_logged(command, output / log)
    for entry in entries:
        if 'behavior_test' in entry:
            host = output / (entry['id'] + '-behavior')
            execute(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', str(ROOT / entry['source']),
                     str(ROOT / entry['behavior_test']), '-o', str(host)], entry['id'] + '-host-compile.log')
            execute([str(host)], entry['id'] + '-behavior.log')
    local_splits = output / 'splits.txt'
    local_splits.write_text(split_text(SPLITS.read_text(), entries))
    config_path = output / 'config.yml'
    config_path.write_text(json.dumps(dict(object=str(ROOT / 'analysis/main.dol'),
        hash=hashlib.sha1(original).hexdigest(), splits=str(local_splits)), indent=2) + '\n')
    dtk = ROOT / 'tools/dtk'
    execute([str(dtk), 'dol', 'split', str(config_path), str(output / 'split')], 'split.log')
    split_config_path = output / 'split/config.json'
    config = json.loads(split_config_path.read_text())
    runner = ROOT / 'tools/wibo'
    cc = ROOT / 'tools/mwcc/GC/1.3.2/mwcceppc.exe'
    linker = ROOT / 'tools/mwcc/GC/1.3.2/mwldeppc.exe'
    compiled, compiled_info = {}, {}
    for entry in entries:
        obj = output / ('compiled_' + entry['id'] + '.o')
        obj.unlink(missing_ok=True)
        execute([str(runner), str(cc), '-c', '-lang', entry['language'], '-proc', 'gekko', '-O4,p',
                 '-fp', 'hardware', '-nodefaults',
                 *(['-Cpp_exceptions', 'on' if entry['cpp_exceptions'] else 'off'] if 'cpp_exceptions' in entry else []),
                 *['-D' + key + '=' + value for key, value in sorted(entry['defines'].items())],
                 str(ROOT / entry['source']), '-o', str(obj)], entry['id'] + '-compile.log')
        code, relocations = function_code(obj, entry['symbol'], int(entry['address'], 0), {})
        if code != original_function(original, entry):
            raise ValueError('Compiled source differs from original function: ' + entry['symbol'])
        verify_relocations(relocations, entry)
        compiled[entry['unit']] = obj
        compiled_info[entry['unit']] = (code, relocations)
    objects, excluded = replacement_plan(config, entries, compiled)
    for entry in entries:
        old, _ = function_code(excluded[entry['unit']], entry['symbol'], int(entry['address'], 0), {})
        if old != original_function(original, entry):
            raise ValueError('Extracted target unit differs from original function')
    definitions = verify_owners(objects, entries, compiled)
    hashes = {display(p): digest(p) for p in objects}
    elf, dol, map_path = [output / ('source.' + extension) for extension in ('elf', 'dol', 'map')]
    for path in (elf, dol, map_path):
        path.unlink(missing_ok=True)
    lcf = Path(config['ldscript'])
    if not lcf.is_absolute():
        lcf = ROOT / lcf
    execute([str(runner), str(linker), '-nodefaults', '-fp', 'hardware', '-lcf', str(lcf),
             '-m', config['entry'], '-o', str(elf), '-map', str(map_path),
             *[str(p) for p in objects]], 'link.log')
    execute([str(dtk), 'elf2dol', str(elf), str(dol)], 'elf2dol.log')
    layout = compare_dols(original, dol.read_bytes())
    map_text = map_path.read_text()
    dependencies = {}
    for entry in entries:
        verify_map_symbol(map_text, entry['symbol'], int(entry['address'], 0), entry['size'], compiled[entry['unit']].name)
        for relocation in entry['relocations']:
            owner = definitions[relocation['symbol']][0]
            verify_map_symbol(map_text, relocation['symbol'], int(relocation['target'], 0), object_name=owner.name)
            dependencies[relocation['symbol']] = dict(address=relocation['target'], object=display(owner))
    if any(digest(ROOT / p if not Path(p).is_absolute() else Path(p)) != expected for p, expected in {**input_hashes, **hashes}.items()):
        raise ValueError('Manifest, source or link input changed during the build')
    replacements = []
    for entry in entries:
        obj, old = compiled[entry['unit']], excluded[entry['unit']]
        code, relocations = compiled_info[entry['unit']]
        replacements.append(dict(entry, source_sha256=input_hashes[entry['source']], object=display(obj),
            object_sha256=digest(obj), excluded_binary_object=display(old), excluded_binary_sha256=digest(old),
            symbol_owner=display(obj), code_sha256=hashlib.sha256(code).hexdigest(), applied_relocations=relocations))
    source_bytes = sum(e['size'] for e in entries)
    report = dict(revision='GJUE78 rev 0', exact_match=True,
        scope='Manifest-selected recovered C/C++ linked with binary-derived fallbacks; no gameplay test',
        source_replacements=len(entries), linked_source_functions=len(entries), linked_source_bytes=source_bytes,
        manifest=display(manifest_path), input_hashes=input_hashes, replacements=replacements,
        relocation_dependencies=dependencies, object_count=len(objects), binary_derived_objects=len(objects)-len(entries),
        original_sha256=EXPECTED_HASH, rebuilt_sha256=digest(dol), rebuilt_size=dol.stat().st_size,
        elf_sha256=digest(elf), map_sha256=digest(map_path),
        split_config_sha256=digest(split_config_path), split_input_sha256=digest(config_path),
        split_file_sha256=digest(local_splits), lcf_sha256=digest(lcf), checker_sha256=digest(Path(__file__).resolve()),
        helper_hashes={display(p):digest(p) for p in (ROOT / 'tools/check_rebuild_foundation.py', ROOT / 'tools/ppc_matching.py')},
        tools={display(p):digest(p) for p in (runner, cc, linker, dtk)},
        object_hashes=hashes, commands=commands, **layout)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(entries)} recovered functions / {source_bytes} bytes + {len(objects)-len(entries)} binary-derived objects; '
          f'exact {len(original):,}-byte DOL; SHA-256 {EXPECTED_HASH}')
    print(report_path)


if __name__ == '__main__':
    main()
