"""Independent scalar DTK reference plus native decoder and WAV validation."""
import ctypes
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from decode_music import load_decoder, decode_blocks, convert


def reference(data):
    # Direct signed integer arithmetic, separate from the native block implementation.
    history = [[0, 0], [0, 0]]
    output = []
    for offset in range(0, len(data), 32):
        for packed in data[offset+4:offset+32]:
            for channel in range(2):
                control = data[offset+channel]
                a, b = ((0, 0), (60, 0), (115, 52), (98, 55))[control//16]
                prediction = (a*history[channel][0]-b*history[channel][1]+32)//64
                prediction = min(2097151, max(-2097152, prediction))
                nibble = (packed//(16**channel)) % 16
                nibble = nibble if nibble < 8 else nibble-16
                current = (nibble*4096//(2**(control%16)))*64+prediction
                history[channel] = [current, history[channel][0]]
                output.append(min(32767, max(-32768, current//64)))
    return struct.pack(f'<{len(output)}h', *output)


class MusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='tak-music-tests-')
        cls.function = staticmethod(load_decoder(cls.temp.name))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def decode(self, data, state=None):
        return decode_blocks(self.function, data, state if state is not None else (ctypes.c_int32*4)())

    def test_channels_and_signed_samples(self):
        pcm = self.decode(bytes([12, 12, 12, 12])+bytes([0x81])*28)
        self.assertEqual(struct.unpack('<56h', pcm), (1, -8)*28)

    def test_history_remains_unclipped(self):
        state = (ctypes.c_int32*4)(3_000_000, 0, -3_000_000, 0)
        pcm = self.decode(bytes([0x1c])*4+bytes(28), state)
        self.assertEqual(struct.unpack_from('<2h', pcm), (32767, -32768))
        # Initial prediction clamp feeds high precision history, not PCM16.
        self.assertGreater(state[0], 32767)
        self.assertLess(state[2], -32768)

    def test_all_predictors_shifts_against_scalar_reference(self):
        import random
        randomizer = random.Random(42)
        data = b''
        for predictor in range(4):
            for shift in range(13):
                left, right = predictor*16+shift, (3-predictor)*16+(12-shift)
                data += bytes([left, right, left, right])+bytes(randomizer.randrange(256) for _ in range(28))
        self.assertEqual(self.decode(data), reference(data))
        state = (ctypes.c_int32*4)()
        self.assertEqual(self.decode(data[:32*17], state)+self.decode(data[32*17:], state), reference(data))

    def test_invalid_data_preserves_history(self):
        for data in (bytes(31), bytes([0, 1, 0, 0])+bytes(28),
                     bytes([0x40])*4+bytes(28), bytes([0x0d])*4+bytes(28)):
            state = (ctypes.c_int32*4)(1, 2, 3, 4)
            with self.assertRaises(ValueError):
                self.decode(data, state)
            self.assertEqual(list(state), [1, 2, 3, 4])

    def test_wav_and_atomic_failure(self):
        root = Path(self.temp.name)
        source, output = root/'test.adp', root/'test.wav'
        source.write_bytes(bytes([12])*4+bytes([0x81])*28)
        info = convert(source, output, self.function)
        with wave.open(str(output), 'rb') as stream:
            self.assertEqual((stream.getnchannels(), stream.getframerate(), stream.getnframes()), (2, 48000, 28))
            self.assertEqual(hashlib.sha256(stream.readframes(28)).hexdigest(), info['pcm_sha256'])
        original = output.read_bytes()
        source.write_bytes(bytes([0x40])*4+bytes(28))
        with self.assertRaises(ValueError):
            convert(source, output, self.function)
        self.assertEqual(output.read_bytes(), original)

    def test_real_stream_against_reference(self):
        root = Path(__file__).resolve().parents[1]/'assets/disc/stream/music'
        paths = sorted(root.glob('*.adp'))
        if not paths:
            self.skipTest('Local music assets unavailable')
        for path in paths:
            data = path.read_bytes()[:32*128]
            self.assertEqual(self.decode(data), reference(data), path.name)


if __name__ == '__main__':
    unittest.main()
