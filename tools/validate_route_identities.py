#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PUBLIC_ORIGIN = 'https://sports.alexlford.com'
errors = []


def load_json(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def slug(value):
    value = str(value).lower().replace('&', 'and')
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')


def check_unique(label, pairs):
    seen = defaultdict(list)
    for identity, source in pairs:
        seen[str(identity)].append(str(source))
    for identity, sources in sorted(seen.items()):
        if not identity:
            errors.append(f'{label}: blank route identity from {sources}')
        elif len(sources) > 1:
            errors.append(f'{label}: duplicate route identity {identity!r}: ' + ' | '.join(sources))
        if '/' in identity or '?' in identity or '#' in identity:
            errors.append(f'{label}: unsafe route identity {identity!r}')


# Assemble all archive events from the chunk manifest.
manifest = load_json('events.json')
chunks = manifest.get('chunks', [])
events = []
for file_name in chunks:
    events.extend(load_json(file_name))

aliases = load_json('team-aliases.json')
venues = load_json('venues.json')
try:
    additions = load_json('venue-additions.json')
except FileNotFoundError:
    additions = []
venue_by_key = {v['key']: v for v in venues}
for venue in additions:
    venue_by_key[venue['key']] = {**venue_by_key.get(venue['key'], {}), **venue}
venues = list(venue_by_key.values())
journeys = load_json('journeys.json')
phases = load_json('phases.json')
config = load_json('config.json')

# Event identities must be globally unique because exact Event Passport URLs key on them.
check_unique('event', [(e.get('id'), f"{e.get('date')} {' vs '.join(e.get('teams', []))}") for e in events])

# Canonical team names are converted to slugs in links. Two different canonical teams
# must never collapse to the same slug or one profile will shadow the other.
canonical_teams = sorted({aliases.get(team, team) for e in events for team in e.get('teams', [])})
check_unique('team slug', [(slug(team), team) for team in canonical_teams])

# Venue profile URLs use the explicit venue slug.
check_unique('venue slug', [(v.get('slug'), f"{v.get('key')} / {v.get('display_name')}") for v in venues if v.get('slug') is not None])
check_unique('venue key', [(v.get('key'), v.get('display_name')) for v in venues])

# Narrative route identities are data keys.
check_unique('journey key', [(j.get('key'), j.get('title')) for j in journeys])
check_unique('chapter key', [(p.get('key'), p.get('title')) for p in phases])

# Every documented event year must be representable by the public annual route and
# remain inside the configured archive range.
years = sorted({int(e['year']) for e in events if e.get('year') is not None})
start = int(config['archive_start_year'])
current = int(config['current_year'])
for year in years:
    if year < start or year > current:
        errors.append(f'year route: event year {year} is outside configured archive range {start}-{current}')
for year in range(start, current + 1):
    if year not in years:
        errors.append(f'year route: configured public year {year} has no archive events')

# Build the complete set of identities that the dynamic public routes can resolve.
valid_identities = {
    'year': {str(year) for year in years},
    'event': {str(e.get('id')) for e in events if e.get('id')},
    'team': {slug(team) for team in canonical_teams},
    'venue': {str(v.get('slug')) for v in venues if v.get('slug')},
    'journey': {str(j.get('key')) for j in journeys if j.get('key')},
    'chapter': {str(p.get('key')) for p in phases if p.get('key')},
}
route_path_to_identity = {
    '/years/': 'year',
    '/events/': 'event',
    '/teams/': 'team',
    '/venues/': 'venue',
    '/journeys/': 'journey',
    '/chapters/': 'chapter',
}

# Audit every identity-bearing sitemap URL, not only the required subset. This catches
# stale links left behind after a record, slug, or narrative key changes.
sitemap = ROOT / 'sitemap.xml'
if not sitemap.is_file():
    errors.append('sitemap identity audit: missing sitemap.xml')
else:
    try:
        tree = ET.parse(sitemap)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap_urls = [node.text.strip() for node in tree.findall('sm:url/sm:loc', ns) if node.text and node.text.strip()]
        for url in sitemap_urls:
            parsed = urlsplit(url)
            if f'{parsed.scheme}://{parsed.netloc}' != PUBLIC_ORIGIN:
                continue
            identity_key = route_path_to_identity.get(parsed.path)
            params = parse_qs(parsed.query)
            if not identity_key or not params:
                continue
            if set(params) != {identity_key} or len(params.get(identity_key, [])) != 1:
                errors.append(f'sitemap identity audit: malformed dynamic route {url}')
                continue
            identity = params[identity_key][0]
            if identity not in valid_identities[identity_key]:
                errors.append(f'sitemap identity audit: stale {identity_key} identity {identity!r}: {url}')
    except Exception as exc:
        errors.append(f'sitemap identity audit: could not parse sitemap.xml: {exc}')

# Route runtime must support every public identity family used above.
route = (ROOT / 'assets' / 'route-bootstrap.js').read_text(encoding='utf-8')
clean = (ROOT / 'assets' / 'clean-urls.js').read_text(encoding='utf-8')
required_route_tokens = (
    "first === 'years'", "first === 'events'", "first === 'teams'", "first === 'venues'",
    "first === 'journeys'", "first === 'chapters'",
    "template = 'year.html'", "template = 'event.html'", "template = 'team-profile.html'",
    "template = 'venue-profile.html'", "template = 'journey-profile.html'", "template = 'phase.html'",
)
for token in required_route_tokens:
    if token not in route:
        errors.append(f'route runtime missing identity mapping: {token}')

required_clean_tokens = (
    '/years/?year=', '/events/?event=', '/teams/?team=', '/venues/?venue=',
    '/journeys/?journey=', '/chapters/?chapter='
)
for token in required_clean_tokens:
    if token not in clean:
        errors.append(f'clean URL runtime missing identity mapping: {token}')

if errors:
    print('\n'.join('ERROR: ' + e for e in errors))
    sys.exit(1)

print(
    f'OK: unique public route identities and sitemap targets validated for {len(events)} events, '
    f'{len(canonical_teams)} canonical teams, {len(venues)} venues, '
    f'{len(journeys)} journeys, {len(phases)} chapters, and {len(years)} annual editions.'
)
