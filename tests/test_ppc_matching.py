"""Guard exact matching against relocation and function-boundary false positives."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'ppc_matching', Path(__file__).resolve().parents[1] / 'tools/ppc_matching.py')
PPC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PPC)


def elf_object(text, size, relocations=()):
    """Tiny synthetic ELF with a named function and one undefined symbol."""
    names = b'\0fn_80001000\0external\0'
    symbols = (bytes(16) + struct.pack('>IIIBBH', 1, 0, size, 0x12, 0, 1)
               + struct.pack('>IIIBBH', 13, 0, 0, 0x10, 0, 0))
    rela = b''.join(struct.pack('>IIi', off, 2 << 8 | kind, addend)
                    for off, kind, addend in relocations)
    payloads = [b'', text, symbols, names, rela, b'\0']
    types = [0, 1, 2, 3, 4, 3]
    header = bytearray(52)
    header[:7] = b'\x7fELF\x01\x02\x01'
    struct.pack_into('>HHI', header, 16, 1, 20, 1)
    sections = []
    body = bytearray()
    for i, payload in enumerate(payloads):
        sections.append(struct.pack('>10I', 0, types[i], 6 if i == 1 else 0,
                                    0, 52 + len(body), len(payload),
                                    3 if i == 2 else (2 if i == 4 else 0),
                                    1 if i == 4 else 0, 1,
                                    16 if i == 2 else (12 if i == 4 else 0)))
        body.extend(payload)
    struct.pack_into('>I', header, 32, 52 + len(body))
    struct.pack_into('>HHHHHH', header, 40, 52, 0, 0, 40, len(sections), 5)
    return bytes(header + body + b''.join(sections))


class RelocationTests(unittest.TestCase):
    def test_rel24_forward_and_backward_preserve_link(self):
        for target, expected in ((0x80001020, 0x48000021), (0x80000fe0, 0x4bffffe1)):
            code = bytearray.fromhex('48000001')
            PPC.relocate(code, 0, 10, target, 0x80001000)
            self.assertEqual(struct.unpack('>I', code)[0], expected)

    def test_high_adjusted_carry_and_low(self):
        code = bytearray(4)
        PPC.relocate(code, 0, 6, 0x802ef19c, 0)
        PPC.relocate(code, 2, 4, 0x802ef19c, 0)
        self.assertEqual(code.hex(), '802ff19c')

    def test_small_data_register_and_signed_displacement(self):
        code = bytearray.fromhex('88600000')
        PPC.relocate(code, 0, 109, 0x803312fc, 0)
        self.assertEqual(code.hex(), '886d907c')
        code = bytearray.fromhex('c0200000')
        PPC.relocate(code, 0, 109, 0x80333140, 0)
        self.assertEqual(code.hex(), 'c0228000')

    def test_invalid_relocations_fail(self):
        for off, kind, target in ((0, 99, 0), (0, 10, 0x84000000),
                                  (0, 10, 0x80001001), (0, 109, 0x80200000),
                                  (3, 6, 0x80001000)):
            with self.subTest(kind=kind, off=off, target=target), self.assertRaises(ValueError):
                PPC.relocate(bytearray.fromhex('48000001'), off, kind, target, 0x80001000)

    def parse(self, raw, symbols=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.o'
            path.write_bytes(raw)
            return PPC.function_code(path, 'fn_80001000', 0x80001000, symbols or {})

    def test_extracts_symbol_size_excluding_neighbor_and_padding(self):
        code, relocations = self.parse(elf_object(bytes.fromhex('4e800020deadbeef'), 4))
        self.assertEqual(code.hex(), '4e800020')
        self.assertEqual(relocations, [])

    def test_applies_addend_and_resolves_branch_without_masking(self):
        raw = elf_object(bytes.fromhex('480000014e800020'), 8, [(0, 10, 4)])
        code, relocations = self.parse(raw, {'external': 0x80001020})
        self.assertEqual(code.hex(), '480000254e800020')
        self.assertEqual(len(relocations), 1)

    def test_unresolved_and_unsupported_relocations_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unresolved symbol'):
            self.parse(elf_object(bytes.fromhex('48000001'), 4, [(0, 10, 0)]))
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            self.parse(elf_object(bytes(4), 4, [(0, 99, 0)]), {'external': 0})

    def test_invalid_function_range_rejected(self):
        with self.assertRaisesRegex(ValueError, 'function range'):
            self.parse(elf_object(bytes(4), 8))


if __name__ == '__main__':
    unittest.main()
