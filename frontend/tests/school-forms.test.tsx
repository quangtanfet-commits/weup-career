import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const createClassMutate = vi.fn();
const assignMemberMutate = vi.fn();
const useClassesMock = vi.fn();

vi.mock("@/features/school/useSchool", () => ({
  useCreateClass: () => ({ mutateAsync: createClassMutate, isPending: false }),
  useAssignMember: () => ({
    mutateAsync: assignMemberMutate,
    isPending: false,
  }),
  useClasses: (schoolId: string | undefined) => useClassesMock(schoolId),
}));

import { CreateClassForm } from "@/features/school/CreateClassForm";
import { AssignMemberForm } from "@/features/school/AssignMemberForm";
import { ClassList } from "@/features/school/ClassList";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("school-admin forms + list", () => {
  beforeEach(() => {
    createClassMutate.mockReset();
    assignMemberMutate.mockReset();
    useClassesMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("CreateClassForm submits name + grade", async () => {
    createClassMutate.mockResolvedValue({ id: "c1" });
    const user = userEvent.setup();
    renderWithIntl(<CreateClassForm schoolId="s1" />);

    await user.type(
      screen.getByLabelText(viMessages.schoolAdmin.createClass.nameLabel),
      "10A1",
    );
    await user.type(
      screen.getByLabelText(viMessages.schoolAdmin.createClass.gradeLabel),
      "10",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.schoolAdmin.createClass.submit,
      }),
    );

    await waitFor(() => expect(createClassMutate).toHaveBeenCalledTimes(1));
    expect(createClassMutate).toHaveBeenCalledWith({
      name: "10A1",
      grade: "10",
    });
    expect(
      await screen.findByText(viMessages.schoolAdmin.createClass.created),
    ).toBeInTheDocument();
  });

  it("AssignMemberForm submits user_id + role and null class_id", async () => {
    assignMemberMutate.mockResolvedValue({ id: "m1", created: true });
    const user = userEvent.setup();
    renderWithIntl(<AssignMemberForm schoolId="s1" />);

    await user.type(
      screen.getByLabelText(viMessages.schoolAdmin.assignMember.userIdLabel),
      "u1",
    );
    await user.selectOptions(
      screen.getByLabelText(viMessages.schoolAdmin.assignMember.roleLabel),
      "counselor",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.schoolAdmin.assignMember.submit,
      }),
    );

    await waitFor(() => expect(assignMemberMutate).toHaveBeenCalledTimes(1));
    expect(assignMemberMutate).toHaveBeenCalledWith({
      user_id: "u1",
      role: "counselor",
      class_id: null,
    });
  });

  it("ClassList renders class rows from fixture data", () => {
    useClassesMock.mockReturnValue({
      data: [{ id: "c1", name: "10A1", grade: "10", school_id: "s1" }],
      isPending: false,
      isError: false,
      error: null,
    });
    renderWithIntl(<ClassList schoolId="s1" />);
    expect(screen.getByText("10A1")).toBeInTheDocument();
  });

  it("ClassList prompts for a school id when none is set", () => {
    useClassesMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: false,
      error: null,
    });
    renderWithIntl(<ClassList schoolId={undefined} />);
    expect(
      screen.getByText(viMessages.schoolAdmin.classes.needSchool),
    ).toBeInTheDocument();
  });
});
