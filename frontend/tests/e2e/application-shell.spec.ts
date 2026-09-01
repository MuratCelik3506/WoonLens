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
  await page.route("**/api/comparisons/live", async (route) => {
    const request = route.request().postDataJSON() as { address_ids: string[] };
    await route.fulfill({
      body: JSON.stringify({
        homes: request.address_ids.map((addressId, index) => ({
          addressId,
          contextNotes: ["CBS neighbourhood reference year 2024"],
          displayName: null,
          sources: [
            {
              dataset: "BAG",
              license: "CC0",
              provider: "PDOK",
              retrievedAt: "2026-09-01T12:00:00Z",
            },
          ],
          unavailableReason: null,
          index,
        })),
        metrics: [
          {
            definition: "Official BAG registered area.",
            key: "registered_area_m2",
            label: "Registered BAG area",
            scope: "property",
            unit: "m²",
            values: request.address_ids.map((addressId, index) => ({
              addressId,
              isBaseline: index === 0,
              missingReason: index === 1 ? "not_reported" : null,
              value: index === 1 ? null : 80,
            })),
          },
        ],
        notices: [{ code: "area", message: "Area definitions remain distinct." }],
        rulesVersion: "1.1.0",
      }),
      contentType: "application/json",
      status: 200,
    });
  });
  await page.route("**/api/comparison-downloads/json", async (route) => {
    await route.fulfill({
      body: JSON.stringify({ schema_version: "1.0.0" }),
      contentType: "application/json",
      headers: {
        "Content-Disposition":
          'attachment; filename="woonlens-comparison-20260901T120000Z.json"',
      },
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
  const compare = page.getByRole("button", { name: "Compare homes" });
  await expect(compare).toBeEnabled();
  await compare.click();
  await expect(
    page.getByRole("heading", { name: "Factual differences, source by source" }),
  ).toBeVisible();
  await expect(page.getByText("80 m²")).toBeVisible();
  await expect(page.getByText("Not reported")).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download JSON" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe(
    "woonlens-comparison-20260901T120000Z.json",
  );

  await page.getByRole("button", { name: /Remove Westblaak 40/ }).click();
  await expect(
    page.getByRole("heading", { name: "Factual differences, source by source" }),
  ).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Download JSON" })).not.toBeVisible();
});
