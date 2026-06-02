# Chiến lược Kiểm thử — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Mục tiêu coverage:** ≥95% dòng; **100% trên auth + consent + sensitive-data + recommendation** (spec.md NFR-19)
**Thay thế:** v1.0.0 (testing Todo app)

> Test là **đặc tả được làm cho chạy được**. Bộ test phải chứng minh các thuộc tính đúng đắn CP-1…CP-8 (spec.md §8) và **không bỏ qua bias testing** (NFR-12) — gate riêng cho công bằng AI.

---

## Triết lý
1. **Test hành vi, không test cách hiện thực.**
2. **Test là tài liệu** — test fail phải chỉ rõ bất biến nào vỡ (ưu tiên đặt tên theo CP).
3. **Không mock DB ở integration** — dùng SQLite in-memory; mock nói dối.
4. **Phản hồi nhanh** — unit <1s; integration <30s; E2E <3min.
5. **Coverage có ý nghĩa** — 95% với assertion thật; **100% trên các lớp pháp lý/nhạy cảm**.
6. **Bias testing là bắt buộc** — không có nó, gợi ý AI không được tin (≠ coverage).

---

## Kim tự tháp test
```
        ┌──────────────────┐
        │   E2E (Playwright)│  3–5% · luồng consent/trắc nghiệm/gợi ý
        ├──────────────────┤
        │ Integration (httpx│  25% · API + DB + consent gate + audit
        │   + SQLite)       │
        ├──────────────────┤
        │  Unit + Property  │  70% · logic; Hypothesis cho CP invariants
        └──────────────────┘
   ┌──────────────────────────────────┐
   │  TLA+/TLC (formal) · Bias tests   │  gate riêng, ngoài kim tự tháp
   └──────────────────────────────────┘
```

---

## Backend Testing

### Unit + Property (pytest + Hypothesis)
**Vị trí:** `backend/tests/unit/`

Test: service layer (mọi nhánh logic), repository (in-memory SQLite), auth (token/hash), **consent logic**, **field crypto**, **recommendation rationale guard**, Pydantic schema.

```python
class TestPasswordHashing:
    @given(password=st.text(min_size=8, max_size=128))
    @settings(max_examples=500)
    def test_hash_verify_roundtrip(self, password: str):
        h = hash_password(password)
        assert verify_password(password, h) is True

class TestTokenGeneration:
    def test_access_token_claims(self):
        claims = decode_token(create_access_token(subject="usr_123", email="a@b.com"))
        assert claims["sub"] == "usr_123"
        assert claims["iss"] == "weup-api"
        assert "jti" in claims and claims["exp"] > claims["iat"]
```

**Property-based tests cho CP invariants (Hypothesis):**
- **CP-1:** với chuỗi thao tác ngẫu nhiên trên user <16, không `AssessmentResult`/`Recommendation` nào được tạo khi consent ≠ active.
- **CP-6:** không thể tạo `Recommendation` với `rationale` rỗng (mọi input).
- **CP-7:** hash/verify token roundtrip; token revoked luôn bị từ chối.
- **CP-8:** với chuỗi `advance_depth` ngẫu nhiên, `depth_achieved` không bao giờ giảm.
- Field crypto: encrypt→decrypt roundtrip cho payload bất kỳ.
- Pydantic fuzz cho input nghề/nội dung; SQL-injection attempts (không crash, sanitized).

### Integration (pytest + httpx + SQLite in-memory)
**Vị trí:** `backend/tests/integration/`

```python
@pytest.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as s: yield s
    await engine.dispose()
```

**Consent gate (CP-1/CP-2 — 100% nhánh):**
```python
class TestConsentGate:
    async def test_under16_blocked_without_consent(self, client, child_token):
        r = await client.post("/api/v1/assessments/riasec/submit",
                              json=SAMPLE, headers=auth(child_token))
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"

    async def test_under16_allowed_after_consent(self, client, child_token, active_consent):
        r = await client.post("/api/v1/assessments/riasec/submit",
                              json=SAMPLE, headers=auth(child_token))
        assert r.status_code == 201

    async def test_revoke_blocks_new_processing(self, client, child_token, active_consent):
        await revoke(active_consent)
        r = await client.post("/api/v1/assessments/riasec/submit",
                              json=SAMPLE, headers=auth(child_token))
        assert r.status_code == 403   # CP-2
```

**Dữ liệu nhạy cảm + audit (CP-3 — 100%):**
```python
class TestSensitiveAccessAudit:
    async def test_every_result_read_writes_one_audit(self, client, user_token, a_result, audit_repo):
        before = await audit_repo.count_sensitive()
        await client.get(f"/api/v1/me/assessments/{a_result.id}", headers=auth(user_token))
        after = await audit_repo.count_sensitive()
        assert after == before + 1            # CP-3
    async def test_result_payload_encrypted_at_rest(self, db, a_result):
        raw = await db.execute(text("SELECT result_payload FROM assessment_result WHERE id=:i"),
                               {"i": a_result.id})
        assert b"realistic" not in raw.scalar()   # không lưu plaintext
```

**RBAC quan hệ (CP-4 — 100%):**
```python
class TestRelationalRBAC:
    async def test_user_cannot_read_others_result(self, client, u1_token, u2_result):
        r = await client.get(f"/api/v1/me/assessments/{u2_result.id}", headers=auth(u1_token))
        assert r.status_code == 404          # không xác nhận tồn tại
    async def test_counselor_cannot_access_other_school_student(self, client, counselor_token, other_school_student):
        r = await client.get(f"/api/v1/school/{OTHER}/students", headers=auth(counselor_token))
        assert r.status_code == 403
    async def test_guardian_only_sees_linked_child(self, client, guardian_token, unlinked_child):
        r = await client.get(f"/api/v1/users/{unlinked_child.id}/progress", headers=auth(guardian_token))
        assert r.status_code in (403, 404)
```

**Gợi ý human-in-the-loop (CP-5/CP-6 — 100%):**
```python
class TestRecommendationGovernance:
    async def test_recommendation_always_has_rationale(self, client, user_token):
        r = await client.post("/api/v1/recommendations", headers=auth(user_token))
        assert r.json()["rationale"]            # CP-6
        assert r.json()["requires_human_confirmation"] is True
    async def test_pathway_not_applied_without_human_confirm(self, client, user_token, proposed_reco):
        # không có endpoint nào tự áp dụng khi chưa confirm
        applied = await get_pathway_state(proposed_reco.user_id)
        assert applied is None                  # CP-5
```

**Coverage integration:** happy path 100%; mọi nhánh 4xx 100%; mọi nhánh consent/ownership/relation 100%; mọi nhánh chuyển trạng thái reco 100%.

---

## Frontend Testing (Vitest + RTL + MSW)
**Vị trí:** `frontend/src/**/*.test.tsx`

Test: hooks (`useAuth`, `useConsent`, `useAssessment`, `useRecommendation`), Zod schema, component states (loading/error/empty/populated), và **các trạng thái cổng consent**.

```typescript
describe('GuardianGate', () => {
  it('chặn vào assessment khi pending_guardian_consent', () => {
    renderWithProviders(<App />, { account_status: 'pending_guardian_consent' })
    expect(screen.getByText(/cần đồng ý của người giám hộ/i)).toBeInTheDocument()
  })
})
describe('RecommendationCard', () => {
  it('luôn hiển thị lý do và nút xác nhận, không tự áp dụng', () => {
    renderWithProviders(<RecommendationCard reco={mockReco} />)
    expect(screen.getByText(mockReco.rationale)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /chấp nhận|từ chối/i })).toBeInTheDocument()
  })
})
describe('AssessmentResultView', () => {
  it('không kết luận cứng một nghề; hiển thị giải thích', () => {
    renderWithProviders(<AssessmentResultView result={mockRiasec} />)
    expect(screen.queryByText(/bạn phải làm nghề/i)).not.toBeInTheDocument()
  })
})
```

---

## E2E Tests (Playwright — Chromium + Firefox + WebKit)
**Vị trí:** `e2e/`

```gherkin
Feature: Xác thực & Đăng ký
  Scenario: Người ≥16 đăng ký và vào dashboard
  Scenario: Người <16 đăng ký → chuyển sang luồng mời giám hộ
  Scenario: Refresh token gia hạn phiên im lặng

Feature: Đồng ý giám hộ (<16)
  Scenario: Giám hộ xác nhận → mở khóa trắc nghiệm
  Scenario: Trẻ <16 chưa consent bị chặn làm trắc nghiệm (403)
  Scenario: Giám hộ thu hồi → trẻ bị chặn xử lý dữ liệu mới

Feature: Trắc nghiệm định hướng
  Scenario: Học sinh làm RIASEC và xem kết quả kèm giải thích
  Scenario: Học sinh xuất/xóa kết quả của mình

Feature: Gợi ý nghề (human-in-the-loop)
  Scenario: Gợi ý hiển thị kèm lý do; người dùng phải xác nhận
  Scenario: Hệ thống không tự áp dụng phân luồng

Feature: Tư vấn học đường (counselor)
  Scenario: Counselor chỉ thấy học sinh trong trường mình
```

```typescript
// playwright.config.ts (trích)
export default defineConfig({
  testDir: './e2e',
  use: { baseURL: 'http://localhost:80', trace: 'on-first-retry',
         screenshot: 'only-on-failure', video: 'retain-on-failure' },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit',   use: { ...devices['Desktop Safari'] } },
    { name: 'mobile',   use: { ...devices['iPhone 13'] } },
  ],
})
```

---

## Security Tests
| Test | Công cụ | Ngưỡng |
|------|---------|--------|
| SAST | Semgrep (`p/python`,`p/react`,`p/security`) | 0 finding |
| Container CVE | Trivy | 0 HIGH/CRITICAL |
| Dependency audit | pip-audit + npm audit | 0 HIGH+ |
| DAST baseline | OWASP ZAP | 0 HIGH |
| Security headers | đánh giá A+ | A+ |
| **Sensitive-data leak** | test riêng: không log/serialize kết quả nhạy cảm | 0 |
| **Consent bypass** | test mọi route dữ liệu hướng nghiệp đều qua Consent Guard | 0 đường vòng |

---

## ⭐ Bias Testing (NFR-12, Luật 134/2025 Đ.4) — gate riêng

> Khung đầy đủ (metric M1–M5, ngưỡng, sinh dữ liệu, cấu trúc test, cổng CI): [`bias-testing.md`](./bias-testing.md).

Không phải coverage; là kiểm thử **công bằng** của bộ trắc nghiệm & thuật toán gợi ý.

- **Phân nhóm:** giới tính, vùng miền, hoàn cảnh KT-XH, học lực.
- **Chỉ số:** so sánh phân phối gợi ý nghề/phân luồng giữa các nhóm với hồ sơ tương đương; phát hiện chênh lệch có hệ thống (vd: cùng RIASEC nhưng nữ ít được gợi ý nghề kỹ thuật hơn nam).
- **Ngưỡng:** chênh lệch vượt ngưỡng đã định ⇒ **fail CI**, phải tài liệu hóa & hiệu chỉnh.
- **Bất biến cứng:** RIASEC/MBTI **không khóa cứng** lựa chọn theo định kiến giới/vùng.
- Đầu ra: báo cáo bias đính kèm mỗi release (Gate C).

---

## Load/Performance (k6)
```javascript
export const options = {
  scenarios: {
    steady: { executor: 'constant-vus', vus: 200, duration: '5m' },
    spike:  { executor: 'ramping-vus', stages: [
      { duration:'30s', target:0 }, { duration:'30s', target:400 },
      { duration:'1m', target:400 }, { duration:'30s', target:0 } ] },
  },
  thresholds: {
    'http_req_duration{op:read}':  ['p(99)<150'],
    'http_req_duration{op:write}': ['p(99)<300'],
    http_req_failed: ['rate<0.01'],
  },
}
```
> Chú ý tải riêng cho endpoint **trắc nghiệm** & **gợi ý** (tốn tính toán hơn CRUD).

---

## Coverage Configuration

### Backend (pytest-cov)
```toml
[tool.coverage.run]
source = ["app"]; branch = true
omit = ["*/tests/*","*/migrations/*","app/main.py"]
[tool.coverage.report]
fail_under = 95
```
**100% line+branch bắt buộc (lớp tới hạn NFR-19) — enforce bằng CI gate riêng:** toàn package `app/auth/*`, `app/guardians/*`, `app/assessments/*`, `app/reco/*` + `app/core/{consent,crypto,security,audit,authz,ratelimit}.py`. Gate này độc lập với cổng toàn cục 95% và **chặn merge** nếu bất kỳ dòng/nhánh nào trong tập trên hở. Cơ chế + lý do phạm vi: xem [coverage-critical-layers-n2.md](./coverage-critical-layers-n2.md).

### Frontend (Vitest)
```typescript
coverage: { provider: 'v8', thresholds: { lines: 95, branches: 90, functions: 95 },
  exclude: ['src/main.tsx','src/mocks/**','**/*.stories.tsx'] }
```

---

## CI Quality Gate Summary
```yaml
backend_coverage:  >= 95%   # cổng toàn cục
backend_critical_coverage: == 100%  # gate riêng: auth/consent/sensitive/reco + authz/ratelimit (coverage-critical-layers-n2.md)
frontend_coverage: >= 95%
type_errors: 0              # mypy --strict && tsc --noEmit
lint_errors: 0
e2e_failures: 0            # playwright × 3 browsers (gồm luồng consent/reco)
security_findings: 0      # trivy + semgrep + zap + sensitive-leak + consent-bypass
bias_test: pass           # công bằng giới/vùng/hoàn cảnh (NFR-12)
tla_invariants: all_pass  # TLC: CP-1..CP-8
```
