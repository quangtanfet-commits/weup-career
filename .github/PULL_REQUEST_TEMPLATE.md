## Summary

<!-- One-paragraph description of what this PR changes and why. -->

## Type of Change

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `refactor` — code change that neither fixes a bug nor adds a feature
- [ ] `test` — adding missing tests or correcting existing tests
- [ ] `docs` — documentation only changes
- [ ] `chore` — maintenance (deps, CI config, tooling)
- [ ] `security` — security fix

## Related Issues

<!-- Closes #123 -->

---

## Checklist

### Code Quality
- [ ] Tests written / updated (TDD — tests first)
- [ ] Coverage remains ≥95% (auth + data-access = 100%)
- [ ] `mypy --strict` passes with zero errors
- [ ] `tsc --noEmit` passes with zero errors
- [ ] No `any` added to TypeScript without a tracked comment
- [ ] `ruff` + `eslint --max-warnings 0` clean

### Security
- [ ] No secrets, tokens, or PII added to code or logs
- [ ] IDOR checks present on all new resource endpoints
- [ ] Rate limiting considered for new public endpoints
- [ ] No new `eval()`, `exec()`, or unsafe deserialization
- [ ] Dependency changes audited (`pip-audit` / `npm audit`)

### Architecture
- [ ] Follows hexagonal architecture (services don't import router; repos don't import services)
- [ ] New DB columns have a migration (`alembic revision --autogenerate`)
- [ ] API changes are backward-compatible (or version bump documented)
- [ ] OpenAPI schema updated (auto if FastAPI types updated)

### Formal Verification (if state machine changed)
- [ ] TLA+ spec updated in `tla/`
- [ ] TLC model check passes locally

### Documentation
- [ ] ADR written (if architectural decision made)
- [ ] Runbook updated (if operational procedure changed)
- [ ] `CHANGELOG.md` entry added

---

## Testing Evidence

<!-- Paste relevant test output or coverage report snippet -->

```
pytest: X passed, 0 failed — coverage: XX%
```

## Screenshots / Demo (if UI change)

<!-- Add before/after screenshots or a screen recording link -->
