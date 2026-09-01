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
        audits: [
          {
            addressId: request.address_ids[0],
            classification: "definition-difference",
            fields: ["bag.registered_area_m2", "ep_online.thermal_zone_area_m2"],
            message:
              "The fields describe different scopes and are not a register error.",
            ruleId: "area.definition.v1",
            values: [80, 75],
          },
        ],
        homes: request.address_ids.map((addressId, index) => ({
          addressId,
          contextNotes: ["CBS neighbourhood reference year 2024"],
          details: [
            {
              facts: [
                { label: "BAG registered area", unit: "m²", value: 80 + index },
                {
                  label: "BAG residential-unit ID",
                  unit: null,
                  value: `059901000029542${index}`,
                },
              ],
              level: "property",
              limitation:
                "BAG registered area is an official register value, not measured living area.",
              title: "BAG property",
            },
          ],
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
        insights: [
          {
            addressIds: [request.address_ids[0]],
            classification: "descriptive_extreme",
            message:
              "This home has the largest reported BAG registered area; larger is a preference fact, not an overall quality verdict.",
            metricKey: "registered_area_m2",
            ruleId: "registered_area_m2.extreme",
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
  await expect(page.getByRole("cell", { name: "80 m²" })).toBeVisible();
  await expect(page.getByText("Not reported")).toBeVisible();
  const details = page.getByRole("region", { name: "Official details by home" });
  await details.getByText(/Home 1 · Westblaak 120/i).click();
  await expect(
    details.getByRole("heading", { name: "BAG property" }).first(),
  ).toBeVisible();
  await expect(details.getByText(/property level/i).first()).toBeVisible();
  await details.getByText("Technical identifiers").first().click();
  await expect(details.getByText("0599010000295420")).toBeVisible();
  const explanations = page.getByRole("region", { name: "Explainable differences" });
  await expect(explanations).toContainText("not an overall quality verdict");
  await explanations.getByText("Technical rule details").click();
  await expect(explanations.getByText("registered_area_m2.extreme")).toBeVisible();
  const audits = page.getByRole("region", { name: "Cross-source checks" });
  await expect(audits).toContainText("not a register error");
  await audits.getByText("Compared source fields").click();
  await expect(audits.getByText("area.definition.v1")).toBeVisible();
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
  await expect(
    page.getByRole("heading", { name: "Explainable differences" }),
  ).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Official details by home" }),
  ).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Download JSON" })).not.toBeVisible();
});
