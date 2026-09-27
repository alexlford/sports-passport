const { test, expect } = require('@playwright/test');

const routes = [
  ['home', '/', /Sports\s*Passport/i],
  ['annual index', '/years/', /Annual\s*Editions/i],
  ['current annual edition', '/years/?year=2026', /2026/],
  ['event passport', '/events/?event=evt-0268', /Denver Broncos|Kansas City Chiefs/i],
  ['team explorer', '/teams/', /Team\s*Explorer/i],
  ['team profile', '/teams/?team=kansas-city-chiefs', /Kansas City Chiefs/i],
  ['venue directory', '/venues/', /Venue/i],
  ['venue profile', '/venues/?venue=arrowhead-stadium', /Arrowhead Stadium/i],
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

test('deep clean routes survive a direct reload', async ({ page }) => {
  await page.goto('/teams/kansas-city-chiefs/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText('Kansas City Chiefs');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText('Kansas City Chiefs');

  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText(/Denver Broncos|Kansas City Chiefs/i);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').first()).toContainText(/Denver Broncos|Kansas City Chiefs/i);
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
  await page.goto('/events/?event=evt-0268', { waitUntil: 'domcontentloaded' });
  const archiveLinks = page.locator('.archive-nav a');
  await expect(archiveLinks.first()).toBeVisible();
  const before = page.url();
  await archiveLinks.first().click();
  await expect(page.locator('.event-hero')).toBeVisible();
  expect(page.url()).not.toBe(before);
});

test('geography map initializes and exposes venue popups', async ({ page }) => {
  await page.goto('/geography/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#geo-map')).toBeVisible();
  const markers = page.locator('#geo-map .leaflet-marker-icon');
  const firstMarker = markers.first();
  await expect(firstMarker).toBeVisible({ timeout: 10000 });
  expect(await markers.count()).toBeGreaterThan(0);

  // At an archive-wide zoom nearby venues can visually overlap. Leaflet markers
  // are keyboard-enabled, so use the accessible interaction path rather than
  // forcing a pointer click through an obscuring marker.
  await firstMarker.focus();
  await expect(firstMarker).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('.leaflet-popup-content')).toBeVisible();
  await expect(page.locator('.leaflet-popup-content a')).toHaveAttribute('href', /venues|venue-profile/);

  const reset = page.locator('#reset-map');
  await expect(reset).toBeVisible();
  await reset.click();
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
