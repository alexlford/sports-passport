const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Analytics insight assertions run once on desktop; route layout is covered at all viewports.');

test('lifetime analytics exposes longitudinal confirmed-archive insights', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/analytics/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#venue-expansion')).toBeVisible();
  await expect(page.locator('#venue-expansion')).toContainText('New places versus return visits');
  await expect(page.locator('#sport-over-time .insight-card')).not.toHaveCount(0);
  await expect(page.locator('#favorite-records')).toContainText('Favorite-team records');
  await expect(page.locator('#streaks .milestone-card')).toHaveCount(4);
});

test('longitudinal insight methodology is explicitly confirmed-record based', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/analytics/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.method-note')).toContainText('confirmed/documented archive');
  await expect(page.locator('#favorite-records')).toContainText('confirmed event');
  await expect(page.locator('#streaks')).toContainText('confirmed/documented events only');
});

test('chapter and state insight panels are populated', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/analytics/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.chapter-insight-grid .insight-card')).toHaveCount(5);
  await expect(page.locator('.panel', { hasText: 'State footprint' }).locator('.leader').first()).toBeVisible();
});
