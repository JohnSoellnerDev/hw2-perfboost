#!/usr/bin/env python3
"""Package HW2-PerfBoost into a clean, ready-to-publish release archive with SHA-256 checksums."""

import argparse
import hashlib
import zipfile
from pathlib import Path

INCLUDE_FILES = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "install.bat",
    "install.sh",
    "configs/Optional_Engine_Tweaks.ini",
    "docs/TECHNICAL_ANALYSIS.md",
    "docs/BENCHMARKS.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Create HW2-PerfBoost release zip")
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    root = args.root.resolve()
    out_dir = (args.out_dir or (root / "build")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / f"HW2-PerfBoost-v{args.version}.zip"
    paks = sorted((root / "presets").glob("HW2PerfBoost_*_P.pak"))
    assert paks, f"No preset .pak files found in {root / 'presets'}"

    checksums = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in INCLUDE_FILES:
            fp = root / rel
            if fp.exists():
                zf.write(fp, arcname=f"HW2-PerfBoost/{rel}")
        for pak in paks:
            rel = f"presets/{pak.name}"
            zf.write(pak, arcname=f"HW2-PerfBoost/{rel}")
            checksums.append(f"{sha256_file(pak)}  {pak.name}")

    checksums.append(f"{sha256_file(zip_path)}  {zip_path.name}")
    sums_path = out_dir / "SHA256SUMS.txt"
    sums_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")

    print(f"Packaged: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    print(f"Checksums: {sums_path}")
    print(sums_path.read_text())


if __name__ == "__main__":
    main()
