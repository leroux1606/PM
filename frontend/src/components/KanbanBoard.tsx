"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { LogoutButton } from "@/components/LogoutButton";
import { fetchBoard, saveBoard } from "@/lib/boardApi";
import { createId, moveCard, type BoardData } from "@/lib/kanban";

const SAVE_DEBOUNCE_MS = 450;

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const lastSavedJson = useRef<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const tryLoad = useCallback(() => {
    setLoadError(null);
    setBoard(null);
    fetchBoard()
      .then((data) => {
        const serverJson = JSON.stringify(data);
        lastSavedJson.current = serverJson;
        setBoard(data);
      })
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : "Failed to load board";
        setLoadError(msg);
      });
  }, []);

  useEffect(() => {
    tryLoad();
  }, [tryLoad]);

  const applyBoardFromAssistant = useCallback((data: BoardData) => {
    lastSavedJson.current = JSON.stringify(data);
    setBoard(data);
  }, []);

  useEffect(() => {
    if (board === null) return;
    const serialized = JSON.stringify(board);
    if (serialized === lastSavedJson.current) return;
    const timer = window.setTimeout(() => {
      saveBoard(board)
        .then(() => {
          lastSavedJson.current = serialized;
          setSaveError(null);
        })
        .catch((e: unknown) => {
          const msg = e instanceof Error ? e.message : "Save failed";
          setSaveError(msg);
        });
    }, SAVE_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [board]);

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);
    if (!over || active.id === over.id) return;
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        columns: moveCard(prev.columns, active.id as string, over.id as string),
      };
    });
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        columns: prev.columns.map((col) =>
          col.id === columnId ? { ...col, title } : col
        ),
      };
    });
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        cards: {
          ...prev.cards,
          [id]: { id, title, details: details || "No details yet." },
        },
        columns: prev.columns.map((col) =>
          col.id === columnId ? { ...col, cardIds: [...col.cardIds, id] } : col
        ),
      };
    });
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((col) =>
          col.id === columnId
            ? { ...col, cardIds: col.cardIds.filter((id) => id !== cardId) }
            : col
        ),
      };
    });
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (loadError) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[var(--surface)] px-6 font-body text-sm text-[var(--gray-text)]">
        <p>{loadError}</p>
        <button
          type="button"
          className="rounded-full border border-[var(--stroke)] bg-white px-5 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
          onClick={() => tryLoad()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (board === null) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] font-body text-sm text-[var(--gray-text)]">
        Loading board
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <ChatSidebar onBoardSynced={applyBoardFromAssistant} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="z-20 flex h-14 shrink-0 items-center justify-between border-b border-[var(--stroke)] bg-white/90 px-6 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <h1 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
              Kanban Studio
            </h1>
            <span className="hidden text-xs font-medium text-[var(--gray-text)] sm:block">
              Single board
            </span>
          </div>
          <div className="flex items-center gap-3">
            {saveError && (
              <p className="text-xs text-red-500" role="alert">
                {saveError}
              </p>
            )}
            <LogoutButton />
          </div>
        </header>

        <div className="relative flex-1 overflow-x-auto overflow-y-auto">
          <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
          <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

          <main className="relative mx-auto max-w-[1500px] px-6 pb-16 pt-8">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <section className="grid gap-5 lg:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.flatMap((id) => {
                      const card = board.cards[id];
                      return card ? [card] : [];
                    })}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                  />
                ))}
              </section>
              <DragOverlay>
                {activeCard ? (
                  <div className="w-[260px]">
                    <KanbanCardPreview card={activeCard} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          </main>
        </div>
      </div>
    </div>
  );
};
