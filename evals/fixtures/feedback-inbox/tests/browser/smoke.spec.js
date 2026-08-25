import { expect, test } from "@playwright/test";

test("renders the established feedback inbox", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Feedback Inbox" })).toBeVisible();
  await expect(page.locator("[data-feedback-id]")).toHaveCount(6);
});
