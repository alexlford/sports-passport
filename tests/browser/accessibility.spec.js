const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const criticalRoutes = [
  '/',
  '/years/?year=2026',
  '/events/?event=evt-0268',
  '/teams/',
  '/teams/?team=kansas-city-chiefs',
  '/venues/?venue=arrowhead-stadium',
  '/favorites/'
];

for (const path of criticalRoutes) {
  test(`critical accessibility rules pass on ${path}`, async ({ page }) => {
    await page.goto(path, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1').first()).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}
