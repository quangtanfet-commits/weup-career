import { describe, it, expect, afterEach } from "vitest";

import {
  API_BASE_PATH,
  backendInternalUrl,
  publicApiBaseUrl,
} from "@/lib/api/config";
import { isLocale, defaultLocale } from "@/lib/i18n/config";
import { makeQueryClient } from "@/lib/query/client";

describe("api config", () => {
  afterEach(() => {
    delete process.env.BACKEND_INTERNAL_URL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  it("exposes the versioned base path", () => {
    expect(API_BASE_PATH).toBe("/api/v1");
  });

  it("falls back to localhost when env is unset", () => {
    expect(backendInternalUrl()).toBe("http://localhost:8000");
    expect(publicApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("strips trailing slashes from configured URLs", () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:8000//";
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.weup.vn/";
    expect(backendInternalUrl()).toBe("http://backend:8000");
    expect(publicApiBaseUrl()).toBe("https://api.weup.vn");
  });
});

describe("i18n config", () => {
  it("defaults to Vietnamese", () => {
    expect(defaultLocale).toBe("vi");
  });

  it("recognises supported locales only", () => {
    expect(isLocale("vi")).toBe(true);
    expect(isLocale("en")).toBe(false);
  });
});

describe("query client", () => {
  it("builds a client that disables refetch-on-focus and bounds retries", () => {
    const client = makeQueryClient();
    const defaults = client.getDefaultOptions().queries;
    expect(defaults?.refetchOnWindowFocus).toBe(false);
    expect(defaults?.retry).toBe(1);
    expect(defaults?.staleTime).toBe(60_000);
  });
});
