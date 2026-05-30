import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, waitFor } from "@testing-library/react";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), prefetch: vi.fn() }),
}));

const restoreSession = vi.fn();
let authLostHandler: (() => void) | null = null;
vi.mock("@/lib/auth/session-restore", () => ({
  restoreSession: (...args: unknown[]) => restoreSession(...args),
  onAuthLost: (handler: () => void) => {
    authLostHandler = handler;
    return () => {
      authLostHandler = null;
    };
  },
}));

import { useSessionBootstrap } from "@/lib/auth/useSessionBootstrap";
import { useAuthStore } from "@/lib/auth/store";

function Harness() {
  useSessionBootstrap();
  return null;
}

describe("useSessionBootstrap", () => {
  beforeEach(() => {
    replace.mockReset();
    restoreSession.mockReset();
    authLostHandler = null;
    act(() =>
      useAuthStore.setState({
        status: "loading",
        accessToken: null,
        user: null,
      }),
    );
  });
  afterEach(() => {
    vi.restoreAllMocks();
    act(() => useAuthStore.getState().clearSession());
  });

  it("runs the restore while loading and finishes loading when no session", async () => {
    restoreSession.mockResolvedValue(null);

    render(<Harness />);

    await waitFor(() => expect(restoreSession).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(useAuthStore.getState().status).toBe("anonymous"),
    );
  });

  it("does not run the restore when the session is already established", () => {
    useAuthStore.getState().setSession("jwt", {
      id: "u1",
      email: "a@b.vn",
      roles: ["working"],
    });

    render(<Harness />);

    expect(restoreSession).not.toHaveBeenCalled();
  });

  it("redirects to /login when the auth-lost handler fires", async () => {
    restoreSession.mockResolvedValue(null);
    render(<Harness />);

    expect(authLostHandler).toBeTypeOf("function");
    authLostHandler?.();

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
  });
});
