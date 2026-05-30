import { z } from "zod";

import type { components } from "@/lib/api/schema";

/**
 * Guardian-invite schema (architecture.md §4.4, FR-03; CP-1/CP-2). A child
 * <16 invites a guardian by email on an independent channel; the guardian then
 * verifies and grants consent. Mirrors the backend `InviteRequest` shape so the
 * request body is contract-checked (NFR-20).
 */
export const relationships = ["mother", "father", "guardian"] as const;

export type Relationship = (typeof relationships)[number];

export const guardianInviteSchema = z.object({
  guardian_email: z
    .string()
    .trim()
    .toLowerCase()
    .min(1, "Vui lòng nhập email của người giám hộ")
    .email("Email không hợp lệ"),
  relationship: z.enum(relationships, {
    errorMap: () => ({ message: "Vui lòng chọn mối quan hệ" }),
  }),
});

export type GuardianInviteFormValues = z.infer<typeof guardianInviteSchema>;

export type GuardianInvitePayload = components["schemas"]["InviteRequest"];

export function toGuardianInvitePayload(
  values: GuardianInviteFormValues,
): GuardianInvitePayload {
  return {
    guardian_email: values.guardian_email,
    relationship: values.relationship,
  };
}
