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
    for token in (
        "D.load('artifacts')",
        'event.html?id=',
        'Image pending digitization',
        'data-artifact-filter',
        'artifact-search',
        'data-status=',
    ):
        if token not in text:
            errors.append(f'artifacts.html missing {token}')

event_page=ROOT/'event.html'
if not event_page.is_file() or "D.load('artifacts')" not in event_page.read_text(encoding='utf-8'):
    errors.append('event passports must load artifact catalog')

annuals=ROOT/'annuals.html'
if not annuals.is_file():
    errors.append('missing annuals.html')
else:
    text=annuals.read_text(encoding='utf-8')
    for token in ("D.load('artifacts')",'artifactByYear','artifact-status','Artifact years'):
        if token not in text:
            errors.append(f'annuals.html missing artifact integration token: {token}')

venue_page=ROOT/'venue-profile.html'
if not venue_page.is_file():
    errors.append('missing venue-profile.html')
else:
    text=venue_page.read_text(encoding='utf-8')
    for token in ("D.load('artifacts')",'venueArtifacts','artifact-badge','Artifacts from this venue','Open the artifact museum'):
        if token not in text:
            errors.append(f'venue-profile.html missing artifact integration token: {token}')

# Artifact context should travel with the annual, chronological, and recurring-story views.
story_pages={
    'year.html':("D.load('artifacts')",'artifactByEvent','yearArtifacts','badge artifact','Physical archive','Open the complete artifact museum'),
    'phase.html':('D.load("artifacts")','chapterArtifacts','Physical archive','Artifacts from this chapter','Open the complete artifact museum'),
    'journey-profile.html':('D.load("artifacts")','journeyArtifacts','artifact-badge','Artifacts in this thread','Open the complete artifact museum'),
}
for name,tokens in story_pages.items():
    path=ROOT/name
    if not path.is_file():
        errors.append(f'missing {name}')
        continue
    text=path.read_text(encoding='utf-8')
    for token in tokens:
        if token not in text:
            errors.append(f'{name} missing artifact storytelling token: {token}')

route=ROOT/'artifacts/index.html'
if not route.is_file():
    errors.append('missing clean /artifacts/ route entry')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'OK: {len(artifacts)} cataloged artifacts validated across museum filters, exact events, annual editions, venue profiles, life chapters, recurring journeys, and ticket-stub evidence locks.')
