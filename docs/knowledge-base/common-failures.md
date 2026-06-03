# Common Failures — WeUp Career

Lỗi **hay lặp** + dấu hiệu + cách phòng. Khi CI đỏ hoặc e2e flaky, soát đây trước.

## CI / [CRED_AAAE13EA]

| Triệu chứng | Nguyên nhân thường gặp | Phòng |
|---|---|---|
| CI đỏ dù `lint` xanh | `format:check` là job riêng, Prettier chưa chạy | `npm run format` trước khi push |
| E2E thấy danh sách rỗng | RSC prerender tĩnh bake dữ liệu rỗng | `force-dynamic` cho public page fetch backend |
| E2E 429 hàng loạt | rate-limit bật, suite 3 trình duyệt đăng ký quá bucket | backend e2e boot với `RATE_LIMIT_ENABLED=false` |
| register 500 trong e2e | seed DB lệch sau migration (thiếu bảng/cột N-3) | copy seed → run-scoped DB rồi `alembic upgrade head` |
| Token verify không thấy | reader/writer khác path outbox | export `WEUP_MAILER_OUTBOX` cho cả backend & Playwright |
| Trivy/Semgrep/ZAP fail | dep CVE / [CRED_3F808F26] cấu hình | vá dep, không nới gate; loại trừ có deadline |

## Backend khởi động

| Triệu chứng | Nguyên nhân | Phòng |
|---|---|---|
| `app.main:app` not found | entrypoint là factory | `uvicorn app.main:get_app --factory` |
| health 000 sau idle | dev backend chết lúc idle | relaunch; readiness poll `/api/v1/health` |
| port `:8000`/`:443` vẫn bị giữ sau kill | `uv run` fork child uvicorn | `setsid` + `kill -- -$PGID`, hoặc kill listener PID |
| CORS preflight thiếu allow-origin | `CORS_ORIGINS` rỗng → middleware không mount | set `CORS_ORIGINS` runtime (csv) |

## Auth / [CRED_AC95AC4D]

| Triệu chứng | Nguyên nhân | Phòng |
|---|---|---|
| login 422 | email special-use TLD (`.local`) bị `EmailStr` từ chối | dùng domain hợp lệ |
| login bị chặn dù đúng pass | `email_verified_at` NULL (N-3) | verify email trước, hoặc set ở seed |
| không vào được `/school-admin` | role không phát trong token (theo trường) | tạo `school_membership` thật |

## Git / [CRED_8FAEFBB7]

| Triệu chứng | Nguyên nhân | Phòng |
|---|---|---|
| `index.lock: File exists` | lock cũ từ thao tác git crash trước | **xác minh không có tiến trình git** rồi mới `rm -f .git/index.lock` |
| `pkill -f` giết nhầm chính nó | pattern khớp cả lệnh đang chạy | kill theo listener PID từ `ss`/`netstat` |
| đọc `.env` bị tool chặn | secret hygiene | `git show HEAD:<file>`; người dùng sửa qua `!` shell |

## Môi trường

| Triệu chứng | Nguyên nhân | Phòng |
|---|---|---|
| `docker compose up` treo/lỗi | DinD aarch64/linuxkit không hỗ trợ | chạy native (uv/npm/playwright) |
| "1 error" teardown async cục bộ | flake môi trường, không phải regression | xác nhận CI xanh trước khi nghi code |
