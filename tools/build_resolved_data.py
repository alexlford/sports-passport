#!/usr/bin/env python3
"""Compile authoring overlays into deterministic public event and venue datasets."""
from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVENT_OUTPUT = DATA / "resolved-events.json"
VENUE_OUTPUT = DATA / "resolved-venues.json"

STATE_NAMES = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO",
    "Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID",
    "Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA",
    "Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
    "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ",
    "New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
    "Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
    "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
    "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY",
}


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def normalize_city(value):
    if not value or not isinstance(value, str):
        return value
    parts = [x.strip() for x in value.split(",")]
    if len(parts) < 2:
        return value.strip()
    state = STATE_NAMES.get(parts[-1], parts[-1])
    return f"{', '.join(parts[:-1])}, {state}"


def compile_events():
    manifest = load("events.json")
    corrections = load("corrections.json")
    aliases = load("team-aliases.json")
    events = []
    seen = set()
    for chunk in manifest.get("chunks", []):
        for source in load(chunk):
            event = dict(source)
            event_id = event.get("id")
            if not event_id or event_id in seen:
                raise ValueError(f"invalid or duplicate event id while compiling: {event_id}")
            seen.add(event_id)
            patch = corrections.get(event_id)
            if patch:
                event.update(patch)
            event["city"] = normalize_city(event.get("city"))
            event["teams_canonical"] = [aliases.get(team, team) for team in event.get("teams", [])]
            events.append(event)
    return events


def compile_venues():
    by_key = OrderedDict()
    for venue in load("venues.json"):
        key = venue.get("key")
        if not key:
            raise ValueError("base venue without key")
        by_key[key] = dict(venue)
    for addition in load("venue-additions.json"):
        key = addition.get("key")
        if not key:
            raise ValueError("venue addition without key")
        by_key[key] = {**by_key.get(key, {}), **addition}
    corrections = load("venue-corrections.json")
    venues = []
    for key, source in by_key.items():
        venue = dict(source)
        if key in corrections:
            venue.update(corrections[key])
        venue["city"] = normalize_city(venue.get("city"))
        venues.append(venue)
    return venues


def rendered(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def write_or_check(path: Path, content: str, check: bool) -> bool:
    if check:
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual != content:
            print(f"ERROR: generated data is stale: {path.relative_to(ROOT)}")
            return False
        return True
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify committed resolved outputs without writing")
    args = parser.parse_args()
    try:
        events = compile_events()
        venues = compile_venues()
    except Exception as exc:
        print(f"ERROR: could not compile resolved data: {exc}")
        return 1
    ok = write_or_check(EVENT_OUTPUT, rendered(events), args.check)
    ok = write_or_check(VENUE_OUTPUT, rendered(venues), args.check) and ok
    if not ok:
        print("Run `python tools/build_resolved_data.py` and commit the generated files.")
        return 1
    action = "Validated" if args.check else "Generated"
    print(f"{action} resolved public data: {len(events)} events, {len(venues)} venues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
