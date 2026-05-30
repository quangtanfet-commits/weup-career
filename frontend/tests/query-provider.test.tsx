import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { useQuery } from "@tanstack/react-query";

import { QueryProvider } from "@/lib/query/provider";

function Probe() {
  const { data } = useQuery({
    queryKey: ["probe"],
    queryFn: () => Promise.resolve("ok"),
  });
  return <span>{data ?? "pending"}</span>;
}

describe("QueryProvider", () => {
  it("supplies a TanStack Query context to client components", async () => {
    render(
      <QueryProvider>
        <Probe />
      </QueryProvider>,
    );
    // Resolves once the query settles — proves the context is wired.
    expect(await screen.findByText("ok")).toBeInTheDocument();
  });
});
