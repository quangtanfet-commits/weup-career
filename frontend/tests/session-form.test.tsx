import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  act,
  render,
  screen,
  waitFor,
  type RenderResult,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";

vi.mock("@/lib/api/endpoints/counseling", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/api/endpoints/counseling")>();
  return { ...actual, createCounselingSession: vi.fn() };
});

import { createCounselingSession } from "@/lib/api/endpoints/counseling";
import { SessionForm } from "@/features/counseling/SessionForm";

const createSessionMock = vi.mocked(createCounselingSession);

function renderForm(ui: ReactElement): RenderResult {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <NextIntlClientProvider locale={defaultLocale} messages={messages}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </NextIntlClientProvider>
    );
  }
  return render(ui, { wrapper: Wrapper });
}

describe("SessionForm (FR-81)", () => {
  beforeEach(() => {
    createSessionMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("logs a Tier 3 session with the chosen student and notes", async () => {
    const user = userEvent.setup();
    createSessionMock.mockResolvedValue({
      id: "s1",
      counselor_id: "c1",
      student_id: "stu-1",
      tier: "3",
      notes: "Trao đổi định hướng",
    });

    renderForm(<SessionForm defaultStudentId="stu-1" />);

    await user.type(
      screen.getByLabelText(messages.counselor.sessionNotesLabel),
      "Trao đổi định hướng",
    );
    await user.click(
      screen.getByRole("button", { name: messages.counselor.sessionSubmit }),
    );

    await waitFor(() => expect(createSessionMock).toHaveBeenCalledTimes(1));
    expect(createSessionMock).toHaveBeenCalledWith({
      student_id: "stu-1",
      tier: "3",
      notes: "Trao đổi định hướng",
    });
    expect(
      await screen.findByText(messages.counselor.sessionSaved),
    ).toBeInTheDocument();
  });

  it("validates that a student id is required before submitting", async () => {
    const user = userEvent.setup();
    renderForm(<SessionForm />);

    await act(async () => {
      await user.click(
        screen.getByRole("button", { name: messages.counselor.sessionSubmit }),
      );
    });

    expect(await screen.findByText("Hãy chọn học sinh")).toBeInTheDocument();
    expect(createSessionMock).not.toHaveBeenCalled();
  });
});
