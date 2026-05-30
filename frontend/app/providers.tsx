"use client";

import type { ReactNode } from "react";

import { QueryProvider } from "@/lib/query/provider";

/**
 * Client-side provider tree (TanStack Query, ADR-004). The auth store is a
 * Zustand store consumed directly by hooks, so it needs no provider. next-intl
 * is provided from the server layout (it supports RSC), so it is not wrapped
 * here.
 */
export function Providers({ children }: { children: ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>;
}
