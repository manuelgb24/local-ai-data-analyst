import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "@playwright/test";

const cwd = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:4173",
    headless: true,
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: "node test-support/mock-api.mjs",
      cwd,
      url: "http://127.0.0.1:8010/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4173",
      cwd,
      url: "http://127.0.0.1:4173",
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        VITE_PROXY_TARGET: "http://127.0.0.1:8010",
      },
    },
  ],
});
