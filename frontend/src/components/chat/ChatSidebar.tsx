"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { postAiChat, type ChatTurn } from "@/lib/aiChatApi";
import type { BoardData } from "@/lib/kanban";

type Props = {
  onBoardSynced: (board: BoardData) => void;
};

export function ChatSidebar({ onBoardSynced }: Props) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  const send = useCallback(async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    setError(null);
    setBusy(true);
    const history: ChatTurn[] = turns.map((t) => ({
      role: t.role,
      content: t.content,
    }));
    try {
      const res = await postAiChat({ message: text, history });
      setTurns((prev) => [
        ...prev,
        { role: "user", content: text },
        { role: "assistant", content: res.assistant_message },
      ]);
      if (res.board_updated && res.board) {
        onBoardSynced(res.board);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Something went wrong";
      setError(msg);
      setDraft(text);
    } finally {
      setBusy(false);
    }
  }, [busy, draft, onBoardSynced, turns]);

  useEffect(() => {
    scrollToBottom();
  }, [turns, busy, scrollToBottom]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  return (
    <aside
      className="flex h-screen w-[min(100vw,22rem)] shrink-0 flex-col border-r border-[var(--stroke)] bg-[var(--surface-strong)] shadow-[var(--shadow)]"
      aria-label="AI assistant chat"
    >
      <div className="border-b border-[var(--stroke)] px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
          Assistant
        </p>
        <p className="mt-1 text-xs leading-5 text-[var(--gray-text)]">
          Ask about the board. Changes from the model apply here when returned.
        </p>
      </div>

      <div
        ref={listRef}
        className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3"
      >
        {turns.length === 0 ? (
          <p className="text-sm text-[var(--gray-text)]">
            Send a message to start.
          </p>
        ) : null}
        {turns.map((t, i) => (
          <div
            key={`${i}-${t.role}`}
            className={
              t.role === "user"
                ? "ml-4 rounded-2xl rounded-br-md border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)]"
                : "mr-4 rounded-2xl rounded-bl-md border border-[var(--primary-blue)]/25 bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)]"
            }
          >
            <span className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              {t.role === "user" ? "You" : "Assistant"}
            </span>
            <p className="whitespace-pre-wrap">{t.content}</p>
          </div>
        ))}
        {busy ? (
          <p className="text-xs text-[var(--gray-text)]" aria-live="polite">
            Thinking
          </p>
        ) : null}
      </div>

      {error ? (
        <div className="border-t border-[var(--stroke)] px-3 py-2 text-xs text-red-600" role="alert">
          {error}
        </div>
      ) : null}

      <form
        className="border-t border-[var(--stroke)] p-3"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <label className="sr-only" htmlFor="chat-draft">
          Message
        </label>
        <textarea
          id="chat-draft"
          rows={3}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy}
          placeholder="Message"
          className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none ring-[var(--primary-blue)] focus:ring-2 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="mt-2 w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </aside>
  );
}
