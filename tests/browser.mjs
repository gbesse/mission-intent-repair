import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
const port = 18764;
const server = spawn(
  process.env.PYTHON || 'python3',
  ['-m', 'mission_repair', 'serve', String(port)],
  { stdio: ['ignore', 'pipe', 'inherit'] },
);
const base = `http://127.0.0.1:${port}`;
let browser;
try {
  for (let i = 0; i < 200; i++) {
    try {
      if ((await fetch(base)).ok) break;
    } catch {}
    if (server.exitCode !== null) throw Error('server exited');
    if (i === 199) throw Error('server readiness timeout');
    await new Promise((r) => setTimeout(r, 100));
  }
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1300, height: 1000 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  for (const lang of ['fr', 'en', 'es']) {
    await page.goto(`${base}/?lang=${lang}`);
    await page.waitForFunction(() => document.getElementById('utility').textContent === '8');
    assert.equal(await page.locator('html').getAttribute('lang'), lang);
    assert.equal(await page.locator('#edits').textContent(), '2');
    assert.equal(await page.locator('.bar.frozen').count(), 2);
    await page.locator('#outage').uncheck();
    await page.locator('#solve').click();
    await page.waitForFunction(() => document.getElementById('utility').textContent === '10');
    assert.equal(await page.locator('#edits').textContent(), '0');
    const downloadEvent = page.waitForEvent('download');
    await page.locator('#download').click();
    const download = await downloadEvent;
    assert.equal(download.suggestedFilename(), 'mission-repair-evidence.json');
    await page.locator('summary').click();
    await page.locator('#case').fill('{');
    await page.locator('#custom').click();
    await page.waitForFunction(() => !document.getElementById('custom').disabled);
    assert.match(
      await page.locator('#status').textContent(),
      { fr: /Entrée non valide/, en: /Invalid input/, es: /Entrada no válida/ }[lang],
    );
  }
  await page.goto(`${base}/?lang=fr`);
  await page.waitForFunction(() => document.getElementById('utility').textContent === '8');
  await mkdir('.local', { recursive: true });
  await page.screenshot({ path: '.local/preview-fr.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  assert.deepEqual(errors, []);
  const response = await fetch(base + '/api/repair', {
    method: 'POST',
    headers: { 'content-type': 'application/json', origin: 'https://example.invalid' },
    body: '{}',
  });
  assert.equal(response.status, 403);
  console.log('FR/EN/ES: repair, frozen past, JSON export, errors and mobile layout verified.');
} finally {
  if (browser) await browser.close();
  server.kill('SIGTERM');
}
