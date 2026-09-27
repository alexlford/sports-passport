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
ALLOWED_CONTEXTS={'event_ids','team_slugs','venue_slugs','phase_keys','ranking_refs'}

def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
manifest=load(Path('data/events.json'))
events=[]
for chunk in manifest.get('chunks',[]): events.extend(load(Path('data')/chunk))
by_id={e.get('id'):e for e in events if e.get('id')}
artifacts=load(Path('data/artifacts.json'))
priorities=load(Path('data/artifact-priorities.json'))
phases=load(Path('data/phases.json'))
phase_by_key={p.get('key'):p for p in phases if p.get('key')}
venues=load(Path('data/venues.json'))+load(Path('data/venue-additions.json'))
venue_slugs={v.get('slug') for v in venues if v.get('slug')}
aliases=load(Path('data/team-aliases.json'))
team_slugs=set()
for event in events:
    for team in event.get('teams') or []:
        canonical=aliases.get(team,team)
        slug='-'.join(''.join(ch.lower() if ch.isalnum() else ' ' for ch in canonical.replace('&','and')).split())
        team_slugs.add(slug)
rankings=load(Path('data/curated-rankings.json'))
valid_ranking_refs=set()
for key in ('sports_experiences','favorite_venues','best_venues'):
    valid_ranking_refs.update(f'{key}:{item.get("rank")}' for item in rankings.get(key,[]) if item.get('rank') is not None)
media_catalog=load(Path('data/media.json'))
if media_catalog.get('schema_version')!=1 or not isinstance(media_catalog.get('items'),list):
    errors.append('data/media.json must use schema_version 1 with an items array')
media_items=media_catalog.get('items') if isinstance(media_catalog.get('items'),list) else []
media_by_id={}
for item in media_items:
    mid=item.get('id')
    if not mid: errors.append('media item missing id'); continue
    if mid in media_by_id: errors.append(f'duplicate media id: {mid}')
    media_by_id[mid]=item
    if item.get('kind')!='image': errors.append(f'{mid} must use kind=image')
    for field in ('src','alt','width','height','contexts','sources'):
        if item.get(field) in (None,'',[],{}): errors.append(f'{mid} missing {field}')
    if not isinstance(item.get('width'),int) or item.get('width',0)<=0 or not isinstance(item.get('height'),int) or item.get('height',0)<=0:
        errors.append(f'{mid} width/height must be positive integers')
    src=item.get('src')
    if src and not (ROOT/src).is_file(): errors.append(f'{mid} fallback media does not exist: {src}')
    formats=set()
    for source in item.get('sources') or []:
        fmt=str(source.get('format','')).lower(); path=source.get('src'); formats.add(fmt)
        if fmt not in {'avif','webp'}: errors.append(f'{mid} unsupported optimized format: {fmt}')
        if not path or not (ROOT/path).is_file(): errors.append(f'{mid} optimized source missing: {path}')
    if media_items and not {'avif','webp'}.issubset(formats): errors.append(f'{mid} must provide both AVIF and WebP sources')
    contexts=item.get('contexts') or {}
    unknown=set(contexts)-ALLOWED_CONTEXTS
    if unknown: errors.append(f'{mid} unsupported context keys: {sorted(unknown)}')
    if not any(isinstance(contexts.get(k),list) and contexts.get(k) for k in ALLOWED_CONTEXTS): errors.append(f'{mid} needs at least one non-empty context')
    for event_id in contexts.get('event_ids') or []:
        if event_id not in by_id: errors.append(f'{mid} references missing event {event_id}')
    for phase_key in contexts.get('phase_keys') or []:
        if phase_key not in phase_by_key: errors.append(f'{mid} references missing phase {phase_key}')
    for venue_slug in contexts.get('venue_slugs') or []:
        if venue_slug not in venue_slugs: errors.append(f'{mid} references missing venue slug {venue_slug}')
    for team_slug in contexts.get('team_slugs') or []:
        if team_slug not in team_slugs: errors.append(f'{mid} references missing team slug {team_slug}')
    for ref in contexts.get('ranking_refs') or []:
        if ref not in valid_ranking_refs: errors.append(f'{mid} references missing ranking {ref}')

artifact_event_ids=set(); seen=set()
for artifact in artifacts:
    aid=artifact.get('id')
    if not aid: errors.append('artifact missing id')
    elif aid in seen: errors.append(f'duplicate artifact id: {aid}')
    else: seen.add(aid)
    event_id=artifact.get('event_id'); artifact_event_ids.add(event_id)
    if event_id not in by_id: errors.append(f'{aid or "artifact"} references missing event {event_id}')
    for field in ('type','title','summary','provenance','digitization_status'):
        if not artifact.get(field): errors.append(f'{aid or "artifact"} missing {field}')
    if artifact.get('type') not in ALLOWED_TYPES: errors.append(f'{aid} unsupported type {artifact.get("type")}')
    if artifact.get('digitization_status') not in ALLOWED_STATUS: errors.append(f'{aid} unsupported digitization status')
    if artifact.get('media') not in (None,''): errors.append(f'{aid} must use media_id rather than legacy media paths')
    media_id=artifact.get('media_id')
    if media_id:
        if media_id not in media_by_id: errors.append(f'{aid} references missing media ID {media_id}')
        if artifact.get('digitization_status')!='digitized': errors.append(f'{aid} with media_id must be digitized')
    elif artifact.get('digitization_status')!='image_pending': errors.append(f'{aid} without media_id must remain image_pending')

priority_seen=set()
for priority in priorities:
    pid=priority.get('id')
    if not pid: errors.append('artifact research priority missing id')
    elif pid in priority_seen: errors.append(f'duplicate artifact research priority id: {pid}')
    else: priority_seen.add(pid)
    for field in ('title','phase_key','category','priority','status','event_ids','summary','research_note','candidate_types'):
        if priority.get(field) in (None,'',[]): errors.append(f'{pid or "artifact research priority"} missing {field}')
    if priority.get('status') not in ALLOWED_PRIORITY_STATUS: errors.append(f'{pid} unsupported research status')
    if priority.get('category') not in ALLOWED_PRIORITY_CATEGORY: errors.append(f'{pid} unsupported research category')
    phase=phase_by_key.get(priority.get('phase_key'))
    if not phase: errors.append(f'{pid} references missing phase {priority.get("phase_key")}')
    event_ids=priority.get('event_ids') or []
    if len(event_ids)!=len(set(event_ids)): errors.append(f'{pid} repeats event IDs')
    for event_id in event_ids:
        event=by_id.get(event_id)
        if not event: errors.append(f'{pid} references missing event {event_id}'); continue
        if event_id in artifact_event_ids: errors.append(f'{pid} references {event_id}, which already has a cataloged artifact')
        if phase and not (int(phase.get('start',-9999))<=int(event.get('year',-9999))<=int(phase.get('end',9999))): errors.append(f'{pid} event {event_id} falls outside phase')
    unsupported=set(priority.get('candidate_types') or [])-ALLOWED_TYPES
    if unsupported: errors.append(f'{pid} unsupported candidate types: {sorted(unsupported)}')
    if priority.get('status')=='needs_exact_event_confirmation' and len(event_ids)<2: errors.append(f'{pid} needs multiple candidate events')
    if priority.get('category')=='verified_early_archive':
        for event_id in event_ids:
            event=by_id.get(event_id)
            if event and (int(event.get('year',9999))>=2006 or event.get('attendance_status')!='verified'): errors.append(f'{pid} early-archive event {event_id} must be verified and pre-2006')

expected={'evt-0001':'artifact-0001','evt-0008':'artifact-0002'}
for event_id,artifact_id in expected.items():
    event=by_id.get(event_id)
    if not event or event.get('attendance_status')!='verified' or event.get('verification')!='old ticket stub': errors.append(f'{event_id} must remain verified by old ticket stub')
    if not any(a.get('id')==artifact_id and a.get('event_id')==event_id and a.get('type')=='ticket_stub' for a in artifacts): errors.append(f'{event_id} must remain linked to {artifact_id}')
priority_by_id={p.get('id'):p for p in priorities if p.get('id')}
indiana=priority_by_id.get('artifact-priority-0001')
if not indiana or indiana.get('event_ids')!=['evt-0020'] or indiana.get('category')!='verified_early_archive': errors.append('artifact-priority-0001 must remain the Indiana-at-SIU candidate')
penny=priority_by_id.get('artifact-priority-0003')
if not penny or penny.get('event_ids')!=['evt-0250','evt-0251'] or penny.get('status')!='needs_exact_event_confirmation': errors.append("Penny's first-game lead must preserve both candidate events")

for rel in ('artifacts.html','artifacts/index.html','ARTIFACT-WORKFLOW.md','data/artifacts.json','data/artifact-priorities.json','data/media.json','assets/archive-media.js','assets/archive-media.css'):
    if not (ROOT/rel).is_file(): errors.append(f'retained artifact/media file missing: {rel}')
workflow=(ROOT/'ARTIFACT-WORKFLOW.md').read_text(encoding='utf-8')
for token in ('data/media.json','stable media','AVIF','WebP','alt text','loading="lazy"','provenance over decoration'):
    if token not in workflow: errors.append(f'ARTIFACT-WORKFLOW.md missing media workflow token: {token}')
helper=(ROOT/'assets/archive-media.js').read_text(encoding='utf-8')
for token in ('loading="lazy"','decoding="async"','image/avif','image/webp','media_id','contextItems'):
    if token not in helper: errors.append(f'archive media helper missing token: {token}')

integration={
    'event.html':("D.load('artifacts')","D.load('media')",'archive-evidence-section'),
    'phase.html':('D.load("artifacts")','D.load("media")','Physical archive'),
    'venue-profile.html':("D.load('artifacts')","D.load('media')",'Physical archive'),
    'team-profile.html':('D.load("artifacts")','D.load("media")','Physical archive'),
    'favorites.html':("D.load('media')",'canonMediaSection','Selected source images')
}
for rel,tokens in integration.items():
    text=(ROOT/rel).read_text(encoding='utf-8')
    for token in tokens:
        if token not in text: errors.append(f'{rel} missing selective media integration: {token}')
    if 'href="artifacts.html"' in text or 'href="/artifacts/"' in text: errors.append(f'{rel} must not expose the full artifact workbench')

sitemap=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
if '/artifacts/' in sitemap or '/artifacts.html' in sitemap: errors.append('public sitemap must keep the full Artifacts workbench unpublished')
robots=(ROOT/'robots.txt').read_text(encoding='utf-8')
for token in ('Disallow: /artifacts/','Disallow: /artifacts.html'):
    if token not in robots: errors.append(f'robots.txt missing {token}')
density=(ROOT/'assets/density.css').read_text(encoding='utf-8')
if 'body:has(.artifact-hero){display:none!important}' not in density: errors.append('retained artifact workbench must stay suppressed from direct presentation')

if errors:
    print('\n'.join('ERROR: '+e for e in errors)); sys.exit(1)
print(f'OK: {len(artifacts)} known physical artifacts, {len(media_items)} stable media items, selective public context integration, optimized-image contract, and {len(priorities)} research priorities validated.')
