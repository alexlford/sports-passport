#!/usr/bin/env python3
"""Generate a deterministic cache version for all public Sports Passport JSON data."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "cache-manifest.json"


def source_files() -> list[Path]:
    return sorted(
        path for path in DATA.glob("*.json")
        if path.name != OUTPUT.name
    )


def build_version(files: list[Path]) -> str:
    digest = sha256()
    for path in files:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:20]


def main() -> None:
    files = source_files()
    manifest = {
        "schema_version": 1,
        "version": build_version(files),
        "strategy": "revalidated-manifest-versioned-data",
        "json_file_count": len(files),
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated data cache version {manifest['version']} from {len(files)} JSON files.")


if __name__ == "__main__":
    main()
