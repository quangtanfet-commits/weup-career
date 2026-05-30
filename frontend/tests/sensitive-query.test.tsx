import { describe, it, expect, vi } from "vitest";
import type { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import {
  QueryClient,
  QueryClientProvider,
  useQueryClient,
} from "@tanstack/react-query";

import { useSensitiveQuery } from "@/lib/query/sensitive";

function wrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  };
}

describe("useSensitiveQuery (no-cache, CP-3)", () => {
  it("fetches and exposes the data via TanStack Query", async () => {
    const client = new QueryClient();
    const queryFn = vi.fn<() => Promise<{ secret: number }>>(() =>
      Promise.resolve({ secret: 42 }),
    );

    function Probe() {
      const { data } = useSensitiveQuery<{ secret: number }>(
        ["sensitive", "x"],
        queryFn,
      );
      return <span>{data ? `value:${data.secret}` : "pending"}</span>;
    }

    render(<Probe />, { wrapper: wrapper(client) });

    expect(await screen.findByText("value:42")).toBeInTheDocument();
    expect(queryFn).toHaveBeenCalledTimes(1);
  });

  it("registers the query with staleTime 0 and gcTime 0 (never cached)", async () => {
    const client = new QueryClient();
    const queryFn = vi.fn().mockResolvedValue("ok");

    function Probe() {
      const qc = useQueryClient();
      const { data } = useSensitiveQuery(["sensitive", "opts"], queryFn);
      // Surface the registered options once the query exists.
      const observer = qc
        .getQueryCache()
        .find({ queryKey: ["sensitive", "opts"] });
      const opts = observer?.options as
        | { staleTime?: number; gcTime?: number }
        | undefined;
      return (
        <span>
          {data ? `s:${opts?.staleTime ?? "?"}/g:${opts?.gcTime ?? "?"}` : "…"}
        </span>
      );
    }

    render(<Probe />, { wrapper: wrapper(client) });

    await waitFor(() =>
      expect(screen.getByText(/^s:0\/g:0$/)).toBeInTheDocument(),
    );
  });

  it("does not fetch when disabled via the only overridable option", async () => {
    const client = new QueryClient();
    const queryFn = vi.fn().mockResolvedValue("ok");

    function Probe() {
      const { isLoading } = useSensitiveQuery(["sensitive", "off"], queryFn, {
        enabled: false,
      });
      return <span>{isLoading ? "loading" : "idle"}</span>;
    }

    render(<Probe />, { wrapper: wrapper(client) });

    expect(screen.getByText("idle")).toBeInTheDocument();
    expect(queryFn).not.toHaveBeenCalled();
  });
});
