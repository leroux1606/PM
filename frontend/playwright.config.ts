import { defineConfig, devices } from "@playwright/test";

const startApi =
  process.env.PW_USE_NEXT_DEV === "1"
    ? "npm run dev -- --hostname 127.0.0.1 --port 3000"
    : "npm run build:site && uv run --directory ../backend uvicorn app.main:app --host 127.0.0.1 --port 3000";

const readyUrl =
  process.env.PW_USE_NEXT_DEV === "1"
    ? "http://127.0.0.1:3000"
    : "http://127.0.0.1:3000/ping";

const baseURL = "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    // Sidebar + five columns need horizontal room so drag tests stay reliable.
    viewport: { width: 1600, height: 900 },
    trace: "retain-on-failure",
  },
  webServer: {
    command: startApi,
    url: readyUrl,
    reuseExistingServer: true,
    timeout: 600_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
