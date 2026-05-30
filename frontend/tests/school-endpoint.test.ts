import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  assignMember,
  createClass,
  listClasses,
} from "@/lib/api/endpoints/school";
import { useAuthStore, type SessionUser } from "@/lib/auth/store";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const adminUser: SessionUser = {
  id: "admin1",
  email: "admin@example.vn",
  roles: ["school_admin"],
};

describe("school endpoints (Bearer, R:school_admin)", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    useAuthStore.getState().setSession("admin-token", adminUser);
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("listClasses GETs /school/{id}/classes with the bearer token", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await listClasses("school-9");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/school/school-9/classes");
    expect(new Headers(init?.headers).get("authorization")).toBe(
      "Bearer admin-token",
    );
  });

  it("createClass POSTs the CreateClassRequest body", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "c1" }, 201));

    await createClass("school-9", { name: "10A1", grade: "10" });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/school/school-9/classes");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("10A1");
  });

  it("assignMember POSTs the AssignMemberRequest body to /members", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: "m1", created: true }, 201));

    await assignMember("school-9", {
      user_id: "u1",
      role: "counselor",
      class_id: null,
    });

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/school/school-9/members");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toContain("counselor");
  });
});
