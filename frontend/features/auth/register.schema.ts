import { z } from "zod";

import type { components } from "@/lib/api/schema";

/**
 * Registration schema — mirrors the backend Pydantic rules (architecture.md §1):
 * email lowercased/trimmed, password ≥8 with upper+lower+digit, date_of_birth a
 * real past date. Keeping the same rules client-side gives instant Vietnamese
 * feedback; the backend stays the final authority (422 on mismatch).
 *
 * `school_level`/`user_type` are constrained to the generated OpenAPI enums so
 * the request body is contract-checked at compile time (NFR-20).
 */
type SchoolLevel = components["schemas"]["SchoolLevel"];
type UserType = components["schemas"]["UserType"];

export const schoolLevels: readonly SchoolLevel[] = [
  "primary",
  "lower_secondary",
  "upper_secondary",
  "tertiary",
  "none",
];

export const userTypes: readonly UserType[] = ["student", "working"];

const passwordSchema = z
  .string()
  .min(8, "Mật khẩu phải có ít nhất 8 ký tự")
  .regex(/[a-z]/, "Mật khẩu phải có ít nhất một chữ thường")
  .regex(/[A-Z]/, "Mật khẩu phải có ít nhất một chữ hoa")
  .regex(/[0-9]/, "Mật khẩu phải có ít nhất một chữ số");

export const registerSchema = z
  .object({
    email: z
      .string()
      .trim()
      .toLowerCase()
      .min(1, "Vui lòng nhập email")
      .email("Email không hợp lệ"),
    password: passwordSchema,
    confirmPassword: z.string(),
    date_of_birth: z
      .string()
      .min(1, "Vui lòng nhập ngày sinh")
      .refine((value) => !Number.isNaN(Date.parse(value)), {
        message: "Ngày sinh không hợp lệ",
      })
      .refine((value) => new Date(value) < new Date(), {
        message: "Ngày sinh phải là một ngày trong quá khứ",
      }),
    school_level: z.enum([
      "primary",
      "lower_secondary",
      "upper_secondary",
      "tertiary",
      "none",
    ]),
    user_type: z.enum(["student", "working"]),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Mật khẩu nhập lại không khớp",
    path: ["confirmPassword"],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

/** The request body the backend expects (no `confirmPassword`). */
export type RegisterPayload = components["schemas"]["RegisterRequest"];

export function toRegisterPayload(values: RegisterFormValues): RegisterPayload {
  return {
    email: values.email,
    password: values.password,
    date_of_birth: values.date_of_birth,
    school_level: values.school_level,
    user_type: values.user_type,
  };
}

/**
 * Whole years between `dob` and `now`. Used to surface the guardian-consent path
 * for under-16 registrants (legal basis: children <16 register via a guardian).
 * This is a UI hint only — the backend derives the authoritative `age_band`.
 */
export function ageInYears(dob: string, now: Date = new Date()): number {
  const birth = new Date(dob);
  if (Number.isNaN(birth.getTime())) return Number.NaN;
  let age = now.getFullYear() - birth.getFullYear();
  const monthDelta = now.getMonth() - birth.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && now.getDate() < birth.getDate())) {
    age -= 1;
  }
  return age;
}

/** True when the date of birth implies a child who must register via a guardian. */
export function requiresGuardian(dob: string, now: Date = new Date()): boolean {
  const age = ageInYears(dob, now);
  return !Number.isNaN(age) && age < 16;
}
