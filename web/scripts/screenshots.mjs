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
const viewport = { width: 1200, height: 900 };

async function main() {
  const browser = await chromium.launch();

  // --- Anonymous context: logged-out front page + sign-in ---
  const anon = await browser.newContext({ viewport, deviceScaleFactor: 2 });
  const a = await anon.newPage();

  await a.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await wait(500);
  await a.screenshot({ path: `${OUT}/home-trending.png`, fullPage: true });

  await a.goto(`${BASE}/signin`, { waitUntil: "networkidle" });
  await wait(300);
  await a.screenshot({ path: `${OUT}/signin.png` });
  await anon.close();

  // --- Signed-in demo context: enter demo, then capture blend + topics ---
  const signed = await browser.newContext({ viewport, deviceScaleFactor: 2 });
  const p = await signed.newPage();

  await p.goto(`${BASE}/signin`, { waitUntil: "networkidle" });
  await p.click('button:has-text("Continue to demo")');
  await p.waitForURL(`${BASE}/`, { waitUntil: "networkidle" });
  await wait(600);
  await p.screenshot({ path: `${OUT}/digest.png`, fullPage: true });

  await p.goto(`${BASE}/topics`, { waitUntil: "networkidle" });
  await wait(400);
  await p.screenshot({ path: `${OUT}/topics.png`, fullPage: true });

  // Onboarding (reachable in demo) with a few topics staged
  await p.goto(`${BASE}/onboarding`, { waitUntil: "networkidle" });
  for (const label of ["Fed policy", "EU AI regulation", "NBA trades"]) {
    const chip = p.locator(`button:has-text("${label}")`).first();
    if (await chip.count()) await chip.click();
  }
  await wait(300);
  await p.screenshot({ path: `${OUT}/onboarding.png` });
  await signed.close();

  await browser.close();
  console.log("Screenshots written to", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
