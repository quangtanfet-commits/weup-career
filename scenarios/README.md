# Holdout Scenarios — WeUp Career

> ⚠️ **HOLDOUT — build agent KHÔNG được đọc thư mục này.**
> Đây là tập kiểm thử trung thực (holdout) viết theo góc nhìn người dùng. Coding agent được trỏ vào `docs/spec.md`, **không** vào `scenarios/`. Chạy sau khi build bằng `/holdout-validate` hoặc dịch sang Playwright bằng `/ui-test`.

Nguồn: [`docs/spec.md`](../docs/spec.md) (FR + CP-1…CP-8). Format: Gherkin (Given-When-Then), giá trị cụ thể, kết quả quan sát được từ bên ngoài (HTTP response, UI text, DB row, audit row).

## Bản đồ feature → FR / CP

| File | Phủ FR | Phủ CP |
|---|---|---|
| `registration-age-gate.feature` | FR-01, FR-02 | CP-1 (vào cổng) |
| `guardian-consent.feature` | FR-02, FR-03, FR-04 | **CP-1, CP-2** |
| `auth-session.feature` | FR-05, FR-06 | **CP-7** |
| `assessment.feature` | FR-10…FR-15 | **CP-3** |
| `competency-progress.feature` | FR-20…FR-24 | **CP-8** |
| `career-library.feature` | FR-30…FR-33, FR-40…FR-42, FR-50 | (Điều 5a/c/d) |
| `recommendation.feature` | FR-60…FR-63 | **CP-5, CP-6** |
| `counseling-rbac.feature` | FR-80…FR-83 | **CP-4** |
| `wellbeing.feature` | FR-70, FR-71 | (ABCD NL4) |
| `account-data-rights.feature` | FR-91, FR-92, FR-14 | (Luật 91/2025) |

Mọi thuộc tính đúng đắn CP-1…CP-8 đều có ít nhất một scenario có thể quan sát được tương ứng.
