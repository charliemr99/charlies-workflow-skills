import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const [baseURL, artifactDirectory] = process.argv.slice(2);
if (!baseURL || !artifactDirectory) {
  throw new Error("usage: node feedback-inbox.mjs <base-url> <artifact-directory>");
}

await mkdir(artifactDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });
const viewports = [
  { name: "small-mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

try {
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport });
    page.setDefaultTimeout(5000);
    await page.goto(baseURL);

    const search = page.getByRole("searchbox", { name: "Search feedback" });
    const status = page.getByRole("combobox", { name: "Status" });
    await search.fill("renewal");
    await status.selectOption("planned");

    const url = new URL(page.url());
    if (url.searchParams.get("q") !== "renewal") {
      throw new Error(`${viewport.name}: q query parameter was not synchronized`);
    }
    if (url.searchParams.get("status") !== "planned") {
      throw new Error(`${viewport.name}: status query parameter was not synchronized`);
    }

    const results = page.locator("[data-feedback-id]");
    if ((await results.count()) !== 1) {
      throw new Error(`${viewport.name}: expected one combined-filter result`);
    }
    await page.reload();
    if ((await search.inputValue()) !== "renewal") {
      throw new Error(`${viewport.name}: search was not restored after reload`);
    }
    if ((await status.inputValue()) !== "planned") {
      throw new Error(`${viewport.name}: status was not restored after reload`);
    }

    await search.fill("no matching customer");
    const reset = page.getByRole("button", { name: "Reset filters" });
    if (!(await reset.isVisible())) {
      throw new Error(`${viewport.name}: accessible empty-state reset is missing`);
    }
    await reset.click();
    if ((await results.count()) !== 6) {
      throw new Error(`${viewport.name}: reset did not restore all feedback`);
    }

    await page.goto(`${baseURL}/?status=unknown`);
    if ((await status.inputValue()) !== "all" || (await results.count()) !== 6) {
      throw new Error(`${viewport.name}: unknown status did not fall back to All`);
    }

    await page.screenshot({
      path: path.join(artifactDirectory, `${viewport.name}.png`),
      fullPage: true,
    });
    await page.close();
  }
} finally {
  await browser.close();
}

process.stdout.write(JSON.stringify({ passed: true, viewports }, null, 2));
