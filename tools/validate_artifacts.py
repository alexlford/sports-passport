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
    unsupported=set(priority.get('candidate_types') or [])-ALLOWED_TYPES
    if unsupported:
        errors.append(f'{pid or "priority"} has unsupported candidate types: {sorted(unsupported)}')
    if priority.get('status')=='needs_exact_event_confirmation' and len(event_ids)<2:
        errors.append(f'{pid or "priority"} needs multiple candidate events for exact-event confirmation')
    if priority.get('category')=='verified_early_archive':
        for event_id in event_ids:
            event=by_id.get(event_id)
            if event and (int(event.get('year',9999))>=2006 or event.get('attendance_status')!='verified'):
                errors.append(f'{pid or "priority"} verified_early_archive event {event_id} must be verified and pre-2006')

# Preserve known evidence and research facts even while the feature is unpublished.
expected={'evt-0001':'artifact-0001','evt-0008':'artifact-0002'}
for event_id,artifact_id in expected.items():
    event=by_id.get(event_id)
    if not event or event.get('attendance_status')!='verified' or event.get('verification')!='old ticket stub':
        errors.append(f'{event_id} must remain verified by old ticket stub')
    if not any(a.get('id')==artifact_id and a.get('event_id')==event_id and a.get('type')=='ticket_stub' for a in artifacts):
        errors.append(f'{event_id} must remain linked to {artifact_id}')

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

# Keep the implementation files intact for possible future use.
for rel in ('artifacts.html','artifacts/index.html','ARTIFACT-WORKFLOW.md','data/artifacts.json','data/artifact-priorities.json'):
    if not (ROOT/rel).is_file():
        errors.append(f'retained artifact file missing: {rel}')

workflow=ROOT/'ARTIFACT-WORKFLOW.md'
if workflow.is_file():
    workflow_text=workflow.read_text(encoding='utf-8')
    for token in ('data/artifacts.json','data/artifact-priorities.json','assets/artifacts/','image_pending','digitized','research lead','provenance over decoration'):
        if token not in workflow_text:
            errors.append(f'ARTIFACT-WORKFLOW.md missing workflow token: {token}')

# The feature is intentionally not public-facing. Core public templates must neither load it nor link to it.
public_templates=('index.html','annuals.html','year.html','event.html','venue-profile.html','phase.html','journey-profile.html')
for name in public_templates:
    path=ROOT/name
    if not path.is_file():
        errors.append(f'missing public template {name}')
        continue
    text=path.read_text(encoding='utf-8')
    forbidden=("D.load('artifacts')",'D.load("artifacts")',"D.load('artifact-priorities')",'D.load("artifact-priorities")','href="artifacts.html"','href="/artifacts/"')
    for token in forbidden:
        if token in text:
            errors.append(f'{name} still exposes retained artifact feature: {token}')

home=(ROOT/'index.html').read_text(encoding='utf-8') if (ROOT/'index.html').is_file() else ''
if '<h3>Artifacts</h3>' in home or 'journeys, artifacts,' in home:
    errors.append('homepage still advertises Artifacts')

sitemap=(ROOT/'sitemap.xml').read_text(encoding='utf-8') if (ROOT/'sitemap.xml').is_file() else ''
if '/artifacts/' in sitemap or '/artifacts.html' in sitemap:
    errors.append('public sitemap still includes Artifacts')
robots=(ROOT/'robots.txt').read_text(encoding='utf-8') if (ROOT/'robots.txt').is_file() else ''
for token in ('Disallow: /artifacts/','Disallow: /artifacts.html'):
    if token not in robots:
        errors.append(f'robots.txt missing artifact exclusion: {token}')

# Retained page is suppressed from presentation if reached directly.
density=(ROOT/'assets'/'density.css').read_text(encoding='utf-8') if (ROOT/'assets'/'density.css').is_file() else ''
if 'body:has(.artifact-hero){display:none!important}' not in density:
    errors.append('retained artifact page is not suppressed from direct public presentation')

if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'OK: {len(artifacts)} cataloged artifacts and {len(priorities)} research priorities remain validated and retained internally while Artifacts stays excluded from public navigation, templates, sitemap, and crawl surface.')
