const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Event Passport interaction checks run once on desktop; route layout is already exercised at every viewport.');

test('annual cards expose explicit Event Passport calls to action', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/years/2026/', { waitUntil: 'domcontentloaded' });
  const link = page.locator('.event-passport-link').first();
  await expect(link).toBeVisible();
  await expect(link).toContainText('Open Event Passport');
  await expect(link).toHaveAttribute('href', /\/events\/[^/?#]+\/$/);
});

test('homepage latest entry opens the exact Event Passport', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const latest = page.locator('#latest-open');
  await expect(latest).toBeVisible();
  await expect(latest).toHaveAttribute('href', /\/events\/[^/?#]+\/$/);
});

test('Event Passport exposes a stable canonical link without internal identifiers', async ({ page, context }, testInfo) => {
  desktopOnly(testInfo);
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#share-event')).toBeVisible();
  await expect(page.locator('#copy-event')).toBeVisible();
  await expect(page.locator('.record-row', { hasText: 'Event ID' })).toHaveCount(0);
  await page.locator('#copy-event').click();
  await expect(page.locator('#share-status')).toContainText('Link copied.');
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toBe('https://sports.alexlford.com/events/evt-0268/');
});
