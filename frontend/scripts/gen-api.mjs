#!/usr/bin/env node
/**
 * Regenerate `lib/api/schema.ts` from the backend OpenAPI 3.1 schema.
 *
 * Source of truth: the backend exporter `python -m app.openapi_export`
 * (hermetic — placeholder secrets, no DB). This script runs the exporter via
 * `uv` from `../backend`, writes `openapi.json`, then runs `openapi-typescript`.
 *
 * CI uses this as the drift gate (NFR-20 / BE-2): regenerate, then `git diff`
 * must be empty.
 *
 * Falls back to a running backend at $OPENAPI_URL if the exporter is not
 * available (e.g. CI without Python).
 */
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const backendDir = resolve(frontendRoot, "..", "backend");
const openapiJson = resolve(frontendRoot, "openapi.json");
const out = resolve(frontendRoot, "lib", "api", "schema.ts");

function run(cmd, args, opts = {}) {
  execFileSync(cmd, args, { stdio: "inherit", ...opts });
}

const url = process.env.OPENAPI_URL;
if (url) {
  console.log(`[gen:api] generating from ${url}`);
  run("npx", ["openapi-typescript", url, "-o", out]);
} else if (existsSync(backendDir)) {
  console.log("[gen:api] exporting OpenAPI from backend (uv)…");
  run("uv", ["run", "python", "-m", "app.openapi_export", openapiJson], {
    cwd: backendDir,
  });
  run("npx", ["openapi-typescript", openapiJson, "-o", out]);
} else {
  console.error(
    "[gen:api] no OPENAPI_URL and no ../backend; cannot generate schema",
  );
  process.exit(1);
}
console.log(`[gen:api] wrote ${out}`);
