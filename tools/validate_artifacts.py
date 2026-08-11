#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
ALLOWED_TYPES={'ticket_stub','credential','program','seat_view','keepsake','photo'}
ALLOWED_STATUS={'image_pending','digitized'}
ALLOWED_PRIORITY_STATUS={'candidate','research_lead','needs_exact_event_confirmation'}
ALLOWED_PRIORITY_CATEGORY={'verified_early_archive','family_history','confidence_upgrade'}

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

manifest=load(Path('data/events.json'))
events=[]
for chunk in manifest.get('chunks',[]):
    events.extend(load(Path('data')/chunk))
by_id={e.get('id'):e for e in events if e.get('id')}
artifacts=load(Path('data/artifacts.json'))
priorities=load(Path('data/artifact-priorities.json'))
rankings=load(Path('data/curated-rankings.json'))
phases=load(Path('data/phases.json'))
phase_by_key={p.get('key'):p for p in phases if p.get('key')}
artifact_event_ids={a.get('event_id') for a in artifacts if a.get('event_id')}

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

# Research priorities are deliberately separate from known physical objects.
priority_seen=set()
for priority in priorities:
    pid=priority.get('id')
    if not pid:
        errors.append('artifact research priority missing id')
    elif pid in priority_seen:
        errors.append(f'duplicate artifact research priority id: {pid}')
    else:
        priority_seen.add(pid)
    for field in ('title','phase_key','category','priority','status','event_ids','summary','research_note','candidate_types'):
        if priority.get(field) in (None,'',[]):
            errors.append(f'{pid or "artifact research priority"} missing {field}')
    if priority.get('status') not in ALLOWED_PRIORITY_STATUS:
        errors.append(f'{pid or "priority"} uses unsupported research status: {priority.get("status")}')
    if priority.get('category') not in ALLOWED_PRIORITY_CATEGORY:
        errors.append(f'{pid or "priority"} uses unsupported research category: {priority.get("category")}')
    phase=phase_by_key.get(priority.get('phase_key'))
    if not phase:
        errors.append(f'{pid or "priority"} references missing phase {priority.get("phase_key")}')
    event_ids=priority.get('event_ids') or []
    if len(event_ids)!=len(set(event_ids)):
        errors.append(f'{pid or "priority"} repeats event IDs')
    for event_id in event_ids:
        event=by_id.get(event_id)
        if not event:
            errors.append(f'{pid or "priority"} references missing event {event_id}')
            continue
        if event_id in artifact_event_ids:
            errors.append(f'{pid or "priority"} references {event_id}, which already has a cataloged artifact')
        if phase and not (int(phase.get('start',-9999)) <= int(event.get('year',-9999)) <= int(phase.get('end',9999))):
            errors.append(f'{pid or "priority"} event {event_id} falls outside phase {phase.get("key")}')
    candidate_types=priority.get('candidate_types') or []
    unsupported=set(candidate_types)-ALLOWED_TYPES
    if unsupported:
        errors.append(f'{pid or "priority"} has unsupported candidate types: {sorted(unsupported)}')
    if priority.get('status')=='needs_exact_event_confirmation' and len(event_ids)<2:
        errors.append(f'{pid or "priority"} needs multiple candidate events for exact-event confirmation')
    if priority.get('category')=='verified_early_archive':
        for event_id in event_ids:
            event=by_id.get(event_id)
            if event and (int(event.get('year',9999))>=2006 or event.get('attendance_status')!='verified'):
                errors.append(f'{pid or "priority"} verified_early_archive event {event_id} must be verified and pre-2006')

# Fact-lock the two known ticket-stub evidence records.
expected={'evt-0001':'artifact-0001','evt-0008':'artifact-0002'}
for event_id,artifact_id in expected.items():
    event=by_id.get(event_id)
    if not event or event.get('attendance_status')!='verified' or event.get('verification')!='old ticket stub':
        errors.append(f'{event_id} must remain verified by old ticket stub')
    if not any(a.get('id')==artifact_id and a.get('event_id')==event_id and a.get('type')=='ticket_stub' for a in artifacts):
        errors.append(f'{event_id} must remain linked to {artifact_id}')

# Fact-lock the first biography-level research priorities without inventing evidence.
priority_by_id={p.get('id'):p for p in priorities if p.get('id')}
indiana=priority_by_id.get('artifact-priority-0001')
if not indiana or indiana.get('event_ids')!=['evt-0020'] or indiana.get('category')!='verified_early_archive':
    errors.append('artifact-priority-0001 must remain the verified Indiana-at-SIU research candidate')
else:
    event=by_id.get('evt-0020')
    if not event or event.get('attendance_status')!='verified' or event.get('verification')!='user-confirmed':
        errors.append('evt-0020 must remain user-confirmed while it is a research priority')
penny=priority_by_id.get('artifact-priority-0003')
if not penny or penny.get('event_ids')!=['evt-0250','evt-0251'] or penny.get('status')!='needs_exact_event_confirmation':
    errors.append("Penny's first-game research lead must preserve both July 2025 candidate events until the exact date is confirmed")
else:
    for event_id in penny.get('event_ids',[]):
        event=by_id.get(event_id)
        teams=set(event.get('teams',[])) if event else set()
        if not event or int(event.get('year',0))!=2025 or not {'St. Louis Cardinals','Colorado Rockies'}.issubset(teams):
            errors.append(f'{event_id} must remain a 2025 Cardinals–Rockies candidate for the unresolved first-game lead')

page=ROOT/'artifacts.html'
if not page.is_file():
    errors.append('missing artifacts.html')
else:
    text=page.read_text(encoding='utf-8')
    for token in (
        "D.load('artifacts')",
        "D.load('artifact-priorities')",
        '/events/?event=',
        'Image pending digitization',
        'data-artifact-filter',
        'artifact-search',
        'data-status=',
        'Collection status',
        'Digitization queue',
        'Biography research priorities',
        'Personal Canon coverage',
        'topTenCandidates',
        'Candidate for a future ticket',
        'research leads',
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

story_pages={
    'year.html':("D.load('artifacts')",'artifactByEvent','yearArtifacts','badge artifact','Physical archive','Open the complete artifact museum'),
    'phase.html':('D.load("artifacts")','D.load("artifact-priorities")','chapterArtifacts','chapterResearch','Physical archive','Artifacts from this chapter','Artifact research','Evidence boundary','Open the complete artifact museum'),
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
    for token in ('data/artifacts.json','data/artifact-priorities.json','assets/artifacts/','image_pending','digitized','research lead','provenance over decoration'):
        if token not in workflow_text:
            errors.append(f'ARTIFACT-WORKFLOW.md missing workflow token: {token}')

route=ROOT/'artifacts/index.html'
if not route.is_file():
    errors.append('missing clean /artifacts/ route entry')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'OK: {len(artifacts)} cataloged artifacts and {len(priorities)} biography research priorities validated across museum coverage, digitization workflow, exact events, annual editions, venue profiles, life chapters, recurring journeys, and evidence fact locks.')
