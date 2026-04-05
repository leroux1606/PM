# Frontend demo (Kanban Studio)

This directory is the **Next.js** UI for the Project Management MVP. **`next.config.ts`** uses **`output: "export"`** so **`npm run build`** produces **`out/`**, which FastAPI serves in production (see **`scripts/copy-site.mjs`** and repo **`Containerfile`**). Board state is still **in-memory** in the browser until later parts wire the API.

**Auth (Part 4):** **`src/app/login/page.tsx`** (demo credentials **`user` / `password`**), **`AuthGate`** on the home page, **`LogoutButton`** on the board. Unauthenticated users are redirected to **`/login`** after **`/api/auth/me`** returns 401.

## Stack

| Area | Choice |
|------|--------|
| Framework | Next.js **16** (App Router) |
| UI | React **19**, **Tailwind CSS 4** (`@import "tailwindcss"` in `src/app/globals.css`) |
| Drag and drop | **@dnd-kit** (`core`, `sortable`, `utilities`) |
| Fonts | **Space Grotesk** (display), **Manrope** (body) via `next/font` in `src/app/layout.tsx` |
| Unit / component tests | **Vitest** + **Testing Library** + **jsdom** |
| E2E | **Playwright** (`tests/kanban.spec.ts`) |
| Package manager | **npm** (see `package-lock.json`); scripts in `package.json` use `npm run` |

## Layout and entry

- **`src/app/layout.tsx`** Root layout, fonts, metadata ("Kanban Studio").
- **`src/app/page.tsx`** Renders `<KanbanBoard />` only.
- **`src/app/globals.css`** CSS variables for the product palette (accent yellow, primary blue, purple, navy, gray) and Tailwind theme hooks.

## Data model (client-only)

- **`src/lib/kanban.ts`** Defines `Card`, `Column`, `BoardData`, **`initialData`** (five fixed columns and eight seed cards), **`moveCard`** (drag logic across and within columns), and **`createId`** for new cards.
- Board shape is a **normalized** structure: `columns[]` with `cardIds`, plus `cards: Record<string, Card>`.

## Components

All under **`src/components/`** (not `src/app/components`):

| File | Role |
|------|------|
| `KanbanBoard.tsx` | Client component: owns `useState` for `BoardData`, wires **DndContext** (pointer sensor, `closestCorners`), drag overlay preview, column rename / add card / delete card handlers. |
| `KanbanColumn.tsx` | Droppable column: column title **input** (rename), `SortableContext` for cards, empty state, embeds `NewCardForm`. `data-testid={`column-${column.id}`}`. |
| `KanbanCard.tsx` | Draggable card; delete control; `data-testid` for e2e. |
| `KanbanCardPreview.tsx` | Drag overlay preview. |
| `NewCardForm.tsx` | Inline form to add a card (title + details). |

There is no `src/components/ui` shadcn-style layer yet; primitives are plain Tailwind-styled elements.

## Tests

| Location | Purpose |
|----------|---------|
| `src/lib/kanban.test.ts` | Unit tests for `moveCard` (and related helpers). |
| `src/components/KanbanBoard.test.tsx` | Component tests for the board. |
| `tests/kanban.spec.ts` | Playwright: loads board, adds card, drags card between columns. |
| `vitest.config.ts`, `playwright.config.ts` | Test runner configuration. |

**Playwright (default):** runs **`npm run build:site`** then **`uv run --directory ../backend uvicorn ...`** on **port 3000** so e2e hits the **same FastAPI + static export** stack as production. Requires **`uv`** on your PATH.

**Playwright (Next dev only):** set **`PW_USE_NEXT_DEV=1`** to use **`npm run dev`** on port 3000 instead (no `build:site`).

## Integration notes (for backend work)

- Replace or hydrate **`initialData`** with API data after auth (see root `AGENTS.md` and `docs/PLAN.md`).
- **`BoardData`** is the natural contract for JSON stored in SQLite on the server.

## Scripts (from `package.json`)

- `npm run dev` — Next dev server  
- `npm run build` — static export to **`out/`**  
- `npm run build:site` — **`build`** then copy **`out/`** to **`../backend/site`**  
- `npm run start` — `next start` (not used when serving via FastAPI static export)  
- `npm run test` / `npm run test:unit` — Vitest  
- `npm run test:e2e` — Playwright (see above)  
- `npm run test:all` — unit then e2e  
