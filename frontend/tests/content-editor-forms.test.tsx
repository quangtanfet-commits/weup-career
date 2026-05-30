import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const createContentMutate = vi.fn();
const publishMutate = vi.fn();
const useEditorContentListMock = vi.fn();
const useEditorContentItemMock = vi.fn();

vi.mock("@/features/content/useContent", () => ({
  useCreateContent: () => ({
    mutateAsync: createContentMutate,
    isPending: false,
  }),
  usePublishContentVersion: () => ({
    mutateAsync: publishMutate,
    isPending: false,
  }),
  useEditorContentList: () => useEditorContentListMock(),
  useEditorContentItem: (id: string | undefined) =>
    useEditorContentItemMock(id),
}));

import { CreateContentForm } from "@/features/content/CreateContentForm";
import { ContentList } from "@/features/content/ContentList";
import { EditorContentDetail } from "@/features/content/EditorContentDetail";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

const published = {
  id: "ct1",
  title: "Hiểu về bản thân",
  body: "Nội dung.",
  competency_code: "NL1",
  dieu5_code: "b",
  depth: "K" as const,
  dev_phase: "awareness" as const,
  school_level: "lower_secondary" as const,
  source_ref: "CTGDPT 2018",
  status: "published" as const,
  version: 1,
};

describe("content editor forms + list + detail", () => {
  beforeEach(() => {
    createContentMutate.mockReset();
    publishMutate.mockReset();
    useEditorContentListMock.mockReset();
    useEditorContentItemMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("CreateContentForm submits all five mandatory tags", async () => {
    createContentMutate.mockResolvedValue({ id: "ctNew" });
    const user = userEvent.setup();
    renderWithIntl(<CreateContentForm />);

    await user.type(
      screen.getByLabelText(viMessages.editor.createContent.titleLabel),
      "Tiêu đề",
    );
    await user.type(
      screen.getByLabelText(viMessages.editor.createContent.bodyLabel),
      "Nội dung mẫu",
    );
    await user.type(
      screen.getByLabelText(viMessages.editor.createContent.competencyLabel),
      "NL1",
    );
    await user.type(
      screen.getByLabelText(viMessages.editor.createContent.dieu5Label),
      "b",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.editor.createContent.submit,
      }),
    );

    await waitFor(() => expect(createContentMutate).toHaveBeenCalledTimes(1));
    const payload = createContentMutate.mock.calls[0]![0];
    expect(payload).toMatchObject({
      title: "Tiêu đề",
      competency_code: "NL1",
      dieu5_code: "b",
      depth: "K",
      dev_phase: "awareness",
      school_level: "lower_secondary",
    });
  });

  it("ContentList renders rows at all statuses with links to detail", () => {
    useEditorContentListMock.mockReturnValue({
      data: [published, { ...published, id: "ct2", status: "draft" }],
      isPending: false,
      isError: false,
      error: null,
    });
    renderWithIntl(<ContentList />);

    expect(
      screen.getByText(viMessages.editor.status.published),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.editor.status.draft),
    ).toBeInTheDocument();
    const link = screen.getAllByRole("link")[0]!;
    expect(link.getAttribute("href")).toBe("/editor/content/ct1");
  });

  it("EditorContentDetail shows the item and publishes a version", async () => {
    useEditorContentItemMock.mockReturnValue({
      data: published,
      isPending: false,
      isError: false,
      error: null,
    });
    publishMutate.mockResolvedValue({ ...published, version: 2 });
    const user = userEvent.setup();
    renderWithIntl(<EditorContentDetail contentId="ct1" />);

    expect(screen.getByText("Hiểu về bản thân")).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: viMessages.editor.publish.submit }),
    );
    await waitFor(() => expect(publishMutate).toHaveBeenCalledTimes(1));
    expect(
      await screen.findByText(viMessages.editor.publish.published),
    ).toBeInTheDocument();
  });

  it("ContentList shows a loading status while pending", () => {
    useEditorContentListMock.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      error: null,
    });
    renderWithIntl(<ContentList />);

    expect(
      screen.getByText(viMessages.editor.list.loading),
    ).toBeInTheDocument();
  });

  it("ContentList shows the empty state when there is no content", () => {
    useEditorContentListMock.mockReturnValue({
      data: [],
      isPending: false,
      isError: false,
      error: null,
    });
    renderWithIntl(<ContentList />);

    expect(screen.getByText(viMessages.editor.list.empty)).toBeInTheDocument();
  });

  it("ContentList surfaces a backend error message", () => {
    useEditorContentListMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new ApiError(401, "Phiên đã hết hạn", "UNAUTHORIZED"),
    });
    renderWithIntl(<ContentList />);

    expect(screen.getByText("Phiên đã hết hạn")).toBeInTheDocument();
  });

  it("ContentList falls back to a generic error for non-ApiError failures", () => {
    useEditorContentListMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new Error("boom"),
    });
    renderWithIntl(<ContentList />);

    expect(
      screen.getByText(viMessages.editor.genericError),
    ).toBeInTheDocument();
  });

  it("EditorContentDetail shows a loading status while pending", () => {
    useEditorContentItemMock.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      error: null,
    });
    renderWithIntl(<EditorContentDetail contentId="ct1" />);

    expect(
      screen.getByText(viMessages.editor.detail.loading),
    ).toBeInTheDocument();
  });

  it("EditorContentDetail renders a neutral not-found on 404 (no id leak, CP-4)", () => {
    useEditorContentItemMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new ApiError(404, "missing", "NOT_FOUND"),
    });
    renderWithIntl(<EditorContentDetail contentId="ct1" />);

    expect(
      screen.getByText(viMessages.editor.detail.notFound),
    ).toBeInTheDocument();
  });

  it("EditorContentDetail surfaces a non-404 backend error message", () => {
    useEditorContentItemMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new ApiError(500, "Lỗi máy chủ", "SERVER_ERROR"),
    });
    renderWithIntl(<EditorContentDetail contentId="ct1" />);

    expect(screen.getByText("Lỗi máy chủ")).toBeInTheDocument();
  });

  it("EditorContentDetail falls back to a generic error for non-ApiError failures", () => {
    useEditorContentItemMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new Error("boom"),
    });
    renderWithIntl(<EditorContentDetail contentId="ct1" />);

    expect(
      screen.getByText(viMessages.editor.genericError),
    ).toBeInTheDocument();
  });
});
