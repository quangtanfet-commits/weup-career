# Kiến trúc Frontend — WeUp Career

**Phiên bản:** 1.0.0 | **Ngày:** 2026-05-30
**Trạng thái:** DESIGN — Blueprint để coder triển khai (chưa viết code)
**Phạm vi:** Toàn bộ frontend `frontend/` cho nền tảng Hướng nghiệp Quốc gia WeUp Career
**Neo vào:** [`docs/spec.md`](../spec.md) (§2 actors, §3 FR, §5 data model, §6 API, §8 CP-1..CP-8), [`docs/ux/user-flows.md`](../ux/user-flows.md), [`docs/security/auth-design.md`](../security/auth-design.md), [`docs/adr/ADR-004-state-management.md`](../adr/ADR-004-state-management.md).

> **Quy ước ngôn ngữ:** Văn xuôi/giải thích bằng tiếng Việt. Định danh kỹ thuật (component, route, type, biến môi trường, design token) giữ tiếng Anh.
>
> **Quyết định framework — ghi nhận tại [ADR-014](../adr/ADR-014-frontend-framework.md):** **Next.js 16 (App Router) + React 19 + TypeScript strict**, thay thế phần SPA React 18 + Vite 5 của ADR-001. Vẫn React/TS, thêm Server Components cho nội dung công khai (SEO Điều 5a) và streaming. Quyết định server-state của **ADR-004 (TanStack Query v5 + Zustand) được giữ nguyên** và áp dụng nguyên vẹn ở lớp client.

---

## 0. Nguyên tắc nền (load-bearing, không thương lượng)

1. **Cổng đồng ý là bất biến UI:** trẻ `under_16` chưa có `GuardianConsent` active **không** thấy/chạm được luồng xử lý dữ liệu (trắc nghiệm, gợi ý, tiến bộ, wellbeing). UI phản chiếu CP-1/CP-2 — không phải lớp trang trí, mà là điều kiện render. Backend vẫn là tầng thực thi cuối (403 `GUARDIAN_CONSENT_REQUIRED`); UI chỉ tránh dẫn người dùng vào ngõ cụt.
2. **Không ép buộc, luôn có lý do:** mọi `Recommendation` hiển thị `rationale` (CP-6) và **luôn** đòi người xác nhận tường minh (CP-5). Không có optimistic update, không có "auto-apply".
3. **Dữ liệu nhạy cảm là khách mời, không phải cư dân:** kết quả trắc nghiệm (`is_sensitive=true`) **không** được cache lâu phía client, không lưu localStorage, không log. Mỗi lần xem là một lần gọi API (backend audit CP-3).
4. **Quyền tối thiểu theo vai trò (CP-4):** route/feature module được gate theo `role` + quan hệ; counselor chỉ thấy view **đã gỡ nhạy cảm**.
5. **Tiếng Việt trước, a11y xuyên suốt:** vi mặc định, WCAG 2.1 AA là ngưỡng CI (axe-core), không phải mục tiêu "cố gắng".

---

## 1. Stack công nghệ & lý do (DECISIVE)

| Lớp | Lựa chọn | Phiên bản neo | Lý do (1–2 dòng) |
|---|---|---|---|
| Framework | **Next.js App Router** | `15.x` (React 19) | RSC cho nội dung công khai Điều 5a (SEO, tải nhanh, không lộ token); client components cho luồng xác thực/trắc nghiệm. App Router là hướng mặc định của Next, hỗ trợ streaming + layout lồng nhau khớp IA theo vai trò. |
| Ngôn ngữ | **TypeScript strict** | `5.x` | `strict: true`, `noUncheckedIndexedAccess`. Type sinh từ OpenAPI ⇒ hợp đồng FE↔BE kiểm tra ở compile-time. |
| Styling | **Tailwind CSS** + **shadcn/ui** (trên **Radix UI**) | Tailwind `3.4.x`, Radix latest | Tailwind = tốc độ + design token qua CSS variable; Radix primitives đã giải quyết a11y khó (focus trap, ARIA roving, dialog, listbox) — không tự viết lại. shadcn/ui = code-in-repo (không phải dependency đen), dễ kiểm toán & sửa token. |
| Server-state | **TanStack Query v5** | `5.x` | Theo ADR-004: cache, refetch nền, retry, invalidation cho REST. **Tắt cache** cho query nhạy cảm (`gcTime: 0`, `staleTime: 0`). |
| Client-state | **Zustand** | `5.x` | Theo ADR-004: chỉ giữ session/role context + UI prefs (theme, reduced-motion). Không nhồi server-state vào đây. |
| Public content fetch | **React Server Components** + `fetch` cache | built-in | `/careers`, `/content` công khai render server-side (ISR/revalidate) cho SEO Điều 5a; không cần token, không qua TanStack Query. |
| Form | **React Hook Form** + **Zod** | RHF `7.x`, Zod `3.x` | Zod schema **phản chiếu Pydantic** backend (cùng luật: password ≥8 hoa/thường/số, email lowercase/trim, dob quá khứ). `@hookform/resolvers/zod` nối liền. |
| HTTP client | **fetch** (native) bọc trong typed client | — | Không thêm axios; một `apiFetch` wrapper xử lý Bearer + refresh-on-401 + credentials cho cookie. |
| Types từ API | **openapi-typescript** | `7.x` | Sinh `types/api.d.ts` từ OpenAPI 3.1 của FastAPI (NFR-20). |
| i18n | **next-intl** | `3.x` | App Router-native, message catalog tách UI-chrome khỏi nội dung versioned server-side. |
| Charts | **Recharts** | `2.x` | Biểu đồ tiến bộ K-A-R (ADR-001 rev đã thêm "thư viện biểu đồ cho dashboard"); SVG, a11y-friendly, không canvas. |
| Test | **Vitest** + **Testing Library** | latest | Unit/component; nhanh, ESM-native; chạy độc lập với runtime Next.js (Vitest tự dùng esbuild/Vite cho transform test). |
| E2E | **Playwright** | latest | CI đã gate (Chromium/Firefox/WebKit); khớp `/ui-test`. |
| a11y CI | **@axe-core/playwright** + **eslint-plugin-jsx-a11y** | latest | Gate a11y (job `a11y` đã chờ sẵn). |

**Top-level cấu trúc:** `frontend/` là root Next.js. CI key trên `frontend/package-lock.json` (npm). `next.config.ts`, `tailwind.config.ts`, `tsconfig.json` ở `frontend/`.

---

## 2. Design system & tokens — bản sắc WeUp Career

**Định hướng thị giác:** *tin cậy thể chế nhưng gần gũi với học sinh* — xanh dương trầm (institutional trust) làm primary, xanh ngọc/teal (growth, hướng tới tương lai) làm secondary, nền ấm-trung tính để dễ đọc tiếng Việt nhiều dấu. Không màu mè trẻ con, không xám-lạnh doanh nghiệp.

### 2.1 Bảng màu (hex + ghi chú tương phản WCAG AA)

| Token | Hex | Dùng cho | Tương phản |
|---|---|---|---|
| `--color-primary-600` | `#1D4ED8` | nút chính, link, focus | 5.9:1 trên `#FFFFFF` ✓ AA text |
| `--color-primary-700` | `#1E40AF` | hover/active | 7.4:1 ✓ AAA |
| `--color-primary-50` | `#EFF5FF` | nền nhấn nhẹ | (nền — cặp với text-900) |
| `--color-secondary-500` | `#0E9F8E` | growth, badge tiến bộ | 3.3:1 → **chỉ cho icon/đồ họa ≥3:1 hoặc text lớn** |
| `--color-secondary-700` | `#0A6F63` | text secondary | 5.2:1 ✓ AA |
| `--color-ink-900` | `#0F172A` | text chính | 16:1 trên trắng ✓ |
| `--color-ink-600` | `#475569` | text phụ | 7.5:1 ✓ |
| `--color-surface` | `#FBFBFD` | nền trang | — |
| `--color-success-600` | `#15803D` | đạt mức K→A→R | 4.8:1 ✓ AA |
| `--color-warning-600` | `#B45309` | chờ consent, cảnh báo | 4.6:1 ✓ AA |
| `--color-danger-600` | `#DC2626` | xóa, lỗi | 4.5:1 ✓ AA |
| `--color-sensitive-700` | `#6D28D9` | nhãn "dữ liệu riêng tư" (tím — phân biệt khỏi semantic) | 5.6:1 ✓ AA |

> **Quy tắc CP/a11y:** không bao giờ truyền tin **chỉ bằng màu** (user-flows §a11y). Mọi trạng thái (giai đoạn, độ sâu, nhạy cảm, consent) = **màu + icon + text**. `--color-sensitive-700` luôn đi kèm icon khóa + chữ "Dữ liệu riêng tư".

### 2.2 Typography (an toàn dấu tiếng Việt)

- **Font chữ:** **Be Vietnam Pro** (UI-chrome + heading) — thiết kế riêng cho tiếng Việt, dấu cân đối, weight 400/500/600/700. Fallback **Inter** → system. Self-host qua `next/font/local` (CSP `font-src 'self'`, khớp Nginx header auth-design).
- **Scale (rem, 1rem=16px):** `xs 0.75` / `sm 0.875` / `base 1` / `lg 1.125` / `xl 1.25` / `2xl 1.5` / `3xl 1.875` / `4xl 2.25`. Line-height nội dung đọc 1.6 (tiếng Việt nhiều dấu cần thoáng dòng).
- **Token:** `--font-sans: "Be Vietnam Pro", Inter, system-ui, sans-serif`.

### 2.3 Spacing / radii / elevation

- **Spacing scale (4px base):** `1=4 2=8 3=12 4=16 5=20 6=24 8=32 10=40 12=48 16=64`.
- **Radii:** `--radius-sm 6px` (input), `--radius-md 10px` (card), `--radius-lg 16px` (modal/sheet), `--radius-full` (badge/avatar).
- **Elevation:** `--shadow-sm` (card nghỉ), `--shadow-md` (card hover/popover), `--shadow-lg` (dialog). Bóng mềm, độ mờ thấp — tin cậy không nặng nề.

### 2.4 Hiện thực token

Tokens là **CSS variables** trên `:root` (file `app/globals.css`), được **map vào `tailwind.config.ts`** theme (`colors`, `spacing`, `borderRadius`, `boxShadow`, `fontFamily`). shadcn/ui đọc cùng biến ⇒ một nguồn sự thật. Hỗ trợ `prefers-reduced-motion` và (tương lai) `data-theme` cho dark mode mà không sửa component.

---

## 3. Information Architecture & Routing (App Router)

Quy ước: **(rsc)** = React Server Component (công khai, SEO); **(client)** = Client Component (cần token/tương tác); **[gate]** = qua consent gate; **[role:x]** = role-gated.

```
frontend/app/
├── (public)/                         # RSC — không cần auth, SEO Điều 5a
│   ├── page.tsx                       (rsc)  Trang chủ / marketing
│   ├── careers/
│   │   ├── page.tsx                   (rsc)  Thư viện nghề (GET /careers) — Luồng 3
│   │   └── [careerId]/page.tsx        (rsc)  Chi tiết nghề (GET /careers/{id})
│   └── content/[contentId]/page.tsx  (rsc)  Nội dung Điều 5a/c/d công khai
│
├── (auth)/                            # client — không có token
│   ├── login/page.tsx                (client) POST /auth/login — Luồng 1
│   └── register/page.tsx             (client) POST /auth/register
│
├── (app)/                             # AUTHENTICATED — layout kiểm tra session
│   ├── layout.tsx                    (client) SessionProvider + AppShell + role nav
│   ├── consent/page.tsx              (client) Cổng giám hộ: invite/resend — pending_guardian_consent
│   ├── dashboard/page.tsx            (client) Dashboard học sinh (3 câu hỏi ECG)
│   ├── assessments/
│   │   ├── page.tsx                  (client) GET /assessments — danh sách instrument
│   │   ├── [type]/page.tsx           (client)[gate] Assessment runner (RIASEC/VIPS/MBTI) — Luồng 2
│   │   └── results/[resultId]/page.tsx (client)[gate] Kết quả nhạy cảm (no-cache)
│   ├── progress/page.tsx             (client)[gate] Tiến bộ K-A-R (GET /me/progress) — Luồng 4
│   ├── recommendations/
│   │   ├── page.tsx                  (client)[gate] Danh sách gợi ý
│   │   └── [recoId]/page.tsx         (client) Thẻ gợi ý + human-confirm — Luồng 5
│   ├── wellbeing/page.tsx            (client)[gate] Sức khỏe tinh thần (NL4)
│   ├── account/
│   │   ├── profile/page.tsx          (client) GET /me/profile, PATCH /me
│   │   ├── security/page.tsx         (client) POST /me/password
│   │   ├── data/page.tsx             (client) GET /me/export, DELETE /me (quyền chủ thể)
│   │   └── children/page.tsx         (client) Guardian: export/xóa dữ liệu con
│   │
│   ├── guardian/                      # [role:guardian]
│   │   ├── consents/page.tsx         (client) Cấp/thu hồi (POST /guardians/consent[/revoke])
│   │   └── children/[childId]/page.tsx (client) Đồng xem tiến bộ/kết quả trẻ liên kết
│   │
│   ├── counselor/                     # [role:counselor]
│   │   ├── students/page.tsx         (client) GET /school/{id}/students (de-sensitized)
│   │   ├── students/[studentId]/page.tsx (client) GET /school/students/{id}/progress
│   │   └── sessions/page.tsx         (client) POST /counseling/sessions (Tier 1/2/3)
│   │
│   ├── school-admin/                  # [role:school_admin]
│   │   ├── classes/page.tsx          (client) GET/POST /school/{id}/classes
│   │   └── members/page.tsx          (client) POST /school/{id}/members
│   │
│   └── editor/                        # [role:content_editor]
│       ├── content/page.tsx          (client) GET/POST /content, GET /content/{id}
│       └── content/[id]/page.tsx     (client) POST /content/{id}/versions
│
└── api/ (KHÔNG dùng làm BFF cho dữ liệu — backend FastAPI là nguồn duy nhất)
```

**Vì sao tách (public) RSC khỏi (app) client:** thư viện nghề (Điều 5a) phải SEO-friendly và **trẻ <16 chờ consent vẫn xem được** (user-flows §Luồng 1 — "không cảm giác bị chặn cụt"). **Backend (BE-1) xác nhận: `GET /careers`, `/careers/{id}`, `/content`, `/content/{id}` là anonymous-readable thật** — đọc được **không cần `Authorization`**, bất biến *published-only* (ẩn danh không thể `?status=` để thấy draft/archived). Vì vậy public RSC **fetch ẩn danh trực tiếp**, không token, không service token đọc-công-khai (xem §5.4).

---

## 4. Kiến trúc Component

### 4.1 Phân lớp

```
primitives (shadcn/ui + Radix)   →  composites (domain-agnostic)  →  feature modules  →  pages (route)
Button, Input, Dialog, Tabs,        Card, DataTable, EmptyState,      mỗi domain 1 thư mục   app/**/page.tsx
Select, Toast, Badge, Progress      FormField, PageHeader, StatPill   (assessments, reco…)   chỉ compose
```

### 4.2 Cấu trúc thư mục `frontend/`

```
frontend/
├── app/                      # route tree (§3)
├── components/
│   ├── ui/                   # shadcn primitives (code-in-repo, kiểm toán được)
│   └── composites/           # Card, DataTable, FormField, ConsentGateBanner...
├── features/                 # feature modules theo domain (đóng gói UI+hook+schema)
│   ├── auth/                 # LoginForm, RegisterForm, useSession
│   ├── consent/              # ConsentGateBanner, GuardianInviteForm, useConsentStatus
│   ├── assessments/          # AssessmentRunner, ResultView, SensitiveBadge
│   ├── competency/           # KARProgressViz, CompetencyTree, DepthStepper
│   ├── careers/              # CareerCard, CareerFilters, CareerDetail (RSC-friendly)
│   ├── recommendations/      # RecommendationCard, RationalePanel, HumanConfirmAction
│   ├── counseling/           # DeSensitizedStudentView, SessionForm, RosterTable
│   └── account/              # ProfileForm, DataExportButton, DeleteAccountDialog
├── lib/
│   ├── api/                  # typed client (§6): client.ts + endpoints/*.ts
│   ├── auth/                 # token store, refresh interceptor, session context
│   ├── query/                # QueryClient config, sensitive-query helpers
│   └── i18n/                 # next-intl config
├── types/                    # api.d.ts (sinh từ OpenAPI) + domain types
├── messages/                 # vi.json (+ locale tương lai)
├── styles/ (globals.css)     # CSS variable tokens
└── tests/ + e2e/             # Vitest + Playwright
```

### 4.3 Quy ước đặt tên

- Component: `PascalCase.tsx`; hook: `useX.ts`; schema Zod: `x.schema.ts`; endpoint group: `endpoints/<domain>.ts`.
- Server Component không có `"use client"`; client component bắt buộc khai báo trên cùng.
- Feature module **không** import chéo nhau ở tầng UI; chia sẻ qua `components/composites` hoặc `lib/`.

### 4.4 Component tái dùng then chốt (load-bearing, gắn CP)

| Component | Vai trò | CP/FR |
|---|---|---|
| `ConsentGateBanner` | Chặn mềm + CTA mời/gửi-lại giám hộ; bọc mọi feature `[gate]` | CP-1/CP-2, FR-02/03 |
| `GuardianInviteForm` | Nhập email/SĐT giám hộ (RHF+Zod) → POST /guardians/invite | FR-03 |
| `AssessmentRunner` | Chạy bài theo bước, progress bar, lưu nháp, ARIA live | FR-10/11, a11y |
| `ResultView` + `SensitiveBadge` | Hiển thị kết quả + giải thích + nhãn "Dữ liệu riêng tư" + ai-xem-được | CP-3, FR-12 |
| `RecommendationCard` | payload + **RationalePanel (bắt buộc)** + nhãn "quyết định thuộc về bạn" | CP-6, FR-61/62 |
| `HumanConfirmAction` | Cụm nút Chấp nhận/Từ chối/Để sau → POST /recommendations/{id}/confirm; **không** auto-apply | CP-5 |
| `KARProgressViz` + `DepthStepper` | Biểu đồ 12 năng lực × (K→A→R) + giai đoạn; màu+icon+text | FR-22/24 |
| `CareerCard` + `CareerFilters` | Thẻ nghề + lọc riasec/field/training_level/pathway_type | FR-30/32 |
| `DeSensitizedStudentView` | View counselor — **chỉ** tiến bộ đã gỡ nhạy cảm, không payload trắc nghiệm | CP-3/CP-4, FR-82 |

---

## 5. Quản lý state & xác thực

### 5.1 Mô hình token (khớp auth-design.md)

- **access_token** (JWT, 15') → giữ **trong memory** (Zustand store, không localStorage/cookie) ⇒ giảm bề mặt XSS; gửi qua header `Authorization: Bearer`.
- **refresh_token** (7 ngày) → **httpOnly cookie** do backend set tại `/auth/login`,`/auth/refresh` với `path=/api/v1/auth`, `samesite=strict`, `secure` (prod). FE **không bao giờ** đọc được — đúng thiết kế.
- **Khôi phục phiên khi reload:** access token in-memory mất khi F5 ⇒ app khởi động gọi **`POST /api/v1/auth/refresh`** (cookie tự gửi) để lấy access token mới + `user`. Nếu 401 ⇒ chưa đăng nhập → điều hướng `/login`.

### 5.2 Refresh-on-401 interceptor

`lib/api/client.ts` bọc `fetch`:
1. Gắn `Authorization` từ token store; `credentials: "include"` cho route `/auth/*`.
2. Nếu response **401** và không phải chính `/auth/refresh`: gọi `/auth/refresh` **một lần** (single-flight — các request song song chờ chung một promise để tránh refresh storm), cập nhật store, **retry** request gốc một lần.
3. Refresh thất bại ⇒ clear store, điều hướng `/login`. Khớp CP-7: refresh token đã thu hồi → 401 → đăng xuất.
4. **Proactive refresh (tùy chọn):** hẹn refresh ~60s trước `exp` (auth-design "tự refresh 60s trước khi hết hạn").

### 5.3 Session/role context

- `useSession()` (Zustand) giữ `{ user, accessToken, status }`. `user` gồm `age_band`, `account_status`, `roles`, `user_type`, `school_level` (từ `/auth/me` hoặc payload login).
- **Route guard (client):** `(app)/layout.tsx` đọc session; nếu `account_status==='pending_guardian_consent'` và route là `[gate]` ⇒ điều hướng `/consent` (chặn mềm trước khi backend trả 403). Role guard cho `guardian/counselor/school-admin/editor` segment.
- **Lưu ý nguồn sự thật:** claim JWT có thể cũ tối đa 15' (auth-design); UI dùng nó để **gợi ý điều hướng**, còn **quyết định cuối là backend** (403/404). UI không bao giờ tự coi mình là tầng thực thi consent.

### 5.4 Ranh giới Server vs Client & token công khai

- **(public) RSC:** gọi backend (server-to-server) cho `/careers`, `/content` **ẩn danh — không gắn `Authorization`**. BE-1 đã làm các GET này anonymous-readable thật, nên **không cần `PUBLIC_READ_TOKEN`** hay chế độ token đọc-công-khai. Phụ thuộc liên-đội đó (trước đây ở §11/Phụ lục) **đã được gỡ**. RSC chỉ cần `BACKEND_INTERNAL_URL` (env server) để gọi đúng địa chỉ nội bộ.
- **(app) client:** mọi gọi dữ liệu cá nhân chạy ở client với access token in-memory — **không** đi qua RSC (tránh rò token/nhạy cảm vào server render cache).

### 5.5 Server-state cache (ADR-004)

- TanStack Query cho REST cá nhân: `competencies`, `progress`, `careers` (client side khi đã đăng nhập), `recommendations`, `account`.
- **Nhạy cảm — KHÔNG cache:** query kết quả trắc nghiệm (`/me/assessments/{id}`) dùng `staleTime:0, gcTime:0, retry:false` và **không** persist; component unmount ⇒ xóa khỏi memory. Phản chiếu CP-3 (mỗi đọc = 1 audit; không "đọc lại từ cache").
- **Không optimistic** cho `recommendations/confirm` và `progress` write nhạy (user-flows §5).

---

## 6. Lớp API (typed client — khớp CHÍNH XÁC spec §6 / backend router)

### 6.1 Sinh type từ OpenAPI (workflow)

1. Backend chạy ⇒ `GET /api/v1/openapi.json`.
2. `npx openapi-typescript http://localhost:8000/api/v1/openapi.json -o frontend/types/api.d.ts`.
3. Script npm `gen:api`; chạy trong CI để **fail nếu type lệch** (NFR-20: "OpenAPI schema không đổi ngoài ý muốn" → Gate B). Endpoint helper dùng `paths` type từ `api.d.ts` ⇒ path/method/param/response type-checked.

### 6.2 Bản đồ endpoint (đã xác minh từ `backend/app/*/router.py`)

Base `/api/v1`. **B**=Bearer, **C**=qua consent gate (`require_career_data_consent`), **P**=public content (**anonymous-readable, BE-1** — không cần đăng nhập; published-only), **R:x**=role.

| Nhóm (file `endpoints/`) | Method · Path | Auth | Ghi chú |
|---|---|---|---|
| **auth** | POST `/auth/register` | — | suy `age_band` → consent gate |
| | POST `/auth/login` | — | set refresh cookie |
| | POST `/auth/refresh` | Cookie | xoay token (CP-7) |
| | POST `/auth/logout` | B | thu hồi server-side |
| | GET `/auth/me` | B | session bootstrap |
| **guardians** | POST `/guardians/invite` | B | trẻ <16 mời |
| | POST `/guardians/consent` | B | guardian cấp |
| | POST `/guardians/consent/revoke` | B | thu hồi → CP-2 |
| **competency** | GET `/competencies` | B | cây 12 NL + indicator |
| | GET `/me/progress` | B+**C** | tiến bộ K-A-R |
| | POST `/me/progress/indicators` | B+**C** | tiến K→A→R (CP-8) |
| | POST `/me/progress/dev-phase` | B+**C** | đặt dev_phase (FR-23) |
| **assessments** | GET `/assessments` | B | danh sách instrument |
| | POST `/assessments/{instrument_type}/submit` | B+**C** | nộp → kết quả nhạy cảm |
| | GET `/me/assessments/{result_id}` | B+**C** | xem (audit-logged, no-cache) |
| | DELETE `/me/assessments/{result_id}` | **B only** | xóa được kể cả khi consent đã thu hồi (quyền chủ thể) |
| **careers** | GET `/careers` | **P** | filter `riasec,field,training_level,pathway_type` |
| | GET `/careers/{career_id}` | **P** | chi tiết |
| | GET `/content` | **P** | filter `dieu5_code,competency_code,dev_phase,school_level,status` |
| | GET `/content/{content_id}` | B (R:editor) | mọi status — traceability |
| | POST `/content` | B (R:editor) | tạo draft (FR-90) |
| | POST `/content/{content_id}/versions` | B (R:editor) | publish version mới |
| **reco** | POST `/recommendations` | B+**C** | sinh kèm rationale (CP-6) |
| | GET `/recommendations/{reco_id}` | B (owner/guardian/counselor) | 404 nếu không quyền |
| | POST `/recommendations/{reco_id}/confirm` | B (owner/guardian/counselor) | human-confirm (CP-5) |
| **school** | POST `/school/{school_id}/classes` | B (R:school_admin của trường) | |
| | GET `/school/{school_id}/classes` | B (R:school_admin) | |
| | POST `/school/{school_id}/members` | B (R:school_admin) | gán counselor/HS |
| | GET `/school/{school_id}/students` | B (R:school_admin∨counselor) | roster, de-sensitized |
| | POST `/counseling/sessions` | B (R:counselor) | Tier 1/2/3 (FR-81) |
| | GET `/school/students/{student_id}/progress` | B (R:counselor được phân công) | view đã gỡ nhạy cảm |
| **wellbeing** | POST `/wellbeing/support-request` | B+**C** | NL4 (FR-70/71) |
| | GET `/wellbeing/support-requests` | B+**C** | danh sách của mình |
| **account** | GET `/me/profile` | B | |
| | PATCH `/me` | B | sửa hồ sơ |
| | POST `/me/password` | B | cần mật khẩu hiện tại (FR-91) |
| | GET `/me/export` | B | xuất dữ liệu (Luật 91/2025) |
| | DELETE `/me` | B | soft delete + cửa sổ khôi phục |
| | GET `/me/children/{child_id}/export` | B (R:guardian) | xuất dữ liệu con |
| | DELETE `/me/children/{child_id}` | B (R:guardian) | xóa tài khoản con |
| **ops** | GET `/health`, GET `/ready` | — | dùng cho status page nội bộ |

> **Sai khác cần lưu khi build (đã đối chiếu router thật):** (a) đường submit trắc nghiệm là `/assessments/{instrument_type}/submit` (không phải `/{type}/submit` chung chung — param tên `instrument_type`); (b) spec §6 ghi `GET /school/{id}/students` nhưng router còn có thêm `classes`, `members`, `students/{id}/progress` — client phải bao trùm đủ; (c) `DELETE /me/assessments/{id}` **không** qua consent gate (cố ý, để trẻ thu hồi consent vẫn xóa được dữ liệu) ⇒ UI **không** hiện ConsentGateBanner cho nút Xóa.

### 6.3 Hình dạng client

`lib/api/client.ts` export `apiFetch<T>(path, init)` (gắn Bearer + refresh-on-401). Mỗi `endpoints/<domain>.ts` export hàm typed (vd `submitAssessment(instrumentType, body)`) trả type từ `api.d.ts`. Hook TanStack Query (`useProgress`, `useRecommendation`) bọc các hàm này; query nhạy cảm dùng helper `useSensitiveQuery` (no-cache §5.5).

---

## 7. Ràng buộc UI theo Correctness Properties (CP)

| CP | UI thực thi/phản chiếu thế nào |
|---|---|
| **CP-1** (consent gate <16) | `(app)/layout.tsx` + `ConsentGateBanner`: nếu `age_band==='under_16'` ∧ `account_status!=='active'` ⇒ mọi route/feature `[gate]` (assessments submit, progress, reco, wellbeing) bị chặn mềm, CTA về `/consent`. Nội dung công khai (careers) **vẫn mở**. Backend 403 là tầng cuối. |
| **CP-2** (thu hồi) | Sau khi guardian revoke, query consent invalidate ⇒ UI quay lại trạng thái gate ngay; thao tác xử lý mới bị khóa. `DELETE assessment` vẫn cho phép (không gate). |
| **CP-3** (sensitive access) | `ResultView` gọi API mỗi lần mở (no-cache, no-persist, no client log); `SensitiveBadge` + panel "Ai xem được?". Không hiện payload trắc nghiệm cho counselor. |
| **CP-4** (ownership/role) | Route segment role-gated; client guard điều hướng; UI **không** render link tới dữ liệu ngoài quyền. Khi backend trả 404 (không sở hữu) ⇒ trang "không tìm thấy" trung tính (không lộ tồn tại). |
| **CP-5** (human-in-the-loop) | `RecommendationCard` **không** có "auto-apply"; chỉ `HumanConfirmAction` (Chấp nhận/Từ chối/Để sau) → `confirm`. Gợi ý chưa xác nhận hiển thị rõ "chưa có hiệu lực". Không optimistic. |
| **CP-6** (rationale) | `RationalePanel` là phần **bắt buộc** của card; nếu thiếu `rationale` ⇒ coi là lỗi dữ liệu, hiện trạng thái lỗi (không render thẻ "trống lý do"). |
| **CP-7** (token) | Refresh-on-401: token thu hồi → 401 → đăng xuất; không thử refresh vô hạn. |
| **CP-8** (progress monotonic) | `DepthStepper` chỉ cho thao tác tiến K→A→R; không UI hạ mức; lịch sử hiển thị append-only. |

---

## 8. Kế hoạch a11y (WCAG 2.1 AA — NFR-21)

- **CI gate:** `@axe-core/playwright` chạy trên mọi trang chính (job `a11y` đã chờ sẵn); `eslint-plugin-jsx-a11y` ở lint-frontend. Fail = chặn merge (Gate B).
- **Keyboard-first:** mọi tương tác reachable bằng Tab; focus ring rõ (`--color-primary-600`, ≥3:1); phím tắt user-flows (`/`, `Esc`, `g a`, `g c`, `g p`) qua một `useKeyboardShortcuts` toàn cục, có thể tắt.
- **Focus management:** Radix Dialog/Sheet tự focus-trap + trả focus; điều hướng route đặt focus về `<h1>` (announce trang mới).
- **AssessmentRunner:** `role="group"` + `aria-live="polite"` báo tiến độ; mỗi câu là fieldset/legend; nút Nộp `aria-describedby` nhắc "kết quả là dữ liệu riêng tư".
- **Màu:** toàn bộ cặp text/nền ≥4.5:1 (đồ họa ≥3:1) — đã chú thích §2.1; **không truyền tin chỉ bằng màu** (màu+icon+text).
- **Screen reader tiếng Việt:** `<html lang="vi">`; label/aria-label tiếng Việt tự nhiên (tránh viết tắt khó đọc); `aria-describedby` nối lỗi field (RHF errorMessage). Số/đơn vị đọc đúng (vd "độ sâu K, A, R" có `aria-label` mô tả).
- **Reduced motion:** `prefers-reduced-motion: reduce` ⇒ tắt confetti/slide, chuyển đổi trạng thái tức thì (user-flows §micro-interactions).

---

## 9. Kế hoạch i18n (vi mặc định — NFR-23)

- **Thư viện:** `next-intl` (App Router-native, hỗ trợ RSC + client).
- **Tách 2 loại chuỗi:**
  1. **UI-chrome** (nút, nhãn, lỗi, điều hướng) → message catalog `messages/vi.json` (key phân theo feature: `auth.*`, `consent.*`, `assessment.*`...). Đây là phần i18n của FE.
  2. **Nội dung versioned** (CareerProfile, ContentItem, Indicator `statement_vi`) → **đến từ backend** (đã versioned theo `school_level`, FR-90/NFR-23). FE **không** dịch nội dung này; chỉ render theo locale/`school_level` mà API trả.
- **Cấu trúc sẵn locale mới:** `messages/<locale>.json`; routing locale để ngỏ (`vi` default, không prefix; thêm `/en` sau mà không phá route). Định dạng ngày/số qua `Intl` với locale `vi-VN`.
- **Tiếng Việt an toàn:** font Be Vietnam Pro (§2.2); không hardcode chuỗi trong component (lint rule cấm literal text trong JSX ở `features/`).

---

## 10. Bản đồ Màn hình ↔ Luồng người dùng (theo actor)

| Luồng (user-flows / FR) | Actor | Route/Screen | Endpoint chính | CP |
|---|---|---|---|---|
| L1 Onboarding + cổng tuổi/consent | Anonymous→Student | `/register`,`/login`,`/consent` | register, login, refresh, guardians/invite | CP-1 |
| L1 Guardian xác nhận | Guardian | `/guardian/consents` | guardians/consent[/revoke] | CP-1/2 |
| L2 Làm trắc nghiệm | Student(consent) | `/assessments`,`/assessments/[type]`,`/assessments/results/[id]` | assessments, .../submit, /me/assessments/{id} | CP-1/3 |
| L3 Khám phá nghề | Anonymous/Student | `(public)/careers`,`/careers/[id]` | careers, careers/{id}, content | — (public) |
| L4 Tiến bộ năng lực | Student(consent) | `/progress` | competencies, /me/progress[/indicators,/dev-phase] | CP-8 |
| L5 Gợi ý (human-in-loop) | Student/Guardian/Counselor | `/recommendations`,`/recommendations/[id]` | recommendations, .../confirm | CP-5/6 |
| Wellbeing NL4 | Student(consent) | `/wellbeing` | wellbeing/support-request[s] | CP-1 |
| L6 Counselor 3 tầng | Counselor | `/counselor/students[/id]`,`/counselor/sessions` | school/{id}/students, students/{id}/progress, counseling/sessions | CP-3/4 |
| Quản trị trường | School admin | `/school-admin/classes`,`/school-admin/members` | school/{id}/classes, members | CP-4 |
| Quản trị nội dung | Content editor | `/editor/content[/id]` | content, content/{id}/versions | FR-90 |
| Quyền chủ thể dữ liệu | Student/Guardian | `/account/data`,`/account/children` | me/export, DELETE /me, children/{id}/export·DELETE | CP-4 |
| Tài khoản & bảo mật | Mọi user | `/account/profile`,`/account/security` | me/profile, PATCH /me, me/password | — |

---

## 11. Kế hoạch Slice Frontend (gương kỷ luật slice backend)

> Mỗi slice là một PR khép kín qua Gate B (lint+test+E2E+a11y). **F1 là nền móng** (auth+consent) vì mọi feature `[gate]` phụ thuộc nó.

- **F1 — Nền móng + Auth + Consent gate.** Khởi tạo `frontend/` (Next App Router, TS strict, Tailwind+shadcn tokens §2, `package-lock.json` để bật CI gate), `apiFetch`+refresh-on-401, SessionProvider, AppShell, `/register`·`/login`·`/consent`·`GuardianInviteForm`, route guards. Sinh `api.d.ts` lần đầu. (FR-01..06, CP-1/2/7)
- **F2 — Public content (RSC) + Thư viện nghề.** `(public)/careers`,`/careers/[id]`,`/content`; filter; SEO; RSC fetch ẩn danh (BE-1, không token — §5.4). (FR-30/32, Điều 5a)
- **F3 — Trắc nghiệm + dữ liệu nhạy cảm.** `AssessmentRunner`, `ResultView`+`SensitiveBadge`, no-cache sensitive query, xuất/xóa. (FR-10..15, CP-3)
- **F4 — Tiến bộ năng lực K-A-R.** `CompetencyTree`+`KARProgressViz`+`DepthStepper`; dev-phase. (FR-20..24, CP-8)
- **F5 — Gợi ý + Human-in-the-loop.** `RecommendationCard`+`RationalePanel`+`HumanConfirmAction`. (FR-60..63, CP-5/6)
- **F6 — Wellbeing (NL4).** support-request + đường dẫn counselor. (FR-70/71)
- **F7 — Counselor console (de-sensitized).** roster, student progress, sessions Tier 1/2/3. (FR-80..83, CP-3/4)
- **F8 — School admin + Content editor.** classes/members; content CRUD + versions. (FR-80, FR-90)
- **F9 — Account & quyền chủ thể dữ liệu + i18n hoàn thiện.** profile/security/data/children; catalog vi đầy đủ; a11y sweep cuối. (FR-91/92, NFR-21/23)

---

## Phụ lục — Phụ thuộc liên-đội cần chốt

1. ~~**Token đọc-công-khai** cho RSC gọi `/careers`·`/content`~~ — **ĐÃ GIẢI QUYẾT (BE-1):** các GET công khai nay anonymous-readable; RSC fetch ẩn danh, không cần token. Phụ thuộc này đóng.
2. **OpenAPI 3.1 ổn định** tại `/api/v1/openapi.json` để `openapi-typescript` sinh `api.d.ts` (Gate B so khớp drift).
3. **Hình dạng `roles`** trong `/auth/me`/JWT để client role-guard (deps trả `roles` claim + `is_content_editor`; xác nhận các role string: `student|guardian|counselor|school_admin|content_editor|working`).
