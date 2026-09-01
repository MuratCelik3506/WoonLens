import { expect, test } from "@playwright/test";

test("renders the guest application shell", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/WoonLens/);
  await expect(page.getByRole("main")).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Compare Dutch homes with trusted public data.",
    }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Compare homes" })).toBeDisabled();
});
