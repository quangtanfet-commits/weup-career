# TLA+ Spec-Pack — WeUp Career

6 module TLA+ kiểm chứng 8 thuộc tính đúng đắn CP-1…CP-8 ([`docs/spec.md`](../docs/spec.md) §8). Thiết kế: [`docs/formal-verification/tla-spec-design.md`](../docs/formal-verification/tla-spec-design.md). Kết quả: [`docs/formal-verification/TLC_REPORT.md`](../docs/formal-verification/TLC_REPORT.md).

| Module | CP | Bất biến |
|---|---|---|
| `ConsentLifecycle` | CP-1, CP-2 | Không xử lý dữ liệu trẻ <16 khi consent ≠ active; thu hồi dừng xử lý mới |
| `SensitiveDataAccess` | CP-3 | Mỗi đọc nhạy cảm ⇒ 1 audit |
| `AuthorizationModel` | CP-4 | Không truy cập chéo trừ quan hệ được cấp quyền |
| `RecommendationGovernance` | CP-5, CP-6 | Human-in-the-loop + luôn có rationale |
| `AuthTokenLifecycle` | CP-7 | Tối đa 1 token active/user (xoay vòng nguyên tử) |
| `CompetencyProgress` | CP-8 | Độ sâu K→A→R không lùi |

Mỗi module có `<M>.tla` (base), `<M>MC.tla` (model constants), `<M>.cfg`, và `<M>Sab.tla` (sabotage — phải báo vi phạm).

**Chạy:** xem cuối `docs/formal-verification/TLC_REPORT.md`. Cần `tla2tools.jar` (có ở `/usr/local/share/tla/`) + Java.
