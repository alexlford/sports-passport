const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Structured evidence assertions run once on desktop.');

const forbiddenPublicPatterns = [
  /Archive confidence/i,
  /Early-archive confidence/i,
  /Evidence class/i,
  /Evidence provenance/i,
  /Event ID/i,
  /Confidence policy/i,
  /Confidence and reconstruction/i,
  /\bVerified\b/i,
  /\bNotional\b/i,
  /Confirmed\s*\/\s*documented/i
];

async function expectNoPublicArchiveBookkeeping(page) {
  const bodyText = await page.locator('body').innerText();
  for (const pattern of forbiddenPublicPatterns) expect(bodyText).not.toMatch(pattern);
}

async function expectInternalMetadataHidden(page) {
  const recordText = await page.locator('.record-list').innerText();
  expect(recordText).not.toContain('Archive confidence');
  expect(recordText).not.toContain('Evidence class');
  expect(recordText).not.toContain('Evidence provenance');
  expect(recordText).not.toContain('Event ID');
  await expect(page.locator('.status-row .status-chip:not(.top10)')).toHaveCount(0);
}

test('ticket-backed early event keeps evidence metadata internal', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0001/', { waitUntil: 'domcontentloaded' });
  await expectInternalMetadataHidden(page);
  await expectNoPublicArchiveBookkeeping(page);

  const internalEvidence = await page.evaluate(async () => {
    const D = window.SportsPassportData;
    const events = await D.load('events');
    const event = events.find(item => item.id === 'evt-0001');
    return {
      type: D.evidenceType(event),
      provenance: D.evidenceProvenance(event),
      confidence: D.confidenceLabel(event)
    };
  });
  expect(internalEvidence.type).toBe('ticket_stub');
  expect(internalEvidence.provenance).toMatch(/ticket/i);
  expect(internalEvidence.confidence).toBeTruthy();
});

test('modern event keeps evidence metadata internal', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expectInternalMetadataHidden(page);
  await expectNoPublicArchiveBookkeeping(page);

  const internalEvidence = await page.evaluate(async () => {
    const D = window.SportsPassportData;
    const events = await D.load('events');
    const event = events.find(item => item.id === 'evt-0268');
    return {
      label: D.evidenceLabel(event),
      provenance: D.evidenceProvenance(event),
      confidence: D.confidenceLabel(event)
    };
  });
  expect(internalEvidence.label).toBeTruthy();
  expect(internalEvidence.provenance).toBeTruthy();
  expect(internalEvidence.confidence).toBeTruthy();
});

test('confidence classifications stay private across archive views', async ({ page }, testInfo) => {
  desktopOnly(testInfo);

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#home-search-input')).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);

  await page.goto('/years/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.year-card').first()).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);

  const earlyContext = await page.evaluate(async () => {
    const D = window.SportsPassportData;
    const [events, venues] = await Promise.all([D.load('events'), D.load('venues')]);
    const event = events.find(item => D.isNotionalEvent(item) && item.venue_key && D.eventTeams(item).length);
    const venue = event ? venues.find(item => item.key === event.venue_key) : null;
    return event ? {
      year: event.year,
      teamSlug: D.slug(D.eventTeams(event)[0]),
      venueSlug: venue?.slug || null
    } : null;
  });
  expect(earlyContext).toBeTruthy();

  await page.goto(`/years/${earlyContext.year}/`, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.event-card').first()).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);

  await page.goto(`/teams/${earlyContext.teamSlug}/`, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.hero h1')).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);
  await expect(page.locator('.stat span', { hasText: 'Confirmed record' })).toHaveCount(0);

  if (earlyContext.venueSlug) {
    await page.goto(`/venues/${earlyContext.venueSlug}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('.hero h1')).toBeVisible();
    await expectNoPublicArchiveBookkeeping(page);
  }

  await page.goto('/about/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.hero h1')).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);
  await expect(page.locator('meta[name="description"]')).not.toHaveAttribute('content', /archive confidence/i);

  await page.goto('/analytics/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.hero h1')).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);
});

test('homepage search hands queries to archive search', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const input = page.locator('#home-search-input');
  await expect(input).toBeVisible();
  await input.fill('Chiefs');
  await Promise.all([
    page.waitForURL(url => url.pathname === '/search/' && url.searchParams.get('q') === 'Chiefs'),
    input.press('Enter')
  ]);
  await expect(page.locator('#global-search')).toHaveValue('Chiefs');
  await expect(page.locator('.search-result[data-result-type="team"]', { hasText: 'Kansas City Chiefs' })).toBeVisible();
});

test('public search does not expose confidence labels or internal event IDs', async ({ page }, testInfo) => {
  desktopOnly(testInfo);

  await page.goto('/search/?q=Chiefs', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.search-result').first()).toBeVisible();
  await expectNoPublicArchiveBookkeeping(page);
  const normalResults = await page.locator('#search-results').innerText();
  expect(normalResults).not.toMatch(/\bDocumented\b|\bVerified\b|\bNotional\b/i);

  await page.goto('/search/?q=evt-0268', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#search-status')).toContainText('0 results');
  await expect(page.locator('.search-result')).toHaveCount(0);
  await expectNoPublicArchiveBookkeeping(page);
});
