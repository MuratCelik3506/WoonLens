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

test("searches and selects official addresses with the keyboard", async ({ page }) => {
  await page.route("**/api/addresses/suggest**", async (route) => {
    const query = new URL(route.request().url()).searchParams.get("q");
    const number = query?.includes("40") ? 40 : 120;
    await route.fulfill({
      body: JSON.stringify({
        items: [
          {
            display_name: `Westblaak ${number}, 3012 KM Rotterdam`,
            id: `11111111-1111-4111-8111-${number.toString().padStart(12, "0")}`,
            source: { dataset: "PDOK Location API", provider: "PDOK" },
          },
        ],
      }),
      contentType: "application/json",
      status: 200,
    });
  });

  await page.goto("/");
  const search = page.getByRole("combobox", { name: "Find an official address" });

  await search.fill("Westblaak 120");
  await expect(page.getByRole("option")).toBeVisible();
  await search.press("ArrowDown");
  await search.press("Enter");
  await expect(page.getByText("1 of 5")).toBeVisible();

  await search.fill("Westblaak 40");
  await expect(page.getByRole("option")).toBeVisible();
  await search.press("ArrowDown");
  await search.press("Enter");

  await expect(page.getByText("2 of 5")).toBeVisible();
  await expect(page.getByRole("button", { name: "Compare homes" })).toBeEnabled();
});
