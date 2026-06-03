# Engineering Rules — WeUp Career

Luật bất biến. Vi phạm = chặn merge. Đây là bản địa phương hoá của
`/engineering-playbook` cho repo này.

## Quy trình & Git

- **Conventional commits.** Tiền tố `feat/fix/chore/test/ci/docs/style/refactor/perf`.
  Lịch sử hiện tại: feat 32 · fix 26 · chore 26 · test 17 · ci 10 · docs 9.
- **KHÔNG ghi AI-attribution** vào commit (không `Co-Authored-By`, không
  "Generated with…").
- **Merge-commit, KHÔNG squash** khi tích hợp PR.
- **Feature-branch + remote-as-truth.** Một slice = một branch = một PR.
- **Stage file theo tên** (không `git add -A` / `git add .`) — tránh lọt
  secret / [CRED_5B9A2B1D] lớn.
- **KHÔNG force-push** trừ khi được yêu cầu tường minh; không bao giờ
  force-push `main`.
- **KHÔNG commit khi chưa được yêu cầu tường minh.**

## Chất lượng

- **TDD.** Coverage **≥90% có ý nghĩa** (line + branch). Test kiểu
  "verifies-call" mock-only KHÔNG được tính.
- **E2E thật** mặc định (Playwright, 3 trình duyệt), không thay bằng mock.
- **TLA+/TLC tại hai gate:** Gate A (spec nhất quán nội tại) + Gate B
  (conformance — trace thật replay qua impl). "TLC pass với spec yếu = FAIL."
  Mỗi invariant lớn phải có **sabotage-check**.
- **Đo lường được, không "nhìn bằng mắt".** Mọi gate xuất evidence
  (`report/<run-id>/`).
- **a11y:** vi phạm axe-core làm FAIL CI trừ khi được waive có lý do ghi rõ.

## Bảo mật & Secret hygiene

- **KHÔNG dán secret/token vào chat.** KHÔNG commit secret / `.env`.
  File `.env*` bị tool chặn đọc — xem qua `git show HEAD:<file>`, người dùng
  sửa qua shell prefix `!`.
- CI security gate: Trivy (image + deps), Semgrep, ZAP baseline, gitleaks,
  pip-audit / npm audit. HIGH = 0.
- Pin action theo **SHA** (N-6), không theo tag động.

## License

- **Chỉ dependency license permissive** (MIT/BSD/Apache-2.0). Tránh
  copyleft mạnh trừ khi được duyệt.

## Holdout discipline

- `scenarios/` là tập kiểm thử trung thực. **Agent build KHÔNG được nhìn thấy.**
- Khi một scenario holdout fail → dịch thành **sửa đổi spec**, KHÔNG dán
  nguyên văn scenario lại cho coder (tránh tối ưu cho scenario thay vì đúng).

## Nới gate?

- "Ngưỡng hạ tạm thời == hạ vĩnh viễn." Loại trừ **một module cụ thể** kèm
  **deadline theo dõi**, KHÔNG hạ chuẩn toàn cục.

## Tương tác & quyết định

- **Xác nhận trước hành động rủi ro / khó đảo / chạm shared-state:**
  push, force-push, sửa CI/CD, migrate DB gốc, xoá branch/file lạ.
- **Đề xuất dứt khoát** thay vì hỏi trắc nghiệm.
- **Doc-first:** viết doc/spec TRƯỚC khi code cho **mọi** task (kể cả migration
  & fix nhỏ).
