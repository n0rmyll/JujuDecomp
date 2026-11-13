#!/usr/bin/env python3
"""Decode headerless GameCube DTK .adp music to stereo 48 kHz PCM WAV."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import wave
from decode_audio import write_gallery

ROOT = Path(__file__).resolve().parents[1]


def load_decoder(directory):
    library = Path(directory)/('dtk_audio.dylib' if sys.platform == 'darwin' else 'dtk_audio.so')
    subprocess.run(['clang', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-dynamiclib' if sys.platform == 'darwin' else '-shared', '-fPIC',
                    str(ROOT/'tools/dtk_audio.c'), '-o', str(library)], check=True)
    dll = ctypes.CDLL(str(library))
    function = dll.tak_dtk_decode
    function.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                         ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_int32)]
    function.restype = ctypes.c_int
    return function


def decode_blocks(function, data, state):
    if len(data) % 32:
        raise ValueError('Truncated DTK block')
    source = (ctypes.c_uint8*len(data)).from_buffer_copy(data)
    target = (ctypes.c_uint8*(len(data)//32*112))()
    status = function(source, len(data), target, state)
    if status:
        raise ValueError({-1: 'Truncated DTK block', -2: 'Repeated block headers differ',
                          -3: 'Unsupported predictor or shift'}[status])
    return bytes(target)


def convert(path, target, function):
    size = path.stat().st_size
    if not size or size % 32:
        raise ValueError('Empty stream or truncated DTK block')
    pcm_size = size//32*112
    if pcm_size > 0xffffffff-36:
        raise ValueError('Stream exceeds standard WAV size limit')
    target.parent.mkdir(parents=True, exist_ok=True)
    state = (ctypes.c_int32*4)()
    source_hash, pcm_hash = hashlib.sha256(), hashlib.sha256()
    # Keep an existing completed WAV intact if input validation fails later.
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.wav', delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with path.open('rb') as source, wave.open(str(temporary), 'wb') as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(48000)
            for block in iter(lambda: source.read(1024*1024), b''):
                source_hash.update(block)
                pcm = decode_blocks(function, block, state)
                pcm_hash.update(pcm)
                stream.writeframesraw(pcm)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    samples = size//32*28
    return dict(source_sha256=source_hash.hexdigest(), pcm_sha256=pcm_hash.hexdigest(),
                source_bytes=size, blocks=size//32, samples=samples, channels=2,
                sample_rate=48000, duration_seconds=samples/48000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'assets/disc/stream/music')
    parser.add_argument('--output', type=Path, default=ROOT/'assets/music')
    args = parser.parse_args()
    paths = [args.source] if args.source.is_file() else sorted(
        p for p in args.source.rglob('*') if p.suffix.lower() == '.adp')
    if not paths:
        parser.error('No ADP files found')
    args.output.mkdir(parents=True, exist_ok=True)
    entries, errors = [], []
    with tempfile.TemporaryDirectory(prefix='tak-music-') as directory:
        function = load_decoder(directory)
        for path in paths:
            relative = Path(path.name) if args.source.is_file() else path.relative_to(args.source)
            wav = relative.with_suffix('.wav')
            try:
                info = convert(path, args.output/wav, function)
                entries.append(dict(source=relative.as_posix(), wav=wav.as_posix(), **info))
                print(f'{path.name}: {info["duration_seconds"]:.2f}s', flush=True)
            except (ValueError, OSError) as error:
                errors.append(dict(source=relative.as_posix(), error=str(error)))
    result = dict(codec='Nintendo DTK ADPCM', files=len(entries), entries=entries, errors=errors,
                  duration_seconds=sum(e['duration_seconds'] for e in entries),
                  limitations='Nominal hardware rate 48000 Hz. One pass, no inferred game loop points or trimming.')
    (args.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    write_gallery(args.output, entries)
    gallery = args.output/'index.html'
    gallery.write_text(gallery.read_text().replace('Tak audio exports', 'Tak music exports').replace(
        'Standalone DSP files decoded to mono PCM WAV, without resampling.',
        'Nintendo DTK music decoded to stereo 48 kHz PCM WAV. Original filenames; full streams, no inferred loops.'))
    print(f'Exported {len(entries)} music tracks ({result["duration_seconds"]/60:.2f} minutes); {len(errors)} errors.')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
