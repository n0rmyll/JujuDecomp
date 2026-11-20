import struct
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_rebuild_foundation import compare_dols, dol_layout


def synthetic_dol():
    data = bytearray(0x120)
    for base, value in ((0, 0x100), (0x48, 0x80003100), (0x90, 8),
                        (7 * 4, 0x110), (0x48 + 7 * 4, 0x80004000), (0x90 + 7 * 4, 4),
                        (0xD8, 0x80005000), (0xDC, 16), (0xE0, 0x80003100)):
        struct.pack_into('>I', data, base, value)
    data[0x100:0x108] = b'CODETEST'
    data[0x110:0x114] = b'DATA'
    return data


class RebuildFoundationTests(unittest.TestCase):
    def test_exact_roundtrip_reports_sections_entry_and_bss(self):
        data = synthetic_dol()
        result = compare_dols(data, bytes(data))
        self.assertEqual(result['entry'], '0x80003100')
        self.assertEqual(result['bss_size'], 16)
        self.assertEqual(result['initialized_bytes'], 12)
        self.assertEqual([s['kind'] for s in result['sections']], ['text', 'data'])

    def test_payload_difference_is_not_masked(self):
        data = synthetic_dol()
        changed = bytearray(data)
        changed[0x102] ^= 1
        with self.assertRaisesRegex(ValueError, '0x102'):
            compare_dols(data, changed)

    def test_header_padding_and_trailing_bytes_are_compared(self):
        data = synthetic_dol()
        for offset in (0xE8, 0x108, 0x11F):
            changed = bytearray(data)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'roundtrip differs'):
                compare_dols(data, changed)
        with self.assertRaisesRegex(ValueError, 'roundtrip differs'):
            compare_dols(data, data + b'\0')

    def test_truncated_header_and_sections_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            dol_layout(b'\0' * 255)
        with self.assertRaisesRegex(ValueError, 'Invalid initialized section'):
            dol_layout(synthetic_dol()[:0x112])

    def test_overlapping_file_and_memory_sections_are_rejected(self):
        for offset, value, message in ((7 * 4, 0x104, 'offset'),
                                       (0x48 + 7 * 4, 0x80003104, 'address')):
            changed = synthetic_dol()
            struct.pack_into('>I', changed, offset, value)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                dol_layout(changed)

    def test_partial_unused_section_and_wrapped_address_are_rejected(self):
        changed = synthetic_dol()
        struct.pack_into('>I', changed, 2 * 4, 0x100)
        with self.assertRaisesRegex(ValueError, 'Invalid initialized section'):
            dol_layout(changed)
        changed = synthetic_dol()
        struct.pack_into('>I', changed, 0x48, 0xFFFFFFFC)
        with self.assertRaisesRegex(ValueError, 'Wrapped'):
            dol_layout(changed)


if __name__ == '__main__':
    unittest.main()
