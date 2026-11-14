#!/usr/bin/env python3
"""Survey post-initial-batch models using direct-memory target-ABI candidates.

Only full relocated byte equality counts as a match. Generated candidates are
ordinary C/C++ expressions and control flow, not assembly substitutions.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess

from ppc_leaf import load_functions
from ppc_matching import function_code

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('leaf_helpers.c', 'resource_leaf_helpers.c', 'scalar_leaf_helpers.c',
           'integer_leaf_helpers.c')
PREAMBLE = '''typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef signed int int32_t;
typedef unsigned long long uint64_t;
typedef signed long long int64_t;
#define UINT32_C(x) x##u
#define INT64_C(x) x##ll
#define UINT16_C(x) x##u
#define UINT32_MAX 0xffffffffu
#define READ8(a) (*(uint8_t *)(a))
#define READ16(a) (*(uint16_t *)(a))
#define READ32(a) (*(uint32_t *)(a))
#define WRITE8(a,v) (READ8(a)=(v))
#define WRITE16(a,v) (READ16(a)=(v))
#define WRITE32(a,v) (READ32(a)=(v))
#define __builtin_clz(x) __cntlzw(x)
'''


def definitions(text):
    """Extract preprocessed function definitions, including macro-defined ones."""
    result = {}
    pattern = r'\b((?:static\s+)?(?:inline\s+)?(?:uint32_t|uint16_t|uint8_t|int|void)\s+(\w+)\s*\([^;{}]*\)\s*)\{'
    for match in re.finditer(pattern, text):
        depth, end = 1, match.end()
        while depth and end < len(text):
            depth += (text[end] == '{') - (text[end] == '}')
            end += 1
        if depth:
            raise ValueError('Unbalanced function definition')
        result[match[2]] = (match[1], text[match.end():end-1])
    return result


def direct(text):
    text = text.replace('(void)m;', '')
    text = re.sub(r'\bm->r(8|16|32)\b', r'READ\1', text)
    text = re.sub(r'\bm->w(8|16|32)\b', r'WRITE\1', text)
    text = re.sub(r'const TakTarget\s*\*\s*m\s*,\s*', '', text)
    text = re.sub(r',\s*const TakTarget\s*\*\s*m', '', text)
    text = re.sub(r'const TakTarget\s*\*\s*m', '', text)
    text = re.sub(r'\bm\s*,\s*', '', text)
    text = re.sub(r',\s*m\b', '', text)
    text = re.sub(r'\(m\)', '()', text)
    if re.search(r'\bm\b|TakTarget', text):
        raise ValueError('Unconverted callback or target context')
    return text


def unroll_offsets(body):
    """Expand only fixed byte-offset lists from the semantic models."""
    declaration = re.search(r'static const uint8_t offsets\[\]\s*=\s*\{([^}]+)\};', body)
    if not declaration:
        return body
    values = [int(x.strip(), 0) for x in declaration[1].split(',') if x.strip()]
    if not values or any(not 0 <= x <= 255 for x in values):
        raise ValueError('Invalid constant byte-offset list')
    loop = re.search(r'for\s*\(unsigned i = 0; i < sizeof\(offsets\); \+\+i\)\s*(m->w32\(a\+offsets\[i\], [^;]+;)', body)
    if not loop:
        raise ValueError('Unsupported offset-list use')
    body = body[:loop.start()] + '\n'.join(loop[1].replace('offsets[i]', hex(x)) for x in values) + body[loop.end():]
    return body.replace(declaration[0], '')


def original_bytes(words):
    return b''.join(value.to_bytes(4, 'big') for _, value in sorted(words.items()))


def adapt_candidate(source, variant):
    """Apply explicitly selected source-level matching adaptations."""
    if variant not in ('globals', 'signed', 'both'):
        raise ValueError('Unknown matching adaptation: ' + variant)
    if variant in ('signed', 'both'):
        source = source.replace('(a ^ 0x80000000u) < (b ^ 0x80000000u)',
                                '(int32_t)a < (int32_t)b')
    if variant in ('globals', 'both'):
        labels = set()
        pattern = r'((?:READ|WRITE)(?:8|16|32)\(\s*\(*\s*)(?:UINT32_C\((0x80[0-9a-fA-F]{6})\)|(0x80[0-9a-fA-F]{6})[uU]?)'
        def replace(match):
            address = int(match[2] or match[3], 16)
            labels.add(address)
            return match[1] + f'((uint32_t)&lbl_{address:08X})'
        source = re.sub(pattern, replace, source)
        declarations = '\n'.join(
            f'extern uint8_t lbl_{address:08X}[{1 if 0x80330280 <= address < 0x80333140 else 16}];'
            for address in sorted(labels))
        marker = '#define __builtin_clz(x) __cntlzw(x)'
        if source.count(marker) != 1:
            raise ValueError('Missing unique candidate preamble')
        source = source.replace(marker, marker + '\n' + declarations, 1)
    return source


def prepare(entries):
    families = {}
    for filename in SOURCES[:-1]:
        raw = (ROOT / 'src/recovered' / filename).read_text()
        raw = re.sub(r'^#include[^\n]*', '', raw, flags=re.M)
        run = subprocess.run(['clang', '-E', '-P', '-x', 'c', '-'],
                             input=PREAMBLE + raw, text=True, capture_output=True, check=True)
        families[filename] = definitions(run.stdout)
    integer_specs = json.loads((ROOT / 'analysis/integer-helper-specs.json').read_text())
    from integer_recovery import HELPERS, render
    if (ROOT / 'src/recovered/integer_leaf_helpers.c').read_text() != render(integer_specs['routines']):
        raise ValueError('Integer source differs from the current specifications')
    integers = {x['address']: x for x in integer_specs['routines']}
    return_checked = {}
    for filename in ('leaf-helpers-summary.json', 'resource-leaf-helpers-summary.json'):
        for item in json.loads((ROOT / 'analysis' / filename).read_text())['routines']:
            return_checked[item['address']] = item['return_checked']
    candidates = {}
    adaptations = json.loads((ROOT / 'analysis/matching-adaptations.json').read_text())['routines']
    for entry in entries:
        filename = Path(entry['source']).name
        address = entry['address']
        name = 'fn_' + address[2:]
        if filename == SOURCES[-1]:
            body = '\n'.join(integers[address]['body']).replace('TAK_INTEGER_STEP();', '')
            body = re.sub(r'input\[(\d)\]', lambda m: 'arg' + m[1], body)
            signature = 'uint32_t ' + name + '(' + ', '.join(f'uint32_t arg{i}' for i in range(8)) + ')'
            helpers = '\n'.join(HELPERS.values())
        else:
            defs = families[filename]
            signature, body = defs[entry['symbol']]
            signature = signature.replace(entry['symbol'], name)
            helpers = '\n'.join(sig + '{' + code + '}' for symbol, (sig, code) in defs.items()
                                if sig.lstrip().startswith('static '))
            if return_checked.get(address) is False:
                signature = re.sub(r'^uint32_t', 'void', signature)
                body = re.sub(r'\breturn\s+([^;]+);', r'{ (void)(\1); return; }', body)
        body = unroll_offsets(body)
        helpers = direct(helpers).replace('static ', 'static inline ')
        candidates[address] = PREAMBLE + '\n' + helpers + '\nextern "C" ' + direct(signature) + '{\n' + direct(body) + '\n}\n'
        if address in adaptations:
            candidates[address] = adapt_candidate(candidates[address], adaptations[address])
    return candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/new-matching')
    parser.add_argument('--function', help='Check one address, e.g. 0x80003140')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'analysis/semantic-functions.json').read_text())
    entries = [x for x in manifest['routines'] if Path(x['source']).name in SOURCES]
    if args.function:
        entries = [x for x in entries if int(x['address'], 0) == int(args.function, 0)]
        if not entries:
            parser.error('Address is not in the new model families')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').unlink(missing_ok=True)
    words = load_functions([x['address'][2:] for x in entries])
    candidates = prepare(entries)
    symbols = {}
    for match in re.finditer(r'\.text\s*\|\s*(0x[0-9A-Fa-f]+)\s*\|[^|\n]*\|\s*(_(?:save|rest)gpr_\d+)', (ROOT / 'analysis/dol-info.txt').read_text()):
        symbols[match[2]] = int(match[1], 0)
    cc = ROOT / 'tools/mwcc/GC/1.3.2/mwcceppc.exe'
    runner = ROOT / 'tools/wibo'
    results = []
    for index, entry in enumerate(entries, 1):
        address = entry['address']; name = 'fn_' + address[2:]
        src = output / (name + '.cpp'); obj = output / (name + '.o')
        for suffix in ('.o', '.bin', '.original.bin', '.diff.txt'):
            (output / (name + suffix)).unlink(missing_ok=True)
        src.write_text(candidates[address])
        command = [str(runner), str(cc), '-c', '-lang', 'c++', '-proc', 'gekko',
                   '-O4,p', '-inline', 'all', '-nodefaults', str(src), '-o', str(obj)]
        run = subprocess.run(command, capture_output=True, text=True)
        (output / (name + '.log')).write_text(run.stdout + run.stderr)
        result = dict(address=address, function=name, model_source=entry['source'],
                      model_symbol=entry['symbol'], original_size=entry['original_bytes'],
                      candidate_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                      exact_match=False, command=command)
        if run.returncode:
            result.update(status='compile_error', error=run.stdout + run.stderr)
        else:
            try:
                candidate, relocs = function_code(obj, name, int(address, 0), symbols)
                expected = original_bytes(words[address[2:]])
                if len(expected) != entry['original_bytes']:
                    raise ValueError('Manifest size differs from verified original')
                exact = candidate == expected
                (output / (name + '.bin')).write_bytes(candidate)
                (output / (name + '.original.bin')).write_bytes(expected)
                diffs = [f'+0x{i:04x}: original {expected[i:i+4].hex() or "<end>"} candidate {candidate[i:i+4].hex() or "<end>"}'
                         for i in range(0, max(len(candidate), len(expected)), 4)
                         if candidate[i:i+4] != expected[i:i+4]]
                (output / (name + '.diff.txt')).write_text('\n'.join(diffs))
                result.update(status='match' if exact else 'different', exact_match=exact,
                              candidate_size=len(candidate), relocations=relocs,
                              object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest())
            except (ValueError, IndexError) as error:
                result.update(status='relocation_error', error=str(error))
        results.append(result)
        if index % 50 == 0 or index == len(entries):
            print(f'{index}/{len(entries)} checked: {dict(collections.Counter(x["status"] for x in results))}', flush=True)
    sources = {entry['source'] for entry in entries} | {
        'analysis/matching-adaptations.json', 'tools/check_new_matching.py'}
    report = dict(dol_sha256=manifest['dol_sha256'],
                  scope='Direct-memory adaptations of semantic C; full relocated function byte comparison, no linked rebuild',
                  compiler_sha256=hashlib.sha256(cc.read_bytes()).hexdigest(),
                  runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
                  model_hashes={path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sorted(sources)},
                  checked=len(results), matched=sum(x['exact_match'] for x in results),
                  matched_bytes=sum(x['original_size'] for x in results if x['exact_match']), results=results)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{report["matched"]}/{len(results)} exact matches, {report["matched_bytes"]} bytes; {output / "report.json"}')
    if any(x['status'].endswith('_error') for x in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
