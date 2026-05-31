#!/usr/bin/env node
// WeUp Career — native validation report generator.
//
// Aggregates the machine-readable artifacts produced by the native validation
// suites into a single self-contained report/<run-id>/index.html. Pure Node
// (no deps); every input is OPTIONAL — a missing artifact renders as a
// "not run" section rather than crashing, so the report is useful even from a
// partial run.
//
// Inputs (all under report/<run-id>/):
//   meta.json                     run metadata (commit, branch, tool versions)
//   backend/junit.xml             pytest JUnit XML
//   backend/coverage.json         coverage.py JSON (totals.percent_covered*)
//   frontend/vitest.json          vitest --reporter=json
//   frontend/coverage-summary.json  vitest v8 json-summary (total.*)
//   e2e/playwright.json           playwright --reporter=json
//   security/summary.json         scripts/security-scan-native.sh summary
//
// Usage:  node scripts/generate-report.mjs [RUN_ID]
//   RUN_ID defaults to the most recent directory under report/.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REPORT_ROOT = path.join(REPO, "report");

function latestRunId() {
  if (!fs.existsSync(REPORT_ROOT)) return null;
  const dirs = fs
    .readdirSync(REPORT_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
  return dirs.length ? dirs[dirs.length - 1] : null;
}

const RUN_ID = process.argv[2] || latestRunId();
if (!RUN_ID) {
  console.error("[generate-report] no run-id given and report/ is empty.");
  process.exit(1);
}
const RUN_DIR = path.join(REPORT_ROOT, RUN_ID);
fs.mkdirSync(RUN_DIR, { recursive: true });

const readJson = (rel) => {
  try {
    return JSON.parse(fs.readFileSync(path.join(RUN_DIR, rel), "utf8"));
  } catch {
    return null;
  }
};
const readText = (rel) => {
  try {
    return fs.readFileSync(path.join(RUN_DIR, rel), "utf8");
  } catch {
    return null;
  }
};

// --- HTML escaping --------------------------------------------------------
const esc = (s) =>
  String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

// --- parse JUnit XML (pytest) without an XML dep --------------------------
function parseJUnit(xml) {
  if (!xml) return null;
  // Aggregate across <testsuite> elements (pytest emits one suite).
  const suites = [...xml.matchAll(/<testsuite\b[^>]*>/g)].map((m) => m[0]);
  const num = (attr, s) => {
    const r = new RegExp(`${attr}="([0-9.]+)"`).exec(s);
    return r ? Number(r[1]) : 0;
  };
  let tests = 0,
    failures = 0,
    errors = 0,
    skipped = 0,
    time = 0;
  for (const s of suites) {
    tests += num("tests", s);
    failures += num("failures", s);
    errors += num("errors", s);
    skipped += num("skipped", s);
    time += num("time", s);
  }
  if (!suites.length) return null;
  // Collect failing testcase names for the detail table.
  const fails = [];
  const caseRe = /<testcase\b([^>]*)>([\s\S]*?)<\/testcase>/g;
  let m;
  while ((m = caseRe.exec(xml))) {
    if (/<(failure|error)\b/.test(m[2])) {
      const name = /name="([^"]*)"/.exec(m[1])?.[1] ?? "?";
      const cls = /classname="([^"]*)"/.exec(m[1])?.[1] ?? "";
      const msg = /message="([^"]*)"/.exec(m[2])?.[1] ?? "";
      fails.push({ name: `${cls}::${name}`, msg });
    }
  }
  const passed = tests - failures - errors - skipped;
  return { tests, passed, failures, errors, skipped, time, fails };
}

// --- parse vitest json ----------------------------------------------------
function parseVitest(j) {
  if (!j) return null;
  const tests = j.numTotalTests ?? 0;
  const passed = j.numPassedTests ?? 0;
  const failed = j.numFailedTests ?? 0;
  const pending = j.numPendingTests ?? 0;
  const files = j.numTotalTestSuites ?? (j.testResults?.length ?? 0);
  const fails = [];
  for (const tr of j.testResults ?? []) {
    for (const a of tr.assertionResults ?? []) {
      if (a.status === "failed")
        fails.push({
          name: `${a.ancestorTitles?.join(" › ") ?? ""} › ${a.title}`,
          msg: (a.failureMessages ?? []).join("\n").slice(0, 300),
        });
    }
  }
  const durationMs =
    (j.testResults ?? []).reduce(
      (acc, tr) => acc + ((tr.endTime ?? 0) - (tr.startTime ?? 0)),
      0,
    ) || null;
  return { files, tests, passed, failed, pending, fails, durationMs };
}

// --- parse playwright json ------------------------------------------------
function parsePlaywright(j) {
  if (!j) return null;
  let passed = 0,
    failed = 0,
    skipped = 0,
    flaky = 0;
  const fails = [];
  const walk = (suite, trail) => {
    for (const sp of suite.specs ?? []) {
      for (const t of sp.tests ?? []) {
        const status = t.status ?? t.results?.[t.results.length - 1]?.status;
        const outcome = t.results?.[t.results.length - 1]?.status;
        if (status === "skipped" || outcome === "skipped") skipped++;
        else if (status === "flaky") flaky++;
        else if (outcome === "passed" || status === "expected") passed++;
        else {
          failed++;
          fails.push({ name: `${trail} › ${sp.title}`, msg: outcome ?? "failed" });
        }
      }
    }
    for (const child of suite.suites ?? [])
      walk(child, `${trail}${trail ? " › " : ""}${child.title ?? ""}`);
  };
  for (const s of j.suites ?? []) walk(s, s.title ?? "");
  const stats = j.stats ?? {};
  return {
    passed,
    failed,
    skipped,
    flaky,
    fails,
    durationMs: stats.duration ?? null,
  };
}

// --- gather ---------------------------------------------------------------
const meta = readJson("meta.json") ?? {};
const backend = parseJUnit(readText("backend/junit.xml"));
const backendCov = readJson("backend/coverage.json");
const vitest = parseVitest(readJson("frontend/vitest.json"));
const frontendCov = readJson("frontend/coverage-summary.json");
const e2e = parsePlaywright(readJson("e2e/playwright.json"));
const security = readJson("security/summary.json");
const storybook = readJson("storybook/summary.json");
const tla = readJson("tla/summary.json");
const gateB = readJson("tla/gate-b/gate-b-summary.json");
const pentest = readJson("security/pentest/findings-adjudicated.json");

// --- render helpers -------------------------------------------------------
const pct = (n) => (n == null ? "—" : `${Number(n).toFixed(1)}%`);
const ms = (n) => (n == null ? "—" : `${(n / 1000).toFixed(1)}s`);
const badge = (ok, label) =>
  `<span class="badge ${ok ? "ok" : "bad"}">${esc(label)}</span>`;
const naBadge = `<span class="badge na">not run</span>`;

function statCard(title, body, statusOk) {
  const cls = statusOk == null ? "" : statusOk ? "card-ok" : "card-bad";
  return `<section class="card ${cls}"><h2>${esc(title)}</h2>${body}</section>`;
}

function failTable(fails) {
  if (!fails || !fails.length) return "";
  const rows = fails
    .slice(0, 50)
    .map(
      (f) =>
        `<tr><td class="mono">${esc(f.name)}</td><td class="mono small">${esc(
          f.msg,
        )}</td></tr>`,
    )
    .join("");
  return `<details><summary>${fails.length} failure(s)</summary><table class="tbl"><thead><tr><th>Test</th><th>Detail</th></tr></thead><tbody>${rows}</tbody></table></details>`;
}

// Backend section
let backendBody;
let backendOk = null;
if (backend) {
  backendOk = backend.failures === 0 && backend.errors === 0;
  const cov =
    backendCov?.totals?.percent_covered ??
    backendCov?.totals?.percent_covered_display ??
    null;
  const branchCov = backendCov?.totals?.percent_covered_branches ?? null;
  backendBody = `
    <div class="metrics">
      <div><b>${backend.passed}</b><span>passed</span></div>
      <div class="${backend.failures ? "bad" : ""}"><b>${backend.failures}</b><span>failed</span></div>
      <div class="${backend.errors ? "bad" : ""}"><b>${backend.errors}</b><span>errors</span></div>
      <div><b>${backend.skipped}</b><span>skipped</span></div>
      <div><b>${pct(cov)}</b><span>line cov</span></div>
      <div><b>${ms(backend.time * 1000)}</b><span>duration</span></div>
    </div>${failTable(backend.fails)}`;
} else backendBody = naBadge;

// Frontend section
let frontendBody;
let frontendOk = null;
if (vitest) {
  frontendOk = vitest.failed === 0;
  const c = frontendCov?.total ?? {};
  frontendBody = `
    <div class="metrics">
      <div><b>${vitest.passed}</b><span>passed</span></div>
      <div class="${vitest.failed ? "bad" : ""}"><b>${vitest.failed}</b><span>failed</span></div>
      <div><b>${vitest.pending}</b><span>pending</span></div>
      <div><b>${vitest.files}</b><span>files</span></div>
      <div><b>${pct(c.lines?.pct)}</b><span>line cov</span></div>
      <div><b>${pct(c.branches?.pct)}</b><span>branch cov</span></div>
      <div><b>${ms(vitest.durationMs)}</b><span>duration</span></div>
    </div>${failTable(vitest.fails)}`;
} else frontendBody = naBadge;

// E2E section
let e2eBody;
let e2eOk = null;
if (e2e) {
  e2eOk = e2e.failed === 0;
  e2eBody = `
    <div class="metrics">
      <div><b>${e2e.passed}</b><span>passed</span></div>
      <div class="${e2e.failed ? "bad" : ""}"><b>${e2e.failed}</b><span>failed</span></div>
      <div class="${e2e.flaky ? "warn" : ""}"><b>${e2e.flaky}</b><span>flaky</span></div>
      <div><b>${e2e.skipped}</b><span>skipped</span></div>
      <div><b>${ms(e2e.durationMs)}</b><span>duration</span></div>
    </div>${failTable(e2e.fails)}`;
} else e2eBody = naBadge;

// Security section
let secBody;
let secOk = null;
if (security) {
  secOk = security.status === "pass";
  const g = security.gates ?? {};
  const gate = (label, val, bad) =>
    `<tr><td>${esc(label)}</td><td class="mono">${val}</td><td>${
      bad ? badge(false, "fail") : badge(true, "ok")
    }</td></tr>`;
  secBody = `
    <p>Overall: ${secOk ? badge(true, "PASS") : badge(false, "FAIL")}</p>
    <table class="tbl"><thead><tr><th>Gate</th><th>Count</th><th></th></tr></thead><tbody>
      ${gate("gitleaks secrets", g.gitleaks_findings ?? 0, (g.gitleaks_findings ?? 0) > 0)}
      ${gate("bandit HIGH", g.bandit_high ?? 0, (g.bandit_high ?? 0) > 0)}
      ${gate("pip-audit fixable", g.pip_audit_fixable ?? 0, (g.pip_audit_fixable ?? 0) > 0)}
      ${gate("npm HIGH", g.npm_high ?? 0, (g.npm_high ?? 0) > 0)}
      ${gate("npm CRITICAL", g.npm_critical ?? 0, (g.npm_critical ?? 0) > 0)}
    </tbody></table>`;
} else secBody = naBadge;

// Storybook section (build-storybook gate + Chromatic visual regression).
// build-storybook runs natively; Chromatic visual diff runs in CI only — it
// needs the external CHROMATIC_PROJECT_TOKEN (see docs/testing/chromatic.md).
// When the summary carries a `chromatic` block (populated from the CI run),
// R8 is judged on it; otherwise it renders as CI-gated / not run natively.
let sbBody;
let sbOk = null;
if (storybook) {
  const buildOk = storybook.status === "pass";
  const chromatic = storybook.chromatic ?? null;
  const chromaticOk = chromatic ? chromatic.status === "pass" : null;
  // R8 PASS requires the native build green AND, when Chromatic ran, its verdict pass.
  sbOk = chromaticOk == null ? buildOk : buildOk && chromaticOk;
  const chromaticRow = chromatic
    ? `<div><b>${chromaticOk ? "PASS" : "FAIL"}</b><span>chromatic (CI)</span></div>
      <div><b>${chromatic.stories ?? "—"}</b><span>published</span></div>`
    : "";
  const chromaticNote = chromatic
    ? `<p class="note">Chromatic visual regression ran in GitHub CI
       (<span class="mono">chromaui/action@v17</span>): published
       <b>${esc(chromatic.stories ?? "—")}</b> stories${
         chromatic.baseline
           ? " as the first <b>baseline</b> (no pixel-diff until the next PR with drift)"
           : ""
       }${
         chromatic.ci_run ? `; ${esc(chromatic.ci_run)}` : ""
       }. Not runnable natively (token masked + absent in the native shell).</p>`
    : `<p class="note">Visual regression (Chromatic) is CI-gated on the external
       <span class="mono">CHROMATIC_PROJECT_TOKEN</span>; not run natively.</p>`;
  sbBody = `
    <div class="metrics">
      <div><b>${buildOk ? "PASS" : "FAIL"}</b><span>build-storybook</span></div>
      <div><b>${storybook.stories ?? "—"}</b><span>native stories</span></div>
      <div><b>${ms(storybook.duration_ms)}</b><span>duration</span></div>
      ${chromaticRow}
    </div>
    ${chromaticNote}`;
} else sbBody = naBadge;

// Formal verification section (Gate A model check + sabotage per module).
// "pass" requires every module's Gate A green AND its sabotage caught.
let tlaBody;
let tlaOk = null;
if (tla && tla.status === "skip") {
  tlaBody = `${naBadge}<p class="note">${esc(
    tla.reason ?? "TLA+/TLC not run",
  )}. See <span class="mono">tla/</span> and <span class="mono">/formal-verify</span>.</p>`;
} else if (tla && Array.isArray(tla.modules) && tla.modules.length) {
  tlaOk = tla.status === "pass";
  const rows = tla.modules
    .map(
      (m) =>
        `<tr><td class="mono">${esc(m.module)}</td><td class="mono small">${esc(
          (m.cp ?? []).join(", "),
        )}</td><td>${badge(m.gate_a === "pass", m.gate_a === "pass" ? "pass" : "fail")}</td><td class="mono">${
          m.distinct_states ?? "—"
        }</td><td class="mono">${m.depth ?? "—"}</td><td>${badge(
          m.sabotage === "caught",
          m.sabotage === "caught" ? "caught" : "missed",
        )}</td></tr>`,
    )
    .join("");
  const caught = tla.modules.filter((m) => m.sabotage === "caught").length;
  const gateA = tla.modules.filter((m) => m.gate_a === "pass").length;
  tlaBody = `
    <div class="metrics">
      <div><b>${gateA}/${tla.modules.length}</b><span>Gate A</span></div>
      <div><b>${caught}/${tla.modules.length}</b><span>sabotage caught</span></div>
    </div>
    <table class="tbl"><thead><tr><th>Module</th><th>CP</th><th>Gate A</th><th>States</th><th>Depth</th><th>Sabotage</th></tr></thead><tbody>${rows}</tbody></table>
    <p class="note">Gate A = TLC model check (spec correct). Sabotage = a broken
    impl predicate MUST trigger a violation (proves the invariant is load-bearing).</p>`;
} else tlaBody = naBadge;

// Formal verification — Gate B (conformance trace replay + sabotage drift).
// conform = TLC consumes the whole trace (Deadlock at l=Len+1); sabotage MUST
// stick early (l < Len+1) — that proves the spec rejects the drifted trace.
let gateBBody;
let gateBOk = null;
if (gateB && Array.isArray(gateB.modules) && gateB.modules.length) {
  gateBOk = gateB.status === "pass";
  const rows = gateB.modules
    .map((m) => {
      const c = m.conformance ?? {};
      const s = m.sabotage ?? {};
      return `<tr><td class="mono">${esc(m.module)}</td><td class="mono small">${esc(
        (m.cp ?? []).join(", "),
      )}</td><td>${badge(c.verdict === "conform", c.verdict ?? "—")}</td><td class="mono">${
        c.l_reached ?? "—"
      }/${c.expected_l ?? "—"}</td><td>${badge(
        s.verdict === "caught",
        s.verdict === "caught" ? "caught" : "missed",
      )}</td></tr>`;
    })
    .join("");
  gateBBody = `
    <div class="metrics">
      <div><b>${gateB.passed}/${gateB.total}</b><span>conformance pass</span></div>
    </div>
    <table class="tbl"><thead><tr><th>Module</th><th>CP</th><th>Conformance</th><th>l reached</th><th>Sabotage</th></tr></thead><tbody>${rows}</tbody></table>
    <p class="note">Gate B = trace replay against the impl. <b>l reached / expected</b>
    = whole trace consumed (Deadlock at <span class="mono">Len(trace)+1</span>).
    Sabotage replays a deliberately drifted trace — the spec MUST get stuck early
    (drift caught), proving conformance is load-bearing, not vacuous.</p>`;
} else gateBBody = naBadge;

// Pentest (adjudicated). R4 passes iff no UNMITIGATED High/Critical after
// evidence-based triage. Raw vs adjudicated severities shown side by side so
// the HIGH→LOW re-classification is transparent, not hidden.
let pentestBody;
let pentestOk = null;
if (pentest) {
  pentestOk =
    pentest.r4_verdict === "pass" &&
    (pentest.unmitigated_high_or_critical ?? 0) === 0;
  const raw = pentest.raw_summary ?? {};
  const adj = pentest.adjudicated_summary ?? {};
  const sevRow = (label, key) =>
    `<tr><td>${esc(label)}</td><td class="mono">${raw[key] ?? 0}</td><td class="mono">${
      adj[key] ?? 0
    }</td></tr>`;
  const reclass = (pentest.reclassified ?? [])
    .map(
      (r) =>
        `<tr><td class="mono">${esc(r.id)}</td><td class="mono">${esc(r.was)}→${esc(
          r.now,
        )}</td><td class="mono">${esc(r.tracked_as ?? "")}</td><td class="small">${esc(
          r.basis,
        )}</td></tr>`,
    )
    .join("");
  pentestBody = `
    <p>R4: ${pentestOk ? badge(true, "PASS") : badge(false, "FAIL")} —
      <span class="mono">${pentest.unmitigated_high_or_critical ?? 0}</span>
      unmitigated High/Critical · ${(pentest.controls_verified ?? []).length} controls verified</p>
    <table class="tbl"><thead><tr><th>Severity</th><th>Raw</th><th>Adjudicated</th></tr></thead><tbody>
      ${sevRow("Critical", "critical")}
      ${sevRow("High", "high")}
      ${sevRow("Medium", "medium")}
      ${sevRow("Low", "low")}
    </tbody></table>
    ${
      reclass
        ? `<details><summary>${
            (pentest.reclassified ?? []).length
          } adjudicated (HIGH→LOW, tracked not suppressed)</summary><table class="tbl"><thead><tr><th>ID</th><th>Sev</th><th>Tracked</th><th>Basis</th></tr></thead><tbody>${reclass}</tbody></table></details>`
        : ""
    }
    <p class="note">Re-classified findings are tracked hardening items (not
    suppressed); revisit dates recorded in <span class="mono">findings-adjudicated.json</span>.</p>`;
} else pentestBody = naBadge;

// Overall status: fail if any present section failed.
const sectionStatuses = [
  backendOk,
  frontendOk,
  e2eOk,
  secOk,
  sbOk,
  tlaOk,
  gateBOk,
  pentestOk,
].filter((s) => s !== null);
const overallOk = sectionStatuses.length
  ? sectionStatuses.every(Boolean)
  : null;

const generatedAt = new Date().toISOString();
const metaRows = Object.entries({
  "Run ID": RUN_ID,
  Commit: meta.commit ?? "—",
  Branch: meta.branch ?? "—",
  "Node": meta.node ?? process.version,
  "Python": meta.python ?? "—",
  Generated: generatedAt,
  Profile: meta.profile ?? "full-stack (native)",
})
  .map(([k, v]) => `<tr><td>${esc(k)}</td><td class="mono">${esc(v)}</td></tr>`)
  .join("");

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WeUp Career — validation report ${esc(RUN_ID)}</title>
<style>
  :root{--ok:#15803d;--bad:#b91c1c;--warn:#b45309;--bg:#0b0f17;--card:#141a24;--ink:#e6edf3;--mut:#8b97a7;--line:#243042}
  *{box-sizing:border-box}
  body{margin:0;font:14px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
  header{padding:24px 28px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:16px;flex-wrap:wrap}
  header h1{font-size:18px;margin:0}
  main{padding:20px 28px;display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));max-width:1400px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
  .card h2{font-size:14px;margin:0 0 12px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
  .card-ok{border-left:4px solid var(--ok)} .card-bad{border-left:4px solid var(--bad)}
  .span2{grid-column:1/-1}
  .metrics{display:flex;flex-wrap:wrap;gap:18px}
  .metrics>div{display:flex;flex-direction:column}
  .metrics b{font-size:22px;font-variant-numeric:tabular-nums}
  .metrics span{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
  .metrics .bad b{color:var(--bad)} .metrics .warn b{color:var(--warn)}
  .badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}
  .badge.ok{background:rgba(21,128,61,.18);color:#4ade80}
  .badge.bad{background:rgba(185,28,28,.18);color:#fca5a5}
  .badge.na{background:rgba(139,151,167,.15);color:var(--mut)}
  .tbl{width:100%;border-collapse:collapse;margin-top:8px}
  .tbl th,.tbl td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
  .tbl th{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
  .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
  .small{color:var(--mut);white-space:pre-wrap}
  details summary{cursor:pointer;color:var(--mut);margin-top:8px}
  .pill{font-size:13px;padding:4px 12px;border-radius:999px;font-weight:700}
  .pill.ok{background:var(--ok);color:#fff}.pill.bad{background:var(--bad);color:#fff}.pill.na{background:#374151;color:#fff}
  .note{color:var(--mut);font-size:12px;margin-top:6px}
</style></head>
<body>
<header>
  <h1>WeUp Career — Validation Report</h1>
  <span class="pill ${overallOk == null ? "na" : overallOk ? "ok" : "bad"}">${
    overallOk == null ? "PARTIAL" : overallOk ? "PASS" : "FAIL"
  }</span>
  <span class="mono" style="color:var(--mut)">${esc(RUN_ID)}</span>
</header>
<main>
  ${statCard("Run metadata", `<table class="tbl"><tbody>${metaRows}</tbody></table>`, null)}
  ${statCard("Backend tests (pytest)", backendBody, backendOk)}
  ${statCard("Frontend unit (vitest)", frontendBody, frontendOk)}
  ${statCard("E2E (playwright)", e2eBody, e2eOk)}
  ${statCard("Security matrix", secBody, secOk)}
  ${statCard("Storybook + Chromatic", sbBody, sbOk)}
  ${statCard("Formal verification (TLA+/TLC)", tlaBody, tlaOk)}
  ${statCard("Formal verification — Gate B (conformance)", gateBBody, gateBOk)}
  ${statCard("Pentest (adjudicated)", pentestBody, pentestOk)}
</main>
<footer style="padding:14px 28px;color:var(--mut);font-size:12px;border-top:1px solid var(--line)">
  Generated ${esc(generatedAt)} • native pipeline (no Docker/nginx) • artifacts in <span class="mono">report/${esc(RUN_ID)}/</span>
</footer>
</body></html>`;

const outPath = path.join(RUN_DIR, "index.html");
fs.writeFileSync(outPath, html);

// Machine-readable rollup alongside the HTML.
fs.writeFileSync(
  path.join(RUN_DIR, "report.json"),
  JSON.stringify(
    {
      run_id: RUN_ID,
      generated_at: generatedAt,
      overall: overallOk == null ? "partial" : overallOk ? "pass" : "fail",
      sections: {
        backend: backend && {
          passed: backend.passed,
          failures: backend.failures,
          errors: backend.errors,
        },
        frontend: vitest && { passed: vitest.passed, failed: vitest.failed },
        e2e: e2e && { passed: e2e.passed, failed: e2e.failed, flaky: e2e.flaky },
        security: security && { status: security.status, ...(security.gates ?? {}) },
        storybook: storybook && {
          status: storybook.status,
          stories: storybook.stories ?? null,
          chromatic: storybook.chromatic
            ? {
                status: storybook.chromatic.status,
                stories: storybook.chromatic.stories ?? null,
              }
            : null,
        },
        tla: tla && {
          status: tla.status,
          modules: Array.isArray(tla.modules) ? tla.modules.length : 0,
        },
        gate_b: gateB && {
          status: gateB.status,
          passed: gateB.passed ?? 0,
          total: gateB.total ?? 0,
        },
        pentest: pentest && {
          r4_verdict: pentest.r4_verdict,
          unmitigated_high_or_critical:
            pentest.unmitigated_high_or_critical ?? 0,
        },
      },
    },
    null,
    2,
  ),
);

console.log(`[generate-report] wrote ${path.relative(REPO, outPath)}`);
console.log(
  `[generate-report] overall=${overallOk == null ? "partial" : overallOk ? "pass" : "fail"}`,
);
