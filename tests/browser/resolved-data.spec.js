const { test, expect } = require('@playwright/test');

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
