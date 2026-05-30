import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./lib/i18n/request.ts");

const nextConfig: NextConfig = {
  // Node-runtime standalone output for the multi-stage Dockerfile (ADR-006):
  // public RSC routes need a Node server, not a static export.
  output: "standalone",
  reactStrictMode: true,
  // Public career/content pages are anonymous RSC reads; the backend base URL
  // is server-only (BACKEND_INTERNAL_URL) and never shipped to the client.
  poweredByHeader: false,
};

export default withNextIntl(nextConfig);
