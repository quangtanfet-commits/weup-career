import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

import { CareerFilters } from "@/features/careers/CareerFilters";

describe("CareerFilters (RSC GET form)", () => {
  it("renders a GET form targeting /careers with the selected values", async () => {
    render(
      await CareerFilters({
        selected: { riasec: "R", training_level: "university" },
      }),
    );

    const form = screen.getByRole("form", {
      name: vi_messages.careers.filtersHeading,
    });
    expect(form).toHaveAttribute("method", "get");
    expect(form).toHaveAttribute("action", "/careers");

    const riasec = screen.getByLabelText(
      vi_messages.careers.riasecLabel,
    ) as HTMLSelectElement;
    expect(riasec.value).toBe("R");

    const level = screen.getByLabelText(
      vi_messages.careers.trainingLevelLabel,
    ) as HTMLSelectElement;
    expect(level.value).toBe("university");
  });

  it("defaults every select to 'all' when no filter is selected", async () => {
    render(await CareerFilters({ selected: {} }));

    const riasec = screen.getByLabelText(
      vi_messages.careers.riasecLabel,
    ) as HTMLSelectElement;
    expect(riasec.value).toBe("");
  });
});
