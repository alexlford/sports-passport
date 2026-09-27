#!/usr/bin/env python3
from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing replacement target in {path}: {old[:120]}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Event Passport: stable deep URL, sharing, durable identity, and optional richer fields.
replace_once(
    "event.html",
    "  const canonicalUrl=`https://sports.alexlford.com/events/?event=${encodeURIComponent(event.id)}`;",
    "  const canonicalUrl=window.SPORTS_ROUTE_PUBLIC_URL?`https://sports.alexlford.com${window.SPORTS_ROUTE_PUBLIC_URL}`:`https://sports.alexlford.com/events/${encodeURIComponent(event.id)}/`;",
)
replace_once(
    "event.html",
    "  const confidence=D.confidenceLabel(event);\n  const title=rank?`${rank.title} | Sports Passport`:`${D.matchup(event)} | Sports Passport`;",
    "  const confidence=D.confidenceLabel(event);\n  const escapeHtml=value=>String(value??'').replace(/[&<>\\\"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\\"':'&quot;',\"'\":'&#39;'}[ch]));\n  const optionalRows=[['Competition round',event.competition_round],['Site type',event.site_type]].filter(([,value])=>value!==undefined&&value!==null&&String(value).trim()).map(([label,value])=>`<div class=\"record-row\"><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`).join('');\n  const personalNote=event.personal_note?`<div class=\"event-note\"><div class=\"kicker\">Personal note</div><p>${escapeHtml(event.personal_note)}</p></div>`:'';\n  const title=rank?`${rank.title} | Sports Passport`:`${D.matchup(event)} | Sports Passport`;",
)
replace_once(
    "event.html",
    "</div><div class=\"scoreboard\">${scoreSide(event.teams?.[0]||'Team 1',0)}",
    "</div><div class=\"event-actions\"><button class=\"event-action primary\" id=\"share-event\" type=\"button\">Share Event Passport</button><button class=\"event-action\" id=\"copy-event\" type=\"button\">Copy link</button><span class=\"share-status\" id=\"share-status\" role=\"status\" aria-live=\"polite\"></span></div><div class=\"scoreboard\">${scoreSide(event.teams?.[0]||'Team 1',0)}",
)
replace_once(
    "event.html",
    "<div class=\"record-row\"><span>Evidence class</span><strong>${evidence}</strong></div></div>${matchingJourneys.length?",
    "<div class=\"record-row\"><span>Evidence class</span><strong>${evidence}</strong></div><div class=\"record-row\"><span>Event ID</span><strong>${event.id}</strong></div>${optionalRows}</div>${personalNote}${matchingJourneys.length?",
)
replace_once(
    "event.html",
    "})();\n</script>",
    "  const shareStatus=document.querySelector('#share-status');\n  const copyLink=async()=>{\n    const url=canonicalUrl;\n    if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(url)}else{const input=document.createElement('textarea');input.value=url;input.setAttribute('readonly','');input.style.position='fixed';input.style.opacity='0';document.body.appendChild(input);input.select();document.execCommand('copy');input.remove()}\n    if(shareStatus)shareStatus.textContent='Link copied.';\n  };\n  document.querySelector('#copy-event')?.addEventListener('click',()=>copyLink().catch(()=>{if(shareStatus)shareStatus.textContent='Copy unavailable.'}));\n  document.querySelector('#share-event')?.addEventListener('click',async()=>{\n    if(navigator.share){try{await navigator.share({title,text:description,url:canonicalUrl});if(shareStatus)shareStatus.textContent='Shared.';return}catch(error){if(error?.name==='AbortError')return}}\n    try{await copyLink()}catch(_){if(shareStatus)shareStatus.textContent='Sharing unavailable.'}\n  });\n})();\n</script>",
)

# Annual editions: every event card exposes the exact Event Passport.
replace_once(
    "year.html",
    '<div class="venue">${venueDisplay} · ${e.date}${recorded}</div></div></article>',
    '<div class="venue">${venueDisplay} · ${e.date}${recorded}</div><a class="event-passport-link" href="event.html?id=${encodeURIComponent(e.id)}">Open Event Passport →</a></div></article>',
)

# Homepage: latest entry deep-links to the exact event.
replace_once(
    "index.html",
    '      </div>\n      <div class="leader"><span>Events so far</span>',
    '      </div>\n      <a class="cta latest-passport hidden" id="latest-open" href="#">Open Event Passport →</a>\n      <div class="leader"><span>Events so far</span>',
)
replace_once(
    "index.html",
    "    document.querySelector('#latest-detail').textContent=`${latest.venue_recorded}${latest.city?` · ${latest.city}`:''}`;",
    "    document.querySelector('#latest-detail').textContent=`${latest.venue_recorded}${latest.city?` · ${latest.city}`:''}`;\n    const latestOpen=document.querySelector('#latest-open');latestOpen.href=`event.html?id=${encodeURIComponent(latest.id)}`;latestOpen.classList.remove('hidden');",
)

# Styling.
with Path("assets/event.css").open("a", encoding="utf-8") as f:
    f.write("\n.event-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:18px 0 0}.event-action{min-height:44px;padding:9px 14px;border:1px solid var(--line);border-radius:999px;background:#fffdf8;color:var(--ink);font:850 .78rem/1 var(--sans,Inter,sans-serif);cursor:pointer}.event-action.primary{background:var(--ink);border-color:var(--ink);color:#fff}.event-action:hover,.event-action:focus-visible{transform:translateY(-1px)}.share-status{min-height:1.2em;color:var(--muted);font-size:.78rem;font-weight:750}.event-note{margin-top:22px;padding:18px;border-left:5px solid var(--event-accent,#b7443a);border-radius:14px;background:#fffaf0}.event-note p{margin:8px 0 0;color:#514b45;line-height:1.6}@media(max-width:600px){.event-actions{align-items:stretch}.event-action{flex:1 1 auto}.share-status{flex-basis:100%}}\n")
with Path("assets/year.css").open("a", encoding="utf-8") as f:
    f.write("\n.event-passport-link{display:inline-flex;align-items:center;min-height:44px;margin-top:12px;padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:#fffdf8;color:var(--ink);text-decoration:none;font-size:.72rem;font-weight:900}.event-passport-link:hover,.event-passport-link:focus-visible{background:var(--ink);color:#fff}\n")
with Path("assets/home.css").open("a", encoding="utf-8") as f:
    f.write("\n.latest-passport{margin-top:14px}\n")

# Durable source-level validation.
p = Path("tools/validate_event_passports.py")
text = p.read_text(encoding="utf-8")
text = text.replace(
    '("venue-profile.html?v=", "venue-profile context links"),',
    '("venue-profile.html?v=", "venue-profile context links"),\n        (\'id="share-event"\', "Event Passport share action"),\n        (\'id="copy-event"\', "Event Passport copy-link action"),\n        ("event.competition_round", "optional competition-round rendering"),\n        ("event.site_type", "optional site-type rendering"),\n        ("event.personal_note", "optional personal-note rendering"),\n        ("Event ID", "stable event identifier rendering"),',
)
text = text.replace(
    '    "venue-profile.html",\n]',
    '    "venue-profile.html",\n    "year.html",\n    "index.html",\n]',
)
p.write_text(text, encoding="utf-8")

# Browser regression coverage.
Path("tests/browser/event-passport.spec.js").write_text(
    r'''const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Event Passport interaction checks run once on desktop; route layout is already exercised at every viewport.');

test('annual cards expose explicit Event Passport calls to action', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/years/2026/', { waitUntil: 'domcontentloaded' });
  const links = page.locator('.event-passport-link:visible');
  expect(await links.count()).toBeGreaterThan(0);
  await expect(links.first()).toContainText('Open Event Passport');
  await expect(links.first()).toHaveAttribute('href', /\/events\/[^/?#]+\/$/);
});

test('homepage latest entry opens the exact Event Passport', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const latest = page.locator('#latest-open');
  await expect(latest).toBeVisible();
  await expect(latest).toHaveAttribute('href', /\/events\/[^/?#]+\/$/);
});

test('Event Passport exposes stable identity and copyable canonical link', async ({ page, context }, testInfo) => {
  desktopOnly(testInfo);
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#share-event')).toBeVisible();
  await expect(page.locator('#copy-event')).toBeVisible();
  await expect(page.locator('.record-row', { hasText: 'Event ID' })).toContainText('evt-0268');
  await page.locator('#copy-event').click();
  await expect(page.locator('#share-status')).toContainText('Link copied.');
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toBe('https://sports.alexlford.com/events/evt-0268/');
});
''',
    encoding="utf-8",
)

print("Applied Event Passport atomic-unit improvements.")
