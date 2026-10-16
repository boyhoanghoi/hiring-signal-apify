import { access, readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Optional artwork exporter, separate from the Actor runtime.
// Override PLAYWRIGHT_MODULE and CHROME_PATH on another workstation.
// Requires a local Playwright installation and Chrome; no network is used.
const playwrightPath = process.env.PLAYWRIGHT_MODULE || 'C:/Users/ADMIN/.cache/codex-tools/browser-check/node_modules/playwright/index.mjs';
const executablePath = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
await access(playwrightPath);
await access(executablePath);
const { chromium } = await import(pathToFileURL(playwrightPath).href);
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const artworkDir = resolve(root, 'assets', 'launch');
const svg = await readFile(resolve(artworkDir, 'jobs-finder.svg'), 'utf8');
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  await page.route('**/*', (route) => route.abort());
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;width:1600px;height:900px;overflow:hidden;background:#141020}svg{display:block;width:1600px;height:900px}</style></head><body>${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: resolve(artworkDir, 'jobs-finder.png') });
  console.log('Rendered assets/launch/jobs-finder.png (1600 x 900).');
} finally {
  await browser.close();
}
