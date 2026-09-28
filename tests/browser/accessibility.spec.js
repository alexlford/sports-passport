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

test('maps expose a textual venue alternative', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  await page.goto('/geography/', { waitUntil: 'domcontentloaded' });
  const alternative = page.locator('.map-text-alternative');
  await expect(alternative.locator('summary')).toContainText(/Text alternative: \d+ mapped venues/);
  await alternative.locator('summary').click();
  await expect(alternative.locator('li').first()).toBeVisible();
  expect(await alternative.locator('li').count()).toBeGreaterThan(20);
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
