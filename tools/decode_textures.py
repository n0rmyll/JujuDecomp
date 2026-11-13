#!/usr/bin/env python3
"""Export base-level GJUE78 DBU/DBL textures to PNG using only Python stdlib."""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import zlib
from inspect_dbu import inspect

ROOT = Path(__file__).resolve().parents[1]


def archive_report(data):
    # Standalone GCN DBLs share the verified chunk layout but use GCN\0 magic.
    start = int(data[:8].strip())
    if data[start+8:start+12] == b'GCN\0':
        patched = bytearray(data)
        patched[start+8:start+10] = b'DB'
        report = inspect(patched)
        report['sha256'] = hashlib.sha256(data).hexdigest()
        report['signature'] = 'GCN'
        return report
    report = inspect(data)
    report['signature'] = 'DB'
    return report


def gx_format(flags):
    mode, depth = flags & 0x38, flags & 7
    if mode == 0 and depth == 5:
        return 'CMPR'
    if mode == 0 and depth == 2:
        return 'RGB565'
    if mode in (8, 0x28) and depth in (0, 1):
        return 'C4' if depth == 0 else 'C8'
    if mode == 0x18 and depth == 2:
        return 'RGB5A3'
    if mode == 0x18 and depth == 4:
        return 'CMPR' if flags & 0x8000 else 'RGBA8'
    if mode == 0x10 and depth in (1, 2):
        return 'IA4' if depth == 1 else 'IA8'
    raise ValueError(f'Unsupported texture flags {flags:#x}')


def expand(value, bits):
    return (value << (8-bits)) | (value >> (2*bits-8)) if bits >= 4 else (value << 5) | (value << 2) | (value >> 1)


def rgb565(v):
    return (expand(v >> 11, 5), expand((v >> 5) & 63, 6), expand(v & 31, 5), 255)


def rgb5a3(v):
    if v & 0x8000:
        return (expand((v >> 10) & 31, 5), expand((v >> 5) & 31, 5), expand(v & 31, 5), 255)
    return (17*((v >> 8) & 15), 17*((v >> 4) & 15), 17*(v & 15), expand(v >> 12, 3))


def checked_slice(data, offset, length):
    if offset <= 0 or offset+length > len(data):
        raise ValueError(f'Pixel/palette range outside payload: {offset:#x}+{length:#x}')
    return data[offset:offset+length]


def decode_pixels(data, record):
    flags, _, _, pixel = struct.unpack_from('>4I', record)
    width, height = struct.unpack_from('>HH', record, 0x10)
    palette_offset = struct.unpack_from('>I', record, 0x1c)[0]
    if not 0 < width <= 4096 or not 0 < height <= 4096:
        raise ValueError('Invalid dimensions')
    fmt = gx_format(flags)
    bw, bh, size = {'C4': (8, 8, 32), 'C8': (8, 4, 32),
                    'CMPR': (8, 8, 32), 'RGBA8': (4, 4, 64),
                    'RGB565': (4, 4, 32), 'RGB5A3': (4, 4, 32),
                    'IA4': (8, 4, 32), 'IA8': (4, 4, 32)}[fmt]
    raw = checked_slice(data, pixel, ((width+bw-1)//bw)*((height+bh-1)//bh)*size)
    palette = None
    if fmt in ('C4', 'C8'):
        count = 16 if fmt == 'C4' else 256
        pal = checked_slice(data, palette_offset, count*2)
        # fn_80182F8C selects IA8 for mode 0x28, RGB565 for bit 0x8000,
        # otherwise RGB5A3. IA8 stores alpha then intensity.
        mode = flags & 0x38
        palette = []
        for i in range(count):
            v = int.from_bytes(pal[i*2:i*2+2], 'big')
            palette.append((v & 255,)*3+(v >> 8,) if mode == 0x28 else
                           rgb565(v) if flags & 0x8000 else rgb5a3(v))
    out = bytearray(width*height*4)

    def put(x, y, color):
        if x < width and y < height:
            pos = (y*width+x)*4
            out[pos:pos+4] = bytes(color)

    cursor = 0
    for ty in range(0, height, bh):
        for tx in range(0, width, bw):
            block = raw[cursor:cursor+size]
            cursor += size
            if fmt == 'CMPR':
                for sub in range(4):
                    b = block[sub*8:sub*8+8]
                    c0, c1 = struct.unpack_from('>HH', b)
                    a, bcolor = rgb565(c0), rgb565(c1)
                    if c0 > c1:
                        # GX uses 3/8 and 5/8 weights rather than desktop DXT1 thirds.
                        colors = [a, bcolor,
                                  tuple((5*a[k]+3*bcolor[k])//8 for k in range(3))+(255,),
                                  tuple((3*a[k]+5*bcolor[k])//8 for k in range(3))+(255,)]
                    else:
                        avg = tuple(a[k]+(bcolor[k]-a[k])//2 if bcolor[k]>=a[k]
                                    else a[k]-((a[k]-bcolor[k])//2) for k in range(3))
                        colors = [a, bcolor, avg+(255,), avg+(0,)]
                    for y in range(4):
                        for x in range(4):
                            put(tx+(sub%2)*4+x, ty+(sub//2)*4+y, colors[(b[4+y] >> (6-x*2)) & 3])
                continue
            for y in range(bh):
                for x in range(bw):
                    i = y*bw+x
                    if fmt == 'C4':
                        color = palette[(block[i//2] >> (4 if i%2 == 0 else 0)) & 15]
                    elif fmt == 'C8':
                        color = palette[block[i]]
                    elif fmt == 'RGBA8':
                        color = (block[2*i+1], block[32+2*i], block[33+2*i], block[2*i])
                    elif fmt == 'IA4':
                        color = (17*(block[i] & 15),)*3+(17*(block[i] >> 4),)
                    elif fmt == 'IA8':
                        color = (block[2*i+1],)*3+(block[2*i],)
                    else:
                        v = int.from_bytes(block[2*i:2*i+2], 'big')
                        color = rgb565(v) if fmt == 'RGB565' else rgb5a3(v)
                    put(tx+x, ty+y, color)
    return width, height, fmt, bytes(out)


def png_bytes(width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
    scanlines = b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>2I5B', width, height, 8, 6, 0, 0, 0))
            +chunk(b'IDAT', zlib.compress(scanlines))+chunk(b'IEND', b''))


def write_gallery(output, entries):
    cards = []
    for row in entries:
        label = f'{Path(row["archive"]).name} / {row["name"]}'
        src = html.escape(row['png'], quote=True)
        cards.append(f'<figure><a href="{src}"><img loading="lazy" src="{src}" alt=""></a>'
                     f'<figcaption>{html.escape(label)}<br>{row["width"]} × {row["height"]} · '
                     f'{row["format"]}</figcaption></figure>')
    document = '''<!doctype html><meta charset="utf-8"><title>Tak texture exports</title>
<style>body{background:#17191e;color:#eee;font:14px system-ui;margin:24px}
input{padding:12px;width:min(600px,90%);margin-bottom:24px}main{display:grid;
grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
figure{margin:0;background:#282c34;padding:12px;overflow-wrap:anywhere}
img{width:100%;height:180px;object-fit:contain;background:repeating-conic-gradient(#555 0% 25%,#444 0% 50%) 0/16px 16px}
figcaption{margin-top:8px}figure[hidden]{display:none}</style>
<h1>Tak texture exports</h1><p>Base texture levels; repeated resources are retained by archive.
See manifest.json for source offsets and unresolved records.</p>
<input id="search" placeholder="Filter by archive or texture name" aria-label="Filter textures">
<main>''' + ''.join(cards) + '''</main><script>
const cards=[...document.querySelectorAll('figure')];
document.querySelector('#search').addEventListener('input',e=>{
 const q=e.target.value.toLowerCase();
 for(const c of cards)c.hidden=!c.textContent.toLowerCase().includes(q);
});</script>'''
    (output/'index.html').write_text(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'assets/disc')
    parser.add_argument('--output', type=Path, default=ROOT/'assets/textures')
    args = parser.parse_args()
    paths = [args.source] if args.source.is_file() else sorted(
        p for p in args.source.rglob('*') if p.suffix.lower() in ('.dbu', '.dbl'))
    if not paths:
        parser.error('No DBU/DBL files found')
    args.output.mkdir(parents=True, exist_ok=True)
    entries, errors, archives = [], [], []
    for path in paths:
        data = path.read_bytes()
        try:
            report = archive_report(data)
        except (ValueError, struct.error) as error:
            errors.append(dict(archive=str(path), error=str(error)))
            continue
        archives.append(dict(archive=str(path), sha256=report['sha256'], chunks=report['chunk_count']))
        for chunk in report['chunks']:
            if int(chunk['type'], 16) not in (0x82, 0x86):
                continue
            start, size = chunk['payload_offset'], chunk['payload_size']
            payload = data[start:start+size]
            count = struct.unpack_from('>I', payload)[0] if len(payload) >= 4 else 0
            if len(payload) < 0x38 or 0x38+count*0x48 > size:
                errors.append(dict(archive=str(path), chunk=chunk['index'], error='Invalid texture directory'))
                continue
            for i in range(count):
                record = payload[0x38+i*0x48:0x38+(i+1)*0x48]
                name = record[0x28:0x48].split(b'\0', 1)[0].decode('ascii', errors='replace')
                row = dict(archive=str(path), chunk=chunk['index'], index=i, name=name,
                           payload_offset=start, record_offset=start+0x38+i*0x48,
                           path_hint=chunk.get('preceding_path_marker'))
                try:
                    width, height, fmt, pixels = decode_pixels(payload, record)
                    # Disc paths/names are metadata only; never used directly as paths.
                    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)[:64] or 'unnamed'
                    relative = Path(path.parent.name)/path.name/f'{chunk["index"]:04d}_{i:04d}_{safe}.png'
                    target = args.output/relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(png_bytes(width, height, pixels))
                    row.update(width=width, height=height, format=fmt, png=relative.as_posix(),
                               rgba_sha256=hashlib.sha256(pixels).hexdigest())
                    entries.append(row)
                except (ValueError, struct.error) as error:
                    errors.append(dict(**row, error=str(error)))
        print(f'{path.name}: processed', flush=True)
    result = dict(base_level_only=True, archives=archives, textures=entries, errors=errors,
                  formats=dict(Counter(row['format'] for row in entries)))
    (args.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    write_gallery(args.output, entries)
    print(f'Exported {len(entries)} PNGs; {len(errors)} errors; formats: {result["formats"]}')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
