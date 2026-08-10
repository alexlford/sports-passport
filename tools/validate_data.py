#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
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
favorites=load_json("favorite-experiences.json", optional=True) or []
curated_rankings=load_json("curated-rankings.json", optional=True) or {}
team_colors=load_json("team-colors.json", optional=True) or {}
team_aliases=load_json("team-aliases.json", optional=True) or {}
config=load_json("config.json") or {}
corrections=load_json("corrections.json") or {}

if not isinstance(venue_additions,list):
    errors.append("data/venue-additions.json must contain an array")
    venue_additions=[]
if not isinstance(favorites,list):
    errors.append("data/favorite-experiences.json must contain an array")
    favorites=[]
if not isinstance(curated_rankings,dict):
    errors.append("data/curated-rankings.json must contain an object")
    curated_rankings={}
if not isinstance(team_colors,dict):
    errors.append("data/team-colors.json must contain an object keyed by exact archive team name")
    team_colors={}
if not isinstance(team_aliases,dict):
    errors.append("data/team-aliases.json must contain an object mapping source labels to canonical team identities")
    team_aliases={}

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
    status=e.get("attendance_status")
    year=e.get("year")
    if isinstance(year,int) and year < 2006:
        if status not in {"verified","notional"}:
            errors.append(f'{eid}: pre-2006 event must declare attendance_status verified or notional')
        if status == "verified" and not e.get("verification"):
            errors.append(f'{eid}: verified pre-2006 event must include verification evidence')
    elif status is not None and status not in {"verified","notional"}:
        errors.append(f'{eid}: attendance_status must be verified or notional when present')

for eid, patch in corrections.items():
    if eid not in ids: errors.append(f"correction references unknown event {eid}")
    if not isinstance(patch,dict): errors.append(f"correction for {eid} must be an object")

favorite_keys=set()
for f in favorites:
    if not isinstance(f,dict):
        errors.append("favorite-experiences.json contains a non-object entry")
        continue
    key=f.get("key")
    if not key: errors.append("favorite experience missing key")
    elif key in favorite_keys: errors.append(f"duplicate favorite experience key {key}")
    favorite_keys.add(key)
    for field in ("title","label","year","category","description","source_label"):
        if not f.get(field): errors.append(f'{key or "<favorite>"}: missing {field}')
    event_id=f.get("event_id")
    if event_id and event_id not in ids: errors.append(f'{key}: unknown event_id {event_id}')

# Curated lists are intentional Top 10s. Validate their shape so future edits cannot silently break rank order.
ranking_keys=("sports_experiences","favorite_venues","best_venues")
if curated_rankings:
    for key in ranking_keys:
        items=curated_rankings.get(key)
        if not isinstance(items,list):
            errors.append(f'curated-rankings.json {key} must contain an array')
            continue
        if len(items)!=10:
            errors.append(f'curated-rankings.json {key} must contain exactly 10 entries')
        ranks=[item.get("rank") for item in items if isinstance(item,dict)]
        if ranks != list(range(1,11)):
            errors.append(f'curated-rankings.json {key} ranks must be ordered 1 through 10')
        titles=[item.get("title") for item in items if isinstance(item,dict)]
        if any(not isinstance(title,str) or not title.strip() for title in titles):
            errors.append(f'curated-rankings.json {key} entries must have non-empty titles')
        if len(titles)!=len(set(titles)):
            errors.append(f'curated-rankings.json {key} contains duplicate titles')

# Source team labels remain immutable in event records. Aliases create a separate canonical identity layer.
archive_teams=sorted({team for e in events for team in (e.get("teams") or []) if isinstance(team,str) and team.strip()})
archive_team_set=set(archive_teams)
for source,target in team_aliases.items():
    if source not in archive_team_set:
        errors.append(f'team-aliases.json source not present in archive: {source}')
    if not isinstance(target,str) or not target.strip():
        errors.append(f'{source}: canonical team identity must be a non-empty string')
    elif target == source:
        errors.append(f'{source}: team alias must not point to itself')
    elif target in team_aliases:
        errors.append(f'{source}: alias target {target} is also an alias source; use one-step canonical mappings only')

canonical=lambda team: team_aliases.get(team,team)
canonical_teams=sorted({canonical(team) for team in archive_teams})

# Every source-label palette must be valid, and every canonical profile must be able to resolve a palette.
for team,palette in team_colors.items():
    if team not in archive_team_set: errors.append(f'team-colors.json contains team not present in archive: {team}')
    if not isinstance(palette,list) or len(palette)!=2 or not all(isinstance(c,str) and re.fullmatch(r"#[0-9A-Fa-f]{6}",c) for c in palette):
        errors.append(f'{team}: team palette must be exactly two six-digit hex colors')
missing_source_colors=[team for team in archive_teams if team not in team_colors]
if missing_source_colors:
    errors.append("missing source-label team color palettes: " + " | ".join(missing_source_colors))

missing_canonical_colors=[]
for team in canonical_teams:
    if team in team_colors:
        continue
    sources=[source for source,target in team_aliases.items() if target==team and source in team_colors]
    if not sources:
        missing_canonical_colors.append(team)
if missing_canonical_colors:
    errors.append("canonical team identities cannot resolve a palette: " + " | ".join(missing_canonical_colors))

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
ranking_count=sum(1 for key in ranking_keys if isinstance(curated_rankings.get(key),list))
print(f"OK: {len(events)} events in {len(chunks)} chunks, {len(all_venues)} venues ({len(venue_additions)} incremental), {len(archive_teams)} source team labels -> {len(canonical_teams)} canonical teams via {len(team_aliases)} aliases, {len(journeys)} journeys, {len(phases)} phases, {len(favorites)} favorite experiences, {ranking_count} curated Top 10 rankings, {len(corrections)} audited corrections.")
