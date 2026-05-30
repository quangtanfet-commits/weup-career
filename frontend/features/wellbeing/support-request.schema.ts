import { z } from "zod";

import type { SupportRequestCreate } from "@/lib/api/endpoints/wellbeing";

/**
 * Support-request schema (architecture.md §4, FR-70/FR-71; NL4). A learner
 * describes, in their own words, that they would like to talk to someone. The
 * field is **free text only** — the form deliberately collects no structured
 * risk/severity signals and performs no assessment (NG-03): it is a routing
 * request to a human counselor, never a diagnosis.
 *
 * The validation here is purely about a usable message (non-empty, bounded
 * length); the backend `SupportRequestCreate` body is `{ message: string }`, so
 * the payload is contract-checked against the generated schema (NFR-20).
 */
export const MESSAGE_MAX_LENGTH = 2000;

export const supportRequestSchema = z.object({
  message: z
    .string()
    .trim()
    .min(1, "Hãy chia sẻ đôi điều để chúng tôi kết nối bạn với người hỗ trợ")
    .max(MESSAGE_MAX_LENGTH, `Nội dung tối đa ${MESSAGE_MAX_LENGTH} ký tự`),
});

export type SupportRequestFormValues = z.infer<typeof supportRequestSchema>;

export function toSupportRequestPayload(
  values: SupportRequestFormValues,
): SupportRequestCreate {
  return { message: values.message };
}
