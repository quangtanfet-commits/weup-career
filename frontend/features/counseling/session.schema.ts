import { z } from "zod";

import type {
  CreateSessionRequest,
  CounselingTier,
} from "@/lib/api/endpoints/counseling";

/**
 * Counseling-session schema (architecture.md §4.4, §6.2; FR-81). A counselor
 * logs a session for one student at a support tier:
 *   Tier 1 = universal content; Tier 2 = targeted group work; Tier 3 =
 *   individual counselling (matches `CounselingTier` "1"|"2"|"3").
 *
 * Validation keeps the payload usable (a student id is chosen, notes bounded);
 * the backend `CreateSessionRequest` body is contract-checked against the
 * generated schema (NFR-20). `notes` is optional free text — the backend
 * defaults it to "".
 */
export const NOTES_MAX_LENGTH = 4000;

const TIERS = ["1", "2", "3"] as const satisfies readonly CounselingTier[];

export const counselingSessionSchema = z.object({
  student_id: z.string().trim().min(1, "Hãy chọn học sinh"),
  tier: z.enum(TIERS),
  notes: z
    .string()
    .trim()
    .max(NOTES_MAX_LENGTH, `Ghi chú tối đa ${NOTES_MAX_LENGTH} ký tự`),
});

export type CounselingSessionFormValues = z.infer<
  typeof counselingSessionSchema
>;

export function toCreateSessionPayload(
  values: CounselingSessionFormValues,
): CreateSessionRequest {
  return {
    student_id: values.student_id,
    tier: values.tier,
    notes: values.notes,
  };
}
