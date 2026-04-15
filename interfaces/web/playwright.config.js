var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";
var cwd = path.dirname(fileURLToPath(import.meta.url));
export default defineConfig({
    testDir: "./e2e",
    timeout: 30000,
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
            cwd: cwd,
            url: "http://127.0.0.1:8010/health",
            reuseExistingServer: !process.env.CI,
        },
        {
            command: "npm run dev -- --host 127.0.0.1 --port 4173",
            cwd: cwd,
            url: "http://127.0.0.1:4173",
            reuseExistingServer: !process.env.CI,
            env: __assign(__assign({}, process.env), { VITE_PROXY_TARGET: "http://127.0.0.1:8010" }),
        },
    ],
});
