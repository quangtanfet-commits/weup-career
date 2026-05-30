import type { ReactElement, ReactNode } from "react";
import { render, type RenderResult } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";

import messages from "@/messages/vi.json";
import { defaultLocale } from "@/lib/i18n/config";

/**
 * Render a client component with the real Vietnamese message catalog so tests
 * assert user-visible copy (mirrors the production `NextIntlClientProvider` in
 * the root layout). Keeps form/banner tests honest about i18n wiring.
 */
export function renderWithIntl(ui: ReactElement): RenderResult {
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <NextIntlClientProvider locale={defaultLocale} messages={messages}>
        {children}
      </NextIntlClientProvider>
    );
  }
  return render(ui, { wrapper: Wrapper });
}

export { messages as viMessages };
