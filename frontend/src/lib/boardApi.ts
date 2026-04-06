import type { BoardData } from "@/lib/kanban";

export async function fetchBoard(): Promise<BoardData> {
  const res = await fetch("/api/board", { credentials: "include" });
  if (!res.ok) {
    throw new Error(`Could not load board (${res.status})`);
  }
  return res.json() as Promise<BoardData>;
}

export async function saveBoard(board: BoardData): Promise<void> {
  const res = await fetch("/api/board", {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(board),
  });
  if (!res.ok) {
    throw new Error(`Could not save board (${res.status})`);
  }
}
