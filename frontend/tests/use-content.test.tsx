import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { type ReactNode } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const listEditorContent = vi.fn();
const getEditorContentItem = vi.fn();
const createContent = vi.fn();
const publishContentVersion = vi.fn();

vi.mock("@/lib/api/endpoints/content-editor", () => ({
  listEditorContent: (...args: unknown[]) => listEditorContent(...args),
  getEditorContentItem: (...args: unknown[]) => getEditorContentItem(...args),
  createContent: (...args: unknown[]) => createContent(...args),
  publishContentVersion: (...args: unknown[]) => publishContentVersion(...args),
}));

import {
  useCreateContent,
  useEditorContentItem,
  useEditorContentList,
  usePublishContentVersion,
} from "@/features/content/useContent";

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

const item = { id: "ct1", title: "T", status: "draft", version: 1 };

describe("useContent hooks", () => {
  beforeEach(() => {
    listEditorContent.mockReset();
    getEditorContentItem.mockReset();
    createContent.mockReset();
    publishContentVersion.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("useEditorContentList forwards the filters to the endpoint", async () => {
    listEditorContent.mockResolvedValue([item]);
    const { result } = renderHook(
      () => useEditorContentList({ status: "draft" }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(listEditorContent).toHaveBeenCalledWith({ status: "draft" });
    expect(result.current.data).toEqual([item]);
  });

  it("useEditorContentItem stays disabled (idle) without an id", () => {
    const { result } = renderHook(() => useEditorContentItem(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(getEditorContentItem).not.toHaveBeenCalled();
  });

  it("useEditorContentItem fetches the item once an id is given", async () => {
    getEditorContentItem.mockResolvedValue(item);
    const { result } = renderHook(() => useEditorContentItem("ct1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getEditorContentItem).toHaveBeenCalledWith("ct1");
    expect(result.current.data).toEqual(item);
  });

  it("useCreateContent posts the payload through the endpoint", async () => {
    createContent.mockResolvedValue(item);
    const { result } = renderHook(() => useCreateContent(), {
      wrapper: createWrapper(),
    });

    const payload = {
      title: "T",
      body: "B",
      competency_code: "NL1",
      dieu5_code: "b",
      depth: "K",
      dev_phase: "awareness",
      school_level: "lower_secondary",
      source_ref: "",
    };
    await result.current.mutateAsync(payload as never);

    expect(createContent).toHaveBeenCalledWith(payload);
  });

  it("usePublishContentVersion publishes for the bound content id", async () => {
    publishContentVersion.mockResolvedValue({ ...item, version: 2 });
    const { result } = renderHook(() => usePublishContentVersion("ct1"), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync();

    expect(publishContentVersion).toHaveBeenCalledWith("ct1");
  });
});
