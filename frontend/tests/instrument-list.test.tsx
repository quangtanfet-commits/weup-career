import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { ReactElement } from "react";
import { render, screen, type RenderResult } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";

const listInstruments = vi.fn();
vi.mock("@/lib/api/endpoints/assessments", () => ({
  listInstruments: () => listInstruments(),
}));

import { InstrumentList } from "@/features/assessments/InstrumentList";
import type { InstrumentOut } from "@/lib/api/endpoints/assessments";

function renderList(): RenderResult {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const ui: ReactElement = (
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale={defaultLocale} messages={messages}>
        <InstrumentList />
      </NextIntlClientProvider>
    </QueryClientProvider>
  );
  return render(ui);
}

const instruments: InstrumentOut[] = [
  { id: "i1", type: "riasec", is_active: true, version: "1" },
  { id: "i2", type: "vips", is_active: true, version: "1" },
  { id: "i3", type: "mbti", is_active: false, version: "1" },
];

describe("InstrumentList (FR-10)", () => {
  beforeEach(() => {
    listInstruments.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("lists only active instruments and links each to its runner", async () => {
    listInstruments.mockResolvedValue(instruments);

    renderList();

    expect(
      await screen.findByText(/RIASEC/, { selector: "*" }),
    ).toBeInTheDocument();
    // The inactive MBTI instrument is filtered out.
    expect(screen.queryByText(/MBTI/)).not.toBeInTheDocument();

    const links = screen.getAllByRole("link", {
      name: messages.assessment.startInstrument,
    });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/assessments/riasec");
    expect(links[1]).toHaveAttribute("href", "/assessments/vips");
  });

  it("shows the empty state when no instrument is active", async () => {
    listInstruments.mockResolvedValue([
      { id: "i3", type: "mbti", is_active: false, version: "1" },
    ]);

    renderList();

    expect(
      await screen.findByText(messages.assessment.noInstruments),
    ).toBeInTheDocument();
  });

  it("surfaces an error alert when the list fails to load", async () => {
    listInstruments.mockRejectedValue(new Error("boom"));

    renderList();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      messages.assessment.loadInstrumentsError,
    );
  });
});
