import { getRequestConfig } from "next-intl/server";

import { defaultLocale } from "./config";
import messages from "@/messages/vi.json";

/**
 * next-intl request config. F1 ships a single locale (`vi`) with no URL prefix,
 * so the locale is fixed here; adding more locales later means resolving it from
 * the request instead of hard-coding the default.
 */
export default getRequestConfig(async () => {
  return {
    locale: defaultLocale,
    messages,
  };
});
