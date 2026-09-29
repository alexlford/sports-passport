const { test, expect } = require('@playwright/test');

const desktopOnly = (testInfo) => test.skip(testInfo.project.name !== 'desktop', 'Structured evidence assertions run once on desktop.');

async function expectInternalMetadataHidden(page) {
  const recordText = await page.locator('.record-list').innerText();
  expect(recordText).not.toContain('Archive confidence');
  expect(recordText).not.toContain('Evidence class');
  expect(recordText).not.toContain('Evidence provenance');
  expect(recordText).not.toContain('Event ID');
  await expect(page.locator('.status-row .status-chip:not(.top10)')).toHaveCount(0);
}

test('ticket-backed early event keeps evidence metadata internal', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0001/', { waitUntil: 'domcontentloaded' });
  await expectInternalMetadataHidden(page);

  const internalEvidence = await page.evaluate(async () => {
    const D = window.SportsPassportData;
    const events = await D.load('events');
    const event = events.find(item => item.id === 'evt-0001');
    return {
      type: D.evidenceType(event),
      provenance: D.evidenceProvenance(event),
      confidence: D.confidenceLabel(event)
    };
  });
  expect(internalEvidence.type).toBe('ticket_stub');
  expect(internalEvidence.provenance).toMatch(/ticket/i);
  expect(internalEvidence.confidence).toBeTruthy();
});

test('modern event keeps documented evidence metadata internal', async ({ page }, testInfo) => {
  desktopOnly(testInfo);
  await page.goto('/events/evt-0268/', { waitUntil: 'domcontentloaded' });
  await expectInternalMetadataHidden(page);

  const internalEvidence = await page.evaluate(async () => {
    const D = window.SportsPassportData;
    const events = await D.load('events');
    const event = events.find(item => item.id === 'evt-0268');
    return {
      label: D.evidenceLabel(event),
      provenance: D.evidenceProvenance(event),
      confidence: D.confidenceLabel(event)
    };
  });
  expect(internalEvidence.label).toBe('Documented archive record');
  expect(internalEvidence.provenance).toBeTruthy();
  expect(internalEvidence.confidence).toBeTruthy();
});
