# Dependabot Triage — 2026-06

**Status:** Design + actioned (this slice fixes #1, dismisses #2)
**Date:** 2026-06-02
**Owner:** Platform / Security
**Scope:** 4 open Dependabot alerts on `main` (2 high, 2 moderate) surfaced when pushing `chore/fe-wellbeing-react-query`.
**Related:** [ADR-007 CI/CD](../adr/ADR-007-cicd.md), [ADR-008 Security Controls](../adr/ADR-008-security-controls.md), [auth-design.md](./auth-design.md), [threat-model.md](./threat-model.md)

---

## 1. Nguyên tắc phân loại

Severity nhãn của Dependabot **không** quyết định ưu tiên — **khả năng khai thác thực tế (reachability)** mới quyết định. Mỗi alert được kiểm tra trong manifest thật + đường dẫn thực thi của ứng dụng, không xử lý theo nhãn đơn thuần.

| # | Gói | Sev | Manifest | Reachable? | Hành động |
|---|-----|-----|----------|------------|-----------|
| 1 | `tj-actions/changed-files@v44` | HIGH | `.github/workflows/ci.yml` | **Có** (CI supply-chain) | **Fix ngay** — pin SHA |
| 2 | `ecdsa` 0.19.2 | HIGH | `backend/uv.lock` | **Không** (HS256-only) | **Dismiss** + justification |
| 3 | `pytest` 8.4.2 | MED | `backend/uv.lock` | Thấp (dev/test-only) | Hoãn — bump major có rủi ro |
| 4 | `postcss` 8.4.31 (nested) | MED | `frontend/package-lock.json` | **Không** (build-time, CSS của chính ta) | Không cần — chờ Next |

Slice này chỉ thực hiện **#1** và **#2**. #3 + #4 ghi nhận ở §5.

---

## 2. #1 — `tj-actions/changed-files` (GHSA-mrrh-fwg8-r2c3)

### Bối cảnh
Đây là vụ **xâm phạm chuỗi cung ứng tháng 3/2025**: action bị cài backdoor để dump bộ nhớ runner — **gồm secrets** — vào build log. Cơ chế tấn công là **repoint các tag mutable** sang commit độc hại. Dùng `@v44` (tag mutable) chính là vector đó.

### Vị trí
`ci.yml:319` và `ci.yml:359` — gate hai job theo path đã đổi:
- `formal-verification` (TLA+ model check — CP-1…CP-8)
- `bias-test` (fairness — Luật 134/2025, NFR-12)

### Đánh giá phơi nhiễm
Cả hai job chạy trong Actions context của repo. Một phiên bản bị xâm phạm có thể lộ bất kỳ secret nào trong context. Đây là rủi ro CI supply-chain thực, độc lập với việc job có khai báo secret riêng hay không.

### Khắc phục — pin commit SHA (không chỉ bump tag)
GitHub Actions hardening khuyến nghị pin third-party action theo **full commit SHA**, không theo tag (tag có thể bị repoint). Bản an toàn mới nhất là **v47.0.6** (2026-04-18), lightweight tag trỏ thẳng tới commit:

```yaml
# trước
uses: tj-actions/changed-files@v44
# sau
uses: tj-actions/changed-files@9426d40962ed5378910ee2e21d5f8c6fcbf2dd96 # v47.0.6
```

Áp dụng cho **cả hai** dòng (319, 359).

### Phạm vi pin SHA
Chỉ pin `tj-actions/*` — đây là action **bên thứ ba** đã từng bị xâm phạm thực tế. Các `actions/*` (GitHub-owned), `docker/*`, `codecov/*`, `aquasecurity/*`, `chromaui/*` giữ nguyên tag major: rủi ro thấp hơn, và việc pin-SHA toàn bộ workflow là một đợt hardening riêng (không gộp vào slice an ninh khẩn này). Ghi nhận như follow-up tùy chọn ở §5.

---

## 3. #2 — `ecdsa` 0.19.2 (GHSA-wj6h-64fc-37mp)

### Lỗ hổng
Minerva — **timing attack trên đường cong P-256** trong `python-ecdsa`. Kẻ tấn công đo thời gian ký/giải để khôi phục private key ECDSA.

### Vì sao **không reachable**
- `ecdsa` được kéo **gián tiếp** qua `python-jose` 3.5.0 (`uv.lock:1006-1011`).
- Backend phát hành/verify JWT bằng **HS256** (`backend/app/core/config.py:52` → `jwt_algorithm = "HS256"`; `security.py:75,85`). HS256 là **HMAC đối xứng** — **không** dùng ECDSA, **không** chạm đường cong P-256.
- Không có module nào khác ký/verify ECDSA. ⇒ Đường dẫn lỗi **không bao giờ được thực thi**.

### Vì sao không "bump version"
`patched = null` — maintainer python-ecdsa **không coi side-channel là trong phạm vi** và sẽ không vá. Không có bản sửa để nâng lên.

### Hành động
**Dismiss** alert với lý do `tolerable_risk` / "vulnerable code not in execution path":
> Backend dùng HS256 (HMAC) cho mọi JWT; `ecdsa` chỉ là transitive qua python-jose và đường dẫn ECDSA P-256 không bao giờ được thực thi. Không có bản vá (maintainer loại side-channel khỏi phạm vi).

### Khắc phục triệt để (slice riêng, doc-first)
`python-jose` thực tế **không còn được bảo trì**. Di trú sang **PyJWT** loại bỏ hẳn transitive `ecdsa` (PyJWT không phụ thuộc nó), xóa alert tại gốc. Việc này **chạm crypto xác thực** (NFR-19: 100% coverage auth/consent), nên cần doc + test riêng — **không** làm drive-by ở đây. Ghi nhận §5.

---

## 4. Cổng kiểm tra (slice này)

- `actionlint` / [CRED_2B4F47AE] workflow YAML parse sạch sau khi sửa (nếu có trong CI).
- Diff `ci.yml` chỉ đổi đúng 2 dòng `uses:`; không đổi logic job.
- Alert #2 chuyển sang `dismissed` với `dismissed_reason` rõ ràng.

## 5. Ngoài phạm vi / [CRED_98C72FB1] theo dõi

- **#3 `pytest` → 9.0.3**: dev/test-only (GHSA-6w46-j5rx-g56g, tmpdir đoán trước được). Runner CI ephemeral single-tenant ⇒ rủi ro thấp. Bump là **major** → cần kiểm tra tương thích `pytest-asyncio` 0.24 + plugin. Làm khi thuận tiện.
- **#4 `postcss` 8.4.31**: bản top-level đã là 8.5.15 (an toàn); bản dính lỗi là `next/node_modules/postcss`, do Next.js pin. Lỗi XSS ở *stringify output* lúc build trên CSS của chính ta ⇒ không reachable. Chờ Next bump; có thể ép bằng npm `overrides` nhưng rủi ro tương thích Next, không đáng.
- **python-jose → PyJWT**: xóa `ecdsa` tận gốc (xem §3). Slice doc-first riêng, chạm auth crypto.
- **Pin-SHA toàn workflow**: hardening rộng cho mọi action third-party. Đợt riêng.
