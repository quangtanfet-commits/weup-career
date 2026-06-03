# Lessons Learned — WeUp Career

Bài học đã **trả giá để có**. Mỗi mục: bối cảnh → vì sao → cách áp dụng.
Rút từ bộ nhớ dự án và sự cố thực tế.

## L-01 · Domain placeholder gây hiểu sai

- **Bối cảnh:** repo khởi đầu mang dấu vết "Todo app"; đây thực ra là nền tảng
  Hướng nghiệp.
- **Vì sao:** scaffold/placeholder không được dọn sớm.
- **Áp dụng:** neo domain + pháp lý vào `spec.md` và KB ngay từ đầu; nghi ngờ
  mọi đặc tả "chung chung".

## L-02 · RSC static prerender bake dữ liệu rỗng

- **Bối cảnh:** public page fetch backend; Next build (không backend) prerender
  tĩnh → danh sách rỗng → E2E locator rỗng.
- **Áp dụng:** public RSC page fetch dữ liệu động phải `export const dynamic =
  "force-dynamic"`.

## L-03 · Prettier không nằm trong `lint`

- **Bối cảnh:** CI có job `format:check` riêng; `npm run lint` không gọi
  Prettier → CI đỏ dù lint xanh.
- **Áp dụng:** chạy `npm run format` (hoặc `format:check`) trước khi báo xong FE.

## L-04 · CORS dev-only chặn cross-origin trong e2e

- **Bối cảnh:** browser ở `:3100`/`:80` gọi thẳng backend `:8000` bị CORS chặn.
- **Áp dụng:** e2e dùng prod build same-origin qua Next rewrite (`E2E_PROXY_API=1`);
  với truy cập thủ công thì set `CORS_ORIGINS` runtime.

## L-05 · Seed DB lệch sau migration

- **Bối cảnh:** `backend/data/app.db` thiếu bảng/cột N-3 → register 500 khi
  INSERT token.
- **Áp dụng:** copy seed → file run-scoped rồi `alembic upgrade head` trên bản
  copy; KHÔNG mutate DB gốc của dev. Cần một script seed+migrate chuẩn hoá.

## L-06 · Email special-use TLD bị từ chối

- **Bối cảnh:** `admin@weup.local` fail `EmailStr` (".local" reserved) → login 422.
- **Áp dụng:** dùng domain hợp lệ (vd `example.com`) cho tài khoản test/seed.

## L-07 · uvicorn factory entrypoint

- **Bối cảnh:** `app.main:app` không tồn tại; chỉ có factory `get_app()`.
- **Áp dụng:** luôn `uvicorn app.main:get_app --factory`. Đã sửa ở `6b181bb`.

## L-08 · `uv run uvicorn` fork tiến trình con giữ port

- **Bối cảnh:** kill wrapper PID để lại child uvicorn ôm `:8000`/`:443`.
- **Áp dụng:** chạy dưới `setsid`, lấy PGID, teardown `kill -- -$PGID`; hoặc kill
  theo listener PID từ `ss -ltnp`.

## L-09 · Quyết định runtime "bay hơi"

- **Bối cảnh:** FE `:80`, CORS, user admin, HTTPS `:443` chỉ sống trong tiến
  trình + chat; restart container là mất.
- **Áp dụng:** codify vào `scripts/` + `.env.dev` + seed script.

## L-10 · Major bump coupling ẩn

- **Bối cảnh:** bump Next 16 kéo theo ràng buộc next-intl ↔ eslint.
- **Áp dụng:** bump cô lập từng lát, đọc release notes coupling trước.

## L-11 · Teardown async flake (môi trường, không phải regression)

- **Bối cảnh:** full-suite cục bộ đôi khi "1 error" ở teardown async; CI luôn xanh.
- **Áp dụng:** đừng đuổi theo như regression; xác nhận trên CI trước khi nghi ngờ code.
