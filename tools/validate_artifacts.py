#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
ALLOWED_TYPES={'ticket_stub','credential','program','seat_view','keepsake','photo'}
ALLOWED_STATUS={'image_pending','digitized'}

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

manifest=load(Path('data/events.json'))
events=[]
for chunk in manifest.get('chunks',[]):
    events.extend(load(Path('data')/chunk))
by_id={e.get('id'):e for e in events if e.get('id')}
artifacts=load(Path('data/artifacts.json'))
rankings=load(Path('data/curated-rankings.json'))

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
    if artifact.get('type') not in ALLOWED_TYPES:
        errors.append(f'{aid or "artifact"} uses unsupported type: {artifact.get("type")}')
    status=artifact.get('digitization_status')
    if status not in ALLOWED_STATUS:
        errors.append(f'{aid or "artifact"} uses unsupported digitization_status: {status}')
    media=artifact.get('media')
    if media:
        asset=ROOT/media
        if not asset.is_file():
            errors.append(f'{aid} media does not exist: {media}')
        if status!='digitized':
            errors.append(f'{aid} has media but digitization_status is not digitized')
    elif status!='image_pending':
        errors.append(f'{aid or "artifact"} has no media and must remain image_pending')

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
        'Collection status',
        'Digitization queue',
        'Personal Canon coverage',
        'topTenCandidates',
        'Candidate for a future ticket',
        'provenance over decoration',
        'assets/clean-urls.js',
    ):
        if token not in text:
            errors.append(f'artifacts.html missing {token}')
    ranked_ids={r.get('event_id') for r in rankings.get('sports_experiences',[]) if r.get('event_id')}
    if len(ranked_ids)!=10:
        errors.append('artifact coverage queue expects exactly 10 unique Personal Canon event IDs')

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

workflow=ROOT/'ARTIFACT-WORKFLOW.md'
if not workflow.is_file():
    errors.append('missing ARTIFACT-WORKFLOW.md')
else:
    workflow_text=workflow.read_text(encoding='utf-8')
    for token in ('data/artifacts.json','assets/artifacts/','image_pending','digitized','provenance over decoration'):
        if token not in workflow_text:
            errors.append(f'ARTIFACT-WORKFLOW.md missing workflow token: {token}')

route=ROOT/'artifacts/index.html'
if not route.is_file():
    errors.append('missing clean /artifacts/ route entry')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'OK: {len(artifacts)} cataloged artifacts validated across museum filters, collection coverage, digitization workflow, exact events, annual editions, venue profiles, life chapters, recurring journeys, and ticket-stub evidence locks.')
