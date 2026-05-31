import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { type ReactNode } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const getProfile = vi.fn();
const updateProfile = vi.fn();
const changePassword = vi.fn();
const deleteAccount = vi.fn();
const exportData = vi.fn();
const exportChildData = vi.fn();
const deleteChildAccount = vi.fn();

vi.mock("@/lib/api/endpoints/account", () => ({
  getProfile: (...args: unknown[]) => getProfile(...args),
  updateProfile: (...args: unknown[]) => updateProfile(...args),
  changePassword: (...args: unknown[]) => changePassword(...args),
  deleteAccount: (...args: unknown[]) => deleteAccount(...args),
  exportData: (...args: unknown[]) => exportData(...args),
  exportChildData: (...args: unknown[]) => exportChildData(...args),
  deleteChildAccount: (...args: unknown[]) => deleteChildAccount(...args),
}));

import {
  useChangePassword,
  useDeleteAccount,
  useDeleteChildAccount,
  useExportChildData,
  useExportData,
  useProfile,
  useUpdateProfile,
} from "@/features/account/useAccount";

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

const profile = { id: "u1", email: "me@example.vn" };

describe("useAccount hooks", () => {
  beforeEach(() => {
    getProfile.mockReset();
    updateProfile.mockReset();
    changePassword.mockReset();
    deleteAccount.mockReset();
    exportData.mockReset();
    exportChildData.mockReset();
    deleteChildAccount.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("useProfile fetches the caller's profile", async () => {
    getProfile.mockResolvedValue(profile);
    const { result } = renderHook(() => useProfile(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getProfile).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(profile);
  });

  it("useUpdateProfile patches the editable fields", async () => {
    updateProfile.mockResolvedValue(profile);
    const { result } = renderHook(() => useUpdateProfile(), {
      wrapper: createWrapper(),
    });

    const payload = { school_level: "tertiary", user_type: "working" };
    await result.current.mutateAsync(payload as never);

    expect(updateProfile).toHaveBeenCalledWith(payload);
  });

  it("useChangePassword posts the password change", async () => {
    changePassword.mockResolvedValue(undefined);
    const { result } = renderHook(() => useChangePassword(), {
      wrapper: createWrapper(),
    });

    const payload = { current_password: "a", new_password: "bbbbbbbb" };
    await result.current.mutateAsync(payload as never);

    expect(changePassword).toHaveBeenCalledWith(payload);
  });

  it("useExportData triggers the export", async () => {
    exportData.mockResolvedValue({ subject_id: "u1" });
    const { result } = renderHook(() => useExportData(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync();

    expect(exportData).toHaveBeenCalledTimes(1);
  });

  it("useDeleteAccount soft-deletes the account", async () => {
    deleteAccount.mockResolvedValue({ recovery_window_days: 30 });
    const { result } = renderHook(() => useDeleteAccount(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync();

    expect(deleteAccount).toHaveBeenCalledTimes(1);
  });

  it("useExportChildData exports for the given child id", async () => {
    exportChildData.mockResolvedValue({ subject_id: "c1" });
    const { result } = renderHook(() => useExportChildData(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync("c1");

    expect(exportChildData).toHaveBeenCalledWith("c1");
  });

  it("useDeleteChildAccount soft-deletes the given child id", async () => {
    deleteChildAccount.mockResolvedValue({ recovery_window_days: 30 });
    const { result } = renderHook(() => useDeleteChildAccount(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync("c1");

    expect(deleteChildAccount).toHaveBeenCalledWith("c1");
  });
});
