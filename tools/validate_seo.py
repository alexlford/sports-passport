#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
ORIGIN='https://sports.alexlford.com'
errors=[]
load=lambda name: json.loads((DATA/name).read_text(encoding='utf-8'))
slug=lambda value: re.sub(r'[^a-z0-9]+','-',str(value).lower().replace('&','and')).strip('-')

events=load('resolved-events.json')
venues=load('resolved-venues.json')
aliases=load('team-aliases.json')
confirmed=lambda e: int(e.get('year') or 0)>=2006 or e.get('attendance_status')=='verified'

try:
    tree=ET.parse(ROOT/'sitemap.xml')
    ns={'sm':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls={node.text.strip() for node in tree.findall('sm:url/sm:loc',ns) if node.text}
except Exception as exc:
    errors.append(f'could not parse sitemap.xml: {exc}')
    urls=set()

for event in events:
    if not event.get('id'): continue
    url=f"{ORIGIN}/events/{event['id']}/"
    page=ROOT/'events'/event['id']/'index.html'
    text=page.read_text(encoding='utf-8') if page.is_file() else ''
    if confirmed(event):
        if url not in urls: errors.append(f'confirmed event missing from sitemap: {event["id"]}')
        if 'name="robots" content="noindex' in text: errors.append(f'confirmed event incorrectly noindexed: {event["id"]}')
    else:
        if url in urls: errors.append(f'notional event must not be in sitemap: {event["id"]}')
        if '<meta name="robots" content="noindex,follow">' not in text: errors.append(f'notional event missing static noindex: {event["id"]}')

canonical_teams={aliases.get(team,team) for event in events for team in event.get('teams',[])}
for team in canonical_teams:
    if f'{ORIGIN}/teams/{slug(team)}/' not in urls: errors.append(f'team missing from sitemap: {team}')
for venue in venues:
    if venue.get('slug') and f"{ORIGIN}/venues/{venue['slug']}/" not in urls: errors.append(f'venue missing from sitemap: {venue.get("display_name",venue["slug"])}')

seo=(ROOT/'assets'/'seo.js').read_text(encoding='utf-8') if (ROOT/'assets'/'seo.js').is_file() else ''
shared=(ROOT/'assets'/'sports-passport-data.js').read_text(encoding='utf-8')
for token,label in (
    ("'@type': 'WebSite'",'WebSite JSON-LD'),
    ("'@type': 'Person'",'Person JSON-LD'),
    ("'@type': 'BreadcrumbList'",'BreadcrumbList JSON-LD'),
    ("'@type': 'SportsEvent'",'SportsEvent JSON-LD'),
    ("'@type': 'Place'",'Place JSON-LD'),
    ("og:image",'Open Graph image'),
    ("twitter:image",'Twitter image'),
    ("noindex,follow",'runtime notional noindex fallback'),
):
    if token not in seo: errors.append(f'SEO runtime missing {label}')
if "seo.src = '/assets/seo.js'" not in shared: errors.append('shared runtime does not load assets/seo.js')
if not (ROOT/'assets'/'social-card.svg').is_file(): errors.append('missing social-card.svg')

if errors:
    print('\n'.join('ERROR: '+e for e in errors)); sys.exit(1)
confirmed_count=sum(1 for e in events if e.get('id') and confirmed(e))
notional_count=sum(1 for e in events if e.get('id') and not confirmed(e))
print(f'OK: SEO policy indexes {confirmed_count} confirmed/documented events, all {len(canonical_teams)} teams and {len(venues)} venues; {notional_count} reconstructed event pages are noindex.')
