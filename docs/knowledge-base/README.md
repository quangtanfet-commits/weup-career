# Knowledge Base — WeUp Career

Bộ nhớ thể chế (institutional memory) của dự án. Bootstrap theo cấu trúc
7-file của `/engineering-playbook`. Nội dung được seed từ thực tế repo
(197 commit / 68 PR, 28/05→03/06/2026) và bộ nhớ dự án — **không phải template
rỗng**. Cập nhật liên tục, đừng để thành "wallpaper".

## Bảy file

| File | Trả lời câu hỏi | Khi nào đọc / cập nhật |
|---|---|---|
| [project-playbook.md](project-playbook.md) | Dự án này là gì, ai dùng, ràng buộc nền tảng? | Onboarding; khi phạm vi/đối tượng thay đổi |
| [engineering-rules.md](engineering-rules.md) | Luật bất biến (gate, commit, license, secret)? | Trước mỗi PR; khi đề xuất nới gate |
| [best-practices.md](best-practices.md) | Cách làm đã chứng minh hiệu quả ở repo này? | Khi bắt đầu một slice mới |
| [lessons-learned.md](lessons-learned.md) | Bài học đã trả giá để có? | Khi gặp vấn đề "ngờ ngợ đã thấy" |
| [architecture-decisions.md](architecture-decisions.md) | Quyết định kiến trúc lớn & lý do? | Trước khi đụng auth/crypto/topology |
| [common-failures.md](common-failures.md) | Lỗi hay lặp & cách phòng? | Khi CI đỏ hoặc e2e flaky |
| [debugging-playbook.md](debugging-playbook.md) | Quy trình gỡ lỗi từng lớp? | Khi đứng hình với một sự cố |

## Quy ước duy trì (ER-13)

Cuối mỗi phiên: **trích xuất → khử trùng lặp → tổng quát hoá → phân loại →
commit**. Bài học cụ thể → `lessons-learned`; lỗi tái diễn → `common-failures`;
quyết định có đánh đổi → `architecture-decisions` (hoặc `docs/adr/` nếu cần ADR
đầy đủ). Mỗi mục nên có **bối cảnh + vì sao + cách áp dụng**, không chỉ "what".

## Quan hệ với tài liệu khác

- `docs/adr/` — ADR chính thức (file này chỉ tóm tắt + trỏ tới).
- `docs/validation/weup-career/` — evidence pack kiến trúc (threat-model,
  fitness-functions, pre-mortem, spike).
- `docs/retrospective/` — hồi cứu quá trình phối hợp.
- `CLAUDE.skills.md` — pipeline skill (cách *thực thi* từng khâu).
