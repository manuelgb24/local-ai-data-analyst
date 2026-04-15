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

test("shows readiness ok and keeps the form enabled", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Estado operativo" })).toBeVisible();
  await expect(page.getByText("Aplicacion", { exact: true })).toBeVisible();
  await expect(page.getByText("Proveedor", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Lanzar run" })).toBeEnabled();
});

test("blocks submit when the provider is not ready", async ({ page, request }) => {
  await setScenario(request, "provider_down");
  await page.goto("/");

  await expect(page.locator(".submit-help")).toContainText("El proveedor local no esta listo.");
  await expect(page.getByRole("button", { name: "Lanzar run" })).toBeDisabled();
  await expect(page.getByText("Ollama no responde en 127.0.0.1:11434.")).toBeVisible();
});

test("submits a valid run and renders narrative, findings, tables, and artifacts", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Ruta local del dataset").fill("DatasetV1/Walmart_Sales.csv");
  await page.getByLabel("Prompt").fill("Resume los hallazgos principales");
  await page.getByRole("button", { name: "Lanzar run" }).click();

  await expect(page.getByText("Narrativa UI para: Resume los hallazgos principales")).toBeVisible();
  await expect(page.getByText("Las ventas tienen un pico claro en el primer bloque analizado.")).toBeVisible();
  await expect(page.getByRole("cell", { name: "240.5" })).toBeVisible();
  await expect(page.locator(".artifact-name", { hasText: "response.md" })).toBeVisible();
  await expect(page.locator(".artifact-name", { hasText: "preview.json" })).toBeVisible();
});

test("renders ApiError feedback when the dataset path is syntactically valid but unusable", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Ruta local del dataset").fill("DatasetV1/missing.csv");
  await page.getByLabel("Prompt").fill("Resume los hallazgos principales");
  await page.getByRole("button", { name: "Lanzar run" }).click();

  await expect(page.getByText("dataset_path_not_found")).toBeVisible();
  await expect(page.getByText("Dataset path does not exist")).toBeVisible();
  await expect(page.getByText("dataset_preparation")).toBeVisible();
});