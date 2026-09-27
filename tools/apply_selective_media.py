#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def replace_once(rel, old, new):
    path=ROOT/rel
    text=path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing replacement target in {rel}: {old[:160]!r}')
    path.write_text(text.replace(old,new,1),encoding='utf-8')

def write(rel, content):
    path=ROOT/rel
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')

# Stable, context-aware media catalog. It starts empty because no source image should be invented.
write('data/media.json', json.dumps({
    'schema_version':1,
    'items':[]
}, indent=2)+'\n')

# Move artifact media linking to stable media IDs while preserving the two known physical objects.
artifacts_path=ROOT/'data/artifacts.json'
artifacts=json.loads(artifacts_path.read_text(encoding='utf-8'))
for artifact in artifacts:
    artifact.setdefault('media_id',None)
    if artifact.get('media') is None:
        artifact.pop('media',None)
artifacts_path.write_text(json.dumps(artifacts,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

write('assets/archive-media.js', r'''window.SportsPassportMedia=(()=>{
  const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const items=catalog=>Array.isArray(catalog)?catalog:(Array.isArray(catalog?.items)?catalog.items:[]);
  const mediaById=(catalog,id)=>id?items(catalog).find(item=>item.id===id)||null:null;
  const typeLabel=type=>({ticket_stub:'Ticket stub',credential:'Credential',program:'Program',seat_view:'Seat view',keepsake:'Keepsake',photo:'Photo'}[type]||'Archive artifact');
  const sourceOf=(item,format)=>(item?.sources||[]).find(source=>String(source.format||'').toLowerCase()===format)?.src||'';
  function picture(item,{className='archive-media-picture'}={}){
    if(!item?.src)return '';
    const avif=sourceOf(item,'avif'),webp=sourceOf(item,'webp');
    const dimensions=(Number(item.width)>0&&Number(item.height)>0)?` width="${Number(item.width)}" height="${Number(item.height)}"`:'';
    return `<picture class="${escapeHtml(className)}">${avif?`<source type="image/avif" srcset="${escapeHtml(avif)}">`:''}${webp?`<source type="image/webp" srcset="${escapeHtml(webp)}">`:''}<img src="${escapeHtml(item.src)}" alt="${escapeHtml(item.alt||'')}"${dimensions} loading="lazy" decoding="async"></picture>`;
  }
  function contextItems(catalog,context={}){
    const wanted={
      event_ids:context.eventIds||[],
      team_slugs:context.teamSlugs||[],
      venue_slugs:context.venueSlugs||[],
      phase_keys:context.phaseKeys||[],
      ranking_refs:context.rankingRefs||[]
    };
    return items(catalog).filter(item=>Object.entries(wanted).some(([key,values])=>values.length&&Array.isArray(item.contexts?.[key])&&item.contexts[key].some(value=>values.includes(value))));
  }
  function mediaCard(item){
    const visual=picture(item);
    if(!visual)return '';
    return `<article class="archive-evidence-card media-card"><div class="archive-evidence-visual">${visual}</div><div class="archive-evidence-body"><div class="archive-evidence-chip">Archive image</div>${item.caption?`<p>${escapeHtml(item.caption)}</p>`:''}${item.credit?`<p class="archive-evidence-provenance">${escapeHtml(item.credit)}</p>`:''}</div></article>`;
  }
  function artifactCard(artifact,catalog,{eventHref=''}={}){
    const media=mediaById(catalog,artifact?.media_id),visual=picture(media);
    return `<article class="archive-evidence-card artifact-card" data-artifact-id="${escapeHtml(artifact?.id||'')}">${visual?`<div class="archive-evidence-visual">${visual}</div>`:''}<div class="archive-evidence-body"><div class="archive-evidence-kicker">${escapeHtml(typeLabel(artifact?.type))}</div><h3>${escapeHtml(artifact?.title||'Archive artifact')}</h3><span class="archive-evidence-chip ${media?'digitized':'pending'}">${media?'Digitized source':'Physical artifact cataloged · image pending'}</span>${artifact?.summary?`<p>${escapeHtml(artifact.summary)}</p>`:''}${artifact?.provenance?`<p class="archive-evidence-provenance"><strong>Provenance:</strong> ${escapeHtml(artifact.provenance)}</p>`:''}${eventHref?`<a class="archive-evidence-link" href="${escapeHtml(eventHref)}">Open Event Passport →</a>`:''}</div></article>`;
  }
  return {items,mediaById,picture,contextItems,mediaCard,artifactCard,typeLabel};
})();
''')

write('assets/archive-media.css', '''.archive-evidence-section{margin:58px 0}.archive-evidence-section .archive-evidence-intro{max-width:680px;color:var(--muted);line-height:1.6}.archive-evidence-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}.archive-evidence-card{overflow:hidden;border:1px solid var(--line);border-radius:19px;background:#fffdf8;box-shadow:0 7px 22px rgba(17,43,60,.035)}.archive-evidence-visual{aspect-ratio:16/10;background:#eee4d1;border-bottom:1px solid var(--line);overflow:hidden}.archive-evidence-picture{display:block;width:100%;height:100%}.archive-evidence-picture img{display:block;width:100%;height:100%;object-fit:cover}.archive-evidence-body{padding:18px}.archive-evidence-kicker{font-size:.68rem;font-weight:950;letter-spacing:.1em;text-transform:uppercase;color:var(--red)}.archive-evidence-body h3{margin:.4rem 0 .65rem;font-size:1.25rem}.archive-evidence-body p{margin:.65rem 0;color:var(--muted);line-height:1.5;font-size:.86rem}.archive-evidence-chip{display:inline-flex;align-items:center;min-height:30px;padding:5px 9px;border:1px solid var(--line);border-radius:999px;background:#eef2f4;color:#315064;font-size:.64rem;font-weight:900;letter-spacing:.04em;text-transform:uppercase}.archive-evidence-chip.digitized{background:#e6f2e9;color:#255d38}.archive-evidence-chip.pending{background:#fff1cf;color:#76520b}.archive-evidence-provenance{font-size:.78rem!important}.archive-evidence-link{display:inline-flex;align-items:center;min-height:44px;margin-top:7px;font-size:.76rem;font-weight:900;text-underline-offset:3px}.canon-media-grid{margin:18px 0 0}.canon-media-grid .archive-evidence-card{min-width:0}@media(max-width:600px){.archive-evidence-section{margin:44px 0}.archive-evidence-grid{grid-template-columns:1fr}}
''')

# Event Passport: actual known artifacts surface only on the events they belong to; catalog media can be attached by event ID later.
replace_once('event.html','  <link rel="stylesheet" href="assets/event.css">\n','  <link rel="stylesheet" href="assets/event.css">\n  <link rel="stylesheet" href="assets/archive-media.css">\n')
replace_once('event.html','<script src="assets/sports-passport-data.js"></script>\n<script>','<script src="assets/sports-passport-data.js"></script>\n<script src="assets/archive-media.js"></script>\n<script>')
replace_once('event.html',"  const D=window.SportsPassportData;\n  const [events,venues,rankings,journeys]=await Promise.all([D.load('events'),D.load('venues'),D.load('curated-rankings'),D.load('journeys')]);","  const D=window.SportsPassportData,M=window.SportsPassportMedia;\n  const [events,venues,rankings,journeys,artifacts,media]=await Promise.all([D.load('events'),D.load('venues'),D.load('curated-rankings'),D.load('journeys'),D.load('artifacts'),D.load('media')]);")
replace_once('event.html',"  const sorted=[...events].sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));","  const eventArtifacts=(artifacts||[]).filter(a=>a.event_id===event.id);\n  const referencedMediaIds=new Set(eventArtifacts.map(a=>a.media_id).filter(Boolean));\n  const eventMedia=M.contextItems(media,{eventIds:[event.id]}).filter(item=>!referencedMediaIds.has(item.id));\n  const archiveCards=[...eventArtifacts.map(a=>M.artifactCard(a,media)),...eventMedia.map(item=>M.mediaCard(item))].filter(Boolean);\n  const physicalArchiveSection=archiveCards.length?`<section class=\"section archive-evidence-section\"><div class=\"head\"><div><div class=\"kicker\">Physical archive</div><h2>Evidence & keepsakes.</h2></div><p class=\"archive-evidence-intro\">Real objects and source images are attached only when they are known to exist and can be tied to this exact event.</p></div><div class=\"archive-evidence-grid\">${archiveCards.join('')}</div></section>`:'';\n  const sorted=[...events].sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));")
replace_once('event.html','</div></div>`:\'\'}</section><section class="section"><div class="head"><div><div class="kicker">Archive sequence</div>','</div></div>`:\'\'}</section>${physicalArchiveSection}<section class="section"><div class="head"><div><div class="kicker">Archive sequence</div>')

# Life chapters: surface only artifacts/media connected to events in the chapter or explicitly attached to the chapter.
replace_once('phase.html','<link rel="stylesheet" href="assets/phase.css">','<link rel="stylesheet" href="assets/phase.css"><link rel="stylesheet" href="assets/archive-media.css">')
replace_once('phase.html','<script src="assets/sports-passport-data.js"></script><script>','<script src="assets/sports-passport-data.js"></script><script src="assets/archive-media.js"></script><script>')
replace_once('phase.html','const D=window.SportsPassportData,[events,phases,narratives,rankings,venues]=await Promise.all([D.load("events"),D.load("phases"),D.load("phase-narratives"),D.load("curated-rankings"),D.load("venues")]);','const D=window.SportsPassportData,M=window.SportsPassportMedia,[events,phases,narratives,rankings,venues,artifacts,media]=await Promise.all([D.load("events"),D.load("phases"),D.load("phase-narratives"),D.load("curated-rankings"),D.load("venues"),D.load("artifacts"),D.load("media")]);')
replace_once('phase.html','chapterMoments=(rankings.sports_experiences||[]).filter(x=>x.event_id&&eventIds.has(x.event_id)),confirmed=','chapterMoments=(rankings.sports_experiences||[]).filter(x=>x.event_id&&eventIds.has(x.event_id)),chapterArtifacts=(artifacts||[]).filter(a=>eventIds.has(a.event_id)),referencedMediaIds=new Set(chapterArtifacts.map(a=>a.media_id).filter(Boolean)),chapterMedia=M.contextItems(media,{eventIds:[...eventIds],phaseKeys:[key]}).filter(item=>!referencedMediaIds.has(item.id)),archiveCards=[...chapterArtifacts.map(a=>M.artifactCard(a,media,{eventHref:`/events/?event=${encodeURIComponent(a.event_id)}`})),...chapterMedia.map(item=>M.mediaCard(item))].filter(Boolean),physicalArchiveSection=archiveCards.length?`<section class="section archive-evidence-section" style="--chapter-accent:${p.accent}"><div class="head"><div><div class="kicker">Physical archive</div><h2>Objects from this chapter.</h2></div><p class="archive-evidence-intro">Only known artifacts and sourced images appear here; missing scans stay labeled instead of being replaced with decorative stand-ins.</p></div><div class="archive-evidence-grid">${archiveCards.join("")}</div></section>`:"",confirmed=')
replace_once('phase.html','${storySection}${traditionsSection}${momentsSection}<section class="section panel">','${storySection}${traditionsSection}${physicalArchiveSection}${momentsSection}<section class="section panel">')

# Venue profiles: source media can be attached by venue slug or by one of the venue's exact events. Camden Yards immediately gains its two known ticket artifacts.
replace_once('venue-profile.html','  <link rel="stylesheet" href="assets/venue-profile.css">\n','  <link rel="stylesheet" href="assets/venue-profile.css">\n  <link rel="stylesheet" href="assets/archive-media.css">\n')
replace_once('venue-profile.html','<script src="assets/sports-passport-data.js"></script>\n<script>','<script src="assets/sports-passport-data.js"></script>\n<script src="assets/archive-media.js"></script>\n<script>')
replace_once('venue-profile.html',"  const D=window.SportsPassportData;\n  const [events,venues,rankings]=await Promise.all([D.load('events'),D.load('venues'),D.load('curated-rankings')]);","  const D=window.SportsPassportData,M=window.SportsPassportMedia;\n  const [events,venues,rankings,artifacts,media]=await Promise.all([D.load('events'),D.load('venues'),D.load('curated-rankings'),D.load('artifacts'),D.load('media')]);")
replace_once('venue-profile.html',"  const experienceById=Object.fromEntries((rankings.sports_experiences||[]).map(x=>[x.event_id,x])),signatureEvents=ev.map(e=>({event:e,rank:experienceById[e.id]})).filter(x=>x.rank).sort((a,b)=>a.rank.rank-b.rank.rank);","  const experienceById=Object.fromEntries((rankings.sports_experiences||[]).map(x=>[x.event_id,x])),signatureEvents=ev.map(e=>({event:e,rank:experienceById[e.id]})).filter(x=>x.rank).sort((a,b)=>a.rank.rank-b.rank.rank),eventIds=new Set(ev.map(e=>e.id)),venueArtifacts=(artifacts||[]).filter(a=>eventIds.has(a.event_id)),referencedMediaIds=new Set(venueArtifacts.map(a=>a.media_id).filter(Boolean)),venueMedia=M.contextItems(media,{eventIds:[...eventIds],venueSlugs:[slug]}).filter(item=>!referencedMediaIds.has(item.id));")
replace_once('venue-profile.html',"  const signatures=signatureEvents.length?`<section class=\"section\"><div class=\"kicker\">Personal canon</div><h2>Signature moments here.</h2><div class=\"signature-grid\">${signatureEvents.map(({event,rank})=>`<a class=\"signature\" href=\"event.html?id=${encodeURIComponent(event.id)}\"><div class=\"rank\">Top 10 experience · #${rank.rank}</div><h3>${rank.title}</h3><p>${rank.detail}</p></a>`).join('')}</div></section>`:'';","  const signatures=signatureEvents.length?`<section class=\"section\"><div class=\"kicker\">Personal canon</div><h2>Signature moments here.</h2><div class=\"signature-grid\">${signatureEvents.map(({event,rank})=>`<a class=\"signature\" href=\"event.html?id=${encodeURIComponent(event.id)}\"><div class=\"rank\">Top 10 experience · #${rank.rank}</div><h3>${rank.title}</h3><p>${rank.detail}</p></a>`).join('')}</div></section>`:'';\n  const archiveCards=[...venueArtifacts.map(a=>M.artifactCard(a,media,{eventHref:`event.html?id=${encodeURIComponent(a.event_id)}`})),...venueMedia.map(item=>M.mediaCard(item))].filter(Boolean),physicalArchiveSection=archiveCards.length?`<section class=\"section archive-evidence-section\"><div class=\"head\"><div><div class=\"kicker\">Physical archive</div><h2>Evidence tied to this place.</h2></div><p class=\"archive-evidence-intro\">Tickets, photographs, and other sourced media stay connected to the exact visits that establish their provenance.</p></div><div class=\"archive-evidence-grid\">${archiveCards.join('')}</div></section>`:'';")
replace_once('venue-profile.html','</div></div></section>${signatures}<section class="section grid2">','</div></div></section>${signatures}${physicalArchiveSection}<section class="section grid2">')

# Team profiles: future media attached to a favorite team (or one of its events) appears automatically; known artifacts also follow their event links.
replace_once('team-profile.html','<link rel="stylesheet" href="assets/team-profile.css">','<link rel="stylesheet" href="assets/team-profile.css"><link rel="stylesheet" href="assets/archive-media.css">')
replace_once('team-profile.html','<script src="assets/sports-passport-data.js"></script><script>','<script src="assets/sports-passport-data.js"></script><script src="assets/archive-media.js"></script><script>')
replace_once('team-profile.html','const D=window.SportsPassportData,[events,teamColors,teamLore,venues,rankings]=await Promise.all([D.load("events"),D.load("team-colors"),D.load("team-lore"),D.load("venues"),D.load("curated-rankings")]);','const D=window.SportsPassportData,M=window.SportsPassportMedia,[events,teamColors,teamLore,venues,rankings,artifacts,media]=await Promise.all([D.load("events"),D.load("team-colors"),D.load("team-lore"),D.load("venues"),D.load("curated-rankings"),D.load("artifacts"),D.load("media")]);')
replace_once('team-profile.html','signatureEvents=ev.map(e=>({event:e,rank:experienceById[e.id]})).filter(x=>x.rank).sort((a,b)=>a.rank.rank-b.rank.rank);const sport=','signatureEvents=ev.map(e=>({event:e,rank:experienceById[e.id]})).filter(x=>x.rank).sort((a,b)=>a.rank.rank-b.rank.rank),eventIds=new Set(ev.map(e=>e.id)),teamArtifacts=(artifacts||[]).filter(a=>eventIds.has(a.event_id)),referencedMediaIds=new Set(teamArtifacts.map(a=>a.media_id).filter(Boolean)),teamMedia=M.contextItems(media,{eventIds:[...eventIds],teamSlugs:[D.slug(team)]}).filter(item=>!referencedMediaIds.has(item.id));const sport=')
replace_once('team-profile.html','const signatures=signatureEvents.length?`<section class="section"><div class="head"><div><div class="kicker">Personal canon</div><h2>Signature moments with ${team}.</h2></div><p>Top 10 experiences that are also part of this team\'s archive.</p></div><div class="signature-grid">${signatureEvents.map(({event,rank})=>`<a class="signature" href="event.html?id=${encodeURIComponent(event.id)}"><div class="rank">Top 10 experience · #${rank.rank}</div><h3>${rank.title}</h3><p>${rank.detail}</p></a>`).join(\'\')}</div></section>`:\'\';app.innerHTML=','const signatures=signatureEvents.length?`<section class="section"><div class="head"><div><div class="kicker">Personal canon</div><h2>Signature moments with ${team}.</h2></div><p>Top 10 experiences that are also part of this team\'s archive.</p></div><div class="signature-grid">${signatureEvents.map(({event,rank})=>`<a class="signature" href="event.html?id=${encodeURIComponent(event.id)}"><div class="rank">Top 10 experience · #${rank.rank}</div><h3>${rank.title}</h3><p>${rank.detail}</p></a>`).join(\'\')}</div></section>`:\'\';const archiveCards=[...teamArtifacts.map(a=>M.artifactCard(a,media,{eventHref:`event.html?id=${encodeURIComponent(a.event_id)}`})),...teamMedia.map(item=>M.mediaCard(item))].filter(Boolean),physicalArchiveSection=archiveCards.length?`<section class="section archive-evidence-section"><div class="head"><div><div class="kicker">Physical archive</div><h2>Evidence connected to ${team}.</h2></div><p class="archive-evidence-intro">Sourced photographs and known keepsakes appear only when they can be tied to this team or one of its exact archive events.</p></div><div class="archive-evidence-grid">${archiveCards.join("")}</div></section>`:"";app.innerHTML=')
replace_once('team-profile.html','${loreSection}${signatures}<section class="section grid2">','${loreSection}${signatures}${physicalArchiveSection}<section class="section grid2">')

# Personal Canon: future source media can attach to a ranking position, ranked event, or ranked venue without turning the page into a photo wall.
replace_once('favorites.html','<link rel="stylesheet" href="assets/favorites.css">','<link rel="stylesheet" href="assets/favorites.css"><link rel="stylesheet" href="assets/archive-media.css">')
replace_once('favorites.html','<script src="assets/sports-passport-data.js"></script><script>','<script src="assets/sports-passport-data.js"></script><script src="assets/archive-media.js"></script><script>')
replace_once('favorites.html',"const D=window.SportsPassportData;const [rankings,events]=await Promise.all([D.load('curated-rankings'),D.load('events')]);","const D=window.SportsPassportData,M=window.SportsPassportMedia;const [rankings,events,media]=await Promise.all([D.load('curated-rankings'),D.load('events'),D.load('media')]);")
replace_once('favorites.html',"const byId=new Map(events.map(e=>[e.id,e])),app=document.querySelector('#app');const list=","const byId=new Map(events.map(e=>[e.id,e])),app=document.querySelector('#app'),canonRefs=[...(rankings.sports_experiences||[]).map(x=>`sports_experiences:${x.rank}`),...(rankings.favorite_venues||[]).map(x=>`favorite_venues:${x.rank}`),...(rankings.best_venues||[]).map(x=>`best_venues:${x.rank}`)],rankedEventIds=(rankings.sports_experiences||[]).map(x=>x.event_id).filter(Boolean),rankedVenueSlugs=[...(rankings.favorite_venues||[]),...(rankings.best_venues||[])].flatMap(x=>x.venue_slugs||[]),canonMedia=M.contextItems(media,{rankingRefs:canonRefs,eventIds:rankedEventIds,venueSlugs:rankedVenueSlugs}).slice(0,6),canonMediaSection=canonMedia.length?`<section class=\"section archive-evidence-section\"><div class=\"head\"><div><div class=\"kicker\">From the archive</div><h2>Selected source images.</h2></div><p class=\"archive-evidence-intro\">A small visual layer for ranked moments and venues, limited to sourced media with stable catalog IDs and descriptive alt text.</p></div><div class=\"archive-evidence-grid canon-media-grid\">${canonMedia.map(item=>M.mediaCard(item)).join('')}</div></section>`:'';const list=")
replace_once('favorites.html','</div></section><section class="section"><div class="head">','</div></section>${canonMediaSection}<section class="section"><div class="head">')

# Document the selective, provenance-first media pipeline.
workflow=ROOT/'ARTIFACT-WORKFLOW.md'
text=workflow.read_text(encoding='utf-8')
section='''\n\n## Selective public media layer\n\nThe public site uses `data/media.json` as the stable media catalog. Media IDs are durable (`media-####`) and presentation contexts are explicit: exact events, team slugs, venue slugs, life chapters, or Personal Canon ranking references. The full Artifacts workbench remains private from navigation and crawl surfaces; only contextual evidence is surfaced on public pages.\n\nFor every published image:\n\n- keep an original/fallback source plus optimized AVIF and WebP derivatives under `assets/media/`;\n- record intrinsic width and height, descriptive alt text, optional caption/credit, and explicit contexts in `data/media.json`;\n- link physical artifacts through `media_id` instead of embedding file paths in `data/artifacts.json`;\n- render through `assets/archive-media.js`, which uses `<picture>`, `loading="lazy"`, and `decoding="async"`;\n- prefer provenance over decoration. If a real source image is unavailable, show the cataloged artifact as text and keep its digitization status explicit.\n'''
if '## Selective public media layer' not in text:
    workflow.write_text(text.rstrip()+section+'\n',encoding='utf-8')

# Replace artifact validator with the new public-context/media contract while preserving existing archive research invariants.
write('tools/validate_artifacts.py', r'''#!/usr/bin/env python3
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
''')

# Browser regression: known objects appear where they belong, while unrelated records stay uncluttered.
write('tests/browser/archive-media.spec.js', r'''const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Selective archive-media assertions run once on desktop; route rendering covers all viewports.');

test('known Camden Yards ticket artifact appears on its exact Event Passport', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0001/', { waitUntil: 'domcontentloaded' });
  const section=page.locator('.archive-evidence-section');
  await expect(section).toBeVisible();
  await expect(section).toContainText('1993 Camden Yards ticket stub');
  await expect(section).toContainText('image pending');
  await expect(section.locator('img')).toHaveCount(0);
});

test('Growing Up chapter gathers its two known physical artifacts', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/chapters/origins/', { waitUntil: 'domcontentloaded' });
  const section=page.locator('.archive-evidence-section');
  await expect(section).toBeVisible();
  await expect(section.locator('[data-artifact-id]')).toHaveCount(2);
  await expect(section).toContainText('1993 Camden Yards ticket stub');
  await expect(section).toContainText('1997 Camden Yards ticket stub');
});

test('ranked Camden Yards venue profile gathers visit artifacts', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/venues/oriole-park-at-camden-yards/', { waitUntil: 'domcontentloaded' });
  const section=page.locator('.archive-evidence-section');
  await expect(section).toBeVisible();
  await expect(section.locator('[data-artifact-id]')).toHaveCount(2);
});

test('unrelated recent Event Passport does not get decorative artifact filler', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.archive-evidence-section')).toHaveCount(0);
});
''')

print('Applied selective archive media/artifact integration.')
