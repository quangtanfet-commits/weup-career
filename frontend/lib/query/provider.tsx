"use client";

import { useState, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";

import { makeQueryClient } from "./client";

/**
 * Wraps client components in a TanStack Query context (ADR-004). The
 * QueryClient is created once per browser session via `useState` so it is
 * stable across re-renders and not shared between requests on the server.
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(makeQueryClient);
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
