#!/usr/bin/env python3
"""Check the host model and original bytes; optionally compare a PPC compile."""
import argparse
import hashlib
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASH = '49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706'
EXPECTED_CODE = bytes.fromhex('38000001 98030004 4e800020')


def original_code(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_HASH:
        raise ValueError('Unexpected executable revision')
    address = 0x8020f9c8
    for index in range(7):
        offset, start, size = (
            struct.unpack_from('>I', data, base + index * 4)[0]
            for base in (0, 0x48, 0x90)
        )
        if start <= address and address + 12 <= start + size:
            return data[offset + address - start:offset + address - start + 12]
    raise ValueError('Original function is not backed by a DOL text section')


def object_text(path):
    data = path.read_bytes()
    if data[:6] != b'\x7fELF\x01\x02':
        raise ValueError('Expected a 32-bit big-endian ELF object')
    if struct.unpack_from('>HH', data, 16) != (1, 20):
        raise ValueError('Expected a relocatable PowerPC object')
    table = struct.unpack_from('>I', data, 32)[0]
    stride, count, names_index = struct.unpack_from('>HHH', data, 46)
    sections = [struct.unpack_from('>10I', data, table + i * stride)
                for i in range(count)]
    names = sections[names_index]
    strings = data[names[4]:names[4] + names[5]]
    for section in sections:
        name = strings[section[0]:].split(b'\0', 1)[0]
        if section[1] in (4, 9) and section[7] < count:
            target = sections[section[7]]
            target_name = strings[target[0]:].split(b'\0', 1)[0]
            if target_name == b'.text' and section[5]:
                raise ValueError('Text relocations require a relocation-aware diff')
        if name == b'.text':
            text_section = section
    if 'text_section' not in locals():
        raise ValueError('No .text section found')
    return data[text_section[4]:text_section[4] + text_section[5]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc', default='clang', help='Host C compiler executable')
    parser.add_argument('--dol', type=Path, default=ROOT / 'analysis/main.dol')
    parser.add_argument('--ppc-cc', help='Optional Clang with the PowerPC backend')
    args = parser.parse_args()
    build = ROOT / 'build/application-flag'
    build.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/recovered/application_flag.c'
    executable = build / 'behavior-test'
    subprocess.run([args.cc, '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-O2', str(source), str(ROOT / 'tests/application_flag.c'),
                    '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
    if original_code(args.dol) != EXPECTED_CODE:
        raise ValueError('Original stop setter differs from the recorded instructions')
    print('PASS: original DOL identity and stop-setter instructions', flush=True)
    if not args.ppc_cc:
        print('SKIP: compiled PowerPC comparison (supply --ppc-cc)')
        return
    obj = build / 'application_flag.o'
    subprocess.run([args.ppc_cc, '--target=powerpc-unknown-eabi', '-ffreestanding',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
                    '-O2', '-c', str(source), '-o', str(obj)], check=True)
    candidate = object_text(obj)
    if candidate != EXPECTED_CODE:
        raise ValueError(f'PowerPC .text differs: {candidate.hex(" ")}; '
                         f'expected {EXPECTED_CODE.hex(" ")}')
    print('PASS: compiled PowerPC .text exactly matches the original 12 bytes')


if __name__ == '__main__':
    main()
