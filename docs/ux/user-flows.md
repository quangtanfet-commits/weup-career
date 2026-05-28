# UX Design: User Flows

**Version:** 1.0.0 | **Date:** 2026-05-27  
**Design Philosophy:** Eliminate friction. Every interaction should feel instant.

---

## Design Principles

These are non-negotiable product constraints, not suggestions:

1. **Zero friction for the primary action**: Creating a todo should take exactly one click + typing + Enter. No modal required.
2. **Instant feedback**: Every action has an immediate visual response (optimistic update or loading state). No request should feel slow.
3. **Safe to be wrong**: Destructive actions (delete) are reversible within 5 seconds. No confirmation dialog — just instant action + undo.
4. **Progressive disclosure**: Advanced features (due date, priority, tags) are accessible but not in the way.
5. **Keyboard-first**: Power users should never need to reach for the mouse.
6. **No visual noise**: Minimal UI. Plenty of whitespace. Task content is the hero.

---

## User Flow 1: Onboarding (First-Time User)

```mermaid
flowchart TD
    START([User opens app]) --> LOGIN_PAGE["/login page\nClean, centered card\nEmail + Password fields\nLogin button\nLink: 'Create account'"]
    
    LOGIN_PAGE --> NEW_USER{New user?}
    
    NEW_USER -->|Yes| REGISTER_LINK["Click 'Create account'"]
    REGISTER_LINK --> REGISTER_PAGE["/register page\nEmail + Password fields\nPassword strength indicator\nCreate account button"]
    REGISTER_PAGE --> VALIDATE["Real-time validation\nas user types\n(Zod + react-hook-form)"]
    VALIDATE --> SUBMIT_REG["Submit form"]
    SUBMIT_REG --> AUTO_LOGIN["Auto-login on success\nNo extra step"]
    AUTO_LOGIN --> EMPTY_STATE["Main todos page\nEmpty state illustration\nCTA: 'Add your first task'"]
    
    NEW_USER -->|No| FILL_LOGIN["Enter credentials"]
    FILL_LOGIN --> SUBMIT_LOGIN["Click Login / Press Enter"]
    SUBMIT_LOGIN --> TODOS_PAGE["Main todos page"]
    SUBMIT_LOGIN --> LOGIN_ERROR["Inline error message\n'Invalid email or password'\n(generic — no enumeration)"]
    
    EMPTY_STATE --> FIRST_TODO["Click CTA → Focus input"]
```

---

## User Flow 2: Creating a Todo (Primary Action)

```mermaid
flowchart TD
    MAIN[Main Page] --> CLICK["Click 'Add task' button\nor press 'N' keyboard shortcut"]
    CLICK --> INLINE_INPUT["Inline input appears\nat top of list\n(no modal)\nAuto-focused"]
    INLINE_INPUT --> TITLE["User types title\n'Buy groceries'"]
    TITLE --> ENTER["Press Enter"]
    ENTER --> OPTIMISTIC["Todo appears instantly\n(optimistic update)\nwith loading indicator"]
    OPTIMISTIC --> SERVER["API call in background"]
    SERVER --> SUCCESS["Loading indicator fades\nReal todo confirmed"]
    
    TITLE --> EXPAND["Click expand icon\nor press Tab"]
    EXPAND --> RICH_FORM["Expanded inline form\n+ Description textarea\n+ Due date picker\n+ Priority selector (Low/Med/High)\n+ Tag multi-select"]
    RICH_FORM --> SAVE["Click Save or Ctrl+Enter"]
    SAVE --> OPTIMISTIC
    
    ENTER --> ESC["User presses Esc"]
    ESC --> CANCEL["Input closes\nNo todo created"]
```

---

## User Flow 3: Managing Todos

```mermaid
flowchart TD
    LIST["Todo List View"] --> HOVER["Hover a todo item"]
    HOVER --> ACTIONS["Reveal action icons:\n✓ Complete | ✏️ Edit | 🗑️ Delete"]
    
    ACTIONS --> COMPLETE["Click ✓ (Complete)"]
    COMPLETE --> DONE_STYLE["Item gets strikethrough\nStatus badge: Done\nMoves to bottom (configurable)"]
    
    ACTIONS --> EDIT["Click ✏️ (Edit)"]
    EDIT --> INLINE_EDIT["Title becomes editable\ninline text field\n(no modal)"]
    INLINE_EDIT --> SAVE_EDIT["Press Enter or click away"]
    SAVE_EDIT --> OPTIMISTIC_UPDATE["Instant optimistic update"]
    
    ACTIONS --> DELETE["Click 🗑️ (Delete)"]
    DELETE --> REMOVE_INSTANT["Item removed instantly\nfrom list\n(optimistic)"]
    REMOVE_INSTANT --> UNDO_TOAST["Toast notification appears:\n'Task deleted  [Undo]'\n5-second countdown"]
    UNDO_TOAST --> UNDO_CLICK["User clicks Undo"]
    UNDO_CLICK --> RESTORE["Item restored to list\nin original position"]
    UNDO_TOAST --> TIMER_EXPIRE["5 seconds pass\nToast dismisses\nSoft delete committed"]
```

---

## User Flow 4: Filtering and Search

```mermaid
flowchart TD
    MAIN_VIEW["Main Todo View\n(Filter bar at top)"]
    
    MAIN_VIEW --> SEARCH["Type in search box\n(debounced 300ms)\n'grocery'"]
    SEARCH --> FILTERED["List narrows in real-time\nMatching text highlighted"]
    
    MAIN_VIEW --> STATUS_FILTER["Click status pills:\n[All] [Open] [In Progress] [Done]"]
    STATUS_FILTER --> STATUS_RESULT["List updates instantly\nfrom TanStack Query cache\n(no loading state for cached filters)"]
    
    MAIN_VIEW --> TAG_FILTER["Click tag name(s)\nin filter bar"]
    TAG_FILTER --> TAG_RESULT["Multi-select: AND logic\nList shows todos\nmatching ALL selected tags"]
    
    MAIN_VIEW --> PRIORITY_SORT["Click column header\nor sort dropdown:\n'Sort by: Priority'"]
    PRIORITY_SORT --> SORTED["List re-sorted\nHigh → Medium → Low"]
    
    MAIN_VIEW --> RESET["'Clear filters' link\n(appears when any filter active)"]
    RESET --> FULL_LIST["Full list restored"]
```

---

## User Flow 5: Drag-and-Drop Reorder

```mermaid
flowchart TD
    LIST["Sorted Todo List"] --> GRAB["User grabs handle icon\n(⠿ drag handle, left side)\non mouse down"]
    GRAB --> DRAG["Item lifts slightly\nShadow effect\n(Framer Motion)"]
    DRAG --> MOVE["User drags up/down\nOther items shift\nto show insertion point"]
    MOVE --> DROP["User releases\n(drop)"]
    DROP --> REORDER_INSTANT["List rearranges instantly\n(local state, optimistic)"]
    REORDER_INSTANT --> API_CALL["POST /api/v1/todos/reorder\n[{id, sort_order}...]"]
    API_CALL --> CONFIRM["Confirmed by server\n(silent, no UI change needed)"]
    API_CALL --> FAIL["Network error\nList reverts to\npre-drag order\nError toast shown"]
```

---

## Page Layouts

### Login / Register Page

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     ✓ Todos                                 │
│                   (logo, centered)                          │
│                                                             │
│              ┌──────────────────────────┐                  │
│              │  Welcome back             │                  │
│              │                          │                  │
│              │  Email                   │                  │
│              │  ┌──────────────────┐   │                  │
│              │  │ user@example.com  │   │                  │
│              │  └──────────────────┘   │                  │
│              │                          │                  │
│              │  Password                │                  │
│              │  ┌──────────────────┐   │                  │
│              │  │ ••••••••••••      │   │                  │
│              │  └──────────────────┘   │                  │
│              │                          │                  │
│              │  ┌──────────────────┐   │                  │
│              │  │    Sign in       │   │                  │
│              │  └──────────────────┘   │                  │
│              │                          │                  │
│              │  Don't have an account? │                  │
│              │  Sign up                 │                  │
│              └──────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Main Todo Page

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Todos                            user@example.com ▾      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Filter bar ─────────────────────────────────────────┐  │
│  │ 🔍 Search todos...    [All][Open][In Progress][Done]  │  │
│  │ Tags: [work ×] [personal ×]  Priority: [High ▾]       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Add task ────────────────────────────────────────────┐  │
│  │  + What do you need to do?              [+ Add detail] │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  TODAY  ─────────────────────────────────────────────────   │
│                                                             │
│  ⠿ [ ] Buy groceries            🏷️ personal  📅 Today  ⚡   │
│  ⠿ [ ] Review PR #142           🏷️ work              🔥   │
│  ⠿ [✓] Book dentist appointment  🏷️ personal  ~~Done~~      │
│                                                             │
│  UPCOMING  ─────────────────────────────────────────────   │
│                                                             │
│  ⠿ [ ] Prepare quarterly report  🏷️ work   📅 Jun 1   🔥   │
│  ⠿ [ ] Call Mom                  🏷️ personal  📅 Jun 3  ─   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Legend: ⠿ drag handle  [ ] checkbox  ~~text~~ strikethrough
        🏷️ tag  📅 due date  🔥 high  ⚡ medium  ─ low priority
```

---

## Accessibility Design

### WCAG 2.1 AA Requirements

| Requirement | Implementation |
|-------------|---------------|
| Color contrast ≥4.5:1 | Tailwind design tokens with pre-tested contrast ratios |
| Keyboard navigation | All interactive elements reachable by Tab; focus ring always visible |
| Screen reader support | Radix UI components have ARIA labels baked in; custom components use `aria-*` attributes |
| No color-only information | Priority shown with text + icon + color (never color alone) |
| Error messages associated with fields | `aria-describedby` links error messages to inputs |
| Focus management | After modal close/delete, focus returns to logical next element |
| Reduced motion | `prefers-reduced-motion` media query disables Framer Motion animations |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `n` | Focus "new todo" input |
| `Escape` | Cancel current editing / close modal |
| `Enter` | Save todo (when input focused) |
| `Ctrl+Enter` | Save with expanded details |
| `/` | Focus search input |
| `Ctrl+Z` | Undo last action (within 5s window) |
| `j` / `k` | Navigate todo list (Vim-style — future) |

---

## Responsive Design

| Breakpoint | Layout |
|------------|--------|
| Mobile (< 640px) | Single column; filter bar collapses to a "Filters" button; no drag-and-drop (use tap-to-select reorder in v2) |
| Tablet (640–1024px) | Same as desktop with slightly tighter spacing |
| Desktop (> 1024px) | Full layout as shown in wireframe above; max-width: 800px centered |
| Wide (> 1280px) | Sidebar available for tag list (future); main column stays max-width |

---

## Micro-Interactions & Animations

**Philosophy:** Animations should feel responsive, not decorative. Every animation serves a functional purpose (communicate state change, guide attention).

| Interaction | Animation | Duration |
|-------------|-----------|----------|
| Todo created | Slide in from top + fade | 150ms |
| Todo deleted | Slide out to right + fade | 200ms |
| Todo completed | Checkbox fill + strikethrough | 200ms ease |
| Status badge change | Cross-fade | 100ms |
| Drag lift | Scale 1.02 + shadow | 150ms |
| Drag drop | Spring return to position | 200ms |
| Filter change | List items animate position change | 200ms |
| Toast appear | Slide up from bottom | 150ms |
| Page load | Skeleton shimmer | 300ms loop |

All animations respect `prefers-reduced-motion: reduce` — degraded to instant state changes.
