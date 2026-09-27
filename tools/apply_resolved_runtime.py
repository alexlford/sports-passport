#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def replace_once(rel, old, new):
    path=ROOT/rel
    text=path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing replacement target in {rel}: {old[:180]!r}')
    path.write_text(text.replace(old,new,1),encoding='utf-8')

old_load='''async function load(name) {
  if (!cache[name]) cache[name] = fetchJson(`/data/${name}.json`).then(async value => {
    if (name === "team-aliases" && value && typeof value === "object" && !Array.isArray(value)) {
      teamAliases = value;
      return value;
    }
    if (name === "events" && value && Array.isArray(value.chunks)) {
      const parts = await Promise.all(value.chunks.map(file => fetchJson(`/data/${file}`)));
      let events = parts.flat();
      try {
        const corrections = await fetchJson("/data/corrections.json", {});
        events = events.map(e => corrections[e.id] ? {...e, ...corrections[e.id]} : e);
      } catch (_) {}
      try {
        const aliases = await fetchJson("/data/team-aliases.json", {});
        if (aliases && typeof aliases === "object" && !Array.isArray(aliases)) teamAliases = aliases;
      } catch (_) {}
      events = events.map(e => ({
        ...e,
        city: normalizeCity(e.city),
        teams_canonical: Array.isArray(e.teams) ? e.teams.map(t => teamAliases[t] || t) : []
      }));
      return events;
    }
    if (name === "venues" && Array.isArray(value)) {
      let venues = value;
      try {
        const additions = await fetchJson("/data/venue-additions.json", []);
        if (Array.isArray(additions) && additions.length) {
          const byKey = new Map(venues.map(v => [v.key, v]));
          additions.forEach(v => byKey.set(v.key, {...(byKey.get(v.key)||{}), ...v}));
          venues = [...byKey.values()];
        }
      } catch (_) {}
      try {
        const corrections = await fetchJson("/data/venue-corrections.json", {});
        return venues.map(v => corrections[v.key] ? {...v, ...corrections[v.key], city: normalizeCity(corrections[v.key].city || v.city)} : {...v, city: normalizeCity(v.city)});
      } catch (_) {
        return venues.map(v => ({...v, city: normalizeCity(v.city)}));
      }
    }
    return value;
  });
  return cache[name];
}
'''
new_load='''async function load(name) {
  if (!cache[name]) {
    if (name === "events") {
      cache[name] = Promise.all([
        fetchJson("/data/resolved-events.json"),
        fetchJson("/data/team-aliases.json", {})
      ]).then(([events,aliases]) => {
        if (aliases && typeof aliases === "object" && !Array.isArray(aliases)) teamAliases = aliases;
        return events;
      });
    } else if (name === "venues") {
      cache[name] = fetchJson("/data/resolved-venues.json");
    } else {
      cache[name] = fetchJson(`/data/${name}.json`).then(value => {
        if (name === "team-aliases" && value && typeof value === "object" && !Array.isArray(value)) teamAliases = value;
        return value;
      });
    }
  }
  return cache[name];
}
'''
replace_once('assets/sports-passport-data.js',old_load,new_load)

# Persistent CI freshness gate.
workflow=ROOT/'.github/workflows/validate.yml'
text=workflow.read_text(encoding='utf-8')
needle='''      - name: Validate archive data
        run: python tools/validate_data.py
'''
replacement='''      - name: Validate archive data
        run: python tools/validate_data.py
      - name: Validate resolved public data
        run: python tools/build_resolved_data.py --check
'''
if 'Validate resolved public data' not in text:
    if needle not in text: raise SystemExit('missing validate.yml archive data step')
    workflow.write_text(text.replace(needle,replacement,1),encoding='utf-8')

# Update authoring workflow documentation.
workflow_doc=ROOT/'UPDATE-WORKFLOW.md'
text=workflow_doc.read_text(encoding='utf-8')
addition='''\n\n## Generated resolved public data\n\nThe event chunks, `corrections.json`, `team-aliases.json`, `venues.json`, `venue-additions.json`, and `venue-corrections.json` are the authoring/source layer. The browser does not merge these overlays. Run `python tools/build_resolved_data.py` after source changes to generate `data/resolved-events.json` and `data/resolved-venues.json`, then refresh the cache manifest and static routes.\n\n`venue-additions.json` is therefore an authoring overlay/history file, not a second public venue database. New keys are appended to the resolved venue list; an existing key updates the base record deterministically. `corrections.json` and `venue-corrections.json` work the same way: they remain auditable source patches while the public runtime reads only compiled results. Generated resolved files must not be hand-edited; CI runs `python tools/build_resolved_data.py --check` and fails if they drift from the source layer.\n'''
if '## Generated resolved public data' not in text:
    workflow_doc.write_text(text.rstrip()+addition+'\n',encoding='utf-8')

# Source-level contract validator for runtime separation.
(ROOT/'tools/validate_resolved_runtime.py').write_text(r'''#!/usr/bin/env python3
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
''',encoding='utf-8')

# Add this small source contract to normal CI after generated freshness.
text=workflow.read_text(encoding='utf-8')
needle='''      - name: Validate resolved public data
        run: python tools/build_resolved_data.py --check
'''
replacement='''      - name: Validate resolved public data
        run: |
          python tools/build_resolved_data.py --check
          python tools/validate_resolved_runtime.py
'''
workflow.write_text(text.replace(needle,replacement,1),encoding='utf-8')

(ROOT/'tests/browser/resolved-data.spec.js').write_text(r'''const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Resolved-data network assertions run once on desktop.');

test('annual edition reads compiled data and never requests source overlays', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  const paths=[];
  page.on('request', request => { try { paths.push(new URL(request.url()).pathname); } catch (_) {} });
  await page.goto('/years/2026/', { waitUntil: 'networkidle' });
  expect(paths).toContain('/data/resolved-events.json');
  expect(paths).toContain('/data/resolved-venues.json');
  expect(paths).not.toContain('/data/corrections.json');
  expect(paths).not.toContain('/data/venue-additions.json');
  expect(paths).not.toContain('/data/venue-corrections.json');
});

test('compiled event corrections remain visible through normal pages', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0222/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.event-hero')).toContainText('Hockey');
});
''',encoding='utf-8')

print('Integrated resolved public datasets into the runtime and CI contract.')
