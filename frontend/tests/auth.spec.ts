import { expect, test } from "@playwright/test";

import { loginAsDemoUser } from "./helpers/login";

test("sends unauthenticated users to login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login\/?$/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("logs in and out", async ({ page }) => {
  await loginAsDemoUser(page);
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login\/?$/);
});
