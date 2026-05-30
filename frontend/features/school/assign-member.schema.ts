import { z } from "zod";

import type {
  AssignMemberRequest,
  SchoolRole,
} from "@/lib/api/endpoints/school";

/**
 * Assign-member schema (architecture.md §4, FR-80). A `school_admin` assigns a
 * user as a `student` or `counselor` in the school, optionally scoped to a
 * class. `school_admin` is intentionally NOT an assignable role here — the
 * backend constrains `role` to the assignable school roles and the form mirrors
 * that so an invalid value never leaves the client. The payload is
 * contract-checked against the generated `AssignMemberRequest` (NFR-20).
 */
export const ASSIGNABLE_ROLES = [
  "student",
  "counselor",
] as const satisfies readonly SchoolRole[];

export const assignMemberSchema = z.object({
  user_id: z.string().trim().min(1, "Hãy nhập mã người dùng"),
  role: z.enum(ASSIGNABLE_ROLES, {
    errorMap: () => ({ message: "Hãy chọn vai trò" }),
  }),
  // Optional class scoping; empty string means "no class".
  class_id: z.string().trim().optional(),
});

export type AssignMemberFormValues = z.infer<typeof assignMemberSchema>;

export function toAssignMemberPayload(
  values: AssignMemberFormValues,
): AssignMemberRequest {
  return {
    user_id: values.user_id,
    role: values.role,
    class_id:
      values.class_id && values.class_id.length > 0 ? values.class_id : null,
  };
}
