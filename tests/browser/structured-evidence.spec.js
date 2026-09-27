const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Structured evidence assertions run once on desktop.');

test('ticket-backed early event renders explicit structured evidence and provenance', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0001/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.status-row')).toContainText('Ticket-stub evidence');
  await expect(page.locator('.record-row', { hasText: 'Evidence provenance' })).toContainText(/ticket/i);
});

test('modern event renders documented evidence without source-string inference', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.status-row')).toContainText('Documented archive record');
  await expect(page.locator('.record-row', { hasText: 'Evidence class' })).toContainText('Documented archive record');
});
