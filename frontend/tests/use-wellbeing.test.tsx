import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { type ReactNode } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const listSupportRequests = vi.fn();
const createSupportRequest = vi.fn();

vi.mock("@/lib/api/endpoints/wellbeing", () => ({
  listSupportRequests: (...args: unknown[]) => listSupportRequests(...args),
  createSupportRequest: (...args: unknown[]) => createSupportRequest(...args),
}));

import {
  useSupportRequests,
  useCreateSupportRequest,
} from "@/features/wellbeing/useWellbeing";

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  };
}

const request = {
  id: "sr1",
  counselor_id: null,
  student_id: "u1",
  tier: "3" as const,
  message: "Em muốn được hỗ trợ.",
  status: "open" as const,
  created_at: "2026-05-30T08:00:00Z",
};

describe("useWellbeing hooks", () => {
  beforeEach(() => {
    listSupportRequests.mockReset();
    createSupportRequest.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("useSupportRequests fetches the learner's own requests", async () => {
    listSupportRequests.mockResolvedValue([request]);
    const { result } = renderHook(() => useSupportRequests(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(listSupportRequests).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual([request]);
  });

  it("useCreateSupportRequest posts the payload", async () => {
    createSupportRequest.mockResolvedValue(request);
    const { result } = renderHook(() => useCreateSupportRequest(), {
      wrapper: createWrapper(),
    });

    const payload = { message: "Em muốn được hỗ trợ." };
    await result.current.mutateAsync(payload as never);

    expect(createSupportRequest).toHaveBeenCalledWith(payload);
  });
});
