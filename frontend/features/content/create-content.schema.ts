import { z } from "zod";

import type { CreateContentRequest } from "@/lib/api/endpoints/content-editor";

/**
 * Create-content schema (architecture.md §4, §10; FR-90). A `content_editor`
 * drafts a content unit with the **five mandatory tags** the backend requires —
 * `competency_code`, `dieu5_code`, `depth`, `dev_phase`, `school_level` — plus
 * title/body/source_ref. The enums mirror the generated schema so an invalid
 * value is caught client-side before the backend's 422 (NFR-20). The payload is
 * contract-checked against `CreateContentRequest`.
 */
export const TITLE_MAX_LENGTH = 200;

export const DEPTH_VALUES = ["K", "A", "R"] as const;
export const DEV_PHASE_VALUES = [
  "awareness",
  "exploration",
  "planning",
] as const;
export const SCHOOL_LEVEL_VALUES = [
  "primary",
  "lower_secondary",
  "upper_secondary",
  "tertiary",
  "none",
] as const;

export const createContentSchema = z.object({
  title: z
    .string()
    .trim()
    .min(1, "Hãy nhập tiêu đề")
    .max(TITLE_MAX_LENGTH, `Tiêu đề tối đa ${TITLE_MAX_LENGTH} ký tự`),
  body: z.string().trim().min(1, "Hãy nhập nội dung"),
  competency_code: z.string().trim().min(1, "Hãy nhập mã năng lực"),
  dieu5_code: z.string().trim().min(1, "Hãy nhập mã Điều 5"),
  depth: z.enum(DEPTH_VALUES, {
    errorMap: () => ({ message: "Hãy chọn độ sâu" }),
  }),
  dev_phase: z.enum(DEV_PHASE_VALUES, {
    errorMap: () => ({ message: "Hãy chọn giai đoạn phát triển" }),
  }),
  school_level: z.enum(SCHOOL_LEVEL_VALUES, {
    errorMap: () => ({ message: "Hãy chọn cấp học" }),
  }),
  source_ref: z.string().trim().optional(),
});

export type CreateContentFormValues = z.infer<typeof createContentSchema>;

export function toCreateContentPayload(
  values: CreateContentFormValues,
): CreateContentRequest {
  return {
    title: values.title,
    body: values.body,
    competency_code: values.competency_code,
    dieu5_code: values.dieu5_code,
    depth: values.depth,
    dev_phase: values.dev_phase,
    school_level: values.school_level,
    source_ref: values.source_ref ?? "",
  };
}
