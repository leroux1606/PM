import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchBoard, saveBoard } from "@/lib/boardApi";

describe("boardApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetchBoard GETs /api/board with credentials", async () => {
    const board = { columns: [], cards: {} };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(board),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchBoard()).resolves.toEqual(board);
    expect(fetchMock).toHaveBeenCalledWith("/api/board", {
      credentials: "include",
    });
  });

  it("saveBoard PUTs JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    const data = {
      columns: [{ id: "c1", title: "A", cardIds: ["x"] }],
      cards: {
        x: { id: "x", title: "T", details: "" },
      },
    };

    await saveBoard(data);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/board",
      expect.objectContaining({
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
    );
  });
});
