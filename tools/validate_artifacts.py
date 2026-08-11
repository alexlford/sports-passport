#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

manifest=load(Path('data/events.json'))
events=[]
for chunk in manifest.get('chunks',[]):
    events.extend(load(Path('data')/chunk))
by_id={e.get('id'):e for e in events if e.get('id')}
artifacts=load(Path('data/artifacts.json'))

seen=set()
for artifact in artifacts:
    aid=artifact.get('id')
    if not aid:
        errors.append('artifact missing id')
    elif aid in seen:
        errors.append(f'duplicate artifact id: {aid}')
    else:
        seen.add(aid)
    event_id=artifact.get('event_id')
    if event_id not in by_id:
        errors.append(f'{aid or "artifact"} references missing event {event_id}')
    for field in ('type','title','summary','provenance','digitization_status'):
        if not artifact.get(field):
            errors.append(f'{aid or "artifact"} missing {field}')
    media=artifact.get('media')
    if media:
        asset=ROOT/media
        if not asset.is_file():
            errors.append(f'{aid} media does not exist: {media}')

# Fact-lock the two known ticket-stub evidence records.
expected={
    'evt-0001':'artifact-0001',
    'evt-0008':'artifact-0002',
}
for event_id,artifact_id in expected.items():
    event=by_id.get(event_id)
    if not event or event.get('attendance_status')!='verified' or event.get('verification')!='old ticket stub':
        errors.append(f'{event_id} must remain verified by old ticket stub')
    if not any(a.get('id')==artifact_id and a.get('event_id')==event_id and a.get('type')=='ticket_stub' for a in artifacts):
        errors.append(f'{event_id} must remain linked to {artifact_id}')

page=ROOT/'artifacts.html'
if not page.is_file():
    errors.append('missing artifacts.html')
else:
    text=page.read_text(encoding='utf-8')
    for token in ("D.load('artifacts')","event.html?id=","Image pending digitization"):
        if token not in text:
            errors.append(f'artifacts.html missing {token}')

event_page=ROOT/'event.html'
if not event_page.is_file() or "D.load('artifacts')" not in event_page.read_text(encoding='utf-8'):
    errors.append('event passports must load artifact catalog')

route=ROOT/'artifacts/index.html'
if not route.is_file():
    errors.append('missing clean /artifacts/ route entry')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'OK: {len(artifacts)} cataloged artifacts validated against {len(events)} archive events, including ticket-stub evidence locks.')
