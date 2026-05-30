import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { type ReactNode } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const listClasses = vi.fn();
const createClass = vi.fn();
const assignMember = vi.fn();

vi.mock("@/lib/api/endpoints/school", () => ({
  listClasses: (...args: unknown[]) => listClasses(...args),
  createClass: (...args: unknown[]) => createClass(...args),
  assignMember: (...args: unknown[]) => assignMember(...args),
}));

import {
  useAssignMember,
  useClasses,
  useCreateClass,
} from "@/features/school/useSchool";

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

const cls = { id: "c1", name: "10A1", grade: 10 };

describe("useSchool hooks", () => {
  beforeEach(() => {
    listClasses.mockReset();
    createClass.mockReset();
    assignMember.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("useClasses stays disabled (idle) until a school id is known", () => {
    const { result } = renderHook(() => useClasses(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(listClasses).not.toHaveBeenCalled();
  });

  it("useClasses fetches the school's classes once scoped", async () => {
    listClasses.mockResolvedValue([cls]);
    const { result } = renderHook(() => useClasses("s1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(listClasses).toHaveBeenCalledWith("s1");
    expect(result.current.data).toEqual([cls]);
  });

  it("useCreateClass posts the class scoped to the school", async () => {
    createClass.mockResolvedValue(cls);
    const { result } = renderHook(() => useCreateClass("s1"), {
      wrapper: createWrapper(),
    });

    const payload = { name: "10A1", grade: 10 };
    await result.current.mutateAsync(payload as never);

    expect(createClass).toHaveBeenCalledWith("s1", payload);
  });

  it("useAssignMember posts the membership scoped to the school", async () => {
    assignMember.mockResolvedValue({ id: "m1" });
    const { result } = renderHook(() => useAssignMember("s1"), {
      wrapper: createWrapper(),
    });

    const payload = { user_id: "u1", role: "student" };
    await result.current.mutateAsync(payload as never);

    expect(assignMember).toHaveBeenCalledWith("s1", payload);
  });
});
