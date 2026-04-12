import { expect, test } from "@playwright/test";

import { initialData } from "../src/lib/kanban";
import { loginAsDemoUser } from "./helpers/login";

test.beforeEach(async ({ page }) => {
  await loginAsDemoUser(page);
  // Restore the demo board so every test starts from a known state with all demo cards.
  await page.evaluate(async (board) => {
    await fetch("/api/board", {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(board),
    });
  }, initialData);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("persists a new card across reload", async ({ page }) => {
  await page.goto("/");
  const label = `Persist ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const savedWithLabel = page.waitForResponse(
    (r) =>
      r.url().includes("/api/board") &&
      r.request().method() === "PUT" &&
      r.ok() &&
      (r.request().postData()?.includes(label) ?? false)
  );
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(label);
  await firstColumn.getByPlaceholder("Details").fill("e2e persistence");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(label)).toBeVisible();
  await savedWithLabel;

  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.getByText(label)).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  await card.scrollIntoViewIfNeeded();
  await targetColumn.scrollIntoViewIfNeeded();
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }
  const startX = cardBox.x + cardBox.width / 2;
  const startY = cardBox.y + cardBox.height / 2;
  const endX = columnBox.x + columnBox.width / 2;
  const endY = columnBox.y + 280;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  // dnd-kit PointerSensor needs a small move after press to activate the drag.
  await page.mouse.move(startX + 10, startY + 10, { steps: 2 });
  await page.mouse.move(endX, endY, { steps: 24 });
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});
