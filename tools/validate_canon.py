#!/usr/bin/env python3
"""Validate the editorial/cross-link layer that sits above the raw archive."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
errors = []


def load(name):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"could not load data/{name}: {exc}")
        return {} if name.endswith(("lore.json", "narratives.json", "aliases.json", "rankings.json")) else []


manifest = load("events.json")
venues = load("venues.json")
venue_additions = load("venue-additions.json")
rankings = load("curated-rankings.json")
phases = load("phases.json")
narratives = load("phase-narratives.json")
team_lore = load("team-lore.json")
team_aliases = load("team-aliases.json")

# Resolve the full event archive.
events = []
for chunk in manifest.get("chunks", []):
    part = load(chunk)
    if isinstance(part, list):
        events.extend(part)

event_by_id = {e.get("id"): e for e in events if isinstance(e, dict) and e.get("id")}

# Venue additions intentionally override a base key, matching the browser/data validator.
venue_by_key = {v.get("key"): v for v in venues if isinstance(v, dict) and v.get("key")}
for v in venue_additions if isinstance(venue_additions, list) else []:
    if isinstance(v, dict) and v.get("key"):
        venue_by_key[v["key"]] = v
venue_by_slug = {v.get("slug"): v for v in venue_by_key.values() if v.get("slug")}

# Every curated sports experience must point to one unique, real archive event.
sports_items = rankings.get("sports_experiences", []) if isinstance(rankings, dict) else []
ranked_event_ids = []
for item in sports_items:
    if not isinstance(item, dict):
        continue
    eid = item.get("event_id")
    if eid:
        ranked_event_ids.append(eid)
        event = event_by_id.get(eid)
        if not event:
            errors.append(f"Top 10 sports experience #{item.get('rank')} references missing event {eid}")
        elif item.get("year") is not None and item.get("year") != event.get("year"):
            errors.append(f"Top 10 sports experience #{item.get('rank')} year does not match event {eid}")
if len(ranked_event_ids) != len(set(ranked_event_ids)):
    errors.append("Top 10 sports experiences must reference ten unique archive events")

# Venue ranking links are generated from slugs, so a bad slug would create a public dead end.
for list_name in ("favorite_venues", "best_venues"):
    seen_slugs = set()
    for item in rankings.get(list_name, []) if isinstance(rankings, dict) else []:
        if not isinstance(item, dict):
            continue
        slugs = item.get("venue_slugs")
        if not isinstance(slugs, list) or not slugs:
            errors.append(f"{list_name} #{item.get('rank')} must include at least one venue_slug")
            continue
        for slug in slugs:
            if slug not in venue_by_slug:
                errors.append(f"{list_name} #{item.get('rank')} references unknown venue slug {slug}")
            if slug in seen_slugs:
                errors.append(f"{list_name} repeats venue slug {slug}")
            seen_slugs.add(slug)

# The five memoir chapters and their narratives are a paired editorial contract.
phase_keys = [p.get("key") for p in phases if isinstance(p, dict) and p.get("key")]
narrative_keys = set(narratives) if isinstance(narratives, dict) else set()
for key in phase_keys:
    if key not in narrative_keys:
        errors.append(f"life chapter {key} has no phase narrative")
for key in sorted(narrative_keys - set(phase_keys)):
    errors.append(f"phase narrative {key} has no matching life chapter")
for key in phase_keys:
    story = narratives.get(key, {}) if isinstance(narratives, dict) else {}
    if not isinstance(story, dict):
        errors.append(f"phase narrative {key} must be an object")
        continue
    if not story.get("headline") or not story.get("pullquote"):
        errors.append(f"phase narrative {key} needs a headline and pullquote")
    paragraphs = story.get("paragraphs")
    if not isinstance(paragraphs, list) or len(paragraphs) < 2 or not all(isinstance(p, str) and p.strip() for p in paragraphs):
        errors.append(f"phase narrative {key} needs at least two non-empty paragraphs")

# Favorite-team dossiers must resolve to canonical team identities seen in the archive.
archive_teams = {t for e in events for t in (e.get("teams") or []) if isinstance(t, str) and t.strip()}
canonical_teams = {team_aliases.get(t, t) for t in archive_teams}
favorite_teams = {team for team, lore in team_lore.items() if isinstance(lore, dict) and lore.get("favorite")}
expected_favorites = {
    "Illinois Fighting Illini",
    "Kansas Jayhawks",
    "Kansas City Chiefs",
    "St. Louis Cardinals",
    "Denver Nuggets",
    "Colorado Avalanche",
    "Denver Summit FC",
}
if favorite_teams != expected_favorites:
    missing = sorted(expected_favorites - favorite_teams)
    extra = sorted(favorite_teams - expected_favorites)
    if missing:
        errors.append("favorite-team dossiers missing: " + " | ".join(missing))
    if extra:
        errors.append("unexpected favorite-team dossiers: " + " | ".join(extra))
for team in favorite_teams:
    if team not in canonical_teams:
        errors.append(f"favorite-team dossier does not resolve to an archive team: {team}")
    lore = team_lore.get(team, {})
    for field in ("history", "championships", "lore", "fun_facts", "sources"):
        if not lore.get(field):
            errors.append(f"{team} favorite-team dossier missing {field}")
    for source in lore.get("sources", []):
        if not isinstance(source, dict) or not source.get("label") or not str(source.get("url", "")).startswith("https://"):
            errors.append(f"{team} has an invalid official-source entry")

if errors:
    print("\n".join("ERROR: " + e for e in errors))
    sys.exit(1)

print(
    f"OK: {len(sports_items)} ranked sports experiences resolve to unique events; "
    f"{len(rankings.get('favorite_venues', []))} favorite-venue ranks and "
    f"{len(rankings.get('best_venues', []))} best-venue ranks resolve to venue profiles; "
    f"{len(phase_keys)} life chapters have narratives; {len(favorite_teams)} favorite-team dossiers are complete."
)
