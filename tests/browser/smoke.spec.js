const { test, expect } = require('@playwright/test');

const routes = [
  ['home', '/', /Sports\s*Passport/i],
  ['annual index', '/years/', /Annual\s*Editions/i],
  ['current annual edition', '/years/2026/', /2026/],
  ['event passport', '/events/evt-0268/', /Denver Broncos|Kansas City Chiefs/i],
  ['team explorer', '/teams/', /Team\s*Explorer/i],
  ['team profile', '/teams/kansas-city-chiefs/', /Kansas City Chiefs/i],
  ['venue directory', '/venues/', /Venue/i],
  ['venue profile', '/venues/arrowhead-stadium/', /Arrowhead Stadium/i],
  ['geography', '/geography/', /Places/i],
  ['life chapters', '/journeys/', /Sports|Journeys/i],
  ['personal canon', '/favorites/', /Top Tens/i],
  ['analytics', '/analytics/', /Lifetime\s*Analytics/i],
  ['hall of fame', '/hall-of-fame/', /Hall of\s*Fame/i],
  ['about', '/about/', /Why this\s*exists/i]
];

for (const [name, path, heading] of routes) {
  test(`${name} renders without overflow`, async ({ page }) => {
    await page.goto(path, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('h1').first()).toContainText(heading);

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth
    }));
    expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 2);
  });
}

test('lifetime analytics renders without overflow and keeps the phone timeline legible', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'phone', 'This regression is specific to the narrow mobile layout.');
  await page.goto('/analytics/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText(/Lifetime\s*Analytics/i);
  await expect(page.locator('.bars')).toBeVisible();

  const summaryMetrics = await page.locator('.stats').evaluate(stats => {
    const last = stats.lastElementChild;
    const statsBox = stats.getBoundingClientRect();
    const lastBox = last.getBoundingClientRect();
    return { statsWidth: statsBox.width, lastWidth: lastBox.width };
  });
  expect(summaryMetrics.lastWidth).toBeGreaterThan(summaryMetrics.statsWidth * 0.95);

  const timeline = await page.locator('.bars').evaluate(bars => ({
    scrollWidth: bars.scrollWidth,
    clientWidth: bars.clientWidth,
    count: bars.querySelectorAll('.barwrap').length,
    visibleYearLabels: [...bars.querySelectorAll('.barwrap span')].filter(label => getComputedStyle(label).display !== 'none').length,
    tallestBar: Math.max(...[...bars.querySelectorAll('.bar')].map(bar => bar.getBoundingClientRect().height))
  }));
  expect(timeline.count).toBeGreaterThan(30);
  expect(timeline.scrollWidth).toBeLessThanOrEqual(timeline.clientWidth + 2);
  expect(timeline.visibleYearLabels).toBeGreaterThanOrEqual(6);
  expect(timeline.visibleYearLabels).toBeLessThan(timeline.count);
  expect(timeline.tallestBar).toBeGreaterThan(120);
});

test('first-class deep routes survive direct reloads without template bootstrapping', async ({ page }) => {
  await page.goto('/teams/kansas-city-chiefs/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText('Kansas City Chiefs');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText('Kansas City Chiefs');

  const teamResources = await page.evaluate(() => performance.getEntriesByType('resource').map(entry => entry.name));
  expect(teamResources.some(url => /team-profile\.html(?:\?|$)/.test(url))).toBe(false);
  await expect(page.locator('script[src*="route-bootstrap.js"]')).toHaveCount(0);

  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText(/Denver Broncos|Kansas City Chiefs/i);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText(/Denver Broncos|Kansas City Chiefs/i);
  const eventResources = await page.evaluate(() => performance.getEntriesByType('resource').map(entry => entry.name));
  expect(eventResources.some(url => /event\.html(?:\?|$)/.test(url))).toBe(false);
});

test('legacy clean query URLs redirect to first-class deep pages', async ({ page }) => {
  await page.goto('/teams/?team=kansas-city-chiefs', { waitUntil: 'domcontentloaded' });
  await page.waitForURL('**/teams/kansas-city-chiefs/');
  await expect(page.locator('h1').first()).toContainText('Kansas City Chiefs');

  await page.goto('/years/?year=2026', { waitUntil: 'domcontentloaded' });
  await page.waitForURL('**/years/2026/');
  await expect(page.locator('h1').first()).toContainText('2026');
});

test('team search and sport filters remain functional', async ({ page }) => {
  await page.goto('/teams/', { waitUntil: 'domcontentloaded' });
  const search = page.locator('#q');
  await expect(search).toBeVisible();
  await search.fill('Chiefs');
  await expect(page.locator('#cards .team-card')).toHaveCount(1);
  await expect(page.locator('#cards .team-card').first()).toContainText('Kansas City Chiefs');

  await search.fill('');
  const football = page.locator('#filters button', { hasText: 'Football' });
  await football.click();
  await expect(football).toHaveClass(/active/);
  await expect(page.locator('#cards .team-card').first()).toBeVisible();
});

test('event passports retain chronological navigation', async ({ page }) => {
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  const archiveLinks = page.locator('.archive-nav a');
  await expect(archiveLinks.first()).toBeVisible();
  const before = page.url();
  await archiveLinks.first().click();
  await expect(page.locator('.event-hero')).toBeVisible();
  expect(page.url()).not.toBe(before);
  await page.waitForURL(url => /\/events\/[^/?#]+\/$/.test(url.pathname), { timeout: 5000 });
  expect(page.url()).toMatch(/\/events\/[^/?#]+\/$/);
});

test('geography map initializes and exposes venue popups', async ({ page }) => {
  await page.goto('/geography/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#geo-map')).toBeVisible();
  const markers = page.locator('#geo-map .leaflet-marker-icon');
  const firstMarker = markers.first();
  await expect(firstMarker).toBeVisible({ timeout: 10000 });
  expect(await markers.count()).toBeGreaterThan(0);

  await firstMarker.focus();
  await expect(firstMarker).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('.leaflet-popup-content')).toBeVisible();
  await expect(page.locator('.leaflet-popup-content a')).toHaveAttribute('href', /\/venues\/[^/?#]+\//);

  const reset = page.locator('#reset-map');
  await expect(reset).toBeVisible();
  await reset.click();
});

test('archive JSON requests use the revalidated cache manifest version', async ({ page }) => {
  await page.goto('/teams/kansas-city-chiefs/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText('Kansas City Chiefs');

  const manifest = await page.evaluate(async () => {
    const response = await fetch('/data/cache-manifest.json', { cache: 'no-cache' });
    return response.json();
  });
  expect(manifest.version).toMatch(/^[0-9a-f]{20}$/);

  const resources = await page.evaluate(() => performance.getEntriesByType('resource').map(entry => entry.name));
  const dataResources = resources.filter(url => /\/data\/[^/?]+\.json(?:\?|$)/.test(url));
  expect(dataResources.some(url => /\/data\/cache-manifest\.json(?:\?|$)/.test(url))).toBe(true);
  const versioned = dataResources.filter(url => !/\/data\/cache-manifest\.json(?:\?|$)/.test(url));
  expect(versioned.length).toBeGreaterThan(0);
  for (const url of versioned) {
    expect(new URL(url).searchParams.get('v')).toBe(manifest.version);
  }
});

test('mobile navigation opens, exposes primary destinations, and closes', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'phone', 'Mobile navigation behavior is phone-specific.');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const menu = page.locator('.menu-toggle');
  await expect(menu).toBeVisible();
  await menu.click();
  await expect(menu).toHaveAttribute('aria-expanded', 'true');
  await expect(page.locator('.global-nav a').filter({ hasText: 'Years' })).toBeVisible();
  await expect(page.locator('.global-nav a').filter({ hasText: 'Teams' })).toBeVisible();
  await expect(page.locator('.global-nav a').filter({ hasText: 'Places' })).toBeVisible();
  await expect(page.locator('.global-nav a').filter({ hasText: 'Life Chapters' })).toBeVisible();
  await expect(page.locator('.global-nav a').filter({ hasText: 'Personal Canon' })).toBeVisible();
  await menu.click();
  await expect(menu).toHaveAttribute('aria-expanded', 'false');
});
