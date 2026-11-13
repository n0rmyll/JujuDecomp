"""Small independent pixel fixtures for GX tile order, palettes, alpha, and bounds."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from decode_textures import decode_pixels, png_bytes, archive_report


def record(flags, width, height, pixel=128, palette=0):
    value = bytearray(72)
    struct.pack_into('>I', value, 0, flags)
    struct.pack_into('>I', value, 12, pixel)
    struct.pack_into('>HH', value, 16, width, height)
    struct.pack_into('>I', value, 28, palette)
    return value


class TextureTests(unittest.TestCase):
    def test_rgba_planes_and_tile_order(self):
        # Two adjacent tiles, each with independently chosen AR and GB planes.
        tile1 = bytes([40, 10])*16+bytes([20, 30])*16
        tile2 = bytes([80, 50])*16+bytes([60, 70])*16
        w, h, fmt, pixels = decode_pixels(bytes(128)+tile1+tile2, record(0x1c, 8, 4))
        self.assertEqual((w, h, fmt), (8, 4, 'RGBA8'))
        for y in range(4):
            self.assertEqual(pixels[y*32:y*32+16], bytes([10, 20, 30, 40])*4)
            self.assertEqual(pixels[y*32+16:y*32+32], bytes([50, 60, 70, 80])*4)

    def test_c4_nibbles_and_palette(self):
        palette = struct.pack('>16H', 0xfc00, 0x00f0, *([0]*14))
        _, _, fmt, pixels = decode_pixels(bytes(128)+bytes([0x01])*32+palette,
                                         record(8, 8, 8, palette=160))
        self.assertEqual(fmt, 'C4')
        self.assertEqual(pixels[:8], bytes([255, 0, 0, 255, 0, 255, 0, 0]))

    def test_cmpr_quadrants(self):
        # Four constant-color subblocks must occupy TL, TR, BL, BR.
        blocks = b''.join(struct.pack('>HHI', v, 0, 0) for v in (0xf800, 0x07e0, 0x001f, 0xffff))
        _, _, _, pixels = decode_pixels(bytes(128)+blocks, record(5, 8, 8))
        for x, y, color in ((0, 0, (255, 0, 0, 255)), (4, 0, (0, 255, 0, 255)),
                            (0, 4, (0, 0, 255, 255)), (4, 4, (255, 255, 255, 255))):
            self.assertEqual(pixels[(y*8+x)*4:(y*8+x)*4+4], bytes(color))

    def test_reject_bad_ranges_and_unknown_format(self):
        for value in (record(0x1c, 4, 4), record(7, 4, 4), record(5, 0, 8),
                      record(8, 8, 8, palette=1000)):
            with self.assertRaises(ValueError):
                decode_pixels(bytes(160), value)

    def test_standalone_signature_preserves_original_hash(self):
        import hashlib
        header = bytearray(32)
        header[8:12] = b'GCN\0'
        struct.pack_into('>4I', header, 16, 0x100, 0, 0, 0)
        data = b'8      \n'+header
        report = archive_report(data)
        self.assertEqual(report['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(report['chunk_count'], 0)

    def test_png_roundtrip_and_crcs(self):
        import zlib
        pixels = bytes([1, 2, 3, 4, 5, 6, 7, 8])
        png = png_bytes(2, 1, pixels)
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        cursor = 8
        while cursor < len(png):
            size = struct.unpack_from('>I', png, cursor)[0]
            kind = png[cursor+4:cursor+8]
            data = png[cursor+8:cursor+8+size]
            crc = struct.unpack_from('>I', png, cursor+8+size)[0]
            self.assertEqual(crc, zlib.crc32(kind+data))
            if kind == b'IDAT':
                self.assertEqual(zlib.decompress(data), b'\0'+pixels)
            cursor += size+12


if __name__ == '__main__':
    unittest.main()
