#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
errors=[]

def load_json(name, optional=False):
    try:
        return json.loads((DATA/name).read_text(encoding="utf-8"))
    except FileNotFoundError:
        if optional:
            return None
        errors.append(f"could not load data/{name}: file not found")
        return None
    except Exception as exc:
        errors.append(f"could not load data/{name}: {exc}")
        return None

manifest=load_json("events.json") or {}
venues=load_json("venues.json") or []
venue_additions=load_json("venue-additions.json", optional=True) or []
journeys=load_json("journeys.json") or []
phases=load_json("phases.json") or []
config=load_json("config.json") or {}
corrections=load_json("corrections.json") or {}

if not isinstance(venue_additions,list):
    errors.append("data/venue-additions.json must contain an array")
    venue_additions=[]

# New-season venue records override an existing key if one is intentionally refreshed.
venue_by_key={v.get("key"):v for v in venues if isinstance(v,dict) and v.get("key")}
for v in venue_additions:
    if isinstance(v,dict) and v.get("key"):
        venue_by_key[v["key"]]=v
    else:
        errors.append("venue-additions.json contains a venue without a key")
all_venues=list(venue_by_key.values())

events=[]
chunks=manifest.get("chunks",[]) if isinstance(manifest,dict) else []
if not chunks: errors.append("events.json must contain a non-empty chunks list")
for chunk in chunks:
    part=load_json(chunk)
    if isinstance(part,list): events.extend(part)
    else: errors.append(f"data/{chunk} must contain an event array")

ids=set(); venue_keys=set(venue_by_key); required=("id","date","year","sport","teams","scores","venue_recorded","city","venue_key")
for e in events:
    for field in required:
        if field not in e: errors.append(f'{e.get("id","<unknown>")}: missing {field}')
    eid=e.get("id")
    if eid in ids: errors.append(f"duplicate event id {eid}")
    ids.add(eid)
    if e.get("venue_key") and e.get("venue_key") not in venue_keys: errors.append(f'{eid}: unknown venue_key {e.get("venue_key")}')

for eid, patch in corrections.items():
    if eid not in ids: errors.append(f"correction references unknown event {eid}")
    if not isinstance(patch,dict): errors.append(f"correction for {eid} must be an object")

slugs=[v.get("slug") for v in all_venues]
if len(slugs)!=len(set(slugs)): errors.append("duplicate venue slug")
if len({j.get("key") for j in journeys})!=len(journeys): errors.append("duplicate journey key")
if len({p.get("key") for p in phases})!=len(phases): errors.append("duplicate phase key")
if events and int(config.get("archive_start_year",0))>min(e["year"] for e in events): errors.append("archive_start_year is later than earliest event")
if manifest.get("event_count") is not None and manifest.get("event_count")!=len(events): errors.append(f'events.json event_count={manifest.get("event_count")} but chunks contain {len(events)}')
if config.get("event_count") is not None and config.get("event_count")!=len(events): errors.append(f'config event_count={config.get("event_count")} but chunks contain {len(events)}')
if config.get("venue_count") is not None and config.get("venue_count")!=len(all_venues): errors.append(f'config venue_count={config.get("venue_count")} but base + additions contain {len(all_venues)}')

if errors:
    print("\n".join("ERROR: "+x for x in errors))
    sys.exit(1)
print(f"OK: {len(events)} events in {len(chunks)} chunks, {len(all_venues)} venues ({len(venue_additions)} incremental), {len(journeys)} journeys, {len(phases)} phases, {len(corrections)} audited corrections.")
