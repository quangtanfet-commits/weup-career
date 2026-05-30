# E2E tests (Playwright)

This directory is the Playwright test root. It is **intentionally empty** in the
F1 foundation slice.

E2E scenarios are authored by the lead from the holdout scenario set
(`scenarios/` at the repo root). Build agents must not read that set, so they do
not write the E2E tests here — only the runnable Playwright config + browsers are
provided so those tests can be dropped in and run.
