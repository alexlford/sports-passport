#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

def replace_once(rel,old,new):
    p=ROOT/rel
    text=p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing replacement target in {rel}: {old[:160]!r}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

def evidence_for(event):
    verification=str(event.get('verification') or '').strip()
    source=str(event.get('source') or '').strip()
    text=f'{verification} {source}'.lower()
    status=event.get('attendance_status')
    if 'ticket' in text:
        kind,basis='ticket_stub','physical_artifact'
    elif 'screenshot' in text or 'attendance record' in text:
        kind,basis='attendance_record','attendance_record'
    elif any(token in text for token in ('direct','confirm','user verified','user-confirmed','specific memory')):
        kind,basis='direct_confirmation','direct_confirmation'
    elif status=='notional':
        kind,basis='reconstructed_archive','reconstruction'
    elif status=='verified':
        kind,basis='verified_archive','verification_note'
    else:
        kind,basis='documented_archive','archive_record'
    evidence={'type':kind,'basis':basis}
    provenance=verification or source
    if provenance:
        evidence['provenance']=provenance
    return evidence

manifest=json.loads((DATA/'events.json').read_text(encoding='utf-8'))
count=0
for chunk in manifest['chunks']:
    path=DATA/chunk
    events=json.loads(path.read_text(encoding='utf-8'))
    for event in events:
        event['evidence']=evidence_for(event)
        count+=1
    path.write_text(json.dumps(events,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

# Shared evidence semantics: UI reads structured evidence only; legacy source remains provenance/history.
replace_once('assets/sports-passport-data.js',
'''  const confidenceLabel = e => isNotionalEvent(e) ? "Notional" : (isVerifiedEvent(e) ? "Verified" : "Documented");

  const canonicalTeam = team => teamAliases[team] || team;''',
'''  const confidenceLabel = e => isNotionalEvent(e) ? "Notional" : (isVerifiedEvent(e) ? "Verified" : "Documented");
  const EVIDENCE_LABELS = {
    ticket_stub: "Ticket-stub evidence",
    attendance_record: "Attendance record",
    direct_confirmation: "Direct confirmation",
    verified_archive: "Verified archive evidence",
    reconstructed_archive: "Reconstructed early archive",
    documented_archive: "Documented archive record"
  };
  const evidenceType = e => e?.evidence?.type || null;
  const evidenceLabel = e => EVIDENCE_LABELS[evidenceType(e)] || "Archive evidence";
  const evidenceProvenance = e => e?.evidence?.provenance || "";

  const canonicalTeam = team => teamAliases[team] || team;''')
replace_once('assets/sports-passport-data.js',
'''  return {load,slug,score,matchup,counts,normalizeCity,isNotionalEvent,isVerifiedEvent,isConfirmedEvent,confirmedEvents,notionalEvents,confidenceLabel,canonicalTeam,eventTeams,teamPalette,venueByKey,venueName,venueHref,venueEvents,yearEvents,teamEvents,phaseEvents,journeyEvents,recordForTeam,enhanceDensity};''',
'''  return {load,slug,score,matchup,counts,normalizeCity,isNotionalEvent,isVerifiedEvent,isConfirmedEvent,confirmedEvents,notionalEvents,confidenceLabel,evidenceType,evidenceLabel,evidenceProvenance,canonicalTeam,eventTeams,teamPalette,venueByKey,venueName,venueHref,venueEvents,yearEvents,teamEvents,phaseEvents,journeyEvents,recordForTeam,enhanceDensity};''')

replace_once('event.html',
'''  const evidence=(()=>{const s=String(event.source||'').toLowerCase();if(s.includes('ticket'))return'Ticket-stub evidence';if(s.includes('screenshot'))return'Attendance record';if(s.includes('direct')||s.includes('confirm'))return'Direct confirmation';if(D.isVerifiedEvent(event))return'Verified archive evidence';if(D.isNotionalEvent(event))return'Reconstructed early archive';return'Documented archive record'})();''',
'''  const evidence=D.evidenceLabel(event),evidenceProvenance=D.evidenceProvenance(event);''')
replace_once('event.html',
'''<div class="record-row"><span>Evidence class</span><strong>${evidence}</strong></div><div class="record-row"><span>Event ID</span>''',
'''<div class="record-row"><span>Evidence class</span><strong>${evidence}</strong></div>${evidenceProvenance?`<div class="record-row"><span>Evidence provenance</span><strong>${escapeHtml(evidenceProvenance)}</strong></div>`:''}<div class="record-row"><span>Event ID</span>''')

# About page explains the distinction between confidence and evidence class.
replace_once('about.html',
'''    <div class="confidence-band"><strong>Pre-2006 records are explicitly marked Verified or Notional.</strong><p>Verified entries have surviving evidence or direct confirmation. The old Camden Yards games are supported by ticket stubs, and Indiana at SIU is directly verified. Other early entries may be plausible reconstructions of games I likely attended and are labeled Notional rather than presented as exact attendance facts.</p></div>''',
'''    <div class="confidence-band"><strong>Pre-2006 records are explicitly marked Verified or Notional.</strong><p>Verified entries have surviving evidence or direct confirmation. The old Camden Yards games are supported by ticket stubs, and Indiana at SIU is directly verified. Other early entries may be plausible reconstructions of games I likely attended and are labeled Notional rather than presented as exact attendance facts.</p><p><strong>Evidence is structured separately from confidence.</strong> Each event records an explicit evidence type and basis, such as ticket stub, attendance record, direct confirmation, documented archive record, or reconstruction. Source notes remain provenance; the site no longer guesses evidence classes from source wording at display time.</p></div>''')

# Data validator: require structured evidence and validate optional richer event fields/media links.
replace_once('tools/validate_data.py',
'''corrections=load_json("corrections.json") or {}
''',
'''corrections=load_json("corrections.json") or {}
media_catalog=load_json("media.json", optional=True) or {"items":[]}
media_ids={item.get("id") for item in media_catalog.get("items",[]) if isinstance(item,dict) and item.get("id")} if isinstance(media_catalog,dict) else set()
EVIDENCE_TYPES={"ticket_stub","attendance_record","direct_confirmation","verified_archive","reconstructed_archive","documented_archive"}
EVIDENCE_BASES={"physical_artifact","attendance_record","direct_confirmation","verification_note","reconstruction","archive_record"}
''')
replace_once('tools/validate_data.py',
'''    elif status is not None and status not in {"verified","notional"}:
        errors.append(f'{eid}: attendance_status must be verified or notional when present')
''',
'''    elif status is not None and status not in {"verified","notional"}:
        errors.append(f'{eid}: attendance_status must be verified or notional when present')
    evidence=e.get("evidence")
    if not isinstance(evidence,dict):
        errors.append(f'{eid}: evidence must be a structured object')
    else:
        if evidence.get("type") not in EVIDENCE_TYPES: errors.append(f'{eid}: unsupported evidence type {evidence.get("type")}')
        if evidence.get("basis") not in EVIDENCE_BASES: errors.append(f'{eid}: unsupported evidence basis {evidence.get("basis")}')
        if "provenance" in evidence and (not isinstance(evidence["provenance"],str) or not evidence["provenance"].strip()): errors.append(f'{eid}: evidence provenance must be a non-empty string when present')
        if status=="notional" and evidence.get("type")!="reconstructed_archive": errors.append(f'{eid}: notional event must use reconstructed_archive evidence')
        if evidence.get("type")=="ticket_stub" and evidence.get("basis")!="physical_artifact": errors.append(f'{eid}: ticket_stub evidence must use physical_artifact basis')
    for field in ("competition_round","site_type","personal_note"):
        if field in e and (not isinstance(e[field],str) or not e[field].strip()): errors.append(f'{eid}: {field} must be a non-empty string when present')
    media_refs=e.get("media_ids")
    if media_refs is not None:
        if not isinstance(media_refs,list) or any(not isinstance(x,str) or not x for x in media_refs): errors.append(f'{eid}: media_ids must be an array of non-empty strings')
        else:
            if len(media_refs)!=len(set(media_refs)): errors.append(f'{eid}: media_ids contains duplicates')
            for media_id in media_refs:
                if media_id not in media_ids: errors.append(f'{eid}: media_ids references unknown media {media_id}')
    personal_context=e.get("personal_context")
    if personal_context is not None:
        if not isinstance(personal_context,dict): errors.append(f'{eid}: personal_context must be an object')
        else:
            for key,value in personal_context.items():
                if not isinstance(key,str) or not key.strip(): errors.append(f'{eid}: personal_context keys must be non-empty strings')
                if not (isinstance(value,str) and value.strip()) and not (isinstance(value,list) and value and all(isinstance(x,str) and x.strip() for x in value)): errors.append(f'{eid}: personal_context values must be non-empty strings or arrays of non-empty strings')
''')

# Lock Event Passport to the structured helper and reject regression to source-string guessing.
replace_once('tools/validate_event_passports.py',
'''        ("Event ID", "stable event identifier rendering"),
''',
'''        ("Event ID", "stable event identifier rendering"),
        ("D.evidenceLabel(event)", "structured evidence rendering"),
        ("Evidence provenance", "evidence provenance rendering"),
''')
replace_once('tools/validate_event_passports.py',
'''    for token, label in (''',
'''    if "String(event.source" in text or "source||''" in text:
        errors.append("event.html must not infer evidence class from source-string wording")
    for token, label in (''')

# Document the richer optional schema for future updates.
workflow=ROOT/'UPDATE-WORKFLOW.md'
text=workflow.read_text(encoding='utf-8')
addition='''\n\n## Structured event evidence and optional context\n\nEvery event record carries an `evidence` object with an explicit `type` and `basis`. Display code reads these structured fields through `SportsPassportData.evidenceLabel()`; `source` and `verification` remain provenance/history and are not parsed to determine the public evidence class.\n\nSupported evidence types are `ticket_stub`, `attendance_record`, `direct_confirmation`, `verified_archive`, `reconstructed_archive`, and `documented_archive`. Optional `evidence.provenance` preserves the human-readable source note.\n\nEvent records may also add `competition_round`, `site_type`, `personal_note`, `media_ids`, and `personal_context`. `media_ids` must resolve to stable IDs in `data/media.json`; `personal_context` is a small structured object whose values are non-empty strings or arrays of strings. These fields are optional so ordinary game additions stay lightweight.\n'''
if '## Structured event evidence and optional context' not in text:
    workflow.write_text(text.rstrip()+addition+'\n',encoding='utf-8')

# Browser checks distinguish a ticket-backed early record from a modern documented record.
(ROOT/'tests/browser/structured-evidence.spec.js').write_text(r'''const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Structured evidence assertions run once on desktop.');

test('ticket-backed early event renders explicit structured evidence and provenance', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0001/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.status-row')).toContainText('Ticket-stub evidence');
  await expect(page.locator('.record-row', { hasText: 'Evidence provenance' })).toContainText(/ticket/i);
});

test('modern event renders documented evidence without source-string inference', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.status-row')).toContainText('Documented archive record');
  await expect(page.locator('.record-row', { hasText: 'Evidence class' })).toContainText('Documented archive record');
});
''',encoding='utf-8')

print(f'Migrated {count} events to structured evidence and added richer event-schema validation.')
