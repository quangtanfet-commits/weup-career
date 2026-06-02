# CI E2E fix — mailer outbox crosses the host/container boundary (N-3)

**Status:** proposed · **Date:** 2026-06-02 · **Scope:** `.github/workflows/ci.yml` (`e2e` job) + `docker-compose.test.yml` (backend service) · **Doc-first:** no code changed by this doc

## Symptom

`main` has been **red on the CI Gate** since the N-3 email-verification work
landed (#70 → #71/#72). All three E2E matrix legs (chromium / firefox / webkit)
fail identically inside the `register → verify → login` fixtures:

```
Error: No verification email for <addr> in /tmp/weup-outbox.ndjson
  at readVerifyToken (tests/e2e/fixtures/auth.ts:111)
  at tests/e2e/fixtures/auth.ts:136   (waitForVerifyToken → toPass timeout)
```

The Dependabot action bumps (#64–#68) are **innocent** — `main` was already red
when they were opened; the bumps neither caused nor can fix this.

## Root cause — two processes, two filesystems, one unset env

Post-N-3 (`docs/frontend/email-verification-2026-06.md`) registration no longer
opens a session. To finish the flow the Playwright fixtures must recover the
mailed token from the backend's **FileMailer outbox** (an NDJSON file appended
on `/auth/register` and `/auth/resend-verification`).

The mailer is selected at `backend/app/api/deps.py:149`:

```python
def mailer(settings: Settings = Depends(settings_dep)) -> IMailer:
    if settings.is_production:
        return SmtpMailer()
    if settings.mailer_outbox_path:          # WEUP_MAILER_OUTBOX
        return FileMailer(settings.mailer_outbox_path)
    return ConsoleMailer()                    # ← CI lands here
```

In CI the backend runs with `ENVIRONMENT=test` and **`WEUP_MAILER_OUTBOX`
unset** (`docker-compose.test.yml` sets neither the env nor a shared volume), so
it selects `ConsoleMailer` — which only logs the verify URL and **writes no
outbox file**.

Even if the env were set, a second problem hides behind it: the backend runs
**inside the docker-compose container** while Playwright runs on the **host
runner**. A file the container writes to `/tmp/weup-outbox.ndjson` is not the
host's `/tmp/weup-outbox.ndjson` (the fixture default at
`frontend/tests/e2e/fixtures/auth.ts:42`). Two distinct filesystems, so the
reader sees `ENOENT` regardless.

So the fix must do **both**: make the backend write an outbox, and put that file
where the host reader can see it.

## Recommended fix — shared bind-mount + matching env on both sides

Keep the existing docker-compose topology (matrix × nginx :80). Bridge the
boundary with one bind-mounted directory and a path that resolves to the same
file on both sides.

**1. `docker-compose.test.yml` — backend service:** mount a host dir into the
container and point the backend at a file inside it.

```yaml
  backend:
    environment:
      # …existing SECRET_KEY / FIELD_ENCRYPTION_KEY / DATABASE_URL / ENVIRONMENT …
      WEUP_MAILER_OUTBOX: /shared/outbox.ndjson
    volumes:
      - ./.e2e-shared:/shared
```

**2. `.github/workflows/ci.yml` — `e2e` job:** create the shared dir writable by
the container user *before* `up`, and point the host-side Playwright step at the
same file via the host path.

```yaml
      - name: Build & start Docker stack for E2E
        env:
          SECRET_KEY: ci-e2e-test-secret-not-for-production
          FIELD_ENCRYPTION_KEY: ci-e2e-test-field-encryption-key-not-for-production
          ENVIRONMENT: test
        run: |
          mkdir -p .e2e-shared && chmod 777 .e2e-shared   # see permissions note
          docker compose -f docker-compose.yml -f docker-compose.test.yml up -d --build
          timeout 60 bash -c 'until curl -sf http://localhost/api/v1/ready; do sleep 2; done'

      - name: Run Playwright E2E
        working-directory: frontend
        env:
          BASE_URL: http://localhost
          WEUP_MAILER_OUTBOX: ${{ github.workspace }}/.e2e-shared/outbox.ndjson
        run: npx playwright test --project=${{ matrix.browser }} --reporter=html
```

The fixture already honors `WEUP_MAILER_OUTBOX` when set
(`fixtures/auth.ts:42`), so no test code changes.

### Permissions note (the subtle part)

The compose backend image runs as a non-root user. A host dir created by the
runner is owned by the runner UID; the container UID may not be able to create
`outbox.ndjson` inside it. Options, least-surprising first:

- `chmod 777 .e2e-shared` on the host before `up` — crude but adequate for an
  ephemeral CI dir that `down -v` and the runner teardown discard.
- A named volume instead of a bind mount does **not** help: the host Playwright
  step can't read a named volume's path directly.
- `FileMailer` already does `self._path.parent.mkdir(parents=True,
  exist_ok=True)`, so the `/shared` mount point existing is enough; the file
  itself is created on first send.

### Failure-artifact bonus

Add the outbox to the on-failure upload so a red leg ships the evidence:

```yaml
      - name: Upload test artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-${{ matrix.browser }}
          path: |
            frontend/playwright-report/
            frontend/test-results/
            .e2e-shared/outbox.ndjson
          retention-days: 7
```

## Alternative — migrate the CI e2e gate to the native harness

`docs/testing/e2e-native-mailer-outbox.md` already solved this exact outbox
problem for `scripts/run-validation-native.sh`: the harness owns an ephemeral
backend on `:8000` with a run-scoped `WEUP_MAILER_OUTBOX =
report/<run-id>/e2e/outbox.ndjson`, hermetic DB copy + `alembic upgrade head`,
rate limiting off, readiness poll, setsid PGID teardown. Because backend and
Playwright run in the **same** filesystem there, there is no host/container
boundary to bridge — the class of bug above cannot occur.

That doc explicitly deferred CI wiring: *"No CI workflow file is modified by
this change… CI wiring, if desired, is a separate doc-first change."* This is
that change's larger sibling: it would replace the docker-compose stack in the
`e2e` job with the native harness invocation.

**Trade-off.** The native harness drops nginx :80 and the prod-image build from
the e2e path — it exercises the app, not the deployed container topology. The
bind-mount fix keeps that topology. Recommendation: take the **bind-mount fix
now** (minimal, unblocks `main` and #67, preserves what the e2e gate currently
asserts); evaluate a native-harness migration separately if we want the e2e gate
to stop depending on docker-compose in CI.

## Acceptance

- [ ] All three E2E legs green on a PR carrying this change.
- [ ] `outbox.ndjson` present in the shared dir after a run (assert ≥1 line).
- [ ] No test code changed (fixtures already honor the env).
- [ ] Coverage / security gates untouched (no thresholds moved).
- [ ] Once `main` is green: merge #67 (dependency-review-action 4→5) as a merge commit.

## References

- Root cause: `backend/app/api/deps.py:149` (mailer selection),
  `backend/app/core/mailer.py` (`FileMailer` / `ConsoleMailer`),
  `backend/app/core/config.py:103` (`WEUP_MAILER_OUTBOX` alias).
- Reader: `frontend/tests/e2e/fixtures/auth.ts:42` (default path + env override),
  `:111` `readVerifyToken`, `:136` `waitForVerifyToken`.
- CI: `.github/workflows/ci.yml` `e2e` job (L424–485); compose:
  `docker-compose.test.yml` backend service.
- Native alternative: `docs/testing/e2e-native-mailer-outbox.md`.
- N-3 flow: `docs/frontend/email-verification-2026-06.md`.
