# ADR-004: Frontend State Management

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Context

The frontend SPA has two categories of state:
1. **Server state**: todo data, tags, user profile (lives on the server, needs caching, background refresh, optimistic updates)
2. **Client state**: auth tokens, UI preferences, pending drag operations (local only)

These have fundamentally different lifecycles and should be managed differently.

---

## Decision

**Use TanStack Query v5 for server state. Use Zustand for client-only state.**

---

## Rationale

### The Two-State Model

Most Redux-era applications used a single global store for everything, mixing server data with UI state. This creates:
- Stale data problems (cached server data goes out of sync)
- Complex normalization logic
- Heavy boilerplate for async operations

The modern pattern: **server state tools handle the cache; client state tools handle local UI state.**

### TanStack Query (React Query) for Server State

**Why not Redux Toolkit Query:**
- RTQ is tightly coupled to Redux; adds RTK overhead for a non-Redux project
- TanStack Query has a larger community, more mature API, and superior TypeScript support

**Why TanStack Query over SWR:**
- More features: optimistic updates, query cancellation, prefetching, dependent queries, infinite scrolling
- Better DevTools
- More active development

**TanStack Query v5 specific benefits:**
- `useMutation` with `onMutate` / `onError` / `onSettled` = clean optimistic update pattern
- `queryClient.invalidateQueries` after mutations = cache coherence
- Automatic background refetch on window focus = data freshness without polling
- `staleTime` configuration per query = granular cache control

### Zustand for Client State

**Why not Redux:**
- Too much boilerplate (actions, reducers, selectors, middleware) for small state
- Adds learning curve overhead

**Why not React Context + useReducer:**
- Performance: Context re-renders every subscriber on every state change
- No built-in selectors (can't subscribe to a slice)
- Not suitable for large state objects

**Why Zustand:**
- Minimal boilerplate (create a store in 10 lines)
- Selector subscriptions: components only re-render when their slice changes
- Works outside React (in Axios interceptors, timers)
- `persist` middleware for localStorage serialization of theme preferences
- `immer` middleware for mutation-style state updates without spread operators
- Zero dependencies in production bundle

### State Architecture

```
Auth Store (Zustand + persist)
  - accessToken: string | null        ← in-memory only (not localStorage)
  - user: UserProfile | null
  - isRefreshing: boolean
  - login(token, user): void
  - logout(): void

UI Store (Zustand)
  - sidebarOpen: boolean
  - activeFilters: FilterState
  - pendingReorder: TodoItem[] | null  ← optimistic drag state

Server State (TanStack Query)
  - ['todos', filters]               ← todo list cache
  - ['todos', id]                    ← single todo cache
  - ['tags']                         ← tag list cache
  - ['user', 'me']                   ← profile cache
```

### Why access_token is NOT in localStorage

localStorage is accessible to any JavaScript on the page (XSS risk). The access token is stored only in Zustand memory (lost on page refresh — intentional; refresh silently from cookie on reload). The httpOnly cookie for refresh token is inaccessible to JavaScript entirely.

---

## Consequences

- Page reload triggers silent token refresh before rendering protected routes
- Zustand store is cleared on logout; TanStack Query cache is cleared via `queryClient.clear()`
- No Redux DevTools — use TanStack Query DevTools + Zustand DevTools (browser extension)
