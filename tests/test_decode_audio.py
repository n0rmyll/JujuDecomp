import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from decode_audio import decode_dsp


def fixture(samples, frames, coefs=None, history=(0, 0)):
    header = bytearray(96)
    nibbles = samples//14*16+(samples%14+2 if samples%14 else 0)
    struct.pack_into('>3I2H3I', header, 0, samples, nibbles, 22050, 0, 0, 2, nibbles-1, 2)
    struct.pack_into('>16h', header, 28, *(coefs or [0]*16))
    struct.pack_into('>2H2h', header, 60, 0, frames[0], *history)
    return header+frames


class AudioTests(unittest.TestCase):
    def test_signed_nibbles_and_partial_frame(self):
        pcm, info = decode_dsp(fixture(3, bytes([0, 0x17, 0x80])))
        self.assertEqual(struct.unpack('<3h', pcm), (1, 7, -8))
        self.assertEqual(info['samples'], 3)
        self.assertEqual(info['sample_rate'], 22050)

    def test_predictor_history_crosses_frames(self):
        coefs = [2048, 0]+[0]*14
        # Predictor adds previous sample; history starts at 100.
        pcm, _ = decode_dsp(fixture(15, bytes([0])+bytes([0x11])*7+bytes([0, 0x10]), coefs, (100, 0)))
        self.assertEqual(struct.unpack('<15h', pcm), tuple(range(101, 116)))

    def test_rounding_and_second_history(self):
        coefs = [1024, 1024]+[0]*14
        pcm, _ = decode_dsp(fixture(2, bytes([0, 0]), coefs, (3, 0)))
        self.assertEqual(struct.unpack('<2h', pcm), (2, 3))

    def test_clipping_and_scale(self):
        pcm, info = decode_dsp(fixture(2, bytes([15, 0x78])))
        self.assertEqual(struct.unpack('<2h', pcm), (32767, -32768))
        self.assertEqual(info['clipped_samples'], 2)

    def test_reject_truncation_and_invalid_headers(self):
        good = fixture(2, bytes([0, 0x10]))
        variants = [good[:20], good[:-1], good+b'\0']
        for offset, value in ((8, b'\0'*4), (14, b'\0\1'), (24, b'\0'*4),
                              (96, b'\x80')):
            bad = bytearray(good)
            bad[offset:offset+len(value)] = value
            variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError):
                decode_dsp(bad)
        bad_frame = fixture(15, bytes(8)+bytes([0x80, 0]))
        with self.assertRaisesRegex(ValueError, 'Invalid predictor'):
            decode_dsp(bad_frame)

    def test_loop_metadata(self):
        data = fixture(14, bytes(8))
        struct.pack_into('>H', data, 12, 1)
        _, info = decode_dsp(data)
        self.assertTrue(info['loop'])
        self.assertEqual((info['loop_start_nibble'], info['loop_end_nibble']), (2, 15))
        struct.pack_into('>I', data, 16, 100)
        with self.assertRaisesRegex(ValueError, 'Invalid loop'):
            decode_dsp(data)


if __name__ == '__main__':
    unittest.main()
