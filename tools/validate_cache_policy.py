#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

runtime = ROOT / "assets" / "sports-passport-data.js"
bootstrap = ROOT / "assets" / "route-bootstrap.js"
manifest = ROOT / "data" / "cache-manifest.json"

if not runtime.is_file():
    errors.append("missing shared data runtime")
else:
    text = runtime.read_text(encoding="utf-8")
    for token in (
        "data/cache-manifest.json",
        "cache:'no-cache'",
        'cache:"force-cache"',
        "versionedDataRequest",
        "fetchJson",
    ):
        if token not in text:
            errors.append(f"shared data runtime missing cache-policy token: {token}")
    if "no-store" in text:
        errors.append("shared data runtime must not bypass the browser cache with no-store")
    if not re.search(r"searchParams\.set\(['\"]v['\"]", text):
        errors.append("shared data runtime must version JSON request URLs")

if not bootstrap.is_file():
    errors.append("missing compatibility route bootstrap")
else:
    text = bootstrap.read_text(encoding="utf-8")
    if "no-store" in text:
        errors.append("compatibility route bootstrap must not use no-store")
    if "cache:'no-cache'" not in text and 'cache:"no-cache"' not in text:
        errors.append("compatibility route bootstrap should revalidate fallback templates")

if not manifest.is_file():
    errors.append("missing data/cache-manifest.json")
else:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            errors.append("cache manifest schema_version must be 1")
        version = data.get("version", "")
        if not re.fullmatch(r"[0-9a-f]{20}", version):
            errors.append("cache manifest version must be a 20-character lowercase SHA-256 prefix")
        if data.get("strategy") != "revalidated-manifest-versioned-data":
            errors.append("cache manifest strategy is not the expected versioned-data policy")
        source_count = len([p for p in (ROOT / "data").glob("*.json") if p.name != "cache-manifest.json"])
        if data.get("json_file_count") != source_count:
            errors.append(f"cache manifest json_file_count is stale: expected {source_count}, found {data.get('json_file_count')}")
    except Exception as exc:
        errors.append(f"could not parse cache manifest: {exc}")

if errors:
    print("\n".join("ERROR: " + error for error in errors))
    sys.exit(1)
print("OK: revalidated manifest + versioned JSON caching policy validated; no no-store archive fetches remain.")
