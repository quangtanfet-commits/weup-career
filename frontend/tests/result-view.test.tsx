import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { ReactElement } from "react";
import {
  render,
  screen,
  waitFor,
  type RenderResult,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";

const getResult = vi.fn();
const deleteResult = vi.fn();
vi.mock("@/lib/api/endpoints/assessments", () => ({
  getResult: (...args: unknown[]) => getResult(...args),
  deleteResult: (...args: unknown[]) => deleteResult(...args),
}));

import { ResultView } from "@/features/assessments/ResultView";
import type { ResultDetailOut } from "@/lib/api/endpoints/assessments";
import { ApiError } from "@/lib/api/errors";

function renderView(props: {
  resultId: string;
  onDeleted?: () => void;
}): RenderResult {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const ui: ReactElement = (
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale={defaultLocale} messages={messages}>
        <ResultView {...props} />
      </NextIntlClientProvider>
    </QueryClientProvider>
  );
  return render(ui);
}

const detail: ResultDetailOut = {
  id: "r1",
  instrument_id: "i1",
  is_sensitive: true,
  created_at: "2026-01-01T00:00:00Z",
  version: 2,
  payload: {
    type: "riasec",
    scores: { R: 1, I: 5, S: 4 },
    code: "IS",
  },
};

describe("ResultView (CP-3, FR-12/14)", () => {
  beforeEach(() => {
    getResult.mockReset();
    deleteResult.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the sensitive badge, scores, career links and the no-verdict note", async () => {
    getResult.mockResolvedValue(detail);

    renderView({ resultId: "r1" });

    expect(await screen.findByTestId("sensitive-badge")).toBeInTheDocument();
    // Read came from the audited per-result fetch.
    expect(getResult).toHaveBeenCalledWith("r1");

    // Scores rendered (top dimension is Investigative = 5).
    expect(
      screen.getByText(messages.assessment.scoresHeading),
    ).toBeInTheDocument();
    // Career-group links to explore, never a hard verdict.
    const links = screen.getAllByRole("link");
    expect(
      links.some((l) => l.getAttribute("href") === "/careers?riasec=I"),
    ).toBe(true);
    expect(screen.getByRole("note", { name: undefined })).toHaveTextContent(
      messages.assessment.noHardVerdict,
    );
    // Privacy panel.
    expect(
      screen.getByText(messages.assessment.whoCanSeeBody),
    ).toBeInTheDocument();
  });

  it("renders without code/scores/links when the payload is bare (defensive)", async () => {
    // Unknown payload type → defaults to riasec interpretation; no scores, no
    // code, no career groups → those optional blocks are all omitted (FR-12),
    // but the sensitive badge, privacy panel and no-verdict note still show.
    getResult.mockResolvedValue({
      ...detail,
      payload: { type: "unknown-instrument" },
    });

    renderView({ resultId: "r1" });

    expect(await screen.findByTestId("sensitive-badge")).toBeInTheDocument();
    expect(
      screen.queryByText(messages.assessment.scoresHeading),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(messages.assessment.careerGroupsHeading),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/^Mã kết quả/)).not.toBeInTheDocument();
    // The no-verdict guardrail is always present.
    expect(screen.getByRole("note")).toHaveTextContent(
      messages.assessment.noHardVerdict,
    );
  });

  it("can cancel the delete confirmation without deleting", async () => {
    getResult.mockResolvedValue(detail);
    const onDeleted = vi.fn();
    const user = userEvent.setup();

    renderView({ resultId: "r1", onDeleted });
    await screen.findByTestId("sensitive-badge");

    await user.click(
      screen.getByRole("button", { name: messages.assessment.deleteResult }),
    );
    await user.click(
      screen.getByRole("button", { name: messages.assessment.cancelDelete }),
    );

    // Back to the single Delete button; nothing was deleted.
    expect(
      screen.getByRole("button", { name: messages.assessment.deleteResult }),
    ).toBeInTheDocument();
    expect(deleteResult).not.toHaveBeenCalled();
    expect(onDeleted).not.toHaveBeenCalled();
  });

  it("shows a loading state then the result", async () => {
    let resolve!: (v: ResultDetailOut) => void;
    getResult.mockReturnValue(
      new Promise<ResultDetailOut>((r) => {
        resolve = r;
      }),
    );

    renderView({ resultId: "r1" });

    expect(screen.getByRole("status")).toHaveTextContent(
      messages.assessment.loadingResult,
    );
    resolve(detail);
    expect(await screen.findByTestId("sensitive-badge")).toBeInTheDocument();
  });

  it("surfaces a backend error when the read fails", async () => {
    getResult.mockRejectedValue(
      new ApiError(404, "Không tìm thấy kết quả", "NOT_FOUND"),
    );

    renderView({ resultId: "missing" });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không tìm thấy kết quả",
    );
  });

  it("requires a confirm step, then deletes and calls onDeleted (FR-14)", async () => {
    getResult.mockResolvedValue(detail);
    deleteResult.mockResolvedValue(undefined);
    const onDeleted = vi.fn();
    const user = userEvent.setup();

    renderView({ resultId: "r1", onDeleted });
    await screen.findByTestId("sensitive-badge");

    // First click reveals the confirm/cancel pair — no delete yet.
    await user.click(
      screen.getByRole("button", { name: messages.assessment.deleteResult }),
    );
    expect(deleteResult).not.toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", { name: messages.assessment.confirmDelete }),
    );

    await waitFor(() => expect(deleteResult).toHaveBeenCalledWith("r1"));
    expect(onDeleted).toHaveBeenCalledTimes(1);
  });

  it("shows a delete error and keeps the result when delete fails", async () => {
    getResult.mockResolvedValue(detail);
    deleteResult.mockRejectedValue(
      new ApiError(403, "Không có quyền xóa", "FORBIDDEN"),
    );
    const onDeleted = vi.fn();
    const user = userEvent.setup();

    renderView({ resultId: "r1", onDeleted });
    await screen.findByTestId("sensitive-badge");

    await user.click(
      screen.getByRole("button", { name: messages.assessment.deleteResult }),
    );
    await user.click(
      screen.getByRole("button", { name: messages.assessment.confirmDelete }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không có quyền xóa",
    );
    expect(onDeleted).not.toHaveBeenCalled();
  });

  it("exports the viewed result as a JSON download", async () => {
    getResult.mockResolvedValue(detail);
    const user = userEvent.setup();

    // jsdom does not implement URL.createObjectURL/revokeObjectURL at all, so
    // they cannot be spied — define stubs on the prototype, then spy on those.
    const createUrl = vi.fn().mockReturnValue("blob:fake");
    const revokeUrl = vi.fn();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: createUrl,
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: revokeUrl,
    });
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    renderView({ resultId: "r1" });
    await screen.findByTestId("sensitive-badge");

    await user.click(
      screen.getByRole("button", { name: messages.assessment.exportResult }),
    );

    expect(createUrl).toHaveBeenCalledTimes(1);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeUrl).toHaveBeenCalledTimes(1);

    delete (URL as { createObjectURL?: unknown }).createObjectURL;
    delete (URL as { revokeObjectURL?: unknown }).revokeObjectURL;
  });
});
