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
