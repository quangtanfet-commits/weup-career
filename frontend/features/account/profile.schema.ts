import { z } from "zod";

import type { ProfileUpdateRequest } from "@/lib/api/endpoints/account";

/**
 * Profile-update schema (architecture.md §11; FR-91). Only the SAFE, editable
 * fields are exposed — `school_level` and `user_type`. Identity/consent
 * attributes (email, age_band, date_of_birth, account_status) are deliberately
 * NOT editable here (they gate consent + ownership, schema `ProfileUpdateRequest`),
 * so the form mirrors that narrow surface. Both selects use closed enum sets
 * that match the generated schema (NFR-20).
 */
export const SCHOOL_LEVELS = [
  "primary",
  "lower_secondary",
  "upper_secondary",
  "tertiary",
  "none",
] as const;

export const USER_TYPES = ["student", "working"] as const;

export const profileUpdateSchema = z.object({
  school_level: z.enum(SCHOOL_LEVELS),
  user_type: z.enum(USER_TYPES),
});

export type ProfileFormValues = z.infer<typeof profileUpdateSchema>;

export function toProfileUpdatePayload(
  values: ProfileFormValues,
): ProfileUpdateRequest {
  return {
    school_level: values.school_level,
    user_type: values.user_type,
  };
}
