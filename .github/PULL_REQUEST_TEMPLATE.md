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
- [ ] Coverage remains ≥95% (auth + consent + sensitive-data + recommendation = 100%)
- [ ] `mypy --strict` passes with zero errors
- [ ] `tsc --noEmit` passes with zero errors
- [ ] No `any` added to TypeScript without a tracked comment
- [ ] `ruff` + `eslint --max-warnings 0` clean

### Security & Tuân thủ
- [ ] No secrets, tokens, or PII (gồm kết quả trắc nghiệm) added to code or logs
- [ ] IDOR + RBAC quan hệ (guardian↔child, counselor↔student) present on new resource endpoints
- [ ] Route xử lý dữ liệu hướng nghiệp đi qua Consent Guard (<16) — CP-1
- [ ] Đọc dữ liệu nhạy cảm sinh audit (CP-3); dữ liệu nhạy cảm mã hóa, không log/cache
- [ ] Gợi ý mới có rationale + human-in-the-loop (CP-5/CP-6); cân nhắc bias test (NFR-12)
- [ ] Rate limiting considered; no new `eval()`/`exec()`/unsafe deserialization
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
