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
  // E2E-only same-origin API proxy. In production nginx serves /api from the
  // backend (same origin), so the browser never makes a cross-origin call. The
  // native e2e harness runs the prod build on its own port (:3100) against the
  // host backend (:8000); without this proxy the browser fetch is cross-origin
  // and the backend CORS allowlist (dev origin only) blocks it. Gated on
  // E2E_PROXY_API so dev (`next dev`) and the real prod image are unaffected.
  async rewrites() {
    if (process.env.E2E_PROXY_API !== "1") return [];
    const backend = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
    return [{ source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` }];
  },
};

export default withNextIntl(nextConfig);
