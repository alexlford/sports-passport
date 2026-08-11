#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://sports.alexlford.com"
errors = []

def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

manifest = load_json("data/events.json")
events = []
for chunk in manifest.get("chunks", []):
    events.extend(load_json(f"data/{chunk}"))
by_id = {e.get("id"): e for e in events if e.get("id")}
rankings = load_json("data/curated-rankings.json")
ranked = rankings.get("sports_experiences", [])

page = ROOT / "event.html"
if not page.is_file():
    errors.append("missing event.html exact-record template")
else:
    text = page.read_text(encoding="utf-8")
    for token, label in (
        ("new URLSearchParams(location.search).get('id')", "event id query handling"),
        ("D.load('events')", "event archive loading"),
        ("D.load('venues')", "venue context loading"),
        ("D.load('curated-rankings')", "Personal Canon context loading"),
        ("event.html?id=", "chronological event-to-event navigation"),
        ("year.html?y=", "annual-edition context link"),
        ("team-profile.html?t=", "team-profile context links"),
        ("venue-profile.html?v=", "venue-profile context links"),
    ):
        if token not in text:
            errors.append(f"event.html missing {label}")

clean_urls = ROOT / "assets" / "clean-urls.js"
if not clean_urls.is_file():
    errors.append("missing clean URL normalizer")
else:
    clean_text = clean_urls.read_text(encoding="utf-8")
    if "/events/?event=" not in clean_text:
        errors.append("clean URL normalizer does not publish exact-event routes")

route_entry = ROOT / "events" / "index.html"
if not route_entry.is_file():
    errors.append("missing /events/ clean route entry")

for item in ranked:
    event_id = item.get("event_id")
    if not event_id or event_id not in by_id:
        errors.append(f"ranked experience #{item.get('rank')} does not resolve to an archive event")

linked_pages = [
    "favorites.html",
    "hall-of-fame.html",
    "phase.html",
    "journey-profile.html",
    "team-profile.html",
    "venue-profile.html",
]
for name in linked_pages:
    path = ROOT / name
    if not path.is_file():
        errors.append(f"missing {name}")
        continue
    text = path.read_text(encoding="utf-8")
    if "event.html?id=" not in text:
        errors.append(f"{name} does not deep-link to exact event passports")

sitemap = ROOT / "sitemap.xml"
if not sitemap.is_file():
    errors.append("missing sitemap.xml")
else:
    try:
        tree = ET.parse(sitemap)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = {n.text.strip() for n in tree.findall("sm:url/sm:loc", ns) if n.text}
        for item in ranked:
            event_id = item.get("event_id")
            expected = f"{ORIGIN}/events/?event={event_id}"
            if expected not in urls:
                errors.append(f"sitemap missing ranked clean exact-event URL: {expected}")
    except Exception as exc:
        errors.append(f"could not parse sitemap.xml: {exc}")

if errors:
    print("\n".join("ERROR: " + e for e in errors))
    sys.exit(1)

print(
    f"OK: exact event passport template, clean /events/ routing, {len(linked_pages)} deep-linking views, "
    f"and {len(ranked)} Personal Canon event URLs validated."
)
