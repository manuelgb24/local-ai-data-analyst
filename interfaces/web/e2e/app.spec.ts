import { expect, test } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";

async function setScenario(request: APIRequestContext, scenario: string) {
  const response = await request.post("http://127.0.0.1:8010/__scenario", {
    data: { scenario },
  });
  expect(response.ok()).toBeTruthy();
}

test.beforeEach(async ({ request }) => {
  await setScenario(request, "ready");
});

test("shows persisted history on load and selects the latest run", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Runs persistidos", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /run-ui-latest/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /run-ui-failed-history/ })).toBeVisible();
  await expect(page.getByText("Narrativa UI para: Revisa el run persistido mas reciente")).toBeVisible();
  await expect(page.getByRole("button", { name: "Lanzar run" })).toBeEnabled();
});

test("allows selecting a previous failed run from persisted history", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /run-ui-failed-history/ }).click();

  await expect(page.getByText("Error persistido")).toBeVisible();
  await expect(page.getByText("dataset_path_not_found")).toBeVisible();
  await expect(page.getByText("dataset_preparation")).toBeVisible();
});

test("blocks submit when the provider is not ready but keeps history browseable", async ({ page, request }) => {
  await setScenario(request, "provider_down");
  await page.goto("/");

  await expect(page.locator(".submit-help")).toContainText("El proveedor local no esta listo.");
  await expect(page.getByRole("button", { name: "Lanzar run" })).toBeDisabled();
  await expect(page.getByText("Ollama no responde en 127.0.0.1:11434.")).toBeVisible();
  await expect(page.getByRole("button", { name: /run-ui-latest/ })).toBeVisible();

  await page.getByRole("button", { name: /run-ui-failed-history/ }).click();
  await expect(page.getByText("Error persistido")).toBeVisible();
});

test("submits a valid run, refreshes history, and selects the new persisted run", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Ruta local del dataset").fill("DatasetV1/Walmart_Sales.csv");
  await page.getByLabel("Prompt").fill("Resume los hallazgos principales");
  await page.getByRole("button", { name: "Lanzar run" }).click();

  await expect(page.getByRole("button", { name: /run-ui-created-001/ })).toBeVisible();
  await expect(page.getByText("Narrativa UI para: Resume los hallazgos principales")).toBeVisible();
  await expect(page.getByText("Las ventas tienen un pico claro en el primer bloque analizado.")).toBeVisible();
  await expect(page.getByRole("cell", { name: "240.5" })).toBeVisible();
  await expect(page.locator(".artifact-name", { hasText: "response.md" })).toBeVisible();
  await expect(page.locator(".artifact-name", { hasText: "preview.json" })).toBeVisible();
});

test("refreshes history after a persisted dataset error and shows the failed run", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Ruta local del dataset").fill("DatasetV1/missing.csv");
  await page.getByLabel("Prompt").fill("Resume los hallazgos principales");
  await page.getByRole("button", { name: "Lanzar run" }).click();

  await expect(page.getByText("dataset_path_not_found")).toBeVisible();
  await expect(page.getByText("Dataset path does not exist").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /run-ui-failed-001/ })).toBeVisible();
  await expect(page.locator(".run-history-button-active")).toContainText("run-ui-failed-001");
  await expect(page.getByText("Error persistido")).toBeVisible();
});
