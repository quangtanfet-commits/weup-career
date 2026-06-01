# Migration: wellbeing support-requests → TanStack Query

- **Group**: C — recorded technical debt (frontend).
- **Branch**: `chore/fe-wellbeing-react-query`
- **Scope**: convert the one remaining manual `useEffect`+`useState` client
  data-read in the app — `features/wellbeing/SupportRequestList.tsx` — to the
  TanStack Query convention already used everywhere else (ADR-004,
  architecture.md §5.4). No backend, no API contract, no TLA+/conformance
  surface, no copy changes.

## Why this slice exists (the debt)

`SupportRequestList.tsx:54` carries the codebase's **only** inline
`react-hooks/set-state-in-effect` eslint-disable:

```tsx
const [items, setItems] = useState<SupportRequestOut[] | null>(null);
const [error, setError] = useState<string | null>(null);
const load = useCallback(async () => {
  setError(null);
  try { setItems(await listSupportRequests()); }
  catch (err) { setError(err instanceof ApiError ? err.message : t("genericError")); }
}, [t]);
useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  void load();
}, [load, refreshKey]);
```

The disable was added during the Next 16 bump (the rule ships enabled in the
React 19 / next-16 ESLint flat config) and explicitly deferred: *"migrating
these feature reads is tracked separately, out of scope for the Next 16 bump."*
This slice is that follow-up.

Manual fetch-in-effect is a fetch/cache pattern react-query was added to
replace. The whole rest of the app already does this — `features/account`
(`useAccount.ts` + `ProfileForm`) and `features/content` (`useContent.ts` +
`ContentList` + `CreateContentForm`) both read through query hooks and refresh
lists via **mutation → cache invalidation**, not a parent `refreshKey` counter.
Wellbeing is the last hold-out. Bringing it in line removes the lint disable
*and* a piece of prop-drilling state.

Confirmed single-instance scope:

```
$ grep -rn "set-state-in-effect" --include="*.tsx" --include="*.ts" frontend/
features/wellbeing/SupportRequestList.tsx:54: // eslint-disable-next-line react-hooks/set-state-in-effect
```

## Target convention (mirror, don't invent)

`features/content/useContent.ts` is the canonical in-repo example and the
direct template:

- a `*Keys` object,
- `useQuery` reads keyed off it,
- `useMutation` writes whose `onSuccess` invalidates the relevant list key so
  the list component re-reads the new truth from the backend.

`ContentList` is the migrated shape `SupportRequestList` should take: **no
props**, `const { data, isPending, isError, error } = useEditorContentList();`,
three guard branches (`isError` → `role="alert"`, `isPending` →
`role="status"`, empty → empty copy), then the list.

## Changes

### 1. New `features/wellbeing/useWellbeing.ts`

Mirror `useContent.ts`:

```ts
export const wellbeingKeys = {
  supportRequests: () => ["wellbeing", "support-requests"] as const,
};

export function useSupportRequests(): UseQueryResult<SupportRequestOut[]> {
  return useQuery({
    queryKey: wellbeingKeys.supportRequests(),
    queryFn: () => listSupportRequests(),
  });
}

export function useCreateSupportRequest(): UseMutationResult<
  SupportRequestOut, unknown, SupportRequestCreate
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => createSupportRequest(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: wellbeingKeys.supportRequests(),
      });
    },
  });
}
```

### 2. `SupportRequestList.tsx`

Drop `useState`/`useCallback`/`useEffect`, the `refreshKey` prop, and the
eslint-disable. Read through the hook and map states exactly like `ContentList`:

```tsx
export function SupportRequestList() {
  const t = useTranslations("wellbeing");
  const { data, isPending, isError, error } = useSupportRequests();

  if (isError) return <p role="alert" …>{error instanceof ApiError ? error.message : t("genericError")}</p>;
  if (isPending) return <p role="status" …>{t("listLoading")}</p>;
  if (data.length === 0) return <p …>{t("listEmpty")}</p>;
  // …unchanged <ul> render (STATUS_TOKENS, vi-VN formatter)…
}
```

Note the error-surface gains the `instanceof ApiError ? … : genericError`
fallback (matching `ContentList`/`ProfileForm`); the old code surfaced
`err.message` directly. The three test cases still pass because the error test
throws an `ApiError` (so `.message` is shown) and react-query's default
`retry: 1` is disabled in the hook-test wrapper.

### 3. `SupportRequestForm.tsx`

Use the mutation; drop the `onCreated` prop. The list refreshes via
invalidation now, so the callback is redundant:

```tsx
const createMutation = useCreateSupportRequest();
const onSubmit = handleSubmit(async (values) => {
  setSubmitError(null);
  try {
    await createMutation.mutateAsync(toSupportRequestPayload(values));
    setStatus("sent");
    reset();
  } catch (err) { setSubmitError(err instanceof ApiError ? err.message : t("genericError")); }
});
```

`isSubmitting` (react-hook-form) still drives the button — it already tracks the
awaited handler, so no behavioural change there.

### 4. `app/(app)/wellbeing/page.tsx`

Drop the `refreshKey` `useState` and the `onCreated` wiring; render
`<SupportRequestForm />` and `<SupportRequestList />` with no coordinating
props. Update the doc-comment that referenced `refreshKey`.

> **Decision — drop `refreshKey`/`onCreated` rather than leave them vestigial.**
> The content slice (`editor/content/page.tsx`) kept a `refreshKey` counter that
> `ContentList` no longer reads — dead state that survives only because that
> slice's debt wasn't in scope when it migrated. We do the clean thing here:
> mutation→invalidation makes both the counter and the callback redundant, so we
> remove them. (The content slice's vestigial `refreshKey` is noted as a
> separate, optional follow-up below — it carries no lint disable, so it is not
> part of Group C.)

## Test changes (two-layer convention)

The repo separates **component tests** (mock the feature hook) from **hook
tests** (mock the endpoint, wrap in `QueryClientProvider`). Follow it:

- **`tests/support-request-list.test.tsx`** → mock `@/features/wellbeing/useWellbeing`'s
  `useSupportRequests` (mirror `account-forms.test.tsx`). The three cases become:
  empty (`{ data: [], isPending: false, isError: false }`), renders
  (`{ data: [...], isPending:false, isError:false }`), error
  (`{ isError: true, error: new ApiError(...) }`). The loading branch (`isPending:
  true` → `role="status"`) gains a fourth case since it is now a first-class
  state.
- **`tests/support-request-form.test.tsx`** → mock `useCreateSupportRequest`
  returning `{ mutateAsync, isPending: false }`. Drop the `onCreated` assertion;
  assert `mutateAsync` called once with the payload, `requestSent` shown,
  `sendAnother` button appears.
- **`tests/use-wellbeing.test.tsx`** (new) → mirror `use-account.test.tsx`:
  mock `@/lib/api/endpoints/wellbeing`, `renderHook` with a local
  `createWrapper()` (`QueryClient` `retry:false`). Cover `useSupportRequests`
  fetches the list, and `useCreateSupportRequest` calls `createSupportRequest`
  with the payload.

Net coverage: the data-read path keeps its component-level cases, the loading
state becomes explicitly tested, and the hook wiring (query key + mutation
invalidation) gains direct hook-level tests — strictly more coverage than today.

## Verification gates

- `npm run test` (vitest) — all green.
- `npm run lint` — no `set-state-in-effect` disable remains; no new warnings.
- `npx tsc --noEmit` — types clean (hook return types explicit like `useAccount`).
- `npm run format:check` — prettier clean (separate CI gate).

## Out of scope / follow-ups

- **Content slice vestigial `refreshKey`**: `editor/content/page.tsx` still
  bumps a `refreshKey` that `ContentList` ignores. Harmless dead state; clean it
  up in a separate tidy-up, not here (no lint disable, not Group C).
- No new sensitive-data caching policy: support requests are routing-only
  (NG-03), so the default `staleTime: 60_000` is fine — same as the profile
  read. No per-query `staleTime:0/gcTime:0` opt-out needed.
