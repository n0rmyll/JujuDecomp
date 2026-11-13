#!/usr/bin/env python3
"""Install pinned local CodeWarrior 1.3.2 and wibo; no system installation."""
import argparse
import hashlib
from pathlib import Path
import platform
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMPILERS_URL = 'https://files.decomp.dev/compilers_20251015.zip'
COMPILERS_HASH = '491cb62317c7f3669ac283ae159e82e3c97a5713b78299571ba4cf023dc7e95e'
COMPILER_HASH = '7cbae0a5bd81e07d7fa8975bbc4e969b5dea265cc29c5ee6bae0453a6e25f225'
RUNNERS = {
    ('Darwin', 'x86_64'): ('wibo-macos', '2b3000ef6a7a490c24ccd71967735ae0005e218922e51806cca1b8d77fd3cf7c'),
    ('Linux', 'x86_64'): ('wibo-x86_64', '13f86a2d618f0dbe67179d349625345eabf9b46450295cb4c904e49f6aff85af'),
}


def verify(data, expected):
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError(f'SHA-256 mismatch: expected {expected}, got {actual}')
    return data


def fetch(url, path, expected):
    if path.exists():
        return verify(path.read_bytes(), expected)
    print(f'Downloading {url}', flush=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        data = verify(response.read(), expected)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an existing compiler archive (hash checked)')
    args = parser.parse_args()
    host = (platform.system(), platform.machine())
    if host not in RUNNERS:
        parser.error(f'No pinned runner for {host}; supply a compiler/runner to check_application_flag.py manually')
    artifact, digest = RUNNERS[host]
    runner = ROOT / 'tools/wibo'
    fetch(f'https://github.com/decompals/wibo/releases/download/1.2.0/{artifact}', runner, digest)
    runner.chmod(runner.stat().st_mode | 0o111)
    archive = args.archive or ROOT / 'tools/mwcc/downloads/compilers_20251015.zip'
    if args.archive:
        verify(archive.read_bytes(), COMPILERS_HASH)
    else:
        fetch(COMPILERS_URL, archive, COMPILERS_HASH)
    destination = ROOT / 'tools/mwcc/GC/1.3.2'
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        # Extract only the selected compiler and its companion files, never arbitrary paths.
        for name in ('mwcceppc.exe', 'mwldeppc.exe', 'mwasmeppc.exe', 'lmgr326b.dll'):
            data = bundle.read(f'GC/1.3.2/{name}')
            if name == 'mwcceppc.exe':
                verify(data, COMPILER_HASH)
            (destination / name).write_bytes(data)
    print('Ready: CodeWarrior GC 1.3.2 (2.4.2 build 81), wibo 1.2.0')
    print('python3 tools/check_application_flag.py --mw-cc tools/mwcc/GC/1.3.2/mwcceppc.exe --runner tools/wibo')


if __name__ == '__main__':
    main()
