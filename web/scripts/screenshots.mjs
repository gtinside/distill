// Captures README screenshots from the running demo-mode app.
// Usage: BASE=http://localhost:3100 node scripts/screenshots.mjs
import { chromium } from "playwright";
import { fileURLToPath } from "url";
import path from "path";

const BASE = process.env.BASE || "http://localhost:3100";
const OUT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../docs/screenshots"
);

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1200, height: 900 },
    deviceScaleFactor: 2,
  });

  // Sign-in
  await page.goto(`${BASE}/signin`, { waitUntil: "networkidle" });
  await wait(300);
  await page.screenshot({ path: `${OUT}/signin.png` });

  // Onboarding — add a few example topics for a populated shot
  await page.goto(`${BASE}/onboarding`, { waitUntil: "networkidle" });
  for (const label of ["Fed policy", "EU AI regulation", "NBA trades"]) {
    const chip = page.locator(`button:has-text("${label}")`).first();
    if (await chip.count()) await chip.click();
  }
  await wait(300);
  await page.screenshot({ path: `${OUT}/onboarding.png` });

  // Digest feed (full page)
  await page.goto(`${BASE}/digest`, { waitUntil: "networkidle" });
  await wait(400);
  await page.screenshot({ path: `${OUT}/digest.png`, fullPage: true });

  // Topics + settings (full page)
  await page.goto(`${BASE}/topics`, { waitUntil: "networkidle" });
  await wait(400);
  await page.screenshot({ path: `${OUT}/topics.png`, fullPage: true });

  await browser.close();
  console.log("Screenshots written to", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
