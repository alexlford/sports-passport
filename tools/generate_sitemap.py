#!/usr/bin/env python3
"""Generate the canonical sitemap from the archive's explicit indexing policy."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
ORIGIN = 'https://sports.alexlford.com'
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
ET.register_namespace('', NS)


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', str(value).lower().replace('&', 'and')).strip('-')


def confirmed(event):
    return int(event.get('year') or 0) >= 2006 or event.get('attendance_status') == 'verified'


def main():
    config = load('config.json')
    events = load('resolved-events.json')
    venues = load('resolved-venues.json')
    aliases = load('team-aliases.json')
    journeys = load('journeys.json')
    phases = load('phases.json')

    paths = {
        '/', '/about/', '/years/', '/teams/', '/venues/', '/geography/', '/geography/map/',
        '/journeys/', '/favorites/', '/analytics/', '/hall-of-fame/', '/search/'
    }
    paths.update(f'/years/{year}/' for year in range(int(config['archive_start_year']), int(config['current_year']) + 1))
    paths.update(f"/events/{event['id']}/" for event in events if event.get('id') and confirmed(event))
    canonical_teams = {aliases.get(team, team) for event in events for team in event.get('teams', [])}
    paths.update(f'/teams/{slug(team)}/' for team in canonical_teams)
    paths.update(f"/venues/{venue['slug']}/" for venue in venues if venue.get('slug'))
    paths.update(f"/journeys/{j['key']}/" for j in journeys if j.get('key'))
    paths.update(f"/chapters/{p['key']}/" for p in phases if p.get('key'))

    root = ET.Element(ET.QName(NS, 'urlset'))
    for path in sorted(paths, key=lambda p: (p.count('/'), p)):
        node = ET.SubElement(root, ET.QName(NS, 'url'))
        ET.SubElement(node, ET.QName(NS, 'loc')).text = ORIGIN + path
    ET.indent(root, space='  ')
    xml = ET.tostring(root, encoding='unicode')
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + xml + '\n', encoding='utf-8')
    print(f'Generated sitemap with {len(paths)} URLs: all public sections, years, teams, venues, chapters, journeys, and confirmed/documented events.')


if __name__ == '__main__':
    main()
