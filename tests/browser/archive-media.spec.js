const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Selective archive-media assertions run once on desktop; route rendering covers all viewports.');

test('known Camden Yards ticket artifact appears on its exact Event Passport', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0001/', { waitUntil: 'domcontentloaded' });
  const section=page.locator('.archive-evidence-section');
  await expect(section).toBeVisible();
  await expect(section).toContainText('1993 Camden Yards ticket stub');
  await expect(section).toContainText('image pending');
  await expect(section.locator('img')).toHaveCount(0);
});

test('Growing Up chapter gathers its two known physical artifacts', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/chapters/origins/', { waitUntil: 'domcontentloaded' });
  const section=page.locator('.archive-evidence-section');
  await expect(section).toBeVisible();
  await expect(section.locator('[data-artifact-id]')).toHaveCount(2);
  await expect(section).toContainText('1993 Camden Yards ticket stub');
  await expect(section).toContainText('1997 Camden Yards ticket stub');
});

test('ranked Camden Yards venue profile gathers visit artifacts', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/venues/oriole-park-at-camden-yards/', { waitUntil: 'domcontentloaded' });
  const section=page.locator('.archive-evidence-section');
  await expect(section).toBeVisible();
  await expect(section.locator('[data-artifact-id]')).toHaveCount(2);
});

test('unrelated recent Event Passport does not get decorative artifact filler', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('.archive-evidence-section')).toHaveCount(0);
});
