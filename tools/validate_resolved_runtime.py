#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
js=(ROOT/'assets/sports-passport-data.js').read_text(encoding='utf-8')
for required in ('/data/resolved-events.json','/data/resolved-venues.json'):
    if required not in js: errors.append(f'runtime missing compiled data request: {required}')
for forbidden in ('/data/corrections.json','/data/venue-additions.json','/data/venue-corrections.json'):
    if forbidden in js: errors.append(f'runtime still reads authoring overlay: {forbidden}')
if 'value.chunks' in js or 'parts.flat()' in js:
    errors.append('runtime still expands event chunks instead of using resolved-events.json')
events=json.loads((ROOT/'data/resolved-events.json').read_text(encoding='utf-8'))
venues=json.loads((ROOT/'data/resolved-venues.json').read_text(encoding='utf-8'))
if not isinstance(events,list) or not events: errors.append('resolved-events.json must be a non-empty array')
if not isinstance(venues,list) or not venues: errors.append('resolved-venues.json must be a non-empty array')
by_id={e.get('id'):e for e in events}
if by_id.get('evt-0222',{}).get('sport')!='Hockey': errors.append('resolved event correction for evt-0222 is missing')
for event in events:
    if not isinstance(event.get('teams_canonical'),list) or len(event.get('teams_canonical'))!=len(event.get('teams') or []):
        errors.append(f"{event.get('id')}: resolved canonical team layer is incomplete")
        break
if len({v.get('key') for v in venues})!=len(venues): errors.append('resolved venues contain duplicate keys')
if errors:
    print('\n'.join('ERROR: '+e for e in errors)); sys.exit(1)
print(f'OK: runtime reads deterministic resolved datasets ({len(events)} events, {len(venues)} venues) and no authoring overlays.')
