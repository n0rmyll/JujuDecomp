#!/usr/bin/env python3
"""Decode standard mono Nintendo DSP ADPCM files to 16-bit PCM WAV."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import struct
import wave

ROOT = Path(__file__).resolve().parents[1]


def decode_dsp(data):
    if len(data) < 96:
        raise ValueError('Truncated DSP header')
    samples, nibbles, rate, loop, codec, loop_start, loop_end, initial = struct.unpack_from('>3I2H3I', data)
    if not 0 < samples <= 100_000_000 or not 5000 <= rate <= 48000:
        raise ValueError('Invalid sample count or rate')
    if codec != 0 or loop not in (0, 1) or initial != 2:
        raise ValueError('Unsupported DSP encoding or initial offset')
    expected_nibbles = samples//14*16+(samples%14+2 if samples%14 else 0)
    if nibbles != expected_nibbles or len(data) != 96+(nibbles+1)//2:
        raise ValueError('Sample/nibble count or file length mismatch')
    coefs = struct.unpack_from('>16h', data, 28)
    gain, initial_ps, hist1, hist2 = struct.unpack_from('>2H2h', data, 60)
    if gain != 0 or initial_ps != data[96]:
        raise ValueError('Unsupported gain or inconsistent initial predictor')
    if loop and not 2 <= loop_start <= loop_end < nibbles:
        raise ValueError('Invalid loop range')
    pcm = bytearray(samples*2)
    peak = clipped = 0
    for index in range(samples):
        frame, slot = divmod(index, 14)
        base = 96+frame*8
        control = data[base]
        predictor, scale = control >> 4, 1 << (control & 15)
        if predictor > 7:
            raise ValueError(f'Invalid predictor in frame {frame}')
        packed = data[base+1+slot//2]
        value = (packed >> (4 if slot%2 == 0 else 0)) & 15
        if value >= 8:
            value -= 16
        value = (value*scale*2048+1024+coefs[2*predictor]*hist1+coefs[2*predictor+1]*hist2) >> 11
        clipped += value < -32768 or value > 32767
        value = max(-32768, min(32767, value))
        struct.pack_into('<h', pcm, index*2, value)
        peak = max(peak, abs(value))
        hist2, hist1 = hist1, value
    return bytes(pcm), dict(samples=samples, sample_rate=rate, channels=1,
                            duration_seconds=samples/rate, loop=bool(loop),
                            loop_start_nibble=loop_start, loop_end_nibble=loop_end,
                            peak=peak, clipped_samples=clipped)


def write_gallery(output, entries):
    rows = []
    for entry in entries:
        src = html.escape(entry['wav'], quote=True)
        name = html.escape(entry['source'])
        rows.append(f'<article><p>{name} · {entry["duration_seconds"]:.2f}s</p>'
                    f'<audio controls preload="none" src="{src}"></audio>'
                    f' <a href="{src}">WAV</a></article>')
    document = '''<!doctype html><meta charset="utf-8"><title>Tak audio exports</title>
<style>body{background:#17191e;color:#eee;font:16px system-ui;margin:32px}a{color:#9cf}
input{padding:12px;width:min(600px,90%)}article{padding:8px;border-bottom:1px solid #444}
article[hidden]{display:none}audio{width:min(500px,90%)}</style>
<h1>Tak audio exports</h1><p>Standalone DSP files decoded to mono PCM WAV, without resampling.</p>
<input id="search" placeholder="Filter by filename" aria-label="Filter audio">
<main>'''+''.join(rows)+'''</main><script>
const rows=[...document.querySelectorAll('article')];
document.querySelector('#search').addEventListener('input',e=>{
 for(const r of rows)r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase());
});</script>'''
    (output/'index.html').write_text(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'assets/disc')
    parser.add_argument('--output', type=Path, default=ROOT/'assets/audio')
    args = parser.parse_args()
    paths = [args.source] if args.source.is_file() else sorted(
        p for p in args.source.rglob('*') if p.suffix.lower() == '.dsp')
    if not paths:
        parser.error('No DSP files found')
    args.output.mkdir(parents=True, exist_ok=True)
    entries, errors = [], []
    for path in paths:
        relative = Path(path.name) if args.source.is_file() else path.relative_to(args.source)
        try:
            data = path.read_bytes()
            pcm, info = decode_dsp(data)
            wav = relative.with_suffix('.wav')
            target = args.output/wav
            target.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(target), 'wb') as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(info['sample_rate'])
                stream.writeframes(pcm)
            entries.append(dict(source=relative.as_posix(), wav=wav.as_posix(),
                                source_sha256=hashlib.sha256(data).hexdigest(),
                                pcm_sha256=hashlib.sha256(pcm).hexdigest(), **info))
        except (ValueError, struct.error) as error:
            errors.append(dict(source=relative.as_posix(), error=str(error)))
    result = dict(codec='Nintendo DSP ADPCM', output='16-bit little-endian PCM WAV',
                  files=len(entries), duration_seconds=sum(e['duration_seconds'] for e in entries),
                  entries=entries, errors=errors,
                  limitations='Standalone mono DSP only. Loop metadata retained in manifest; WAVs play once. DBA banks and ADP music are not decoded.')
    (args.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    write_gallery(args.output, entries)
    print(f'Exported {len(entries)} WAVs ({result["duration_seconds"] / 60:.2f} minutes); {len(errors)} errors.')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
