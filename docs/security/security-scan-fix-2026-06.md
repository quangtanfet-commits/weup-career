# Security Scan workflow fix — 2026-06

**Status:** Design + actioned
**Date:** 2026-06-02
**Owner:** Platform / Security
**Scope:** The weekly `Security — Scheduled Scan` workflow (`.github/workflows/security-scan.yml`) has been failing on every scheduled run. GitHub surfaces the failed run of this CodeQL-containing workflow as a **"Code scanning configuration error"** banner on the repo Security tab.
**Related:** [ADR-007 CI/CD](../adr/ADR-007-cicd.md), [ADR-008 Security Controls](../adr/ADR-008-security-controls.md), [dependabot-2026-06.md](./dependabot-2026-06.md)

---

## 1. Triệu chứng

- Lần chạy `schedule` gần nhất của `security-scan.yml` (run 26740001789, 2026-06-01) **failure**.
- 2/4 job hỏng: **OWASP ZAP Baseline** và **Dependency Review**. Hai job **CodeQL** (python + javascript) **pass**.
- CodeQL là công cụ code-scanning trong workflow này; khi cả lần chạy workflow đỏ, GitHub gắn cờ "Code scanning configuration error" trỏ tới run hỏng.
- Repo là **public** ⇒ code scanning hoạt động không cần GHAS; không có analysis nào mang `error` ⇒ banner KHÔNG phải do SARIF bị từ chối, mà do **lần chạy workflow thất bại**.

---

## 2. Nguyên nhân gốc (3 lỗi độc lập)

### #1 — `dependency-review` chạy sai loại event
```
##[error]Both a base ref and head ref must be provided, either via the
`base_ref`/`head_ref` config options, `base-ref`/`head-ref` workflow action
options, or by running a `pull_request`/`pull_request_target`/`merge_group` workflow.
```
`actions/dependency-review-action` **diff** hai ref (base…head) nên chỉ chạy được trên event kiểu PR. Đặt nó trong workflow `schedule`/`workflow_dispatch` ⇒ **chưa bao giờ thành công**.

### #2 — ZAP không có quyền tạo issue
```
##[error]Resource not accessible by integration - .../issues#create-an-issue
```
`zaproxy/action-baseline` mặc định tạo/cập nhật một GitHub issue chứa kết quả. Job không khai báo `permissions:` ⇒ `GITHUB_TOKEN` mặc định không có `issues: write` ⇒ action thoát mã 1. (Bản thân lần quét ZAP **không** có phát hiện chặn: `FAIL-NEW: 0`, chỉ `WARN-NEW: 10` — `-I` khiến cảnh báo không làm fail.)

### #3 — Hai lỗi nhiễu cùng job ZAP
- `Error when reading the rules file: .zap/rules.tsv ... ENOENT` — workflow trỏ `rules_file_name: ".zap/rules.tsv"` nhưng file không tồn tại.
- `env file .../backend/.env not found` ở bước "Stop application stack" — bước teardown chạy `docker compose down` trần, chỉ đọc base `docker-compose.yml` (vốn **bắt buộc** `./backend/.env`, dòng 13), trong khi bước "up" dùng cả `-f docker-compose.test.yml` (đánh dấu `.env` `required: false`, dòng 19-21). Teardown thiếu override ⇒ lỗi.

---

## 3. Khắc phục

### ZAP job (`security-scan.yml`)
- Thêm `permissions: { contents: read }` ở cấp job (least privilege).
- Đặt `allow_issue_writing: false` trên bước ZAP ⇒ không tạo issue ⇒ hết lỗi quyền, không cần nâng token. Giữ `fail_action: true` để phát hiện thật (`FAIL-NEW`) vẫn fail gate.
- Teardown phản chiếu startup: `docker compose -f docker-compose.yml -f docker-compose.test.yml down -v`.

### `.zap/rules.tsv` (mới)
File ruleset tài liệu hoá, mọi alert ở mặc định `WARN`. Hết ENOENT và cho phép tinh chỉnh (IGNORE/WARN/FAIL theo plugin id) về sau.

### dependency-review — **dời chỗ, không bỏ gate**
- Gỡ job `dependency-review` khỏi `security-scan.yml` (không thể chạy trên `schedule`).
- Thêm vào `ci.yml` trên event `pull_request`, nơi nó thực sự **chặn PR** đưa dependency lỗ hổng `high` vào. Quyền `contents: read` + `pull-requests: write` (để comment tóm tắt). Kết quả: gate **mạnh hơn**, không yếu đi.
- Bao phủ dependency vẫn liên tục qua **Dependabot** (xem [dependabot-2026-06.md](./dependabot-2026-06.md)) + `npm audit`/`pip-audit` per-PR trong `ci.yml`.

---

## 4. Cổng kiểm tra

- `security-scan.yml` parse sạch; chỉ còn 3 job (owasp-zap, codeql×2) và đều xanh khi `workflow_dispatch`.
- `ci.yml` thêm job `dependency-review` chạy trên PR; PR này (chỉ đổi workflow + doc + rules.tsv) không đổi manifest ⇒ job pass trivially.
- Sau khi merge: kích `workflow_dispatch` cho `security-scan.yml`; một lần chạy xanh xoá banner "Code scanning configuration error".

## 5. Ngoài phạm vi / theo dõi

- **CodeQL chỉ chạy weekly** (`schedule` + `workflow_dispatch`), không chạy trên `push`/`pull_request`. PR hiện chỉ có Semgrep (trong `ci.yml`) gác code-scanning. Nếu banner còn sau khi run xanh, cân nhắc thêm trigger `push`/`pull_request` cho CodeQL — slice riêng (đánh đổi thời gian CI mỗi PR).
- **Pin-SHA toàn workflow**: hardening cho mọi action bên thứ ba (đã ghi nhận ở [dependabot-2026-06.md](./dependabot-2026-06.md) §5).
