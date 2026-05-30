import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  createContent,
  getEditorContentItem,
  listEditorContent,
  publishContentVersion,
} from "@/lib/api/endpoints/content";
import { useAuthStore, type SessionUser } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const editorUser: SessionUser = {
  id: "ed1",
  email: "editor@example.vn",
  roles: ["content_editor"],
};

describe("content editor endpoints (Bearer, R:content_editor)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().setSession("editor-token", editorUser);
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("listEditorContent GETs /content WITH the token and may forward status", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await listEditorContent({ status: "draft" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toBe(
      "http://localhost:8000/api/v1/content?status=draft",
    );
    // Unlike the public list, the editor list attaches the bearer token.
    expect(new Headers(init?.headers).get("authorization")).toBe(
      "Bearer editor-token",
    );
  });

  it("getEditorContentItem GETs /content/{id} (any status, traceability)", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "ct1" }));

    await getEditorContentItem("ct1");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/content/ct1");
    expect(new Headers(init?.headers).get("authorization")).toBe(
      "Bearer editor-token",
    );
  });

  it("createContent POSTs the CreateContentRequest body to /content", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "ct2" }, 201));

    await createContent({
      title: "T",
      body: "B",
      competency_code: "NL1",
      dieu5_code: "b",
      depth: "K",
      dev_phase: "awareness",
      school_level: "lower_secondary",
      source_ref: "",
    });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/content");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("NL1");
  });

  it("publishContentVersion POSTs to /content/{id}/versions with no body", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "ct2", version: 2 }, 201));

    await publishContentVersion("ct2");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/content/ct2/versions");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toBeUndefined();
  });
});
