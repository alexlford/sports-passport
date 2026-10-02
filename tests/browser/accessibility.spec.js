const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const criticalRoutes = [
  '/',
  '/years/2026/',
  '/events/evt-0268/',
  '/teams/',
  '/teams/kansas-city-chiefs/',
  '/venues/arrowhead-stadium/',
  '/favorites/',
  '/search/?q=Chiefs'
];

for (const path of criticalRoutes) {
  test(`critical accessibility rules pass on ${path}`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop', 'Run the WCAG scan once per route; responsive behavior is covered separately.');
    await page.goto(path, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1').first()).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}

test('skip link targets main content', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const skip = page.locator('.skip-link');
  await expect(skip).toHaveAttribute('href', '#main-content');
  await expect(page.locator('#main-content')).toHaveCount(1);
});

test('mobile menu closes with Escape and returns focus', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const menu = page.locator('.menu-toggle');
  await expect(menu).toBeVisible();
  await menu.click();
  await expect(menu).toHaveAttribute('aria-expanded', 'true');
  await page.keyboard.press('Escape');
  await expect(menu).toHaveAttribute('aria-expanded', 'false');
  await expect(menu).toBeFocused();
});

test('team filters announce live result counts', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/teams/', { waitUntil: 'domcontentloaded' });
  const status = page.locator('#team-filter-status');
  await expect(status).toHaveAttribute('aria-live', 'polite');
  await page.locator('#q').fill('Chiefs');
  await expect(status).toContainText('1 team shown');
});

test('the venue atlas exposes a textual venue alternative', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/geography/map/', { waitUntil: 'domcontentloaded' });
  const alternative = page.locator('.map-text-alternative');
  await expect(alternative.locator('summary')).toContainText(/Text alternative: \d+ mapped venues/);
  await alternative.locator('summary').click();
  await expect(alternative.locator('li').first()).toBeVisible();
  expect(await alternative.locator('li').count()).toBeGreaterThan(20);
});

test('geography overview preview is labeled and points to the accessible atlas', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/geography/', { waitUntil: 'domcontentloaded' });
  const footprint = page.locator('#venue-footprint');
  await expect(footprint).toHaveAttribute('role', 'img');
  await expect(footprint).toHaveAttribute('aria-label', /venues/i);
  await expect(page.locator('.atlas-cta')).toHaveAttribute('href', /(?:\/geography\/map\/|venue-map\.html)/);
  await expect(page.locator('#geo-map')).toHaveCount(0);
});

test('venue atlas filters reduce the map to ranked Top 10 venues and announce the count', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  // Geography is a lightweight overview (no map) since #115; the atlas is the one full map.
  for (const path of ['/geography/map/']) {
    await page.goto(path, { waitUntil: 'domcontentloaded' });
    const controls = page.locator('.map-filter-controls');
    await expect(controls).toBeVisible({ timeout: 10000 });
    const all = controls.locator('button[data-map-filter="all"]');
    const ranked = controls.locator('button[data-map-filter="ranked"]');
    await expect(all).toHaveAttribute('aria-pressed', 'true');
    const markers = page.locator('.leaflet-marker-icon');
    await expect(markers.first()).toBeVisible({ timeout: 10000 });
    const total = await markers.count();
    expect(total).toBeGreaterThan(20);
    await ranked.click();
    await expect(ranked).toHaveAttribute('aria-pressed', 'true');
    await expect(all).toHaveAttribute('aria-pressed', 'false');
    const visible = await markers.evaluateAll(nodes => nodes.filter(node => !node.hidden).length);
    expect(visible).toBeGreaterThan(0);
    expect(visible).toBeLessThan(total);
    await expect(controls.locator('.map-filter-status')).toContainText(`${visible} of ${total} venues shown`);
  }
});

test('dynamic team themes enforce AA contrast against white text', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/teams/kansas-city-chiefs/', { waitUntil: 'domcontentloaded' });
  const theme = page.locator('.team-theme');
  await expect(theme).toHaveAttribute('data-contrast-checked', 'true');
  const ratio = Number(await theme.getAttribute('data-contrast-ratio'));
  expect(ratio).toBeGreaterThanOrEqual(4.5);

  const failures = await page.evaluate(async () => {
    const colors = await window.SportsPassportData.load('team-colors');
    const helper = window.SportsPassportAccessibility;
    return Object.entries(colors).flatMap(([team, palette]) => palette.map(color => {
      const result = helper.accessibleThemeColor(color);
      return result.ratio < 4.5 ? { team, color, ratio: result.ratio } : null;
    }).filter(Boolean));
  });
  expect(failures).toEqual([]);
});

test('archive data failures render a recoverable fallback without hiding navigation', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/teams/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.global-nav')).toBeVisible();
  await expect.poll(async () => page.evaluate(() => Boolean(window.SportsPassportAccessibility))).toBe(true);

  await page.evaluate(() => {
    Promise.reject(new Error('Could not load /data/resolved-events.json'));
  });

  const fallback = page.locator('.data-load-error');
  await expect(fallback).toBeVisible();
  await expect(fallback).toHaveAttribute('role', 'alert');
  await expect(fallback.locator('h1')).toContainText('data did not load');
  await expect(fallback.locator('.data-load-retry')).toBeVisible();
  await expect(fallback.locator('.data-load-retry')).toHaveCSS('min-height', '44px');
  await expect(fallback.locator('a[href="/"]')).toBeVisible();
  await expect(page.locator('.global-nav')).toBeVisible();
});

test('global footer exposes archive through-date, archive version, and data revision', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const freshness = page.locator('.archive-freshness');
  await expect(freshness).toBeVisible();
  await expect(freshness).toContainText(/Archive through [A-Z][a-z]{2} \d{1,2}, 2026/);
  await expect(freshness).toContainText(/v26-2026-in-progress/);
  await expect(freshness).toContainText(/rev [0-9a-f]{8}/);
  await expect(freshness).toHaveAttribute('title', /Data revision [0-9a-f]{20}/);
});
