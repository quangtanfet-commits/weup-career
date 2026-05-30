import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";

import { Providers } from "./providers";
import "@/styles/globals.css";

/**
 * Be Vietnam Pro — designed for Vietnamese diacritics (architecture.md §2.2).
 * Exposed as `--font-be-vietnam-pro`, consumed by the `--font-sans` token.
 */
const beVietnamPro = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-be-vietnam-pro",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "WeUp Career",
    template: "%s · WeUp Career",
  },
  description:
    "Nền tảng hướng nghiệp quốc gia cho học sinh THCS & THPT tại Việt Nam.",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} className={beVietnamPro.variable}>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
