#!/usr/bin/env python3
"""Extract local disc resources and inventory their original bytes (no decoding)."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", type=Path)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    output = ROOT / "assets" / "disc"
    if not args.inventory_only:
        if args.image is None or not args.image.is_file():
            parser.error("supply a local disc image, or use --inventory-only")
        output.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(ROOT / "tools" / "dtk"), "vfs", "cp", "-q",
                        f"{args.image.resolve()}:files/data_gcn", str(output) + "/"],
                       check=True)
    if not output.is_dir():
        parser.error("no extracted assets/disc directory")
    records = []
    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            magic = stream.read(16)
            digest.update(magic)
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        records.append(dict(path=path.relative_to(output).as_posix(),
                            size=path.stat().st_size, sha256=digest.hexdigest(),
                            prefix_hex=magic.hex()))
    counts = Counter(Path(row["path"]).suffix.lower() for row in records)
    report = dict(source="files/data_gcn", decoded=False, files=len(records),
                  bytes=sum(row["size"] for row in records),
                  extensions=dict(sorted(counts.items())), entries=records)
    manifest = ROOT / "assets" / "manifest.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "entries"}, indent=2))
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
