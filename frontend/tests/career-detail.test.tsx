import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

import { CareerDetail } from "@/features/careers/CareerDetail";
import type { CareerDetail as CareerDetailData } from "@/lib/api/endpoints/careers";

const detail: CareerDetailData = {
  id: "c1",
  name: "Điều dưỡng viên",
  field: "Y tế",
  riasec_codes: ["S", "C"],
  training_level: "college",
  dieu5_code: "5a",
  version: 1,
  required_competencies: ["NL3"],
  training_paths: "Cao đẳng điều dưỡng 3 năm.",
  labor_market_outlook: "Thiếu hụt nhân lực y tế.",
  source_ref: "Bộ Y tế",
  pathways: [
    {
      id: "p1",
      name: "Trường trung học nghề",
      description: "Học nghề điều dưỡng.",
      type: "vocational_secondary",
    },
  ],
};

describe("CareerDetail", () => {
  it("renders prose fields, RIASEC codes and the localized training level", async () => {
    render(await CareerDetail({ career: detail }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Điều dưỡng viên" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Thiếu hụt nhân lực y tế.")).toBeInTheDocument();
    expect(screen.getByText("Cao đẳng điều dưỡng 3 năm.")).toBeInTheDocument();
    expect(
      screen.getByText(vi_messages.trainingLevel.college),
    ).toBeInTheDocument();
    expect(screen.getByText("Trường trung học nghề")).toBeInTheDocument();
    expect(
      screen.getByText(vi_messages.pathwayType.vocational_secondary),
    ).toBeInTheDocument();
    expect(screen.getByText("S")).toBeInTheDocument();
    expect(screen.getByText("NL3")).toBeInTheDocument();
  });

  it("omits the competencies and pathways sections when empty", async () => {
    render(
      await CareerDetail({
        career: { ...detail, required_competencies: [], pathways: [] },
      }),
    );

    expect(
      screen.queryByText(vi_messages.careerDetail.pathwaysLabel),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(vi_messages.careerDetail.requiredCompetenciesLabel),
    ).not.toBeInTheDocument();
  });
});
