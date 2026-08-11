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
        return {} if name.endswith(("lore.json", "narratives.json", "aliases.json", "rankings.json", "config.json")) else []


manifest = load("events.json")
venues = load("venues.json")
venue_additions = load("venue-additions.json")
rankings = load("curated-rankings.json")
phases = load("phases.json")
narratives = load("phase-narratives.json")
team_lore = load("team-lore.json")
team_aliases = load("team-aliases.json")
config = load("config.json")

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

# Explicitly protect user-confirmed Personal Canon corrections from regression.
rank_by_number = {item.get("rank"): item for item in sports_items if isinstance(item, dict)}
protected_ranks = {
    2: ("evt-0261", "Illinois at the 2026 Final Four"),
    7: ("evt-0046", "Illinois–Penn State"),
}
for rank, (event_id, title) in protected_ranks.items():
    item = rank_by_number.get(rank, {})
    if item.get("event_id") != event_id or item.get("title") != title:
        errors.append(f"protected Personal Canon rank #{rank} must remain {title} ({event_id})")

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
expected_phase_titles = ["Growing Up", "Undergrad", "Grad School", "Baltimore / East Coast", "Denver"]
actual_phase_titles = [p.get("title") for p in phases if isinstance(p, dict)]
if actual_phase_titles != expected_phase_titles:
    errors.append("life chapter titles/order must remain: " + " | ".join(expected_phase_titles))
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

# Protect early-archive confidence decisions that were confirmed directly by the user.
wrigley_1999 = event_by_id.get("evt-0013a", {})
if wrigley_1999.get("attendance_status") != "notional":
    errors.append("1999 Twins–Cubs at Wrigley (evt-0013a) must remain notional")
indiana_siu = event_by_id.get("evt-0020", {})
if indiana_siu.get("attendance_status") != "verified":
    errors.append("2001 Indiana at SIU (evt-0020) must remain verified")
camden_early = [e for e in events if e.get("year", 9999) < 2006 and e.get("venue_key") == "Oriole Park at Camden Yards"]
for event in camden_early:
    if event.get("attendance_status") != "verified" or event.get("verification") != "old ticket stub":
        errors.append(f"{event.get('id')}: pre-2006 Camden Yards attendance must remain verified by old ticket stub")

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

# Keep the static homepage fallbacks synchronized with config so the page remains sensible before JS loads.
current_year = int(config.get("current_year", 0) or 0)
archive_start = int(config.get("archive_start_year", 0) or 0)
index_text = (ROOT / "index.html").read_text(encoding="utf-8")
for needle, label in (
    (f">{archive_start} → {current_year}<", "homepage archive-range fallback"),
    (f'href="year.html?y={current_year}"', "homepage current-year link fallback"),
    (f'data-year="{current_year}"', "homepage current-year feature fallback"),
):
    if needle not in index_text:
        errors.append(f"{label} is not synchronized to config current_year={current_year}")

# Stale labels that have been explicitly replaced should never return to public-facing source.
public_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in list(ROOT.glob("*.html")) + [DATA / "phases.json", DATA / "phase-narratives.json", DATA / "curated-rankings.json"]
)
for stale in ("The Cardinals Thread", "Illinois at the 2005 Final Four"):
    if stale in public_text:
        errors.append(f"stale public wording returned: {stale}")

if errors:
    print("\n".join("ERROR: " + e for e in errors))
    sys.exit(1)

print(
    f"OK: {len(sports_items)} ranked sports experiences resolve to unique events; "
    f"{len(rankings.get('favorite_venues', []))} favorite-venue ranks and "
    f"{len(rankings.get('best_venues', []))} best-venue ranks resolve to venue profiles; "
    f"{len(phase_keys)} life chapters have narratives; {len(favorite_teams)} favorite-team dossiers are complete; "
    f"protected rankings, early-archive confidence, and {current_year} homepage fallbacks are locked."
)
