"""Strict single-function ELF32/PPC relocation for original-address comparison.

No bytes are masked. Unsupported relocations and unresolved symbols fail.
This places one function at its original address; it is not an executable link.
"""
import re
import struct


def relocate(code, offset, kind, target, place):
    """Apply a supported explicit-addend PPC relocation to a bytearray."""
    width = 2 if kind in (4, 5, 6) else 4
    if not 0 <= offset <= len(code) - width:
        raise ValueError('Relocation outside function')
    if kind in (4, 5, 6):  # ADDR16_LO, ADDR16_HI, ADDR16_HA
        value = {4: target, 5: target >> 16, 6: (target + 0x8000) >> 16}[kind]
        struct.pack_into('>H', code, offset, value & 0xffff)
    elif kind == 1:  # ADDR32
        struct.pack_into('>I', code, offset, target & 0xffffffff)
    elif kind == 10:  # REL24
        delta = target - place
        word = struct.unpack_from('>I', code, offset)[0]
        if word >> 26 != 18 or word & 2 or delta % 4 or not -0x2000000 <= delta < 0x2000000:
            raise ValueError('Invalid or out-of-range REL24 branch')
        struct.pack_into('>I', code, offset, (word & 0xfc000003) | (delta & 0x03fffffc))
    elif kind == 109:  # EMB_SDA21; bases verified against DOL startup by caller
        if 0x80330280 <= target < 0x80333140:
            register, base = 13, 0x80338280
        elif 0x80333140 <= target < 0x803378b0:
            register, base = 2, 0x8033b140
        else:
            raise ValueError(f'SDA21 target outside known small-data sections: {target:#x}')
        delta = target - base
        if not -0x8000 <= delta <= 0x7fff:
            raise ValueError('SDA21 displacement out of range')
        word = struct.unpack_from('>I', code, offset)[0]
        struct.pack_into('>I', code, offset, (word & ~0x1fffff) | register << 16 | (delta & 0xffff))
    else:
        raise ValueError(f'Unsupported PPC relocation {kind}')


def function_code(path, name, address, symbols):
    data = path.read_bytes()
    if data[:7] != b'\x7fELF\x01\x02\x01' or struct.unpack_from('>HH', data, 16) != (1, 20):
        raise ValueError('Expected big-endian ELF32 relocatable PPC object')
    table = struct.unpack_from('>I', data, 32)[0]
    stride, count, names_index = struct.unpack_from('>HHH', data, 46)
    if stride != 40 or table + count * stride > len(data) or names_index >= count:
        raise ValueError('Invalid section table')
    sections = [struct.unpack_from('>10I', data, table + i * stride) for i in range(count)]

    def contents(section):
        start, size = section[4:6]
        if start + size > len(data):
            raise ValueError('Truncated ELF section')
        return data[start:start + size]

    def string(strings, offset):
        if offset >= len(strings) or b'\0' not in strings[offset:]:
            raise ValueError('Invalid ELF string')
        return strings[offset:].split(b'\0', 1)[0].decode('ascii')

    tables = {}
    for index, section in enumerate(sections):
        if section[1] == 2:
            if section[9] != 16 or section[5] % 16:
                raise ValueError('Invalid symbol table')
            names = contents(sections[section[6]])
            tables[index] = []
            raw = contents(section)
            for offset in range(0, len(raw), 16):
                symbol = struct.unpack_from('>IIIBBH', raw, offset)
                tables[index].append((string(names, symbol[0]), *symbol[1:]))
    matches = [sym for table in tables.values() for sym in table
               if sym[0] == name and sym[4] & 0xf == 0 and sym[5] not in (0, 0xfff1)]
    # Symbol tuple: name, value, size, info, other, shndx.
    if len(matches) != 1 or matches[0][3] & 0xf != 2:
        raise ValueError(f'Expected one defined function symbol: {name}')
    _, start, size, _, _, section_index = matches[0]
    section = sections[section_index]
    if section[1] != 1 or not section[2] & 4 or not size or start + size > section[5]:
        raise ValueError('Invalid function range')
    code = bytearray(contents(section)[start:start + size])
    applied = []
    for section in sections:
        if section[1] not in (4, 9) or section[7] != section_index:
            continue
        if section[1] != 4 or section[9] != 12 or section[5] % 12:
            raise ValueError('Only explicit-addend ELF32 RELA relocations supported')
        raw = contents(section)
        for pos in range(0, len(raw), 12):
            offset, info, addend = struct.unpack_from('>IIi', raw, pos)
            if not start <= offset < start + size:
                continue
            symbol = tables[section[6]][info >> 8]
            symbol_name, value, _, _, _, symbol_section = symbol
            if symbol_section == 0:
                if symbol_name in symbols:
                    target = symbols[symbol_name]
                elif re.fullmatch(r'(?:fn|lbl)_[0-9A-F]{8}', symbol_name):
                    target = int(symbol_name[-8:], 16)
                else:
                    raise ValueError(f'Unresolved symbol {symbol_name}')
            elif symbol_section == section_index and start <= value < start + size:
                target = address + value - start
            elif symbol_section == 0xfff1:
                target = value
            else:
                raise ValueError(f'No placement for symbol {symbol_name}')
            relative = offset - start
            relocate(code, relative, info & 0xff, target + addend, address + relative)
            applied.append(dict(offset=relative, type=info & 0xff, symbol=symbol_name,
                                target=f'0x{target:08X}', addend=addend))
    return bytes(code), applied
