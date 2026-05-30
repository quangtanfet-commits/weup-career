import { z } from "zod";

/**
 * Child-identifier schema (architecture.md §11; FR-92). A guardian exercises a
 * linked child's data-subject rights by the child's id; the backend re-checks
 * the guardian link per request (CP-4), so this only enforces a non-empty id
 * before firing the call.
 */
export const childIdSchema = z.object({
  child_id: z.string().trim().min(1, "Hãy nhập mã định danh của trẻ"),
});

export type ChildIdFormValues = z.infer<typeof childIdSchema>;
