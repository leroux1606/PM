import { expect, test } from "@playwright/test";

import { initialData } from "../src/lib/kanban";
import { loginAsDemoUser } from "./helpers/login";

/** Chat tests can persist a minimal board; restore demo data so other suites see the default Kanban. */
test.afterEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(async (board) => {
    await fetch("/api/board", {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(board),
    });
  }, initialData);
});

const mockChatReply = (body: object) => {
  return async (route: import("@playwright/test").Route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  };
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/ai/chat", mockChatReply({
    assistant_message: "Mock reply",
    board_updated: false,
    board: null,
  }));
  await loginAsDemoUser(page);
});

test("sends a chat message and shows assistant reply", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Message").fill("Hello assistant");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Mock reply")).toBeVisible();
});

test("applies board update from chat response", async ({ page }) => {
  await page.unroute("**/api/ai/chat");
  await page.route(
    "**/api/ai/chat",
    mockChatReply({
      assistant_message: "Board updated.",
      board_updated: true,
      board: {
        columns: [
          { id: "c1", title: "Only column", cardIds: ["x1"] },
        ],
        cards: {
          x1: {
            id: "x1",
            title: "E2E-AI-CARD-TITLE",
            details: "From mock",
          },
        },
      },
    })
  );
  await page.goto("/");
  await page.getByLabel("Message").fill("Change the board");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Board updated.")).toBeVisible();
  await expect(page.getByText("E2E-AI-CARD-TITLE")).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(1);
});
