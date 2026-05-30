import type { InstrumentType } from "@/lib/api/endpoints/assessments";

/**
 * Frontend item bank + result interpretation for the three instruments
 * (FR-10/FR-13). The backend scorer (`assessments/scoring.py`) accepts
 * **answers only** — a map of `"<DIM>_<n>" -> Likert 1..5` — and tags each item
 * by its leading-letter dimension. It exposes no prompt text, so the runner owns
 * the Vietnamese prompts here, keyed to match that scoring convention.
 *
 * Keeping the bank deliberately small (MVP) and the keys stable means a
 * submission always maps onto a known dimension; unknown keys are ignored
 * server-side, so this can never produce a 422.
 */

/** A single Likert item shown in the runner. `key` matches the backend scorer. */
export interface AssessmentItem {
  /** Backend scoring key: `<DIM>_<n>`, dimension = leading letter (uppercased). */
  readonly key: string;
  /** Vietnamese prompt (the dimension is never surfaced to avoid priming). */
  readonly prompt_vi: string;
}

/** Likert anchor labels (1..5), shared across instruments. */
export const LIKERT_MIN = 1;
export const LIKERT_MAX = 5;
export const LIKERT_LABELS_VI: readonly string[] = [
  "Hoàn toàn không đúng",
  "Không đúng",
  "Phân vân",
  "Đúng",
  "Hoàn toàn đúng",
];

/** RIASEC item bank — one item per Holland dimension (R/I/A/S/E/C). */
const RIASEC_ITEMS: readonly AssessmentItem[] = [
  {
    key: "R_1",
    prompt_vi:
      "Tôi thích lắp ráp, sửa chữa hoặc làm việc với máy móc, dụng cụ.",
  },
  {
    key: "I_1",
    prompt_vi: "Tôi thích tìm hiểu, phân tích và giải các bài toán khó.",
  },
  {
    key: "A_1",
    prompt_vi: "Tôi thích vẽ, viết, âm nhạc hoặc các hoạt động sáng tạo.",
  },
  {
    key: "S_1",
    prompt_vi: "Tôi thích giúp đỡ, hướng dẫn và làm việc cùng người khác.",
  },
  {
    key: "E_1",
    prompt_vi: "Tôi thích thuyết phục, dẫn dắt và khởi xướng công việc mới.",
  },
  {
    key: "C_1",
    prompt_vi:
      "Tôi thích sắp xếp, ghi chép và làm việc theo quy trình rõ ràng.",
  },
];

/** VIPS item bank — one item per Values/Interests/Personality/Skills axis. */
const VIPS_ITEMS: readonly AssessmentItem[] = [
  {
    key: "V_1",
    prompt_vi:
      "Tôi coi trọng việc công việc của mình có ý nghĩa với cộng đồng.",
  },
  {
    key: "I_1",
    prompt_vi: "Tôi bị cuốn hút bởi những chủ đề mình thực sự thấy thú vị.",
  },
  {
    key: "P_1",
    prompt_vi:
      "Tôi hiểu rõ tính cách và cách mình phản ứng trong các tình huống.",
  },
  {
    key: "S_1",
    prompt_vi: "Tôi tự tin vào những kỹ năng mình đã rèn luyện được.",
  },
];

/** MBTI item bank — one item per pole of the four axes. */
const MBTI_ITEMS: readonly AssessmentItem[] = [
  {
    key: "E_1",
    prompt_vi:
      "Tôi lấy lại năng lượng khi ở cùng và trò chuyện với nhiều người.",
  },
  {
    key: "I_1",
    prompt_vi: "Tôi cần thời gian một mình để suy nghĩ và nạp lại năng lượng.",
  },
  {
    key: "S_1",
    prompt_vi:
      "Tôi chú ý tới chi tiết cụ thể và những gì đang thực sự diễn ra.",
  },
  {
    key: "N_1",
    prompt_vi: "Tôi thích nghĩ về ý tưởng, khả năng và bức tranh tổng thể.",
  },
  {
    key: "T_1",
    prompt_vi: "Tôi ra quyết định dựa trên logic và sự công bằng khách quan.",
  },
  {
    key: "F_1",
    prompt_vi: "Tôi ra quyết định dựa trên cảm xúc và ảnh hưởng tới mọi người.",
  },
  {
    key: "J_1",
    prompt_vi: "Tôi thích lên kế hoạch và sắp xếp mọi thứ ngăn nắp, dứt điểm.",
  },
  {
    key: "P_1",
    prompt_vi: "Tôi thích linh hoạt và để ngỏ các lựa chọn đến phút cuối.",
  },
];

const ITEMS_BY_TYPE: Record<InstrumentType, readonly AssessmentItem[]> = {
  riasec: RIASEC_ITEMS,
  vips: VIPS_ITEMS,
  mbti: MBTI_ITEMS,
};

/** Items for an instrument type, in display order. */
export function itemsFor(type: InstrumentType): readonly AssessmentItem[] {
  return ITEMS_BY_TYPE[type];
}

/** Short Vietnamese display name for an instrument type. */
export function instrumentNameVi(type: InstrumentType): string {
  switch (type) {
    case "riasec":
      return "RIASEC — Sở thích nghề nghiệp (Holland)";
    case "vips":
      return "VIPS — Giá trị · Sở thích · Tính cách · Kỹ năng";
    case "mbti":
      return "MBTI — Phong cách tính cách";
  }
}

/** One-line Vietnamese description of what an instrument explores (FR-10). */
export function instrumentBlurbVi(type: InstrumentType): string {
  switch (type) {
    case "riasec":
      return "Khám phá nhóm sở thích nghề nghiệp của bạn theo mô hình Holland.";
    case "vips":
      return "Hiểu điều bạn coi trọng, quan tâm và những điểm mạnh của bản thân.";
    case "mbti":
      return "Nhận biết phong cách tính cách và cách bạn tương tác với thế giới.";
  }
}

/** A RIASEC dimension paired with its Vietnamese interest-group label. */
const RIASEC_GROUP_VI: Record<string, string> = {
  R: "Kỹ thuật — Thực hành (Realistic)",
  I: "Nghiên cứu — Phân tích (Investigative)",
  A: "Nghệ thuật — Sáng tạo (Artistic)",
  S: "Xã hội — Hỗ trợ (Social)",
  E: "Quản lý — Khởi xướng (Enterprising)",
  C: "Nghiệp vụ — Tổ chức (Conventional)",
};

/** Maps a single RIASEC letter to a `/careers?riasec=` filter link + label. */
export interface CareerGroupLink {
  readonly code: string;
  readonly label_vi: string;
  readonly href: string;
}

/**
 * Interpreted, non-prescriptive view of a result payload (FR-12). It never
 * concludes "you must do job X" — it surfaces the strongest interest groups as
 * *links to explore*, with the explanation that the decision stays with the
 * learner / [CRED_DC4F1A36] / [CRED_4FE03DE2].
 */
export interface InterpretedResult {
  /** A short headline code (RIASEC top-3 / [CRED_E8B5A24A] dominant), if present. */
  readonly code?: string;
  /** Per-dimension totals as `[label, score]`, sorted high→low. */
  readonly scores: ReadonlyArray<readonly [string, number]>;
  /** Career-group links to explore (RIASEC only); empty for others. */
  readonly careerGroups: readonly CareerGroupLink[];
}

const RIASEC_ORDER: readonly string[] = ["R", "I", "A", "S", "E", "C"];

function dimensionLabel(type: InstrumentType, dim: string): string {
  if (type === "riasec") return RIASEC_GROUP_VI[dim] ?? dim;
  return dim;
}

/**
 * Interpret a decrypted result payload into a non-prescriptive view. The payload
 * shape is produced by the backend scorer: `{ type, scores: {dim:int}, code? ,
 * dominant? }`. We read defensively (it is `Record<string, unknown>` over the
 * wire) so a schema drift degrades to "no interpretation" rather than crashing.
 */
export function interpretResult(
  type: InstrumentType,
  payload: Record<string, unknown>,
): InterpretedResult {
  const rawScores =
    payload.scores && typeof payload.scores === "object"
      ? (payload.scores as Record<string, unknown>)
      : {};

  const scores: Array<readonly [string, number]> = [];
  for (const [dim, value] of Object.entries(rawScores)) {
    if (typeof value === "number") {
      scores.push([dimensionLabel(type, dim.toUpperCase()), value]);
    }
  }
  scores.sort((a, b) => b[1] - a[1]);

  const code =
    typeof payload.code === "string"
      ? payload.code
      : typeof payload.dominant === "string"
        ? payload.dominant
        : undefined;

  let careerGroups: CareerGroupLink[] = [];
  if (type === "riasec" && typeof payload.code === "string") {
    const letters = payload.code
      .toUpperCase()
      .split("")
      .filter((c) => RIASEC_ORDER.includes(c));
    careerGroups = letters.map((c) => ({
      code: c,
      label_vi: RIASEC_GROUP_VI[c] ?? c,
      href: `/careers?riasec=${c}`,
    }));
  }

  return { code, scores, careerGroups };
}
