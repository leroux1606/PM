import type { BoardData } from "@/lib/kanban";

export type ChatTurn = { role: "user" | "assistant"; content: string };

export type AiChatResponse = {
  assistant_message: string;
  board_updated: boolean;
  board: BoardData | null;
};

function errorDetail(data: unknown): string {
  if (data && typeof data === "object" && "detail" in data) {
    const d = (data as { detail: unknown }).detail;
    if (typeof d === "string") return d;
  }
  return "Chat request failed";
}

export async function postAiChat(body: {
  message: string;
  history: ChatTurn[];
}): Promise<AiChatResponse> {
  const res = await fetch("/api/ai/chat", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(errorDetail(data));
  }
  return data as AiChatResponse;
}
