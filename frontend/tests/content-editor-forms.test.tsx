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
});
