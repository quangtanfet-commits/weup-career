import { z } from "zod";

import type { CreateClassRequest } from "@/lib/api/endpoints/school";

/**
 * Create-class schema (architecture.md §4, FR-80). A `school_admin` names a new
 * class and tags its grade. The backend `CreateClassRequest` body is
 * `{ name: string; grade: string }`, so the payload is contract-checked against
 * the generated schema (NFR-20). Validation here is about a usable name/grade
 * (non-empty, bounded length); the backend stays the authority on scoping.
 */
export const CLASS_NAME_MAX_LENGTH = 120;
export const CLASS_GRADE_MAX_LENGTH = 40;

export const createClassSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Hãy nhập tên lớp")
    .max(
      CLASS_NAME_MAX_LENGTH,
      `Tên lớp tối đa ${CLASS_NAME_MAX_LENGTH} ký tự`,
    ),
  grade: z
    .string()
    .trim()
    .min(1, "Hãy nhập khối/cấp")
    .max(CLASS_GRADE_MAX_LENGTH, `Khối tối đa ${CLASS_GRADE_MAX_LENGTH} ký tự`),
});

export type CreateClassFormValues = z.infer<typeof createClassSchema>;

export function toCreateClassPayload(
  values: CreateClassFormValues,
): CreateClassRequest {
  return { name: values.name, grade: values.grade };
}
