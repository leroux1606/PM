import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { postAiChat } from "@/lib/aiChatApi";

describe("postAiChat", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs /api/ai/chat and returns JSON", async () => {
    const payload = {
      assistant_message: "Hi",
      board_updated: false,
      board: null,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(payload),
      })
    );

    await expect(
      postAiChat({ message: "m", history: [] })
    ).resolves.toEqual(payload);
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "/api/ai/chat",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ message: "m", history: [] }),
      })
    );
  });

  it("throws with detail on error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: () => Promise.resolve({ detail: "bad" }),
      })
    );

    await expect(postAiChat({ message: "x", history: [] })).rejects.toThrow(
      "bad"
    );
  });
});
