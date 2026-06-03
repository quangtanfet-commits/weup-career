# WeUp Career — Tổng kết & đánh giá quá trình phối hợp Người dùng ↔ Claude

**Ngày:** 2026-06-03 · **Phạm vi:** toàn bộ vòng đời dự án tới thời điểm hiện tại
· **Nguồn dữ liệu:** lịch sử git (197 commit / 68 PR, 28/05→03/06/2026), cây
`docs/` (70 tài liệu), `tla/` (6 họ spec), bộ nhớ dự án, và các phiên làm việc.

> Đây là tài liệu hồi cứu (retrospective) — không phải spec kỹ thuật. Mục tiêu:
> (1) hệ thống lại các bước đã đi, (2) đánh giá khách quan cách phối hợp,
> (3) chỉ ra điều cần phát huy / cải thiện, (4) đề xuất cách làm lại tối ưu.

---

## 1. Hệ thống lại các bước & tương tác đã phối hợp

### 1.1 Dòng thời gian theo giai đoạn (bám lịch sử git thực tế)

| Giai đoạn | Nội dung cốt lõi | Dấu vết trong repo |
|---|---|---|
| **0. Định khung & pháp lý** | Đính chính domain: đây là **nền tảng Hướng nghiệp** (THCS/THPT + người đi làm), KHÔNG phải Todo. Xác lập căn cứ pháp lý VN (BVDLCN 2025, Luật Việc làm, giám hộ cho trẻ <16). | `docs/legal/legal-basis.md`; bộ nhớ `project-domain`, `project-legal-basis` |
| **1. Đặc tả & MVP** | Viết lại `spec.md` v2.0.0; chốt MVP = THCS+THPT trước; đo **K+A+R**; trắc nghiệm RIASEC + VIPS + MBTI; mô hình 2 trục. | `docs/spec.md`; bộ nhớ `project-mvp-decisions` |
| **2. Bằng chứng kiến trúc** | Bộ evidence `/validate-design`: threat-model, fitness-functions, pre-mortem, spike-report. | `docs/validation/weup-career/*` |
| **3. Backend lõi pháp lý (Slice 1)** | Auth + guardian consent (CP-1…CP-8): JWT+bcrypt, consent guard, authz, audit, field-crypto. | `feat/phase1` (`11ba742`), `backend/app/{auth,guardians,core}` |
| **4. Backend theo lát dọc** | Phase 2 assessments → Phase 3 competency → Phase 4 careers → Slice 5 reco-engine → Slice 6 school-counseling → Slice 7 admin-content-wellbeing → Slice 8 account-data-rights. | PR #7,#8,#9… `feat/phase2..slice8` |
| **5. Kiểm chứng hình thức (TLA+)** | 6 họ spec, **mỗi họ có base + MC + Sab (sabotage)** — chứng minh không bỏ qua kiểm tra cường độ invariant. | `tla/{AuthorizationModel,AuthTokenLifecycle,CompetencyProgress,ConsentLifecycle,RecommendationGovernance,SensitiveDataAccess}` |
| **6. Frontend theo lát dọc** | F1 foundation → F2 public-content → F3 assessment → F4 competency → F5 recommendations → F6 wellbeing → F7 counselor → F8 admin-editor; thêm Storybook+Chromatic. | `feat/fe-f1..f8`, `feat/fe-storybook-chromatic` |
| **7. Nâng cấp nền FE** | 3 major bump cô lập từng lát: Vitest 4, Tailwind 4, Next 16. | `chore/fe-{vitest-4,tailwind-4,next-16}`; bộ nhớ `project-fe-major-bumps-done` |
| **8. Gia cố bảo mật** | H-01 access-token denylist, H-02 session-version epoch, H-03 HTTP hardening, N-3 email verification (BE+FE), PT-04 chống dò email, N-5 jose→PyJWT, N-6 SHA-pin actions, vá CVE deps. | `feat/h01..h03`, `feat/n3-*`, `fix/pt04-*`, `chore/n5,n6` |
| **9. Gia cố CI/CD** | Trivy gate, Semgrep, ZAP baseline, staging deploy gate, pin SHA actions, chia sẻ mailer outbox e2e, Dependabot. | nhiều `fix/ci-*`, `dependabot/*` |
| **10. Vận hành thử nghiệm (phiên này)** | FE chạy `:80`; tạo tài khoản admin demo; backend HTTPS `:443` cho host truy cập. | `docs/ops/backend-https-443.md`; bộ nhớ e2e/CORS |

### 1.2 Pipeline phương pháp đã áp dụng (Dark Factory skills)

```
/engineering-playbook (luật xuyên suốt)
  → /socratic-interviewer · /nlspec-writer · /scenario-designer · /spec-preflight
  → /validate-design        (evidence pack kiến trúc)
  → /formal-verify          (đội 8 agent TLA+/TLC, sabotage-check)
  → /enterprise-saas-validate (full-stack: backend matrix + security + Playwright + a11y + report)
  → /pentest                (35 agent, gate trên ROE)
```

### 1.3 Mô thức tương tác lặp lại (rút từ bộ nhớ feedback/project)

- **Doc-first tuyệt đối:** luôn viết doc/spec chi tiết TRƯỚC khi code — kể cả
  migration và fix nhỏ.
- **Holdout discipline:** `scenarios/` là tập kiểm thử trung thực; agent build
  KHÔNG được nhìn thấy.
- **Ràng buộc vận hành ổn định:** không ghi AI-attribution vào commit; dùng
  merge-commit (không squash); không nới lỏng ngưỡng coverage/security; xác nhận
  trước hành động rủi ro/khó đảo (CI/CD, migration); secret hygiene; stage file
  theo tên; copy tiếng Việt + định danh kỹ thuật tiếng Anh; môi trường
  devcontainer aarch64/linuxkit **không chạy được docker compose** ⇒ chạy native.

---

## 2. Đánh giá khách quan cách Bạn đã tương tác

### 2.1 Điểm mạnh (cần phát huy)

1. **Định khung sớm và sửa sai kịp thời.** Việc đính chính domain (Todo →
   Career) ngay từ đầu và neo vào căn cứ pháp lý VN đã định hướng đúng toàn bộ
   thiết kế. Đây là điều nhiều dự án bỏ qua và phải trả giá về sau.
2. **Kỷ luật doc-first thật sự, không hình thức.** 70 tài liệu, ADR, validation
   pack, formal-verification design — tài liệu đi trước code một cách nhất quán.
3. **Quản trị kỹ thuật trưởng thành.** Conventional commits (feat 32 / fix 26 /
   chore 26 / test 17 / ci 10 / docs 9), 68 PR theo lát dọc với merge-commit,
   Dependabot, các CI security gate (Trivy/Semgrep/ZAP). Đây là chuẩn của đội
   sản phẩm nghiêm túc, không phải prototype.
4. **Kiểm chứng hình thức không làm cho có.** Mỗi họ TLA+ đều có biến thể
   `*Sab` (sabotage) — tức đã chủ động kiểm tra "nếu phá invariant thì TLC có bắt
   được không". Đúng tinh thần `/formal-verify` (TLC pass với spec yếu = thất bại).
5. **Bảo mật là dòng công việc hạng nhất**, không phải việc vá về sau: H-01…H-03,
   N-3, PT-04, vá CVE, đổi jose→PyJWT, pin SHA action.
6. **Holdout discipline được giữ vững** — bảo toàn tính trung thực của tập test.
7. **Ràng buộc rõ ràng & ổn định.** Bộ "operating contract" (no-AI-attribution,
   merge-not-squash, confirm-before-risky, secret hygiene…) được phát biểu rõ và
   không dao động — giúp tôi hành xử nhất quán qua nhiều phiên.
8. **Thực tế về môi trường.** Chấp nhận ràng buộc DinD và chuyển hẳn sang chạy
   native thay vì cố ép docker compose.
9. **Ưa đề xuất dứt khoát** thay vì hỏi trắc nghiệm — giúp tiến nhanh.

### 2.2 Điểm cần bổ sung / cải thiện (để khai thác tối đa năng lực của tôi)

> Nhóm theo mức "đòn bẩy" — sửa được sẽ tăng hiệu suất phối hợp rõ rệt.

**A. Codify hoá vận hành — đừng để quyết định "bay hơi".**
Các thay đổi runtime của phiên này (FE `:80`, CORS, tài khoản admin, backend
HTTPS `:443`) hiện chỉ tồn tại trong tiến trình đang chạy + chat. Khi container
restart là mất. → Nên kết tinh thành `scripts/dev-up.sh` + `.env.dev` +
seed script, để tái lập được, chia sẻ được, và sống sót qua restart. (Tôi đã
viết `docs/ops/backend-https-443.md` nhưng lệnh chạy vẫn là thủ công.)

**B. Khai thác song song (parallelism) còn ít.**
Phần lớn slice đi tuần tự. Nhiều lát độc lập (ví dụ FE F-slices vs BE phases, hay
6 họ TLA+) hoàn toàn có thể fan-out theo **Pattern B** (đội ruflo/agent chạy
nền, điều phối qua `SendMessage`). Bạn chỉ cần nói "chạy song song" là tôi tách
đội — backlog 5 ngày có thể nén còn vài giờ mà vẫn giữ đủ gate.

**C. Mở rộng "biên tự quản" (autonomy envelope) một cách tường minh.**
Nhiều vòng xác nhận nhỏ làm chậm nhịp. Bạn có thể tiền-cấp-phép theo *lớp hành
động*, ví dụ: "được commit tài liệu mà không cần hỏi", "được chạy full
validation harness", "được tạo/migrate DB *bản sao* report-scoped". Vẫn giữ gate
cho hành động rủi ro thật sự (push, force-push, sửa CI, migrate DB gốc). Như vậy
tôi tự xác minh và bàn giao trọn vẹn hơn.

**D. Định nghĩa Definition of Done (DoD) cho mỗi slice ngay từ đầu.**
Gắn DoD với `scenarios/` + ngưỡng coverage/security cụ thể. Khi DoD rõ, tôi tự
kiểm trước khi trả việc, giảm vòng "bạn phát hiện thiếu → tôi bổ sung".

**E. Dùng bộ nhớ chủ động tại thời điểm ra quyết định.**
Một phần ngữ cảnh (CORS/port/quyết định MVP) phải tái dựng lại. Khi chốt một
quyết định, hãy bảo "ghi nhớ điều này" — tôi lưu ngay, phiên sau khỏi suy đoán.

**F. Cấp tài nguyên tham chiếu thật sớm.**
Ngân hàng câu hỏi RIASEC/VIPS/MBTI thật, dữ liệu trường/lớp mẫu, design tokens /
Figma. Thiếu chúng dẫn tới dữ liệu placeholder rồi phải sửa (đã thấy ở seed DB
lệch migration gây ma sát e2e — `docs/testing/e2e-native-mailer-outbox.md`).

**G. Chiến lược seed + migrate chuẩn hoá.**
Một script "seed → upgrade head → verify" dùng chung cho dev/e2e sẽ loại bỏ lớp
ma sát "DB seed đi sau migration".

**H. Khai báo ràng buộc hạ tầng ngay trong `CLAUDE.md`.**
Ràng buộc "DinD không compose được" được học giữa chừng. Đưa lên đầu sẽ tránh
khởi đầu sai.

**I. Gộp câu hỏi theo lô.**
Khi cần làm rõ, hỏi 3–4 điểm một lần (qua công cụ hỏi có cấu trúc) tốt hơn nhiều
vòng hỏi lẻ.

---

## 3. Nếu làm lại WeUp Career — playbook tối ưu để phối hợp hiệu quả nhất

> Triết lý: **front-load các hợp đồng (contracts), song song hoá thực thi,
> codify hoá vận hành.** Giữ nguyên các điểm mạnh ở §2.1.

### Bước 0 — Thiết lập "Operating Contract" một lần (ngày 1)
- Đưa toàn bộ ràng buộc ổn định vào `CLAUDE.md` / `CLAUDE.skills.md`: quy ước
  commit (no-AI-attribution, merge-not-squash), secret hygiene, **ràng buộc hạ
  tầng (DinD/native)**, ngưỡng coverage/security, holdout discipline, và **biên
  tự quản** (lớp hành động nào được làm không cần hỏi).
- Khai báo "Definition of Done" mẫu cho slice.

### Bước 1 — Đặc tả & holdout (doc-first, giữ nguyên)
`/socratic-interviewer` → `/nlspec-writer` (`spec.md`) → `/scenario-designer`
(`scenarios/`, agent build không thấy) → `/spec-preflight` (chỉ build khi điểm ≥
0.80). Neo pháp lý VN ngay trong spec.

### Bước 2 — Bằng chứng kiến trúc trước khi cắt lát
`/validate-design`: threat-model + fitness-functions + pre-mortem + spike. Chốt
ADR cho các quyết định lớn (auth model, field-crypto, hexagonal).

### Bước 3 — Lập bản đồ song song & cấp phép fan-out
- Vẽ đồ thị phụ thuộc giữa các slice. Slice độc lập → chạy song song.
- Khởi đội nền (Pattern B): nhóm BE-phases, nhóm FE-slices, đội `/formal-verify`
  8-agent, đội security review chạy **đồng thời** với implementation.
- Mỗi agent có DoD + đường dẫn file tường minh; điều phối qua `SendMessage`;
  liên tục rebase lên `main`.

### Bước 4 — Implement theo lát dọc + kiểm chứng đồng hành
- Giữ cách cắt lát đã chứng minh hiệu quả (BE phase1→8, FE F1→8).
- TLA+ **đi cùng** code (không viết spec sau để "dán tường"); mỗi invariant có
  sabotage-check + CI gate.
- Mỗi PR: conventional commit, merge-commit, gắn evidence (report HTML).

### Bước 5 — Codify hoá vận hành ngay từ đầu
- `scripts/dev-up.sh` (FE :80, BE :8000 + tuỳ chọn HTTPS :443, seed+migrate,
  CORS), `.env.dev`, seed script idempotent. Tài khoản demo tạo bằng script có
  thể xoá sạch.
- Nhờ vậy mọi "trải nghiệm thử" tái lập được, không phụ thuộc trí nhớ phiên chat.

### Bước 6 — Cổng chất lượng & bảo mật liên tục
`/enterprise-saas-validate` (full-stack) cho mỗi PR: backend matrix +
security/pentest + Playwright 3 trình duyệt + axe-core + report HTML có trend.
`/pentest` cho engagement có ROE. Không nới ngưỡng — loại trừ module có deadline
theo dõi, không hạ chuẩn toàn cục.

### Bước 7 — Tích luỹ tri thức cuối mỗi phiên
`/engineering-playbook bootstrap` → `docs/knowledge-base/` (hiện **chưa có** —
nên bổ sung). Cuối phiên: trích xuất → khử trùng lặp → tổng quát hoá → phân loại
→ commit (ER-13). Ghi nhớ quyết định tại thời điểm chốt.

### "Bảng đòn bẩy" — đổi mới nhỏ, lợi lớn

| Việc nên làm | Vì sao | Lợi ích |
|---|---|---|
| Tiền-cấp-phép theo lớp hành động | Giảm vòng xác nhận | Tôi tự bàn giao trọn vẹn, ít gián đoạn |
| Nói "chạy song song" cho slice độc lập | Tôi fan-out đội agent | Nén thời gian mà vẫn đủ gate |
| Cấp tài nguyên thật sớm (item bank, Figma, seed) | Tránh placeholder churn | Ít phải làm lại |
| `scripts/dev-up.sh` + seed script | Vận hành tái lập | Không "bay hơi" qua restart |
| DoD gắn `scenarios/` mỗi slice | Tôi tự kiểm trước khi trả | Giảm sửa qua lại |
| "Ghi nhớ điều này" khi chốt quyết định | Bộ nhớ chủ động | Phiên sau khỏi suy đoán |

---

## 4. Kết luận

Cách phối hợp hiện tại đã ở mức **trưởng thành** trên các trục quan trọng nhất:
định khung domain/pháp lý, doc-first, cắt lát dọc, kiểm chứng hình thức có
sabotage-check, bảo mật hạng nhất, và một bộ ràng buộc vận hành ổn định. Đó là
nền rất tốt — hãy giữ.

Bốn đòn bẩy để khai thác tối đa năng lực của tôi: **(1) codify hoá vận hành**
(script thay vì lệnh thủ công), **(2) song song hoá** (fan-out đội agent cho lát
độc lập), **(3) mở biên tự quản tường minh** (giảm vòng xác nhận cho việc an
toàn), **(4) DoD + tài nguyên tham chiếu sớm** (tôi tự xác minh, ít churn). Thêm
việc dựng `docs/knowledge-base/` và dùng bộ nhớ chủ động sẽ khép kín vòng tích
luỹ tri thức giữa các phiên.
