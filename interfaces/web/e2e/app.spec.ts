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

test("creates a dataset chat and renders an embedded chart instead of raw artifact paths", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Chats analíticos locales", exact: true })).toBeVisible();
  await page
    .getByLabel("Dataset local")
    .selectOption("DatasetV1/student_lifestyle_performance_dataset.csv");
  await page
    .getByLabel("Pregunta inicial")
    .fill("dime cual es la carrera (branch) en la que mas se estudia");
  await page.getByRole("button", { name: "Crear chat" }).click();

  await expect(page.getByText("Civil lidera por horas de estudio")).toBeVisible();
  await expect(page.getByTestId("chart-ranking_Branch_by_Study_Hours_per_Day")).toBeVisible();
  await expect(page.getByText("Exportaciones técnicas")).toHaveCount(0);
  await expect(page.getByText("artifacts/runs/chat-created-001/response.md")).toHaveCount(0);
  await expect(page.getByText("preview", { exact: true })).toHaveCount(0);
  await expect(page.getByText("numeric_summary", { exact: true })).toHaveCount(0);
});

test("allows manual dataset path fallback", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Usar ruta manual" }).click();
  await page.getByLabel("Ruta local del dataset").fill("DatasetV1/student_lifestyle_performance_dataset.csv");
  await page.getByLabel("Pregunta inicial").fill("dime cual es la carrera branch en la que mas se estudia");
  await page.getByRole("button", { name: "Crear chat" }).click();

  await expect(page.getByText("Civil lidera por horas de estudio")).toBeVisible();
});

test("switches compatible chart views without requesting new analysis", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Students lifestyle/ }).click();

  await expect(page.getByTestId("chart-ranking_Branch_by_Study_Hours_per_Day")).toBeVisible();
  await page.getByRole("button", { name: "Línea" }).click();
  await expect(page.getByTestId("chart-view-line")).toBeVisible();
  await page.getByRole("button", { name: "Puntos" }).click();
  await expect(page.getByTestId("chart-view-scatter")).toBeVisible();
  await page.getByRole("button", { name: "Tabla" }).click();
  await expect(page.getByTestId("chart-view-table")).toBeVisible();
});

test("continues the selected chat with conversational memory", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /Students lifestyle/ }).click();
  await expect(page.getByText("Civil lidera por horas de estudio")).toBeVisible();

  await page.getByLabel("Nueva pregunta").fill("y comparalo con la segunda carrera");
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect(page.getByText("Comparado con ECE")).toBeVisible();
  await expect(page.getByTestId("chat-memory-note")).toContainText("Mismo dataset");
});

test("keeps chats browseable when provider is down and blocks new submissions", async ({ page, request }) => {
  await setScenario(request, "provider_down");
  await page.goto("/");

  await expect(page.getByText("Ollama no responde en 127.0.0.1:11434.")).toBeVisible();
  await expect(page.getByText("Proveedor y modelo")).toBeVisible();
  await expect(page.getByText("deepseek-r1:8b")).toBeHidden();
  await expect(page.getByRole("button", { name: "Crear chat" })).toBeDisabled();
  await page.getByRole("button", { name: /Students lifestyle/ }).click();
  await expect(page.getByText("Civil lidera por horas de estudio")).toBeVisible();
});

test("renders helpful empty states when there are no local chats yet", async ({ page, request }) => {
  await setScenario(request, "empty_chats");
  await page.goto("/");

  await expect(page.getByText("Sin chats todavía")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Crea o selecciona un chat" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Crear chat" })).toBeEnabled();
});

test("prioritizes the selected conversation on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Students lifestyle" })).toBeVisible();
  const chatBox = await page.getByRole("heading", { name: "Students lifestyle" }).boundingBox();
  const formBox = await page.getByRole("heading", { name: "Crear chat" }).boundingBox();

  expect(chatBox).not.toBeNull();
  expect(formBox).not.toBeNull();
  expect(chatBox!.y).toBeLessThan(formBox!.y);
});
