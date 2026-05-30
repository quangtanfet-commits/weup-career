import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import vi_messages from "@/messages/vi.json";

vi.mock("next-intl/server", () => ({
  getTranslations: async (ns: keyof typeof vi_messages) => {
    const table = vi_messages[ns] as Record<string, string>;
    return (key: string) => table[key] ?? `${String(ns)}.${key}`;
  },
}));

import { ContentView } from "@/features/content/ContentView";
import type { ContentItem } from "@/lib/api/endpoints/content";

const item: ContentItem = {
  id: "ct1",
  title: "Hiểu về bản thân",
  body: "Dòng một.\nDòng hai.",
  competency_code: "NL1",
  dieu5_code: "5a",
  depth: null,
  dev_phase: null,
  school_level: "upper_secondary",
  source_ref: "CTGDPT 2018",
  status: "published",
  version: 1,
};

describe("ContentView", () => {
  it("renders the title, body and tag metadata", async () => {
    render(await ContentView({ item }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Hiểu về bản thân" }),
    ).toBeInTheDocument();
    expect(screen.getByText("NL1")).toBeInTheDocument();
    expect(screen.getByText("5a")).toBeInTheDocument();
    expect(
      screen.getByText(vi_messages.schoolLevel.upper_secondary),
    ).toBeInTheDocument();
    expect(screen.getByText(/Dòng một\./)).toBeInTheDocument();
  });

  it("omits the school-level row when not set", async () => {
    render(await ContentView({ item: { ...item, school_level: null } }));

    expect(
      screen.queryByText(`${vi_messages.content.schoolLevelLabel}:`),
    ).not.toBeInTheDocument();
  });
});
