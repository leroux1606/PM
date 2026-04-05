import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

/** Logs in via fetch in the page so JSON body and Set-Cookie behave like the real UI. */
export async function loginAsDemoUser(page: Page) {
  await page.goto("/login");
  const status = await page.evaluate(async () => {
    const r = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username: "user", password: "password" }),
    });
    return r.status;
  });
  expect(status).toBe(200);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
}
