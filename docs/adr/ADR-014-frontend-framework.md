# ADR-014: Frontend Framework — Next.js 15 (App Router) thay cho React+Vite SPA

**Status:** Accepted
**Date:** 2026-05-30
**Deciders:** Engineering Team
**Supersedes:** Phần Frontend của [ADR-001](ADR-001-framework-selection.md) (React 18 + Vite 5, CSR-only SPA). Backend (FastAPI) của ADR-001 **giữ nguyên**.
**Liên quan:** [ADR-004](ADR-004-state-management.md) (TanStack Query v5 + Zustand — **giữ nguyên**), [docs/frontend/architecture.md](../frontend/architecture.md) (blueprint hiện thực), BE-1 (public reads anonymous-readable).

---

## Context

ADR-001 (2026-05-27) chọn **React 18 + TypeScript 5 + Vite 5** dạng **SPA CSR-only**, và **bác bỏ Next.js** với lý do *"SSR thêm phức tạp vận hành… overkill cho một SPA chỉ-đăng-nhập"*. Lý do đó đúng với giả định ban đầu: toàn bộ ứng dụng nằm sau đăng nhập.

Giả định đó **không còn đúng** với quy mô thực của WeUp Career:

1. **Có một nửa public, SEO-quan trọng.** Thư viện nghề (Điều 5a) + nội dung học tập 5c/5d là **thông tin công khai theo luật**, và là kênh tiếp cận chính cho học sinh/phụ huynh tìm kiếm trên Google. Một nền tảng hướng nghiệp **quốc gia** mà các trang nghề không index được là hỏng mục tiêu tiếp cận.
2. **BE-1 đã biến các read này thành anonymous-readable thật.** `GET /careers`, `/careers/{id}`, `/content`, `/content/{id}` nay đọc được **không cần đăng nhập** (`optional_current_user`), bất biến *published-only*. Đây chính là điều kiện kỹ thuật để render server-side công khai — không cần token, không cần workaround.
3. **Tách public/sensitive là yêu cầu kiến trúc, không phải tối ưu.** Dữ liệu nhạy cảm (kết quả trắc nghiệm `is_sensitive=true`) **không** được lọt vào server render cache; nội dung công khai thì **nên** render server-side để SEO + tải nhanh. Một SPA CSR-only không phân tách được hai chế độ này ở tầng framework — phải tự dựng SSR thủ công, tức là tái phát minh Next.js kém hơn.

`docs/frontend/architecture.md` (blueprint, v1.0.0) đã **tiến hóa** quyết định sang Next.js và forward-reference ADR này. ADR-014 chính thức hóa quyết định để các tài liệu đồng nhất.

---

## Decision

**Dùng Next.js 15 (App Router) + React 19 + TypeScript 5 (`strict`) cho toàn bộ frontend `frontend/`.**

- **Public routes** (`(public)/careers`, `/careers/[id]`, `/content/[id]`, trang chủ) = **React Server Components** (RSC), render server-side với ISR/revalidate. Gọi backend anonymous (BE-1) — **không token, không qua TanStack Query**.
- **Authenticated routes** (`(app)/*`, `(auth)/*`) = **Client Components**, access token in-memory, dữ liệu cá nhân **không** đi qua server render (tránh rò token/nhạy cảm vào cache).
- **Giữ nguyên** mọi quyết định lớp client của ADR-004: TanStack Query v5 (server-state REST cá nhân, **tắt cache** cho query nhạy cảm) + Zustand (session/role + UI prefs).
- **Giữ nguyên** Vitest + Testing Library (chạy native với Next.js; không phụ thuộc Vite runtime của app) và Playwright E2E.

---

## Alternatives Considered

| Phương án | Verdict |
|---|---|
| **React 18 + Vite 5 SPA (ADR-001 nguyên bản)** | ❌ Không SEO được nửa public Điều 5a; phải tự dựng SSR/pre-render thủ công cho trang nghề → tái phát minh Next.js kém hơn. Bundle CSR-only làm trang công khai tải chậm trên mạng yếu (đối tượng học sinh vùng xa). |
| **Vite SPA + pre-render tĩnh (vite-plugin-ssg) cho phần public** | ❌ Nội dung nghề/learning là **versioned theo `school_level` và cập nhật bởi content editor** (FR-90) → cần ISR/revalidate động, không hợp pre-render build-time tĩnh. Hai cơ chế render rời rạc trong một repo = phức tạp hơn một framework thống nhất. |
| **Next.js `output: export` (static export, không Node runtime)** | ❌ Vô hiệu hóa RSC server-side + ISR — đúng thứ ta cần cho SEO + nội dung versioned. Mất luôn streaming. |
| **Remix / [CRED_36CB66A5]** | ⚠️ Khả thi về kỹ thuật (SSR tốt) nhưng hệ sinh thái nhỏ hơn, pool tuyển dụng VN nhỏ hơn React/Next; không đủ lợi thế để bỏ chuẩn React-team đã định ở ADR-001. |
| **Next.js 15 App Router + React 19 (CHỌN)** | ✅ Một framework xử lý cả hai chế độ ở tầng kiến trúc: RSC cho public SEO, client cho luồng nhạy cảm. App Router map thẳng IA theo vai trò (layout lồng nhau). Vẫn là React/TS → giữ nguyên pool tuyển + ADR-004 + Vitest. |

---

## Consequences

**Tích cực:**
- Trang nghề/nội dung Điều 5a index được trên Google, tải nhanh (server-render + streaming), không kéo theo JS bundle của khu vực đăng nhập.
- Ranh giới public/sensitive được framework **bắt buộc** ở tầng route segment (`(public)` RSC vs `(app)` client), không phải kỷ luật thủ công.
- `openapi-typescript` drift gate (BE-2) + ADR-004 + chiến lược test **không đổi**.

**Chi phí / [CRED_8B85B1FF] buộc mới:**
- **Cần Node.js runtime cho frontend ở production** (RSC public routes), không còn là static-nginx + `index.html` fallback đơn thuần. Topology: container Node (`next start`) sau nginx reverse proxy. → cập nhật [deployment.md](../architecture/deployment.md) + [ADR-006](ADR-006-docker-strategy.md).
- Dev server là **Next.js dev (`next dev`)**, không phải Vite dev `:5173`.
- **Bất biến nhạy cảm:** tuyệt đối không fetch dữ liệu `is_sensitive` trong RSC/server context (chỉ client, in-memory). Đây là quy tắc review bắt buộc, phản chiếu CP-3.
- React 19 (Next 15) — kiểm thư viện bên thứ ba (Recharts, Radix/shadcn, RHF) tương thích React 19 trước khi pin phiên bản ở F1.

**Đã lỗi thời (xóa khỏi tài liệu):** giả định "public reads là Bearer-only → cần `PUBLIC_READ_TOKEN`" trong architecture.md §5.4/Appendix. BE-1 đã làm các read này anonymous thật ⇒ RSC fetch ẩn danh trực tiếp, **không cần service token đọc-công-khai**. Phụ thuộc liên-đội đó được gỡ.
