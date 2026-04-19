"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { postAiChat, type ChatTurn } from "@/lib/aiChatApi";
import type { BoardData } from "@/lib/kanban";

type Props = {
  onBoardSynced: (board: BoardData) => void;
};

function SendIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function ChevronLeftIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

export function ChatSidebar({ onBoardSynced }: Props) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);
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

  if (collapsed) {
    return (
      <aside
        className="flex h-screen w-12 shrink-0 flex-col items-center border-r border-[var(--stroke)] bg-[var(--surface-strong)] py-3"
        aria-label="AI assistant chat (collapsed)"
      >
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="rounded-lg p-2 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          aria-label="Expand assistant"
        >
          <ChevronRightIcon />
        </button>
        <div className="mt-6 flex flex-1 items-center justify-center">
          <span
            className="text-[10px] font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]"
            style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
          >
            AI
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside
      className="flex h-screen w-[min(100vw,22rem)] shrink-0 flex-col border-r border-[var(--stroke)] bg-[var(--surface-strong)] shadow-[var(--shadow)]"
      aria-label="AI assistant chat"
    >
      <div className="flex items-center justify-between border-b border-[var(--stroke)] px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
            Assistant
          </p>
          <p className="mt-0.5 text-xs leading-5 text-[var(--gray-text)]">
            Ask about the board.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="rounded-lg p-2 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          aria-label="Collapse assistant"
        >
          <ChevronLeftIcon />
        </button>
      </div>

      <div
        ref={listRef}
        className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3"
      >
        {turns.length === 0 ? (
          <p className="text-sm text-[var(--gray-text)]">Send a message to start.</p>
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
        <div
          className="border-t border-[var(--stroke)] px-3 py-2 text-xs text-red-600"
          role="alert"
        >
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
        <div className="flex items-end gap-2">
          <textarea
            id="chat-draft"
            rows={3}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={busy}
            placeholder="Message"
            className="min-w-0 flex-1 resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none ring-[var(--primary-blue)] focus:ring-2 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--secondary-purple)] text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </div>
      </form>
    </aside>
  );
}
